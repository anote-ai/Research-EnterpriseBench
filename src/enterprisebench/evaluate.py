from __future__ import annotations
import math
from dataclasses import dataclass
from .core import BenchmarkTask, TaskResult, EvaluationDimension


@dataclass
class DimensionScore:
    dimension: EvaluationDimension
    score: float
    details: dict


def _value_jaccard(pred_args: dict, exp_args: dict) -> float:
    """Jaccard similarity on the string representations of argument values."""
    pred_vals = {str(v).lower() for v in pred_args.values()}
    exp_vals = {str(v).lower() for v in exp_args.values()}
    union = pred_vals | exp_vals
    return len(pred_vals & exp_vals) / len(union) if union else 1.0


def _fuzzy_token_overlap(a: str, b: str) -> float:
    """Token-level Jaccard between two strings."""
    import re
    tokens_a = set(re.split(r"[\s,._\-]+", a.lower())) - {""}
    tokens_b = set(re.split(r"[\s,._\-]+", b.lower())) - {""}
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union) if union else 1.0


def score_syntactic(predicted_call: dict, expected_call: dict) -> DimensionScore:
    """Tool name match + parameter key Jaccard + argument value Jaccard."""
    if not predicted_call or not expected_call:
        return DimensionScore(EvaluationDimension.SYNTACTIC, 0.0, {"reason": "empty call"})
    name_match = float(predicted_call.get("name") == expected_call.get("name"))
    pred_args = predicted_call.get("arguments", {})
    exp_args = expected_call.get("arguments", {})
    pred_keys = set(pred_args.keys())
    exp_keys = set(exp_args.keys())
    union = exp_keys | pred_keys
    key_score = len(pred_keys & exp_keys) / len(union) if union else 1.0
    val_score = _value_jaccard(pred_args, exp_args)
    score = 0.4 * name_match + 0.35 * key_score + 0.25 * val_score
    return DimensionScore(
        EvaluationDimension.SYNTACTIC,
        score,
        {"name_match": name_match, "key_jaccard": key_score, "value_jaccard": val_score},
    )


def score_semantic(
    predicted_call: dict,
    expected_call: dict,
    *,
    instruction: str = "",
) -> DimensionScore:
    """Fuzzy semantic scoring using token-overlap on argument values and tool name."""
    if not predicted_call or not expected_call:
        return DimensionScore(EvaluationDimension.SEMANTIC, 0.0, {"reason": "empty call"})

    pred_name = str(predicted_call.get("name", ""))
    exp_name = str(expected_call.get("name", ""))
    name_sim = _fuzzy_token_overlap(pred_name, exp_name)

    pred_args = predicted_call.get("arguments", {})
    exp_args = expected_call.get("arguments", {})

    if exp_args:
        key_sims = []
        for k, exp_val in exp_args.items():
            pred_val = pred_args.get(k, "")
            key_sims.append(_fuzzy_token_overlap(str(pred_val), str(exp_val)))
        arg_sim = sum(key_sims) / len(key_sims)
    else:
        arg_sim = 1.0

    instruction_boost = 0.0
    if instruction and pred_name:
        instruction_boost = 0.1 * _fuzzy_token_overlap(instruction, pred_name)

    score = min(1.0, 0.45 * name_sim + 0.45 * arg_sim + instruction_boost)
    return DimensionScore(
        EvaluationDimension.SEMANTIC,
        score,
        {
            "name_similarity": name_sim,
            "arg_similarity": arg_sim,
            "instruction_boost": instruction_boost,
        },
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


def score_reliability(
    predicted_calls: list[dict],
    expected_calls: list[dict],
) -> DimensionScore:
    """Fraction of runs where the tool name was called correctly (consistency).

    Pass a list of predicted calls from repeated runs against the same task to
    measure how reliably an agent picks the right tool.  A single-element list
    is valid and returns 1.0 when the name matches, 0.0 otherwise.
    """
    if not expected_calls or not predicted_calls:
        return DimensionScore(EvaluationDimension.RELIABILITY, 0.0, {"reason": "empty calls"})
    expected_name = expected_calls[0].get("name", "")
    hits = sum(
        1 for p in predicted_calls if p.get("name", "") == expected_name
    )
    score = hits / len(predicted_calls)
    return DimensionScore(
        EvaluationDimension.RELIABILITY,
        score,
        {"hits": hits, "total": len(predicted_calls), "expected_name": expected_name},
    )


def evaluate_result(result: TaskResult, task: BenchmarkTask) -> dict[str, DimensionScore]:
    return {
        "syntactic": score_syntactic(result.predicted_call, task.expected_call),
        "semantic": score_semantic(
            result.predicted_call, task.expected_call, instruction=task.instruction
        ),
        "reliability": score_reliability([result.predicted_call], [task.expected_call]),
        "latency": score_latency(result.latency_ms),
        "cost": score_cost(result.cost_usd),
    }


def leaderboard(agent_results: dict[str, list[float]]) -> list[dict]:
    rows = []
    for agent, scores in agent_results.items():
        agg = aggregate_scores(scores)
        rows.append({"agent": agent, **agg})
    return sorted(rows, key=lambda r: r["mean"], reverse=True)


def pareto_frontier(
    points: list[dict], x_key: str = "cost", y_key: str = "score"
) -> list[dict]:
    """Return non-dominated points (minimize x, maximize y)."""
    sorted_pts = sorted(points, key=lambda p: p[x_key])
    frontier = []
    best_y = float("-inf")
    for pt in sorted_pts:
        if pt[y_key] > best_y:
            frontier.append(pt)
            best_y = pt[y_key]
    return frontier


def task_complexity_score(
    n_required_tools: int, n_dependencies: int, has_conditional: bool
) -> float:
    """Heuristic complexity score in [0, 1] for a benchmark task."""
    tool_factor = min(n_required_tools / 5.0, 1.0)
    dep_factor = min(n_dependencies / 4.0, 1.0)
    branch_factor = 0.2 if has_conditional else 0.0
    raw = 0.4 * tool_factor + 0.4 * dep_factor + 0.2 * branch_factor
    return min(raw + branch_factor * 0.1, 1.0)


def agent_leaderboard(
    agent_results: dict[str, list[float]],
    weights: dict[str, float] | None = None,
) -> list[dict]:
    """Rank agents by weighted mean score across evaluation dimensions."""
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
