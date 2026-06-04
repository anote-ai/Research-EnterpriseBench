import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.evaluate import (
    score_syntactic,
    score_semantic,
    score_latency,
    score_cost,
    aggregate_scores,
    pareto_frontier,
)


def test_score_syntactic_perfect_match():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_syntactic(pred, exp)
    assert result.score == 1.0


def test_score_syntactic_name_mismatch():
    pred = {"name": "wrong_tool", "arguments": {"ticker": "AAPL"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    result = score_syntactic(pred, exp)
    assert result.score < 0.6


def test_score_syntactic_empty_dicts():
    result = score_syntactic({}, {})
    assert result.score == 0.0


def test_score_syntactic_includes_value_jaccard():
    """Value Jaccard is included; partial match should be intermediate."""
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "wrong-date"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_syntactic(pred, exp)
    assert 0.5 < result.score < 1.0
    assert "value_jaccard" in result.details


def test_score_syntactic_key_jaccard_in_details():
    pred = {"name": "tool", "arguments": {"a": "1"}}
    exp = {"name": "tool", "arguments": {"a": "1", "b": "2"}}
    result = score_syntactic(pred, exp)
    assert "key_jaccard" in result.details
    assert result.details["key_jaccard"] < 1.0


def test_score_semantic_perfect_match():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_semantic(pred, exp)
    assert result.score >= 0.9


def test_score_semantic_fuzzy_value_tolerance():
    """Slight variation in value format should still score reasonably well."""
    pred = {"name": "get_stock_price", "arguments": {"ticker": "aapl", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_semantic(pred, exp)
    assert result.score > 0.7


def test_score_semantic_name_mismatch_penalised():
    pred = {"name": "wrong_tool", "arguments": {"ticker": "AAPL"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    result = score_semantic(pred, exp)
    assert result.score < 0.8


def test_score_semantic_empty():
    result = score_semantic({}, {})
    assert result.score == 0.0


def test_score_semantic_details_keys():
    pred = {"name": "tool", "arguments": {"x": "1"}}
    exp = {"name": "tool", "arguments": {"x": "1"}}
    result = score_semantic(pred, exp, instruction="call tool x")
    for key in ("name_similarity", "arg_similarity", "instruction_boost"):
        assert key in result.details


def test_score_latency_under_budget():
    result = score_latency(500.0, budget_ms=2000.0)
    assert result.score > 0.5


def test_score_cost_over_budget():
    result = score_cost(0.05, budget_usd=0.01)
    assert result.score == 0.0


def test_aggregate_scores():
    agg = aggregate_scores([1.0, 0.0, 0.5])
    assert abs(agg["mean"] - 0.5) < 1e-9
    assert agg["min"] == 0.0
    assert agg["max"] == 1.0
    assert agg["n"] == 3
    assert agg["std"] > 0


def test_pareto_frontier():
    points = [
        {"cost": 0.1, "score": 0.9},
        {"cost": 0.2, "score": 0.8},
        {"cost": 0.3, "score": 0.95},
    ]
    frontier = pareto_frontier(points)
    assert len(frontier) >= 1
    assert frontier[0]["cost"] == 0.1
