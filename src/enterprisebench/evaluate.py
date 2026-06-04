"""Evaluation utilities for EnterpriseBench."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SyntacticScore:
    """Container for syntactic evaluation results."""

    tool_name_match: bool
    param_keys_match: bool
    score: float


def score_syntactic(
    predicted_call: dict[str, Any],
    expected_call: dict[str, Any],
) -> float:
    """Score syntactic correctness of a predicted tool call.

    Checks whether the predicted call matches the expected call on
    tool name and parameter keys (values are ignored).

    Args:
        predicted_call: Dict with keys ``tool_name`` and ``arguments``.
        expected_call: Dict with keys ``tool_name`` and ``arguments``.

    Returns:
        Float in [0.0, 1.0]; 1.0 means both name and param keys match.
    """
    name_match = predicted_call.get("tool_name") == expected_call.get("tool_name")
    pred_keys = set(predicted_call.get("arguments", {}).keys())
    exp_keys = set(expected_call.get("arguments", {}).keys())
    keys_match = pred_keys == exp_keys
    return float(name_match and keys_match)


def score_semantic(
    predicted_output: Any,  # noqa: ARG001
    expected_output: Any,  # noqa: ARG001
) -> float:
    """Score semantic correctness of a predicted output (placeholder).

    Args:
        predicted_output: The output produced by the agent.
        expected_output: The ground-truth output.

    Returns:
        Always 0.0 until a semantic scorer is implemented.
    """
    return 0.0


def aggregate_scores(scores: list[float]) -> dict[str, float]:
    """Compute summary statistics over a list of scores.

    Args:
        scores: List of float scores in [0, 1].

    Returns:
        Dict with keys ``mean``, ``std``, ``min``, ``max``.

    Raises:
        ValueError: If ``scores`` is empty.
    """
    if not scores:
        raise ValueError("scores must be non-empty")
    arr = np.array(scores, dtype=float)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def pareto_frontier(results: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return the Pareto-optimal subset of results.

    A result is dominated if another result is at least as good on all
    dimensions and strictly better on at least one dimension.  All
    dimension values are treated as higher-is-better.

    Args:
        results: List of dicts mapping dimension names to float scores.

    Returns:
        Non-dominated subset of ``results`` (preserves original order).
    """
    if not results:
        return []
    keys = list(results[0].keys())
    dominated: list[bool] = [False] * len(results)
    for i, r_i in enumerate(results):
        for j, r_j in enumerate(results):
            if i == j or dominated[i]:
                continue
            if all(r_j.get(k, 0.0) >= r_i.get(k, 0.0) for k in keys) and any(
                r_j.get(k, 0.0) > r_i.get(k, 0.0) for k in keys
            ):
                dominated[i] = True
    return [r for r, d in zip(results, dominated) if not d]
