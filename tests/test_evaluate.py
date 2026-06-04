import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.evaluate import (
    score_syntactic, score_latency, score_cost, aggregate_scores, pareto_frontier
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
    # First point dominates second; third has higher score despite higher cost
    assert len(frontier) >= 1
    assert frontier[0]["cost"] == 0.1
