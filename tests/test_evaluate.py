"""Tests for enterprisebench.evaluate."""

import pytest

from enterprisebench.evaluate import (
    aggregate_scores,
    pareto_frontier,
    score_semantic,
    score_syntactic,
)


# ---------------------------------------------------------------------------
# score_syntactic
# ---------------------------------------------------------------------------

def test_score_syntactic_perfect_match() -> None:
    pred = {"tool_name": "get_price", "arguments": {"symbol": "AAPL"}}
    exp = {"tool_name": "get_price", "arguments": {"symbol": "MSFT"}}
    assert score_syntactic(pred, exp) == 1.0


def test_score_syntactic_name_mismatch() -> None:
    pred = {"tool_name": "wrong_tool", "arguments": {"symbol": "AAPL"}}
    exp = {"tool_name": "get_price", "arguments": {"symbol": "AAPL"}}
    assert score_syntactic(pred, exp) == 0.0


def test_score_syntactic_param_key_mismatch() -> None:
    pred = {"tool_name": "get_price", "arguments": {"ticker": "AAPL"}}
    exp = {"tool_name": "get_price", "arguments": {"symbol": "AAPL"}}
    assert score_syntactic(pred, exp) == 0.0


def test_score_syntactic_empty_arguments() -> None:
    pred = {"tool_name": "ping", "arguments": {}}
    exp = {"tool_name": "ping", "arguments": {}}
    assert score_syntactic(pred, exp) == 1.0


# ---------------------------------------------------------------------------
# score_semantic
# ---------------------------------------------------------------------------

def test_score_semantic_placeholder() -> None:
    assert score_semantic("anything", "anything") == 0.0


# ---------------------------------------------------------------------------
# aggregate_scores
# ---------------------------------------------------------------------------

def test_aggregate_scores_basic() -> None:
    stats = aggregate_scores([1.0, 0.0, 0.5])
    assert stats["mean"] == pytest.approx(0.5)
    assert stats["min"] == pytest.approx(0.0)
    assert stats["max"] == pytest.approx(1.0)
    assert "std" in stats


def test_aggregate_scores_single_element() -> None:
    stats = aggregate_scores([0.8])
    assert stats["mean"] == pytest.approx(0.8)
    assert stats["std"] == pytest.approx(0.0)


def test_aggregate_scores_empty_raises() -> None:
    with pytest.raises(ValueError):
        aggregate_scores([])


# ---------------------------------------------------------------------------
# pareto_frontier
# ---------------------------------------------------------------------------

def test_pareto_frontier_empty() -> None:
    assert pareto_frontier([]) == []


def test_pareto_frontier_single() -> None:
    result = [{"accuracy": 0.9, "speed": 0.8}]
    assert pareto_frontier(result) == result


def test_pareto_frontier_dominated_removed() -> None:
    results = [
        {"accuracy": 0.9, "speed": 0.9},  # dominates the next
        {"accuracy": 0.5, "speed": 0.5},  # dominated
        {"accuracy": 0.3, "speed": 1.0},  # trade-off — not dominated
    ]
    frontier = pareto_frontier(results)
    assert {"accuracy": 0.5, "speed": 0.5} not in frontier
    assert len(frontier) == 2
