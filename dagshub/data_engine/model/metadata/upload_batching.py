from dataclasses import dataclass
from types import SimpleNamespace
from typing import Optional

from gql.transport.exceptions import TransportConnectionFailed, TransportServerError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout
from tenacity import wait_exponential

from dagshub.data_engine.model.errors import DataEngineGqlError

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
class AdaptiveUploadBatchConfig:
    max_batch_size: int
    min_batch_size: int
    initial_batch_size: int
    target_batch_time_seconds: float

    @classmethod
    def from_values(
        cls,
        max_batch_size: int,
        min_batch_size: int,
        initial_batch_size: int,
        target_batch_time_seconds: float,
    ) -> "AdaptiveUploadBatchConfig":
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


def next_batch_after_success(
    batch_size: int,
    config: AdaptiveUploadBatchConfig,
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


def next_batch_after_retryable_failure(
    batch_size: int,
    config: AdaptiveUploadBatchConfig,
    good_batch_size: Optional[int],
    bad_batch_size: Optional[int],
) -> int:
    if batch_size <= 1:
        return 1

    upper_bound = min(batch_size, bad_batch_size) if bad_batch_size is not None else batch_size
    if good_batch_size is not None and good_batch_size < upper_bound:
        next_batch_size = _midpoint(good_batch_size, upper_bound)
    else:
        next_batch_size = batch_size // 2

    next_batch_size = min(next_batch_size, upper_bound - 1, batch_size - 1, config.max_batch_size)
    return max(1, next_batch_size)


def is_retryable_metadata_upload_error(exc: Exception) -> bool:
    if isinstance(exc, DataEngineGqlError):
        return isinstance(exc.original_exception, (TransportServerError, TransportConnectionFailed))

    return isinstance(
        exc,
        (
            TransportServerError,
            TransportConnectionFailed,
            TimeoutError,
            ConnectionError,
            RequestsConnectionError,
            RequestsTimeout,
        ),
    )


def get_retry_delay_seconds(consecutive_retryable_failures: int) -> float:
    retry_state = SimpleNamespace(attempt_number=max(1, consecutive_retryable_failures))
    return float(_retry_delay_strategy(retry_state))
