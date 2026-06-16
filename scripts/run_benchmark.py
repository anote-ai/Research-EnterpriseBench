#!/usr/bin/env python3
"""Demo: run EnterpriseBench with a mock agent."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.data import make_suite
from enterprisebench.core import BenchmarkSuite
from enterprisebench.evaluate import evaluate_result, aggregate_scores, leaderboard


def mock_agent(task):
    """Pretend agent that always returns the expected call."""
    return {
        "call": task.expected_call,
        "output": task.expected_output,
        "cost_usd": 0.002,
        "agent_name": "mock-agent",
    }


def main():
    suite = BenchmarkSuite(tasks=make_suite(20))
    print(f"Suite stats: {suite.stats()}")

    dim_scores: dict[str, list[float]] = {d: [] for d in ["syntactic", "semantic", "reliability", "cost", "latency"]}
    for task in suite.tasks:
        result = suite.run_agent(mock_agent, task)
        scores = evaluate_result(result, task)
        for dim, ds in scores.items():
            dim_scores[dim].append(ds.score)

    for dim, vals in dim_scores.items():
        agg = aggregate_scores(vals)
        print(f"{dim:12s}: mean={agg['mean']:.3f}  std={agg['std']:.3f}")
    board = leaderboard({"mock-agent": dim_scores["syntactic"]})
    print("Leaderboard:", board)


if __name__ == "__main__":
    main()
