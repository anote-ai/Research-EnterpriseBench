"""Experiment 2: Full-Suite Policy Violation Rate + Multi-Turn Consistency.

Runs an agent across all 16 policy-annotated tasks (8 workflow categories
× 2 tasks each) and reports:
  - Overall Policy Violation Rate (PVR) with 95% bootstrap CI
  - PVR broken down by workflow category
  - Multi-Turn Consistency Score (MTCS) for tasks that have decisions

Usage — mock agent (no API key needed):
    python experiments/exp2_full_suite.py --mock

Usage — real OpenAI agent:
    OPENAI_API_KEY=sk-... python experiments/exp2_full_suite.py --model gpt-4o-mini

Results saved to results/exp2_full_suite/results.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.tasks import make_workflow_suite, WorkflowCategory
from enterprisebench.core import BenchmarkSuite
from enterprisebench.policy import check_policies, policy_violation_rate
from enterprisebench.consistency import check_consistency, aggregate_mtcs
from enterprisebench.evaluate import bootstrap_ci


def mock_agent(task):
    """Always returns the task's expected_call — perfect instruction follower."""
    return {
        "call": task.expected_call,
        "output": task.expected_output,
        "cost_usd": 0.0,
        "agent_name": "mock/always-expected",
    }


def run(agent_fn) -> dict:
    workflow_tasks = make_workflow_suite()
    suite = BenchmarkSuite(tasks=[wt.task for wt in workflow_tasks])

    policy_results = []
    consistency_results = []
    rows = []

    for wt in workflow_tasks:
        task_result = suite.run_agent(agent_fn, wt.task)
        action = wt.to_action(task_result.predicted_call)

        # Policy check
        check = check_policies(wt.task.task_id, wt.rules, wt.pre_state, action, {})
        policy_results.append(check)

        # MTCS — only for tasks that have decisions defined
        mtcs_score = None
        if wt.decisions:
            cr = check_consistency(wt.task.task_id, wt.decisions)
            consistency_results.append(cr)
            mtcs_score = cr.mtcs

        rows.append({
            "task_id": wt.task.task_id,
            "category": wt.category.value,
            "agent_name": task_result.agent_name,
            "has_violation": check.has_violation,
            "violations": [
                {"rule_id": v.rule_id, "category": v.category.value, "severity": v.severity.value}
                for v in check.violations
            ],
            "mtcs": mtcs_score,
            "cost_usd": task_result.cost_usd,
        })

    # Overall PVR with bootstrap CI
    # Encode as 1=compliant, 0=violation so CI is on the compliance rate;
    # PVR = 1 - compliance_rate
    compliance_scores = [0.0 if r.has_violation else 1.0 for r in policy_results]
    pvr = policy_violation_rate(policy_results)
    pvr_ci_raw = bootstrap_ci(compliance_scores)
    # CI on compliance → invert for PVR CI
    pvr_ci = {"low": 1.0 - pvr_ci_raw["ci_high"], "high": 1.0 - pvr_ci_raw["ci_low"]}

    # PVR by category
    pvr_by_category: dict[str, dict] = {}
    for cat in WorkflowCategory:
        cat_results = [
            r for r, wt in zip(policy_results, workflow_tasks)
            if wt.category == cat
        ]
        pvr_by_category[cat.value] = {
            "pvr": policy_violation_rate(cat_results),
            "n_tasks": len(cat_results),
            "n_violations": sum(1 for r in cat_results if r.has_violation),
        }

    # MTCS aggregate
    mtcs_mean = aggregate_mtcs(consistency_results)
    mtcs_scores = [r.mtcs for r in consistency_results]
    mtcs_ci_raw = bootstrap_ci(mtcs_scores) if mtcs_scores else {}
    mtcs_ci = (
        {"low": mtcs_ci_raw["ci_low"], "high": mtcs_ci_raw["ci_high"]}
        if mtcs_ci_raw else None
    )

    total_cost = sum(r["cost_usd"] for r in rows)

    return {
        "n_tasks": len(workflow_tasks),
        "n_categories": len(WorkflowCategory),
        "agent": rows[0]["agent_name"] if rows else "unknown",
        "pvr": pvr,
        "pvr_ci_95": pvr_ci,
        "pvr_by_category": pvr_by_category,
        "mtcs_mean": mtcs_mean,
        "mtcs_ci_95": mtcs_ci,
        "n_tasks_with_mtcs": len(consistency_results),
        "total_cost_usd": total_cost,
        "tasks": rows,
    }


def print_report(results: dict) -> None:
    ci = results["pvr_ci_95"]
    mci = results["mtcs_ci_95"]

    print(f"\n{'='*62}")
    print(f"  EnterpriseBench — Experiment 2  |  agent: {results['agent']}")
    print(f"{'='*62}")
    print(f"  Tasks : {results['n_tasks']} across {results['n_categories']} workflow categories")
    print(f"  PVR   : {results['pvr']:.0%}  [95% CI {ci['low']:.0%}–{ci['high']:.0%}]")
    if mci:
        print(f"  MTCS  : {results['mtcs_mean']:.2f}  "
              f"[95% CI {mci['low']:.2f}–{mci['high']:.2f}]  "
              f"(n={results['n_tasks_with_mtcs']} tasks with decisions)")
    if results["total_cost_usd"] > 0:
        print(f"  Cost  : ${results['total_cost_usd']:.4f} total")

    print(f"\n  PVR by category:")
    for cat, stats in results["pvr_by_category"].items():
        bar = "■" * stats["n_violations"] + "□" * (stats["n_tasks"] - stats["n_violations"])
        print(f"    {cat:<28s}  {bar}  {stats['pvr']:.0%}")

    print(f"\n  Per-task:")
    for row in results["tasks"]:
        flag = "VIOLATION" if row["has_violation"] else "ok      "
        mtcs = f"MTCS={row['mtcs']:.2f}" if row["mtcs"] is not None else "      "
        print(f"    {row['task_id']:<12s}  {flag}  {mtcs}  [{row['category']}]")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 2: Full Suite PVR + MTCS")
    parser.add_argument("--mock", action="store_true", help="Use mock agent (no API key needed)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
    args = parser.parse_args()

    if args.mock:
        agent_fn = mock_agent
        print("Using mock agent (always returns expected_call).")
    else:
        from enterprisebench.adapters import OpenAIAdapter
        agent_fn = OpenAIAdapter(model=args.model)
        print(f"Using OpenAI adapter (model={args.model}).")

    results = run(agent_fn)
    print_report(results)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "results", "exp2_full_suite")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
