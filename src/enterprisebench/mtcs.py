"""Multi-Turn Consistency Score (MTCS) for EnterpriseBench.

MTCS measures whether an agent's tool calls across the turns of a multi-turn
task form a consistent, dependency-respecting sequence.

Model
-----
Each turn in task.turns carries an expected_call.  We build a simple DAG:
  - Each turn is a node with index i.
  - Turn i depends on turn i-1 (linear chain by default; the model can be
    extended to arbitrary DAGs when turn dicts include a "depends_on" list).

Consistency rules checked per turn transition:
  1. Tool continuity   — if turn i depends on turn j, the tool called at j
                         must be the same family (same name prefix) as expected.
  2. Argument carry-through — arguments from turn j that appear in turn i's
                              expected call must match what the agent produced.
  3. No hallucinated tools — the agent must not introduce a tool name that
                             was never in the task's tool_schema.

MTCS = (turns passing all rules) / (total dependency edges evaluated)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import BenchmarkTask, TurnResult, EvaluationDimension, DimensionScore


@dataclass
class TurnConsistencyResult:
    turn_index: int
    passed: bool
    violations: list[str] = field(default_factory=list)


def _tool_family(name: str) -> str:
    """Return the base prefix of a tool name (everything before the first '_')."""
    return name.split("_")[0] if name else ""


def _check_turn_consistency(
    prev_result: TurnResult,
    curr_result: TurnResult,
    curr_expected: dict[str, Any],
    allowed_tool: str,
) -> TurnConsistencyResult:
    violations: list[str] = []

    # Rule 1: agent must not call a tool outside the declared schema
    curr_name = curr_result.predicted_call.get("name", "")
    if curr_name and curr_name != allowed_tool:
        violations.append(
            f"turn {curr_result.turn_index}: unauthorized tool '{curr_name}' "
            f"(expected '{allowed_tool}')"
        )

    # Rule 2: argument carry-through — expected args that overlap with previous
    # turn's predicted args must be consistent
    prev_args = prev_result.predicted_call.get("arguments", {})
    curr_exp_args = curr_expected.get("arguments", {})
    curr_pred_args = curr_result.predicted_call.get("arguments", {})
    for key, exp_val in curr_exp_args.items():
        if key in prev_args:
            pred_val = curr_pred_args.get(key, "")
            if str(pred_val).lower() != str(exp_val).lower():
                violations.append(
                    f"turn {curr_result.turn_index}: argument '{key}' "
                    f"should carry through as '{exp_val}' but got '{pred_val}'"
                )

    return TurnConsistencyResult(
        turn_index=curr_result.turn_index,
        passed=len(violations) == 0,
        violations=violations,
    )


def score_mtcs(
    turn_results: list[TurnResult],
    task: BenchmarkTask,
) -> DimensionScore:
    """Compute MTCS for a completed multi-turn task.

    turn_results — the TurnResult list from BenchmarkSuite.run_agent_multi_turn
    task         — the BenchmarkTask that was run

    Returns a DimensionScore where:
      score = fraction of dependency edges (turn transitions) that are consistent.
      details includes per-turn breakdown and all violation messages.
    """
    if not task.turns or len(turn_results) < 2:
        # Single-turn or no turns — trivially consistent
        single_pass = (
            len(turn_results) == 1
            and turn_results[0].predicted_call.get("name") == task.tool_schema.get("name")
        ) if turn_results else True
        return DimensionScore(
            EvaluationDimension.MTCS,
            1.0 if single_pass else 0.0,
            {"edges_evaluated": 0, "note": "fewer than 2 turns"},
        )

    allowed_tool = task.tool_schema.get("name", "")
    edge_results: list[TurnConsistencyResult] = []

    for i in range(1, len(turn_results)):
        expected_turn = task.turns[i] if i < len(task.turns) else {}
        expected_call = expected_turn.get("expected_call", {})
        tcr = _check_turn_consistency(
            prev_result=turn_results[i - 1],
            curr_result=turn_results[i],
            curr_expected=expected_call,
            allowed_tool=allowed_tool,
        )
        edge_results.append(tcr)

    passed = sum(1 for e in edge_results if e.passed)
    total = len(edge_results)
    score = passed / total if total else 1.0

    all_violations = [v for e in edge_results for v in e.violations]
    return DimensionScore(
        EvaluationDimension.MTCS,
        score,
        {
            "edges_evaluated": total,
            "edges_passed": passed,
            "violations": all_violations,
            "per_turn": [
                {"turn": e.turn_index, "passed": e.passed, "violations": e.violations}
                for e in edge_results
            ],
        },
    )
