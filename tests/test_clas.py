"""Tests for CLAS composite metric and cost-per-success (#3)."""
import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from enterprisebench.evaluate import clas_score, cost_per_success, clas_leaderboard


# ---------------------------------------------------------------------------
# clas_score
# ---------------------------------------------------------------------------

def test_clas_perfect_agent():
    scores = {"syntactic": 1.0, "semantic": 1.0, "reliability": 1.0, "cost": 1.0, "latency": 1.0}
    assert abs(clas_score(scores) - 1.0) < 1e-9


def test_clas_zero_agent():
    scores = {"syntactic": 0.0, "semantic": 0.0, "reliability": 0.0, "cost": 0.0, "latency": 0.0}
    assert abs(clas_score(scores)) < 1e-9


def test_clas_missing_dimensions_default_to_zero():
    # Only syntactic provided → weight 0.30
    result = clas_score({"syntactic": 1.0})
    assert abs(result - 0.30) < 1e-9


def test_clas_custom_weights():
    scores = {"syntactic": 1.0, "semantic": 0.0, "reliability": 0.0, "cost": 0.0, "latency": 0.0}
    weights = {"syntactic": 1.0, "semantic": 0.0, "reliability": 0.0, "cost": 0.0, "latency": 0.0}
    assert abs(clas_score(scores, weights=weights) - 1.0) < 1e-9


def test_clas_partial_score():
    # syntactic=0.5, rest=0 → 0.5 * 0.30 = 0.15
    scores = {"syntactic": 0.5, "semantic": 0.0, "reliability": 0.0, "cost": 0.0, "latency": 0.0}
    assert abs(clas_score(scores) - 0.15) < 1e-9


# ---------------------------------------------------------------------------
# cost_per_success
# ---------------------------------------------------------------------------

def test_cost_per_success_all_succeed():
    costs = [0.002, 0.003, 0.001]
    scores = [1.0, 0.9, 0.85]
    result = cost_per_success(costs, scores, success_threshold=0.8)
    assert abs(result - sum(costs) / 3) < 1e-9


def test_cost_per_success_none_succeed():
    result = cost_per_success([0.01, 0.02], [0.3, 0.5], success_threshold=0.8)
    assert math.isinf(result)


def test_cost_per_success_partial():
    # Only tasks 0 and 2 succeed (scores >= 0.8)
    costs = [0.002, 0.010, 0.004]
    scores = [1.0, 0.5, 0.9]
    result = cost_per_success(costs, scores, success_threshold=0.8)
    assert abs(result - (0.002 + 0.004) / 2) < 1e-9


def test_cost_per_success_length_mismatch():
    with pytest.raises(ValueError):
        cost_per_success([0.01], [0.9, 0.8])


# ---------------------------------------------------------------------------
# clas_leaderboard
# ---------------------------------------------------------------------------

def _make_dim_scores(syntactic, semantic, reliability, cost, latency, n=5):
    return {
        "syntactic":   [syntactic] * n,
        "semantic":    [semantic] * n,
        "reliability": [reliability] * n,
        "cost":        [cost] * n,
        "latency":     [latency] * n,
    }


def test_clas_leaderboard_sorted_by_clas():
    agent_dims = {
        "strong": _make_dim_scores(0.9, 0.9, 0.9, 0.9, 0.9),
        "weak":   _make_dim_scores(0.3, 0.3, 0.3, 0.3, 0.3),
    }
    board = clas_leaderboard(agent_dims)
    assert board[0]["agent"] == "strong"
    assert board[1]["agent"] == "weak"


def test_clas_leaderboard_includes_cost_per_success():
    agent_dims = {
        "agent_a": _make_dim_scores(1.0, 1.0, 1.0, 1.0, 1.0),
    }
    costs = {"agent_a": [0.002] * 5}
    board = clas_leaderboard(agent_dims, agent_costs_usd=costs)
    assert "cost_per_success_usd" in board[0]
    assert abs(board[0]["cost_per_success_usd"] - 0.002) < 1e-9


def test_clas_leaderboard_per_dimension_means():
    agent_dims = {"agent": _make_dim_scores(0.6, 0.7, 0.8, 0.9, 1.0)}
    board = clas_leaderboard(agent_dims)
    row = board[0]
    assert abs(row["syntactic_mean"] - 0.6) < 1e-9
    assert abs(row["latency_mean"] - 1.0) < 1e-9


def test_clas_leaderboard_empty_agent_skipped():
    board = clas_leaderboard({"ghost": {}})
    # No tasks → n_tasks=0, still returns a row but with clas_mean=0
    assert board[0]["agent"] == "ghost"
    assert board[0]["clas_mean"] == 0.0


def test_clas_leaderboard_no_costs_defaults_to_zero():
    agent_dims = {"agent": _make_dim_scores(1.0, 1.0, 1.0, 1.0, 1.0)}
    board = clas_leaderboard(agent_dims)  # no costs provided
    assert board[0]["cost_per_success_usd"] == 0.0
