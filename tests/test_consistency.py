"""Tests for Multi-Turn Consistency Score (MTCS)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.consistency import (
    Decision,
    check_consistency,
    aggregate_mtcs,
)


def test_no_decisions_returns_perfect_score():
    result = check_consistency("s1", [])
    assert result.mtcs == 1.0
    assert result.violations == []
    assert result.n_pairs_checked == 0


def test_single_decision_no_contradiction():
    decisions = [Decision(turn_index=0, key="priority", value="HIGH")]
    result = check_consistency("s1", decisions)
    assert result.mtcs == 1.0
    assert result.n_pairs_checked == 0


def test_consistent_repeated_decision():
    # Agent says priority=HIGH at turns 0 and 3 — consistent
    decisions = [
        Decision(turn_index=0, key="priority", value="HIGH"),
        Decision(turn_index=3, key="priority", value="HIGH"),
    ]
    result = check_consistency("s1", decisions)
    assert result.mtcs == 1.0
    assert result.violations == []
    assert result.n_pairs_checked == 1


def test_single_contradiction():
    # Turn 0: priority=HIGH, turn 3: priority=LOW → contradiction
    decisions = [
        Decision(turn_index=0, key="priority", value="HIGH"),
        Decision(turn_index=3, key="priority", value="LOW"),
    ]
    result = check_consistency("s1", decisions)
    assert result.mtcs == 0.0
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.key == "priority"
    assert v.earlier_value == "HIGH"
    assert v.later_value == "LOW"
    assert v.earlier_turn == 0
    assert v.later_turn == 3


def test_partial_contradiction():
    # Two keys: one consistent, one not → 1 violation out of 2 pairs → MTCS=0.5
    decisions = [
        Decision(turn_index=0, key="priority", value="HIGH"),
        Decision(turn_index=1, key="assignee", value="Alice"),
        Decision(turn_index=5, key="priority", value="LOW"),   # contradiction
        Decision(turn_index=6, key="assignee", value="Alice"),  # consistent
    ]
    result = check_consistency("s1", decisions)
    assert result.n_pairs_checked == 2
    assert len(result.violations) == 1
    assert abs(result.mtcs - 0.5) < 1e-9


def test_multiple_contradictions_same_key():
    # Three values for same key: (0,1) consistent, (0,2) contradiction, (1,2) contradiction
    decisions = [
        Decision(turn_index=0, key="status", value="open"),
        Decision(turn_index=2, key="status", value="open"),
        Decision(turn_index=5, key="status", value="closed"),
    ]
    result = check_consistency("s1", decisions)
    # Pairs: (0,2)=consistent, (0,5)=contradiction, (2,5)=contradiction → 2/3
    assert result.n_pairs_checked == 3
    assert len(result.violations) == 2
    assert abs(result.mtcs - 1 / 3) < 1e-9


def test_different_keys_no_cross_checking():
    # Different keys are never compared to each other
    decisions = [
        Decision(turn_index=0, key="priority", value="HIGH"),
        Decision(turn_index=1, key="status", value="open"),
    ]
    result = check_consistency("s1", decisions)
    assert result.mtcs == 1.0
    assert result.n_pairs_checked == 0


def test_aggregate_mtcs_empty():
    assert aggregate_mtcs([]) == 1.0


def test_aggregate_mtcs_single():
    decisions = [
        Decision(turn_index=0, key="x", value="a"),
        Decision(turn_index=1, key="x", value="b"),
    ]
    result = check_consistency("s1", decisions)
    assert aggregate_mtcs([result]) == 0.0


def test_aggregate_mtcs_mixed():
    # Session 1: perfect (1.0), session 2: zero (0.0) → mean = 0.5
    d_ok = [Decision(turn_index=0, key="k", value="v")]
    d_bad = [
        Decision(turn_index=0, key="k", value="v1"),
        Decision(turn_index=1, key="k", value="v2"),
    ]
    r1 = check_consistency("s1", d_ok)
    r2 = check_consistency("s2", d_bad)
    assert abs(aggregate_mtcs([r1, r2]) - 0.5) < 1e-9


def test_violation_str_readable():
    decisions = [
        Decision(turn_index=0, key="priority", value="HIGH"),
        Decision(turn_index=5, key="priority", value="LOW"),
    ]
    result = check_consistency("s1", decisions)
    assert "turn 5" in str(result.violations[0]).lower()
    assert "HIGH" in str(result.violations[0])
    assert "LOW" in str(result.violations[0])
