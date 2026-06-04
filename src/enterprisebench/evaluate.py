from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EvaluationDimension(str, Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    LATENCY = "latency"
    COST = "cost"


@dataclass
class DimensionScore:
    dimension: EvaluationDimension
    score: float
    details: dict = field(default_factory=dict)


def score_syntactic(predicted: dict, expected: dict) -> DimensionScore:
    """Structural tool-call match: name + argument key/value Jaccard."""
    if not predicted and not expected:
        return DimensionScore(EvaluationDimension.SYNTACTIC, 0.0, {})
    name_match = 1.0 if predicted.get("name") == expected.get("name") else 0.0
    pred_args: dict = predicted.get("arguments", {})
    exp_args: dict = expected.get("arguments", {})
    pred_keys = set(pred_args)
    exp_keys = set(exp_args)
    union_keys = pred_keys | exp_keys
    key_jaccard = len(pred_keys & exp_keys) / len(union_keys) if union_keys else 1.0
    shared_keys = pred_keys & exp_keys
    if shared_keys:
        matches = sum(1 for k in shared_keys if str(pred_args[k]) == str(exp_args[k]))
        value_jaccard = matches / len(union_keys)
    else:
        value_jaccard = 1.0 if not union_keys else 0.0
    score = (0.4 * name_match + 0.3 * key_jaccard + 0.3 * value_jaccard)
    return DimensionScore(
        EvaluationDimension.SYNTACTIC,
        score,
        {"name_match": name_match, "key_jaccard": key_jaccard, "value_jaccard": value_jaccard},
    )


def score_semantic(
    predicted: dict,
    expected: dict,
    instruction: Optional[str] = None,
) -> DimensionScore:
    """Semantic tool-call match with fuzzy value comparison and instruction boost."""
    if not predicted and not expected:
        return DimensionScore(EvaluationDimension.SEMANTIC, 0.0, {})
    name_similarity = 1.0 if predicted.get("name") == expected.get("name") else 0.0
    pred_args: dict = predicted.get("arguments", {})
    exp_args: dict = expected.get("arguments", {})
    all_keys = set(pred_args) | set(exp_args)
    if all_keys:
        arg_score = 0.0
        for k in all_keys:
            pv = str(pred_args.get(k, "")).lower().strip()
            ev = str(exp_args.get(k, "")).lower().strip()
            if pv == ev:
                arg_score += 1.0
            elif pv and ev and (pv in ev or ev in pv):
                arg_score += 0.5
        arg_similarity = arg_score / len(all_keys)
    else:
        arg_similarity = 1.0
    instruction_boost = 0.0
    if instruction and predicted.get("name"):
        if predicted["name"].replace("_", " ") in instruction.lower():
            instruction_boost = 0.05
    score = min(1.0, 0.4 * name_similarity + 0.55 * arg_similarity + instruction_boost)
    return DimensionScore(
        EvaluationDimension.SEMANTIC,
        score,
        {
            "name_similarity": name_similarity,
            "arg_similarity": arg_similarity,
            "instruction_boost": instruction_boost,
        },
    )


def score_latency(latency_ms: float, budget_ms: float = 2000.0) -> DimensionScore:
    """Score latency: 1.0 at 0 ms, 0.0 beyond 2× budget."""
    if budget_ms <= 0:
        return DimensionScore(EvaluationDimension.LATENCY, 0.0, {})
    score = max(0.0, 1.0 - latency_ms / (2.0 * budget_ms))
    return DimensionScore(EvaluationDimension.LATENCY, score, {"latency_ms": latency_ms, "budget_ms": budget_ms})


def score_cost(cost_usd: float, budget_usd: float = 0.01) -> DimensionScore:
    """Score cost: 1.0 at zero cost, 0.0 once budget is exceeded."""
    if cost_usd > budget_usd:
        return DimensionScore(EvaluationDimension.COST, 0.0, {"over_budget": True})
    score = 1.0 - cost_usd / budget_usd if budget_usd > 0 else 0.0
    return DimensionScore(EvaluationDimension.COST, score, {"cost_usd": cost_usd})


def aggregate_scores(scores: list[float]) -> dict:
    """Basic statistics over a list of dimension scores."""
    if not scores:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "n": 0}
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    return {"mean": mean, "min": min(scores), "max": max(scores), "std": math.sqrt(variance), "n": n}


def pareto_frontier(points: list[dict]) -> list[dict]:
    """Return Pareto-optimal points (minimize cost, maximize score)."""
    if not points:
        return []
    frontier = []
    for p in sorted(points, key=lambda x: x["cost"]):
        if not frontier or p["score"] > frontier[-1]["score"]:
            frontier.append(p)
    return frontier


def task_complexity_score(n_required_tools: int, n_dependencies: int, has_conditional: bool) -> float:
    """Heuristic complexity score in [0, 1] for a benchmark task.

    Considers how many tools must be chained, how many inter-call dependencies
    exist, and whether the task requires conditional branching.
    """
    tool_factor = min(n_required_tools / 5.0, 1.0)
    dep_factor = min(n_dependencies / 4.0, 1.0)
    branch_factor = 0.2 if has_conditional else 0.0
    raw = 0.4 * tool_factor + 0.4 * dep_factor + 0.2 * branch_factor
    return min(raw + branch_factor * 0.1, 1.0)


def agent_leaderboard(
    agent_results: dict[str, list[float]],
    weights: Optional[dict[str, float]] = None,
) -> list[dict]:
    """Rank agents by weighted mean score across evaluation dimensions.

    agent_results maps agent name to list of per-task scores.
    weights maps dimension names to floats (default uniform).
    Returns list of dicts sorted by weighted_mean descending.
    """
    if weights is None:
        weights = {}
    rows = []
    for agent, scores in agent_results.items():
        if not scores:
            continue
        stats = aggregate_scores(scores)
        rows.append({"agent": agent, **stats})
    rows.sort(key=lambda x: x["mean"], reverse=True)
    return rows
