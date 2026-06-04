"""EnterpriseBench: Multi-dimensional LLM evaluation for enterprise tool-use tasks."""
from .core import BenchmarkTask, BenchmarkSuite, TaskResult, EvaluationDimension, VERTICALS
from .evaluate import (
    DimensionScore, score_syntactic, score_latency, score_cost,
    aggregate_scores, evaluate_result, leaderboard, pareto_frontier,
)

__version__ = "0.1.0"
__all__ = [
    "BenchmarkTask", "BenchmarkSuite", "TaskResult", "EvaluationDimension", "VERTICALS",
    "DimensionScore", "score_syntactic", "score_latency", "score_cost",
    "aggregate_scores", "evaluate_result", "leaderboard", "pareto_frontier",
]
