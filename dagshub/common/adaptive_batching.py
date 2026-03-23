import itertools
import logging
import math
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sized, Tuple, TypeVar

import rich.progress

import dagshub.common.config as dgs_config
from dagshub.common.rich_util import get_rich_progress

logger = logging.getLogger(__name__)

T = TypeVar("T")

MIN_TARGET_BATCH_TIME_SECONDS = 0.01
SOFT_UPPER_LIMIT_MIN_STEP_FRACTION = 0.05
SOFT_UPPER_LIMIT_RETRY_AFTER_SUCCESSES = 3

# Overall strategy:
# - Grow aggressively on fast successes until we hit a slow or failing batch.
# - A slow or failing batch becomes last_bad_batch_size, and a fast batch becomes
#   last_fast_batch_size.
# - last_bad_batch_size acts as a soft_upper_limit while the gap to
#   last_fast_batch_size is still meaningful, and we probe within that range.
# - Once that gap is below the search resolution, hold the current fast batch size
#   instead of micro-searching.
# - Several consecutive fast batches near last_bad_batch_size trigger one more
#   probe at soft_upper_limit, since the earlier failure may have been transient.


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
    soft_upper_limit: Optional[int],
) -> int:
    """Pick the next batch size after a fast successful batch.

    Strategy:
    - If we have a previous slow/failing size, binary-search toward it as a soft upper hint.
    - Otherwise, multiply by the growth factor.
    """
    if soft_upper_limit is not None and batch_size < soft_upper_limit:
        # Binary search: try the midpoint between current and the soft upper limit.
        candidate = (batch_size + soft_upper_limit) // 2
    else:
        # No upper hint (or we've already reached it): grow aggressively.
        candidate = batch_size * config.batch_growth_factor

    return _clamp(candidate, config.min_batch_size, config.max_batch_size)


