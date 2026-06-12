"""Core data structures and benchmark orchestration for EnterpriseBench."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


VERTICALS: list[str] = ["finance", "healthcare", "legal", "devops"]


class EvaluationDimension(Enum):
    """The five dimensions evaluated by EnterpriseBench."""

    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    RELIABILITY = "reliability"
    COST = "cost"
    LATENCY = "latency"


@dataclass
class BenchmarkTask:
    """A single task in the EnterpriseBench benchmark suite."""

    task_id: str
    vertical: str
    instruction: str
    tool_schema: dict[str, Any]
    expected_call: dict[str, Any]
    expected_output: Any

    def __post_init__(self) -> None:
        if self.vertical not in VERTICALS:
            raise ValueError(f"vertical must be one of {VERTICALS}, got {self.vertical!r}")


class BenchmarkSuite:
    """Orchestrates loading, running, and scoring EnterpriseBench tasks."""

    def __init__(self, tasks: list[BenchmarkTask] | None = None) -> None:
        self.tasks: list[BenchmarkTask] = tasks or []
        self._results: list[dict[str, Any]] = []

    def load_tasks(self, source: str | None = None) -> list[BenchmarkTask]:
        """Load tasks from a dataset source (stub).

        Args:
            source: HuggingFace dataset name or local path.

        Returns:
            List of BenchmarkTask instances.
        """
        # TODO: implement dataset loading via `datasets` library
        raise NotImplementedError("load_tasks is not yet implemented")

    def run_agent(
        self,
        task: BenchmarkTask,
        agent_fn: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run an agent function on a single task (stub).

        Args:
            task: The benchmark task to evaluate.
            agent_fn: Callable that accepts a task instruction and tool schema.
            **kwargs: Additional arguments forwarded to agent_fn.

        Returns:
            Dict with keys ``predicted_call``, ``predicted_output``, ``latency_ms``, ``cost_usd``.
        """
        # TODO: implement timed agent invocation
        raise NotImplementedError("run_agent is not yet implemented")

    def score_task(
        self,
        task: BenchmarkTask,
        result: dict[str, Any],
    ) -> dict[str, float]:
        """Compute per-dimension scores for one task result (stub).

        Args:
            task: The ground-truth task.
            result: Output from :meth:`run_agent`.

        Returns:
            Dict mapping EvaluationDimension names to float scores in [0, 1].
        """
        # TODO: call evaluate module scorers
        raise NotImplementedError("score_task is not yet implemented")
