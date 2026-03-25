from unittest.mock import patch

import pytest

from dagshub.common.adaptive_batching import (
    AdaptiveBatchConfig,
    AdaptiveBatcher,
    _clamp,
    _get_retry_delay_seconds,
    _is_next_step_above_limit,
    _min_step_size,
    _next_batch_after_retryable_failure,
    _next_batch_after_success,
)


class RetryableTestError(Exception):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cfg(
    max_batch_size=1000,
    min_batch_size=1,
    initial_batch_size=10,
    target_batch_time_seconds=5.0,
    batch_growth_factor=10,
    retry_backoff_base_seconds=0.25,
    retry_backoff_max_seconds=4.0,
):
    """Shortcut to build a config without going through from_values (avoids config import)."""
    return AdaptiveBatchConfig(
        max_batch_size=max_batch_size,
        min_batch_size=min_batch_size,
        initial_batch_size=initial_batch_size,
        target_batch_time_seconds=target_batch_time_seconds,
        batch_growth_factor=batch_growth_factor,
        retry_backoff_base_seconds=retry_backoff_base_seconds,
        retry_backoff_max_seconds=retry_backoff_max_seconds,
    )


# ---------------------------------------------------------------------------
# AdaptiveBatchConfig.from_values
# ---------------------------------------------------------------------------


class TestAdaptiveBatchConfigFromValues:
    def test_normalizes_max_batch_size_to_at_least_1(self):
        cfg = AdaptiveBatchConfig.from_values(max_batch_size=0, min_batch_size=1)
        assert cfg.max_batch_size == 1

    def test_clamps_min_to_max(self):
        cfg = AdaptiveBatchConfig.from_values(max_batch_size=5, min_batch_size=100)
        assert cfg.min_batch_size == 5

    def test_clamps_initial_between_min_and_max(self):
        cfg = AdaptiveBatchConfig.from_values(max_batch_size=100, min_batch_size=10, initial_batch_size=5)
        assert cfg.initial_batch_size == 10

        cfg2 = AdaptiveBatchConfig.from_values(max_batch_size=100, min_batch_size=10, initial_batch_size=200)
        assert cfg2.initial_batch_size == 100

    def test_batch_growth_factor_minimum_is_2(self):
        cfg = AdaptiveBatchConfig.from_values(batch_growth_factor=1)
        assert cfg.batch_growth_factor == 2

    def test_backoff_seconds_non_negative(self):
        cfg = AdaptiveBatchConfig.from_values(retry_backoff_base_seconds=-1.0, retry_backoff_max_seconds=-5.0)
        assert cfg.retry_backoff_base_seconds == 0.0
        assert cfg.retry_backoff_max_seconds == 0.0


class TestClamp:
    def test_within_range(self):
        assert _clamp(5, 1, 10) == 5

    def test_below_minimum(self):
        assert _clamp(0, 3, 10) == 3

    def test_above_maximum(self):
        assert _clamp(20, 1, 10) == 10

    def test_equal_bounds(self):
        assert _clamp(5, 7, 7) == 7


# ---------------------------------------------------------------------------
# _next_batch_after_success
# ---------------------------------------------------------------------------


class TestNextBatchAfterSuccess:
    def test_grows_by_growth_factor_when_no_bad_size(self):
        cfg = _cfg(batch_growth_factor=10, max_batch_size=10000)
        assert _next_batch_after_success(10, cfg, soft_upper_limit=None) == 100

    def test_capped_at_max_batch_size(self):
        cfg = _cfg(batch_growth_factor=10, max_batch_size=50)
        assert _next_batch_after_success(10, cfg, soft_upper_limit=None) == 50

    def test_binary_search_toward_bad_size(self):
        cfg = _cfg(max_batch_size=10000)
        result = _next_batch_after_success(10, cfg, soft_upper_limit=20)
        assert 10 < result < 20

    def test_stays_below_soft_upper_limit_when_midpoint_advances(self):
        cfg = _cfg(max_batch_size=10000)
        result = _next_batch_after_success(18, cfg, soft_upper_limit=20)
        assert result <= 19  # bad_batch_size - 1

    def test_respects_min_batch_size(self):
        cfg = _cfg(min_batch_size=5, max_batch_size=10)
        result = _next_batch_after_success(1, cfg, soft_upper_limit=None)
        assert result >= 5

    def test_holds_near_soft_upper_limit_before_reprobing(self):
        cfg = _cfg(max_batch_size=1000, batch_growth_factor=2)
        result = _next_batch_after_success(9, cfg, soft_upper_limit=10)
        assert result == 9

    def test_makes_progress_when_growth_factor_would_not_increase(self):
        cfg = _cfg(batch_growth_factor=2, max_batch_size=100)
        # batch_size=99, growth gives 198 capped to 100, which is > 99 so it works.
        # But let's test the edge: batch_size at max-1 should reach max.
        result = _next_batch_after_success(99, cfg, soft_upper_limit=None)
        assert result == 100


