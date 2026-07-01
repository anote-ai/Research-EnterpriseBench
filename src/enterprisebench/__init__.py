"""EnterpriseBench: Multi-dimensional LLM evaluation for enterprise tool-use tasks."""
from .core import BenchmarkTask, BenchmarkSuite, TaskResult, TurnResult, EvaluationDimension, VERTICALS
from .tasks import WorkflowCategory, WorkflowTask, make_workflow_suite, tasks_by_category
from .consistency import (
    Decision,
    ConsistencyViolation,
    ConsistencyResult,
    check_consistency,
    aggregate_mtcs,
)
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
    "WorkflowCategory",
    "WorkflowTask",
    "make_workflow_suite",
    "tasks_by_category",
    "Decision",
    "ConsistencyViolation",
    "ConsistencyResult",
    "check_consistency",
    "aggregate_mtcs",
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
