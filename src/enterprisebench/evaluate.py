from __future__ import annotations
import math
import random
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


# ---------------------------------------------------------------------------
# CLAS composite metric — issue #3
# ---------------------------------------------------------------------------

# Default weights inspired by CEBench (arXiv:2407.12797).
# All five dimensions sum to 1.0. Adjust per deployment context.
_DEFAULT_CLAS_WEIGHTS: dict[str, float] = {
    "syntactic":   0.30,   # C — Correctness (tool-call accuracy)
    "semantic":    0.20,   # C — semantic fidelity
    "reliability": 0.20,   # L/S — consistency across runs
    "cost":        0.15,   # A — cost efficiency (higher = cheaper)
    "latency":     0.15,   # L — latency efficiency (higher = faster)
}


def clas_score(
    dim_scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """Weighted composite of the five evaluation dimensions.

    Args:
        dim_scores: mapping of dimension name → score in [0, 1].
                    Keys: "syntactic", "semantic", "reliability", "cost", "latency".
        weights:    optional override of _DEFAULT_CLAS_WEIGHTS. Must sum to 1.0.

    Returns a single float in [0, 1]. Higher is better.
    """
    w = weights if weights is not None else _DEFAULT_CLAS_WEIGHTS
    return sum(dim_scores.get(dim, 0.0) * weight for dim, weight in w.items())


def cost_per_success(
    costs_usd: list[float],
    syntactic_scores: list[float],
    success_threshold: float = 0.8,
) -> float:
    """Mean cost (USD) per task where syntactic score >= success_threshold.

    Returns float('inf') if no task meets the threshold (agent never succeeds).
    This surfaces the true cost of a correct answer, not cost per attempt.
    """
    if len(costs_usd) != len(syntactic_scores):
        raise ValueError("costs_usd and syntactic_scores must be the same length")
    successful_costs = [
        c for c, s in zip(costs_usd, syntactic_scores) if s >= success_threshold
    ]
    return sum(successful_costs) / len(successful_costs) if successful_costs else float("inf")


def clas_leaderboard(
    agent_dim_scores: dict[str, dict[str, list[float]]],
    agent_costs_usd: dict[str, list[float]] | None = None,
    weights: dict[str, float] | None = None,
    success_threshold: float = 0.8,
) -> list[dict]:
    """Rank agents by CLAS composite score with cost-per-success column.

    Args:
        agent_dim_scores: {agent_name: {dim_name: [per-task scores]}}.
        agent_costs_usd:  {agent_name: [per-task cost in USD]}.
        weights:          dimension weights for clas_score().
        success_threshold: syntactic score threshold defining "success".

    Returns a list of dicts sorted by clas_mean descending, each with:
        agent, clas_mean, clas_ci_low, clas_ci_high, cost_per_success_usd,
        and per-dimension means.
    """
    rows = []
    for agent, dims in agent_dim_scores.items():
        # Compute per-task CLAS scores
        n_tasks = max((len(v) for v in dims.values()), default=0)
        per_task_clas = [
            clas_score(
                {dim: scores[i] for dim, scores in dims.items() if i < len(scores)},
                weights=weights,
            )
            for i in range(n_tasks)
        ]
        ci = bootstrap_ci(per_task_clas)

        # Cost per success
        syntactic_scores = dims.get("syntactic", [])
        costs = (agent_costs_usd or {}).get(agent, [0.0] * n_tasks)
        cps = cost_per_success(costs, syntactic_scores, success_threshold)

        row: dict = {
            "agent": agent,
            "clas_mean": ci["mean"],
            "clas_ci_low": ci["ci_low"],
            "clas_ci_high": ci["ci_high"],
            "cost_per_success_usd": cps,
        }
        # Also include per-dimension means for transparency
        for dim, scores in dims.items():
            row[f"{dim}_mean"] = sum(scores) / len(scores) if scores else 0.0

        rows.append(row)

    rows.sort(key=lambda r: r["clas_mean"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Statistical utilities — issue #15
# ---------------------------------------------------------------------------

def bootstrap_ci(
    scores: list[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    """95% bootstrap confidence interval for the mean of `scores`.

    Returns {"mean": float, "ci_low": float, "ci_high": float, "n": int}.
    Resample tasks (not individual steps) to account for task-level clustering.
    """
    if not scores:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}

    rng = random.Random(seed)
    n = len(scores)
    boot_means = []
    for _ in range(n_resamples):
        sample = [rng.choice(scores) for _ in range(n)]
        boot_means.append(sum(sample) / n)

    boot_means.sort()
    alpha = 1.0 - confidence
    lo_idx = int(alpha / 2 * n_resamples)
    hi_idx = int((1 - alpha / 2) * n_resamples) - 1

    return {
        "mean": sum(scores) / n,
        "ci_low": boot_means[lo_idx],
        "ci_high": boot_means[hi_idx],
        "n": n,
    }


def paired_bootstrap_test(
    scores_a: list[float],
    scores_b: list[float],
    n_resamples: int = 1000,
    seed: int = 42,
) -> dict:
    """Paired bootstrap significance test: is mean(A) > mean(B)?

    Returns {"observed_diff": float, "p_value": float}.
    p_value is the fraction of bootstrap resamples where the difference
    reverses — i.e. P(boot_diff <= 0) when observed_diff > 0.

    Reference: Dror et al. (2018), "The Hitchhiker's Guide to Testing
    Statistical Significance in NLP."
    """
    if len(scores_a) != len(scores_b):
        raise ValueError("scores_a and scores_b must be the same length")
    if not scores_a:
        raise ValueError("scores must be non-empty")

    n = len(scores_a)
    observed_diff = sum(scores_a) / n - sum(scores_b) / n

    rng = random.Random(seed)
    count_reversed = 0
    for _ in range(n_resamples):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        diff = sum(scores_a[i] - scores_b[i] for i in indices) / n
        if diff <= 0:
            count_reversed += 1

    p_value = count_reversed / n_resamples

    return {"observed_diff": observed_diff, "p_value": p_value}
