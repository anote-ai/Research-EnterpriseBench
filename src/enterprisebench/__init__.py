"""EnterpriseBench: Multi-dimensional LLM evaluation for enterprise tool-use tasks."""
from .core import BenchmarkTask, BenchmarkSuite, TaskResult, TurnResult, EvaluationDimension, VERTICALS
from .evaluate import (
    DimensionScore,
    score_syntactic,
    score_semantic,
    score_reliability,
    score_latency,
    score_cost,
    aggregate_scores,
    evaluate_result,
    leaderboard,
    pareto_frontier,
    bootstrap_ci,
    paired_bootstrap_test,
)

__version__ = "0.1.0"
__all__ = [
    "BenchmarkTask",
    "BenchmarkSuite",
    "TaskResult",
    "TurnResult",
    "EvaluationDimension",
    "VERTICALS",
    "DimensionScore",
    "score_syntactic",
    "score_semantic",
    "score_reliability",
    "score_latency",
    "score_cost",
    "aggregate_scores",
    "evaluate_result",
    "leaderboard",
    "pareto_frontier",
    "bootstrap_ci",
    "paired_bootstrap_test",
]
