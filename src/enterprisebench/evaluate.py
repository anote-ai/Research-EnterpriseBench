from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any
from .core import BenchmarkTask, TaskResult, EvaluationDimension


@dataclass
class DimensionScore:
    dimension: EvaluationDimension
    score: float  # 0..1
    details: dict


def score_syntactic(predicted_call: dict, expected_call: dict) -> DimensionScore:
    """Checks tool name match + parameter key overlap."""
    if not predicted_call or not expected_call:
        return DimensionScore(EvaluationDimension.SYNTACTIC, 0.0, {"reason": "empty call"})
    name_match = float(predicted_call.get("name") == expected_call.get("name"))
    pred_keys = set(predicted_call.get("arguments", {}).keys())
    exp_keys = set(expected_call.get("arguments", {}).keys())
    union = exp_keys | pred_keys
    key_score = len(pred_keys & exp_keys) / len(union) if union else 1.0
    score = 0.5 * name_match + 0.5 * key_score
    return DimensionScore(
        EvaluationDimension.SYNTACTIC,
        score,
        {"name_match": name_match, "key_jaccard": key_score},
    )


def score_latency(latency_ms: float, budget_ms: float = 2000.0) -> DimensionScore:
    score = max(0.0, 1.0 - latency_ms / budget_ms)
    return DimensionScore(
        EvaluationDimension.LATENCY,
        score,
        {"latency_ms": latency_ms, "budget_ms": budget_ms},
    )


def score_cost(cost_usd: float, budget_usd: float = 0.01) -> DimensionScore:
    score = max(0.0, 1.0 - cost_usd / budget_usd)
    return DimensionScore(
        EvaluationDimension.COST,
        score,
        {"cost_usd": cost_usd, "budget_usd": budget_usd},
    )


def aggregate_scores(scores: list[float]) -> dict:
    if not scores:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    n = len(scores)
    mean = sum(scores) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in scores) / n)
    return {"mean": mean, "std": std, "min": min(scores), "max": max(scores), "n": n}


def evaluate_result(result: TaskResult, task: BenchmarkTask) -> dict[str, DimensionScore]:
    return {
        "syntactic": score_syntactic(result.predicted_call, task.expected_call),
        "latency": score_latency(result.latency_ms),
        "cost": score_cost(result.cost_usd),
    }


def leaderboard(agent_results: dict[str, list[float]]) -> list[dict]:
    """agent_results: {agent_name: [syntactic_scores]}. Returns sorted leaderboard."""
    rows = []
    for agent, scores in agent_results.items():
        agg = aggregate_scores(scores)
        rows.append({"agent": agent, **agg})
    return sorted(rows, key=lambda r: r["mean"], reverse=True)


def pareto_frontier(points: list[dict], x_key: str = "cost", y_key: str = "score") -> list[dict]:
    """Return non-dominated points (minimize x, maximize y)."""
    sorted_pts = sorted(points, key=lambda p: p[x_key])
    frontier = []
    best_y = float("-inf")
    for pt in sorted_pts:
        if pt[y_key] > best_y:
            frontier.append(pt)
            best_y = pt[y_key]
    return frontier
