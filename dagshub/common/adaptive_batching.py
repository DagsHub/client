import itertools
import logging
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sized, TypeVar

import rich.progress

import dagshub.common.config as dgs_config
from dagshub.common.rich_util import get_rich_progress

logger = logging.getLogger(__name__)

T = TypeVar("T")

MIN_TARGET_BATCH_TIME_SECONDS = 0.01


@dataclass
class AdaptiveBatchConfig:
    max_batch_size: int
    min_batch_size: int
    initial_batch_size: int
    target_batch_time_seconds: float
    batch_growth_factor: int
    retry_backoff_base_seconds: float
    retry_backoff_max_seconds: float

    @classmethod
    def from_values(
        cls,
        max_batch_size: Optional[int] = None,
        min_batch_size: Optional[int] = None,
        initial_batch_size: Optional[int] = None,
        target_batch_time_seconds: Optional[float] = None,
        batch_growth_factor: Optional[int] = None,
        retry_backoff_base_seconds: Optional[float] = None,
        retry_backoff_max_seconds: Optional[float] = None,
    ) -> "AdaptiveBatchConfig":
        if max_batch_size is None:
            max_batch_size = dgs_config.dataengine_metadata_upload_batch_size_max
        if min_batch_size is None:
            min_batch_size = dgs_config.dataengine_metadata_upload_batch_size_min
        if initial_batch_size is None:
            initial_batch_size = dgs_config.dataengine_metadata_upload_batch_size_initial
        if target_batch_time_seconds is None:
            target_batch_time_seconds = dgs_config.dataengine_metadata_upload_target_batch_time_seconds
        if batch_growth_factor is None:
            batch_growth_factor = dgs_config.adaptive_batch_growth_factor
        if retry_backoff_base_seconds is None:
            retry_backoff_base_seconds = dgs_config.adaptive_batch_retry_backoff_base_seconds
        if retry_backoff_max_seconds is None:
            retry_backoff_max_seconds = dgs_config.adaptive_batch_retry_backoff_max_seconds

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
            batch_growth_factor=max(2, batch_growth_factor),
            retry_backoff_base_seconds=max(0.0, retry_backoff_base_seconds),
            retry_backoff_max_seconds=max(0.0, retry_backoff_max_seconds),
        )


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def _next_batch_after_success(
    batch_size: int,
    config: AdaptiveBatchConfig,
    bad_batch_size: Optional[int],
) -> int:
    """Pick the next batch size after a fast successful batch.

    Strategy:
    - If we have a previous slow/failing size, binary-search toward it as a soft upper hint.
    - Otherwise, multiply by the growth factor.
    - If the midpoint rounds back to the current size, advance by 1 so the search
      keeps moving. That may revisit the previous failing size, because these hints
      are soft signals rather than permanent bans.
    """
    if bad_batch_size is not None and batch_size < bad_batch_size:
        # Binary search: try the midpoint between current and the soft upper hint.
        candidate = (batch_size + bad_batch_size) // 2
    else:
        # No upper hint (or we've already reached it): grow aggressively.
        candidate = batch_size * config.batch_growth_factor

    # Always make forward progress in the search.
    candidate = max(candidate, batch_size + 1)

    return _clamp(candidate, config.min_batch_size, config.max_batch_size)


def _next_batch_after_retryable_failure(
    batch_size: int,
    config: AdaptiveBatchConfig,
    good_batch_size: Optional[int],
    bad_batch_size: Optional[int],
) -> int:
    """Pick the next batch size after a failed or slow batch.

    Strategy:
    - If we have a known-good lower bound, binary-search between it and the
      failing size.
    - Otherwise, probe the midpoint between config.min_batch_size and the
      largest allowed size below the failing batch.
    - Must be strictly less than the current size (so we converge downward).
    """
    if batch_size <= config.min_batch_size:
        return config.min_batch_size

    ceiling = batch_size - 1  # must shrink
    if bad_batch_size is not None:
        ceiling = min(ceiling, bad_batch_size - 1)

    if good_batch_size is not None and good_batch_size < ceiling:
        # Binary search: try the midpoint between good and failing
        candidate = (good_batch_size + ceiling) // 2
    else:
        # No good lower bound — probe midpoint of the valid range
        candidate = (config.min_batch_size + ceiling) // 2

    return _clamp(candidate, config.min_batch_size, ceiling)


def _get_retry_delay_seconds(consecutive_retryable_failures: int, config: AdaptiveBatchConfig) -> float:
    if config.retry_backoff_base_seconds <= 0.0 or config.retry_backoff_max_seconds <= 0.0:
        return 0.0

    attempt_number = max(1, consecutive_retryable_failures)
    delay = config.retry_backoff_base_seconds * (2 ** (attempt_number - 1))
    return min(delay, config.retry_backoff_max_seconds)


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
        # Consume the source iterable incrementally across retries and successes.
        it = iter(items)
        pending: List[T] = []

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task(f"{self._progress_label}...", total=total)

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

                    exhausted_shrink = batch_size <= config.min_batch_size and batch_size == current_batch_size
                    if exhausted_shrink:
                        logger.error(
                            f"{self._progress_label} failed at minimum batch size ({batch_size}); aborting.",
                            exc_info=True,
                        )
                        raise

                    consecutive_retryable_failures += 1
                    time.sleep(_get_retry_delay_seconds(consecutive_retryable_failures, config))

                    last_bad_batch_size = (
                        batch_size if last_bad_batch_size is None else min(last_bad_batch_size, batch_size)
                    )
                    if last_good_batch_size is not None and last_good_batch_size >= last_bad_batch_size:
                        last_good_batch_size = None
                    if batch_size < config.min_batch_size:
                        # Tail batches below configured min cannot be split further.
                        # Retry that exact size once before treating it as exhausted.
                        current_batch_size = batch_size
                    else:
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

                # On success.
                elapsed = time.monotonic() - start_time
                consecutive_retryable_failures = 0
                processed += batch_size
                progress.update(total_task, advance=batch_size)

                if elapsed <= config.target_batch_time_seconds:
                    last_good_batch_size = (
                        batch_size if last_good_batch_size is None else max(last_good_batch_size, batch_size)
                    )
                    # Clear the soft upper hint if we succeeded fast at or above it.
                    if last_bad_batch_size is not None and batch_size >= last_bad_batch_size:
                        last_bad_batch_size = None
                    current_batch_size = _next_batch_after_success(batch_size, config, last_bad_batch_size)
                else:
                    logger.debug(
                        f"{self._progress_label} batch size {batch_size} took {elapsed:.2f}s "
                        f"(target {config.target_batch_time_seconds:.2f}s); shrinking."
                    )
                    last_bad_batch_size = (
                        batch_size if last_bad_batch_size is None else min(last_bad_batch_size, batch_size)
                    )
                    if last_good_batch_size is not None and last_good_batch_size >= last_bad_batch_size:
                        last_good_batch_size = None
                    current_batch_size = _next_batch_after_retryable_failure(
                        batch_size, config, last_good_batch_size, last_bad_batch_size
                    )

            progress.update(total_task, completed=processed, total=processed, refresh=True)
