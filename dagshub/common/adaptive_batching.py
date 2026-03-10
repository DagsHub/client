import logging
import time
from dataclasses import dataclass
from types import SimpleNamespace
import itertools
from typing import Callable, Iterable, List, Optional, Sized, TypeVar

import rich.progress
from tenacity import wait_exponential

from dagshub.common.rich_util import get_rich_progress

logger = logging.getLogger(__name__)

T = TypeVar("T")

MIN_TARGET_BATCH_TIME_SECONDS = 0.01
BATCH_GROWTH_FACTOR = 10
RETRY_BACKOFF_BASE_SECONDS = 0.25
RETRY_BACKOFF_MAX_SECONDS = 4.0

_retry_delay_strategy = wait_exponential(
    multiplier=RETRY_BACKOFF_BASE_SECONDS,
    min=RETRY_BACKOFF_BASE_SECONDS,
    max=RETRY_BACKOFF_MAX_SECONDS,
)


@dataclass(frozen=True)
class AdaptiveBatchConfig:
    max_batch_size: int
    min_batch_size: int
    initial_batch_size: int
    target_batch_time_seconds: float

    @classmethod
    def from_values(
        cls,
        max_batch_size: Optional[int] = None,
        min_batch_size: Optional[int] = None,
        initial_batch_size: Optional[int] = None,
        target_batch_time_seconds: Optional[float] = None,
    ) -> "AdaptiveBatchConfig":
        import dagshub.common.config as dgs_config

        if max_batch_size is None:
            max_batch_size = dgs_config.dataengine_metadata_upload_batch_size
        if min_batch_size is None:
            min_batch_size = dgs_config.dataengine_metadata_upload_batch_size_min
        if initial_batch_size is None:
            initial_batch_size = dgs_config.dataengine_metadata_upload_batch_size_initial
        if target_batch_time_seconds is None:
            target_batch_time_seconds = dgs_config.dataengine_metadata_upload_target_batch_time_seconds

        normalized_max_batch_size = max(1, max_batch_size)
        normalized_min_batch_size = max(1, min(min_batch_size, normalized_max_batch_size))
        normalized_initial_batch_size = max(
            normalized_min_batch_size,
            min(initial_batch_size, normalized_max_batch_size),
        )
        normalized_target_batch_time_seconds = max(target_batch_time_seconds, MIN_TARGET_BATCH_TIME_SECONDS)
        return cls(
            max_batch_size=normalized_max_batch_size,
            min_batch_size=normalized_min_batch_size,
            initial_batch_size=normalized_initial_batch_size,
            target_batch_time_seconds=normalized_target_batch_time_seconds,
        )