# ---------------------------------------------------------------------------
# _next_batch_after_retryable_failure
# ---------------------------------------------------------------------------


class TestNextBatchAfterRetryableFailure:
    def test_halves_when_no_bounds(self):
        cfg = _cfg(min_batch_size=1)
        assert _next_batch_after_retryable_failure(100, cfg, None, None) == 50

    def test_returns_min_when_at_min(self):
        cfg = _cfg(min_batch_size=5)
        assert _next_batch_after_retryable_failure(5, cfg, None, None) == 5

    def test_binary_search_between_good_and_bad(self):
        cfg = _cfg(min_batch_size=1)
        result = _next_batch_after_retryable_failure(100, cfg, last_fast_batch_size=40, soft_upper_limit=100)
        assert 40 < result < 100

    def test_never_returns_below_min_batch_size(self):
        cfg = _cfg(min_batch_size=10)
        result = _next_batch_after_retryable_failure(20, cfg, None, None)
        assert result >= 10

    def test_strictly_decreases_from_current(self):
        cfg = _cfg(min_batch_size=1)
        for batch_size in [2, 5, 10, 50, 100, 1000]:
            result = _next_batch_after_retryable_failure(batch_size, cfg, None, None)
            assert result < batch_size


# ---------------------------------------------------------------------------
# _get_retry_delay_seconds
# ---------------------------------------------------------------------------


class TestGetRetryDelaySeconds:
    def test_returns_base_for_first_failure(self):
        cfg = _cfg(retry_backoff_base_seconds=0.25, retry_backoff_max_seconds=4.0)
        delay = _get_retry_delay_seconds(1, cfg)
        assert delay == pytest.approx(0.25, abs=0.01)

    def test_increases_with_more_failures(self):
        cfg = _cfg(retry_backoff_base_seconds=0.25, retry_backoff_max_seconds=4.0)
        d1 = _get_retry_delay_seconds(1, cfg)
        d2 = _get_retry_delay_seconds(2, cfg)
        d3 = _get_retry_delay_seconds(3, cfg)
        assert d1 < d2 < d3

    def test_capped_at_max(self):
        cfg = _cfg(retry_backoff_base_seconds=0.25, retry_backoff_max_seconds=4.0)
        delay = _get_retry_delay_seconds(100, cfg)
        assert delay <= 4.0

    def test_zero_failures_treated_as_one(self):
        cfg = _cfg(retry_backoff_base_seconds=0.5, retry_backoff_max_seconds=10.0)
        assert _get_retry_delay_seconds(0, cfg) == _get_retry_delay_seconds(1, cfg)


class TestSoftUpperHintResolution:
    def test_min_step_size_scales_with_hint(self):
        assert _min_step_size(10) == 1
        assert _min_step_size(1000) == 50

    def test_holds_when_gap_is_within_resolution(self):
        assert _is_next_step_above_limit(9, 10)
        assert not _is_next_step_above_limit(8, 10)
        assert not _is_next_step_above_limit(10, 10)
        assert not _is_next_step_above_limit(9, None)


# ---------------------------------------------------------------------------
# AdaptiveBatcher.run — integration tests
# ---------------------------------------------------------------------------