def _next_batch_after_retryable_failure(
    batch_size: int,
    config: AdaptiveBatchConfig,
    last_fast_batch_size: Optional[int],
    soft_upper_limit: Optional[int],
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
    if soft_upper_limit is not None:
        ceiling = min(ceiling, soft_upper_limit - 1)

    if last_fast_batch_size is not None and last_fast_batch_size < ceiling:
        # Binary search: try the midpoint between good and failing
        candidate = (last_fast_batch_size + ceiling) // 2
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


def _min_step_size(soft_upper_limit: int) -> int:
    return max(1, math.ceil(soft_upper_limit * SOFT_UPPER_LIMIT_MIN_STEP_FRACTION))


def _is_next_step_above_limit(batch_size: int, soft_upper_limit: Optional[int]) -> bool:
    if soft_upper_limit is None or batch_size >= soft_upper_limit:
        return False

    return soft_upper_limit - batch_size <= _min_step_size(soft_upper_limit)


def _update_bounds_after_bad_batch(
    batch_size: int,
    last_fast_batch_size: Optional[int],
    last_bad_batch_size: Optional[int],
) -> Tuple[Optional[int], int]:
    updated_last_bad_batch_size = batch_size if last_bad_batch_size is None else min(last_bad_batch_size, batch_size)
    if last_fast_batch_size is not None and last_fast_batch_size >= updated_last_bad_batch_size:
        last_fast_batch_size = None
    return last_fast_batch_size, updated_last_bad_batch_size


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
        desired_batch_size = config.initial_batch_size
        # Consume the source iterable incrementally across retries and successes.
        it = iter(items)
        pending: List[T] = []

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task(f"{self._progress_label}...", total=total)

        last_fast_batch_size: Optional[int] = None
        last_bad_batch_size: Optional[int] = None
        consecutive_retryable_failures = 0
        consecutive_fast_successes_near_upper_limit = 0
        processed = 0

        with progress:
            while True:
                # Draw from pending (failed-batch leftovers) first, then the source iterator
                batch = pending[:desired_batch_size]
                pending = pending[desired_batch_size:]
                if len(batch) < desired_batch_size:
                    batch.extend(itertools.islice(it, desired_batch_size - len(batch)))
                if not batch:
                    break
                actual_batch_size = len(batch)

                progress.update(total_task, description=f"{self._progress_label} (batch size: {actual_batch_size})...")
                logger.debug(f"{self._progress_label}: {actual_batch_size} entries...")

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

                    is_short_tail_batch = (
                        actual_batch_size <= config.min_batch_size and actual_batch_size < desired_batch_size
                    )
                    if not is_short_tail_batch and actual_batch_size <= config.min_batch_size:
                        logger.error(
                            f"{self._progress_label} failed at minimum batch size ({actual_batch_size}); aborting.",
                            exc_info=True,
                        )
                        raise

                    consecutive_fast_successes_near_upper_limit = 0

                    # Exponential backoff
                    consecutive_retryable_failures += 1
                    time.sleep(_get_retry_delay_seconds(consecutive_retryable_failures, config))

                    last_fast_batch_size, last_bad_batch_size = _update_bounds_after_bad_batch(
                        actual_batch_size, last_fast_batch_size, last_bad_batch_size
                    )
                    if is_short_tail_batch:
                        # A naturally short tail batch cannot be shrunk further in a useful way.
                        # Retry that exact size once before treating it as exhausted.
                        desired_batch_size = actual_batch_size
                    else:
                        # Binary search downwards
                        desired_batch_size = _next_batch_after_retryable_failure(
                            actual_batch_size, config, last_fast_batch_size, last_bad_batch_size
                        )
                    logger.warning(
                        f"{self._progress_label} failed for batch size {actual_batch_size} "
                        f"({exc.__class__.__name__}: {exc}). Retrying with batch size {desired_batch_size}."
                    )
                    # Re-queue the failed batch items for retry with smaller batch size
                    pending = batch + pending
                    continue

                # On success.
                elapsed = time.monotonic() - start_time
                consecutive_retryable_failures = 0
                processed += actual_batch_size
                progress.update(total_task, advance=actual_batch_size)

                if elapsed <= config.target_batch_time_seconds:
                    if last_fast_batch_size is None or actual_batch_size > last_fast_batch_size:
                        last_fast_batch_size = actual_batch_size
                    if last_bad_batch_size is not None and actual_batch_size >= last_bad_batch_size:
                        # A fast success at the upper limit means the last_bad_batch_size is stale.
                        # We can resume unconstrained growth.
                        last_bad_batch_size = None
                        consecutive_fast_successes_near_upper_limit = 0
                        desired_batch_size = _next_batch_after_success(
                            actual_batch_size, config, last_bad_batch_size
                        )
                    elif _is_next_step_above_limit(actual_batch_size, last_bad_batch_size):
                        # Once the gap is smaller than our useful search resolution,
                        # hold the current known-good size and only re-probe the hint
                        # after a few stable fast successes.
                        consecutive_fast_successes_near_upper_limit += 1
                        if consecutive_fast_successes_near_upper_limit >= SOFT_UPPER_LIMIT_RETRY_AFTER_SUCCESSES:
                            # We've had enough stable fast successes to re-probe the last_bad_batch_size.
                            desired_batch_size = last_bad_batch_size
                            consecutive_fast_successes_near_upper_limit = 0
                        else:
                            # Hold current size for one more iteration
                            desired_batch_size = actual_batch_size
                    else:
                        # Binary search or unconstrained growth upwards
                        consecutive_fast_successes_near_upper_limit = 0
                        desired_batch_size = _next_batch_after_success(
                            actual_batch_size, config, last_bad_batch_size
                        )
                else:
                    # Binary search downwards due to a slow batch
                    consecutive_fast_successes_near_upper_limit = 0
                    logger.debug(
                        f"{self._progress_label} batch size {actual_batch_size} took {elapsed:.2f}s "
                        f"(target {config.target_batch_time_seconds:.2f}s); shrinking."
                    )
                    last_fast_batch_size, last_bad_batch_size = _update_bounds_after_bad_batch(
                        actual_batch_size, last_fast_batch_size, last_bad_batch_size
                    )
                    desired_batch_size = _next_batch_after_retryable_failure(
                        actual_batch_size, config, last_fast_batch_size, last_bad_batch_size
                    )

            progress.update(total_task, completed=processed, total=processed, refresh=True)