def _midpoint(lower_bound: int, upper_bound: int) -> int:
    return lower_bound + max(1, (upper_bound - lower_bound) // 2)


def _next_batch_after_success(
    batch_size: int,
    config: AdaptiveBatchConfig,
    bad_batch_size: Optional[int],
) -> int:
    if bad_batch_size is not None and batch_size < bad_batch_size:
        next_batch_size = _midpoint(batch_size, bad_batch_size)
        next_batch_size = min(next_batch_size, bad_batch_size - 1)
    else:
        next_batch_size = batch_size * BATCH_GROWTH_FACTOR

    next_batch_size = min(config.max_batch_size, next_batch_size)
    if next_batch_size <= batch_size and batch_size < config.max_batch_size:
        next_batch_size = min(config.max_batch_size, batch_size + 1)
        if bad_batch_size is not None:
            next_batch_size = min(next_batch_size, bad_batch_size - 1)

    return max(config.min_batch_size, next_batch_size)


def _next_batch_after_retryable_failure(
    batch_size: int,
    config: AdaptiveBatchConfig,
    good_batch_size: Optional[int],
    bad_batch_size: Optional[int],
) -> int:
    if batch_size <= config.min_batch_size:
        return config.min_batch_size

    upper_bound = min(batch_size, bad_batch_size) if bad_batch_size is not None else batch_size
    if good_batch_size is not None and good_batch_size < upper_bound:
        next_batch_size = _midpoint(good_batch_size, upper_bound)
    else:
        next_batch_size = batch_size // 2

    next_batch_size = min(next_batch_size, upper_bound - 1, batch_size - 1, config.max_batch_size)
    return max(config.min_batch_size, next_batch_size)


def _get_retry_delay_seconds(consecutive_retryable_failures: int) -> float:
    retry_state = SimpleNamespace(attempt_number=max(1, consecutive_retryable_failures))
    return float(_retry_delay_strategy(retry_state))


class AdaptiveBatcher:
    """Sends items in adaptively-sized batches, growing on success and shrinking on failure."""

    def __init__(
        self,
        is_retryable: Callable[[Exception], bool],
        config: Optional[AdaptiveBatchConfig] = None,
        progress_label: str = "Uploading",
    ):
        self._config = config if config is not None else AdaptiveBatchConfig.from_values()
        self._is_retryable = is_retryable
        self._progress_label = progress_label

    def run(self, items: Iterable[T], operation: Callable[[List[T]], None]) -> None:
        total: Optional[int] = len(items) if isinstance(items, Sized) else None
        if total == 0:
            return

        config = self._config
        current_batch_size = config.initial_batch_size
        it = iter(items)
        pending: List[T] = []

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task(
            f"{self._progress_label} (adaptive batch {config.min_batch_size}-{config.max_batch_size})...",
            total=total,
        )

        last_good_batch_size: Optional[int] = None
        last_bad_batch_size: Optional[int] = None
        consecutive_retryable_failures = 0
        processed = 0

        with progress:
            while True:
                # Draw from pending (failed-batch leftovers) first, then the source iterator
                batch = pending[:current_batch_size]
                pending = pending[current_batch_size:]
                if len(batch) < current_batch_size:
                    batch.extend(itertools.islice(it, current_batch_size - len(batch)))
                if not batch:
                    break
                batch_size = len(batch)

                progress.update(
                    total_task,
                    description=f"{self._progress_label} (batch size {batch_size})...",
                )
                logger.debug(f"{self._progress_label}: {batch_size} entries...")

                start_time = time.monotonic()
                try:
                    operation(batch)
                except Exception as exc:
                    if not self._is_retryable(exc):
                        logger.error(
                            f"{self._progress_label} failed with a non-retryable error; aborting.",
                            exc_info=True,
                        )
                        raise

                    if batch_size <= config.min_batch_size:
                        logger.error(
                            f"{self._progress_label} failed at minimum batch size ({batch_size}); aborting.",
                            exc_info=True,
                        )
                        raise

                    consecutive_retryable_failures += 1
                    time.sleep(_get_retry_delay_seconds(consecutive_retryable_failures))

                    last_bad_batch_size = (
                        batch_size if last_bad_batch_size is None else min(last_bad_batch_size, batch_size)
                    )
                    current_batch_size = _next_batch_after_retryable_failure(
                        batch_size, config, last_good_batch_size, last_bad_batch_size
                    )
                    logger.warning(
                        f"{self._progress_label} failed for batch size {batch_size} "
                        f"({exc.__class__.__name__}: {exc}). Retrying with batch size {current_batch_size}."
                    )
                    # Re-queue the failed batch items for retry with smaller batch size
                    pending = batch + pending
                    continue

                elapsed = time.monotonic() - start_time
                consecutive_retryable_failures = 0
                processed += batch_size
                progress.update(total_task, advance=batch_size)

                if elapsed <= config.target_batch_time_seconds:
                    last_good_batch_size = (
                        batch_size if last_good_batch_size is None else max(last_good_batch_size, batch_size)
                    )
                    current_batch_size = _next_batch_after_success(batch_size, config, last_bad_batch_size)
                else:
                    last_bad_batch_size = (
                        batch_size if last_bad_batch_size is None else min(last_bad_batch_size, batch_size)
                    )
                    current_batch_size = _next_batch_after_retryable_failure(
                        batch_size, config, last_good_batch_size, last_bad_batch_size
                    )

            progress.update(total_task, completed=processed, total=processed, refresh=True)
