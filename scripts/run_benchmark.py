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

    all_syntactic = []
    for task in suite.tasks:
        result = suite.run_agent(mock_agent, task)
        scores = evaluate_result(result, task)
        all_syntactic.append(scores["syntactic"].score)

    agg = aggregate_scores(all_syntactic)
    print(f"Syntactic scores: mean={agg['mean']:.3f} std={agg['std']:.3f}")
    board = leaderboard({"mock-agent": all_syntactic})
    print("Leaderboard:", board)


if __name__ == "__main__":
    main()