class TestAdaptiveBatcherRun:
    @staticmethod
    def _make_batcher(**config_overrides):
        cfg = _cfg(
            **{
                **dict(
                    initial_batch_size=3,
                    max_batch_size=100,
                    min_batch_size=1,
                    target_batch_time_seconds=999,  # fast enough to always grow
                    retry_backoff_base_seconds=0.0,
                    retry_backoff_max_seconds=0.0,
                ),
                **config_overrides,
            }
        )
        return AdaptiveBatcher(
            is_retryable=lambda exc: isinstance(exc, RetryableTestError),
            config=cfg,
        )

    def test_processes_all_items(self):
        batcher = self._make_batcher()
        received = []
        batcher.run(list(range(10)), lambda batch: received.extend(batch))
        assert received == list(range(10))

    def test_empty_list(self):
        batcher = self._make_batcher()
        called = []
        batcher.run([], lambda batch: called.append(batch))
        assert called == []

    def test_generator_input(self):
        batcher = self._make_batcher()
        received = []

        def gen():
            for i in range(7):
                yield i

        batcher.run(gen(), lambda batch: received.extend(batch))
        assert received == list(range(7))

    def test_retries_on_retryable_error(self):
        batcher = self._make_batcher(initial_batch_size=5, min_batch_size=1)
        call_count = 0
        received = []

        def op(batch):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RetryableTestError("transient")
            received.extend(batch)

        batcher.run(list(range(5)), op)
        assert received == list(range(5))
        assert call_count > 1

    def test_aborts_on_non_retryable_error(self):
        batcher = self._make_batcher()

        with pytest.raises(TypeError):
            batcher.run(list(range(5)), lambda batch: (_ for _ in ()).throw(TypeError("fatal")))

    def test_aborts_at_min_batch_size(self):
        batcher = self._make_batcher(initial_batch_size=1, min_batch_size=1)

        with pytest.raises(RetryableTestError, match="always fails"):
            batcher.run([1], lambda batch: (_ for _ in ()).throw(RetryableTestError("always fails")))

    def test_short_tail_batch_retries_exact_size_once_before_aborting(self):
        batcher = self._make_batcher(initial_batch_size=5, min_batch_size=4, max_batch_size=5)
        attempts = 0

        def op(batch):
            nonlocal attempts
            attempts += 1
            if attempts >= 3:
                raise TypeError("retried too many times")
            raise RetryableTestError("always fails")

        with pytest.raises(RetryableTestError, match="always fails"):
            batcher.run([1, 2, 3], op)

        assert attempts == 2

    def test_no_items_lost_on_retry(self):
        """All items from a failed batch must be retried."""
        batcher = self._make_batcher(initial_batch_size=4, min_batch_size=1)
        fail_once = True
        all_received = []

        def op(batch):
            nonlocal fail_once
            if fail_once and len(batch) == 4:
                fail_once = False
                raise RetryableTestError("fail big batch once")
            all_received.extend(batch)

        items = list(range(8))
        batcher.run(items, op)
        assert all_received == items

    def test_generator_retry_no_items_lost(self):
        """Items from a failed batch are retried even with generator input."""
        batcher = self._make_batcher(initial_batch_size=3, min_batch_size=1)
        fail_once = True
        all_received = []

        def op(batch):
            nonlocal fail_once
            if fail_once:
                fail_once = False
                raise RetryableTestError("transient")
            all_received.extend(batch)

        def gen():
            for i in range(6):
                yield i

        batcher.run(gen(), op)
        assert all_received == list(range(6))

    def test_batch_size_shrinks_on_failure(self):
        batcher = self._make_batcher(initial_batch_size=10, min_batch_size=1)
        batch_sizes = []

        def op(batch):
            batch_sizes.append(len(batch))
            if batch_sizes[-1] == 10:
                raise RetryableTestError("too big")

        batcher.run(list(range(20)), op)
        # First call is size 10 (fails), next should be smaller
        assert batch_sizes[0] == 10
        assert batch_sizes[1] < 10

    @patch("dagshub.common.adaptive_batching.time")
    def test_batch_size_grows_on_fast_success(self, mock_time):
        # Make monotonic() return increasing values, but elapsed always < target
        mock_time.monotonic.side_effect = [0.0, 0.001] * 50
        mock_time.sleep = lambda _: None

        batcher = self._make_batcher(
            initial_batch_size=2,
            max_batch_size=100,
            target_batch_time_seconds=5.0,
        )
        batch_sizes = []
        batcher.run(list(range(100)), lambda batch: batch_sizes.append(len(batch)))
        # Should grow from initial=2
        assert max(batch_sizes) > 2

    @patch("dagshub.common.adaptive_batching.time")
    def test_batch_size_shrinks_on_slow_success(self, mock_time):
        # Make elapsed always > target (slow batches)
        mock_time.monotonic.side_effect = [0.0, 100.0] * 100
        mock_time.sleep = lambda _: None

        batcher = self._make_batcher(
            initial_batch_size=20,
            min_batch_size=1,
            max_batch_size=100,
            target_batch_time_seconds=1.0,
        )
        received = []
        batch_sizes = []

        def op(batch):
            batch_sizes.append(len(batch))
            received.extend(batch)

        items = list(range(50))
        batcher.run(items, op)
        # All items processed despite slow batches
        assert received == items
        # Batch size should shrink from 20
        assert batch_sizes[0] == 20
        assert min(batch_sizes) < 20

    def test_reprobes_soft_upper_limit_after_stable_fast_successes(self):
        batcher = self._make_batcher(
            initial_batch_size=10,
            min_batch_size=1,
            max_batch_size=1000,
        )
        fail_once = True
        batch_sizes = []

        def op(batch):
            nonlocal fail_once
            batch_sizes.append(len(batch))
            if fail_once:
                fail_once = False
                raise RetryableTestError("transient")

        items = list(range(200))
        batcher.run(items, op)
        assert batch_sizes[:4] == [10, 5, 7, 8]
        assert batch_sizes[4:7] == [9, 9, 9]
        assert 10 in batch_sizes[7:]
