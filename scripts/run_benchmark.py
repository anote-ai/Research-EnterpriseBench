#!/usr/bin/env python3
"""Demo: run EnterpriseBench with a mock agent and persist results to DuckDB."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.data import make_suite
from enterprisebench.core import BenchmarkSuite
from enterprisebench.evaluate import evaluate_result, aggregate_scores, leaderboard
from enterprisebench.db import init_db, save_tasks, save_run, save_result, load_run_summary, load_leaderboard, new_run_id

SEED = 42


def mock_agent(task):
    """Pretend agent that always returns the expected call."""
    return {
        "call": task.expected_call,
        "output": task.expected_output,
        "cost_usd": 0.002,
        "agent_name": "mock-agent",
    }


def main():
    conn = init_db()
    run_id = new_run_id()

    suite = BenchmarkSuite(tasks=make_suite(20, seed=SEED))
    print(f"Suite stats: {suite.stats()}")

    save_tasks(conn, suite.tasks)
    save_run(conn, run_id, agent_name="mock-agent", n_tasks=len(suite.tasks), seed=SEED)

    dim_scores: dict[str, list[float]] = {d: [] for d in ["syntactic", "semantic", "reliability", "cost", "latency"]}
    for task in suite.tasks:
        result = suite.run_agent(mock_agent, task)
        scores = evaluate_result(result, task)
        save_result(conn, run_id, result, scores)
        for dim, ds in scores.items():
            dim_scores[dim].append(ds.score)

    print(f"\nRun ID: {run_id}")
    print("\n--- Per-dimension summary (from DB) ---")
    for row in load_run_summary(conn, run_id):
        print(f"  {row['dimension']:12s}: mean={row['mean']:.3f}  std={row['std']:.3f}  n={row['n']}")

    print("\n--- Leaderboard (all runs, from DB) ---")
    for row in load_leaderboard(conn):
        print(f"  {row['agent_name']:20s}  {row['dimension']:12s}  mean={row['mean']:.3f}  n={row['n_tasks']}")

    conn.close()


if __name__ == "__main__":
    main()
