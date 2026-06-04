from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time


class EvaluationDimension(str, Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    RELIABILITY = "reliability"
    COST = "cost"
    LATENCY = "latency"


VERTICALS = ["finance", "healthcare", "legal", "devops"]


@dataclass
class BenchmarkTask:
    task_id: str
    vertical: str
    instruction: str
    tool_schema: dict[str, Any]
    expected_call: dict[str, Any]
    expected_output: str
    difficulty: str = "medium"

    def __post_init__(self):
        if self.vertical not in VERTICALS:
            raise ValueError(f"vertical must be one of {VERTICALS}")
        if self.difficulty not in ("easy", "medium", "hard"):
            raise ValueError("difficulty must be easy/medium/hard")


@dataclass
class TaskResult:
    task_id: str
    vertical: str
    predicted_call: dict[str, Any]
    predicted_output: str
    latency_ms: float
    cost_usd: float
    agent_name: str


@dataclass
class BenchmarkSuite:
    tasks: list[BenchmarkTask] = field(default_factory=list)

    def add_task(self, task: BenchmarkTask) -> None:
        self.tasks.append(task)

    def filter_by_vertical(self, vertical: str) -> list[BenchmarkTask]:
        return [t for t in self.tasks if t.vertical == vertical]

    def filter_by_difficulty(self, difficulty: str) -> list[BenchmarkTask]:
        return [t for t in self.tasks if t.difficulty == difficulty]

    def run_agent(self, agent_fn, task: BenchmarkTask) -> TaskResult:
        start = time.perf_counter()
        result = agent_fn(task)
        latency_ms = (time.perf_counter() - start) * 1000
        return TaskResult(
            task_id=task.task_id,
            vertical=task.vertical,
            predicted_call=result.get("call", {}),
            predicted_output=result.get("output", ""),
            latency_ms=latency_ms,
            cost_usd=result.get("cost_usd", 0.0),
            agent_name=result.get("agent_name", "unknown"),
        )

    def stats(self) -> dict:
        from collections import Counter
        return {
            "total": len(self.tasks),
            "by_vertical": dict(Counter(t.vertical for t in self.tasks)),
            "by_difficulty": dict(Counter(t.difficulty for t in self.tasks)),
        }
