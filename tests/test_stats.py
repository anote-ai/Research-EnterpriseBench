"""Tests for bootstrap CI and paired bootstrap significance test (#15)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.evaluate import bootstrap_ci, paired_bootstrap_test


# ---------------------------------------------------------------------------
# bootstrap_ci
# ---------------------------------------------------------------------------

def test_bootstrap_ci_empty():
    result = bootstrap_ci([])
    assert result == {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}


def test_bootstrap_ci_constant_scores():
    # All 1.0 → CI should be [1.0, 1.0]
    result = bootstrap_ci([1.0] * 20)
    assert result["mean"] == 1.0
    assert result["ci_low"] == 1.0
    assert result["ci_high"] == 1.0
    assert result["n"] == 20


def test_bootstrap_ci_mean_is_correct():
    scores = [0.2, 0.4, 0.6, 0.8, 1.0]
    result = bootstrap_ci(scores)
    assert abs(result["mean"] - 0.6) < 1e-9


def test_bootstrap_ci_interval_ordering():
    scores = [float(i) / 10 for i in range(11)]  # 0.0 … 1.0
    result = bootstrap_ci(scores)
    assert result["ci_low"] <= result["mean"] <= result["ci_high"]


def test_bootstrap_ci_interval_width_shrinks_with_more_data():
    # Larger samples → narrower CI
    rng_scores_small = [0.0, 1.0] * 5          # n=10
    rng_scores_large = [0.0, 1.0] * 50         # n=100
    ci_small = bootstrap_ci(rng_scores_small)
    ci_large = bootstrap_ci(rng_scores_large)
    width_small = ci_small["ci_high"] - ci_small["ci_low"]
    width_large = ci_large["ci_high"] - ci_large["ci_low"]
    assert width_large < width_small


def test_bootstrap_ci_reproducible_with_same_seed():
    scores = [0.3, 0.5, 0.7, 0.9]
    r1 = bootstrap_ci(scores, seed=0)
    r2 = bootstrap_ci(scores, seed=0)
    assert r1 == r2


def test_bootstrap_ci_different_seeds_may_differ():
    scores = [0.3, 0.5, 0.7, 0.9]
    r1 = bootstrap_ci(scores, seed=0)
    r2 = bootstrap_ci(scores, seed=99)
    # Results may differ (not guaranteed, but almost always will for small n)
    # We just verify both produce valid structure
    assert "ci_low" in r1 and "ci_low" in r2


# ---------------------------------------------------------------------------
# paired_bootstrap_test
# ---------------------------------------------------------------------------

def test_paired_bootstrap_clearly_better():
    # A always beats B → p_value should be very small
    a = [1.0] * 50
    b = [0.0] * 50
    result = paired_bootstrap_test(a, b)
    assert result["observed_diff"] == 1.0
    assert result["p_value"] == 0.0  # no resamples can reverse this


def test_paired_bootstrap_no_difference():
    # Identical → observed_diff == 0
    scores = [0.5] * 20
    result = paired_bootstrap_test(scores, scores)
    assert result["observed_diff"] == 0.0


def test_paired_bootstrap_length_mismatch():
    import pytest
    with pytest.raises(ValueError, match="same length"):
        paired_bootstrap_test([0.5, 0.6], [0.5])


def test_paired_bootstrap_empty():
    import pytest
    with pytest.raises(ValueError, match="non-empty"):
        paired_bootstrap_test([], [])


def test_paired_bootstrap_p_value_in_range():
    a = [0.6, 0.7, 0.8, 0.5, 0.9]
    b = [0.4, 0.5, 0.6, 0.3, 0.7]
    result = paired_bootstrap_test(a, b)
    assert 0.0 <= result["p_value"] <= 1.0
    assert result["observed_diff"] > 0


def test_paired_bootstrap_reproducible():
    a = [0.8, 0.7, 0.9]
    b = [0.5, 0.4, 0.6]
    r1 = paired_bootstrap_test(a, b, seed=7)
    r2 = paired_bootstrap_test(a, b, seed=7)
    assert r1 == r2
