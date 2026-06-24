from __future__ import annotations
from collections import Counter
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
    # System state before the agent acts; used for state-diff verification
    pre_state: dict[str, Any] = field(default_factory=dict)
    # Key-value constraints that must hold after a correct tool call
    expected_post_state: dict[str, Any] = field(default_factory=dict)
    # For multi-turn tasks: ordered list of (instruction, expected_call) pairs
    turns: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.vertical not in VERTICALS:
            raise ValueError(f"vertical must be one of {VERTICALS}")
        if self.difficulty not in ("easy", "medium", "hard"):
            raise ValueError("difficulty must be easy/medium/hard")

    @property
    def is_multi_turn(self) -> bool:
        return len(self.turns) > 0


@dataclass
class TurnResult:
    turn_index: int
    predicted_call: dict[str, Any]
    predicted_output: str


@dataclass
class TaskResult:
    task_id: str
    vertical: str
    predicted_call: dict[str, Any]
    predicted_output: str
    latency_ms: float
    cost_usd: float
    agent_name: str
    turn_results: list[TurnResult] = field(default_factory=list)


@dataclass
class BenchmarkSuite:
    tasks: list[BenchmarkTask] = field(default_factory=list)

    def add_task(self, task: BenchmarkTask) -> None:
        self.tasks.append(task)

    def filter_by_vertical(self, vertical: str) -> list[BenchmarkTask]:
        return [t for t in self.tasks if t.vertical == vertical]

    def filter_by_difficulty(self, difficulty: str) -> list[BenchmarkTask]:
        return [t for t in self.tasks if t.difficulty == difficulty]

    def run_agent(self, agent_fn: Any, task: BenchmarkTask) -> TaskResult:
        start = time.perf_counter()
        result = agent_fn(task)
        latency_ms = (time.perf_counter() - start) * 1000

        turn_results: list[TurnResult] = []
        if task.is_multi_turn:
            for i, turn_result in enumerate(result.get("turn_results", [])):
                turn_results.append(
                    TurnResult(
                        turn_index=i,
                        predicted_call=turn_result.get("call", {}),
                        predicted_output=turn_result.get("output", ""),
                    )
                )

        return TaskResult(
            task_id=task.task_id,
            vertical=task.vertical,
            predicted_call=result.get("call", {}),
            predicted_output=result.get("output", ""),
            latency_ms=latency_ms,
            cost_usd=result.get("cost_usd", 0.0),
            agent_name=result.get("agent_name", "unknown"),
            turn_results=turn_results,
        )

    def run_agent_multi_turn(
        self, agent_fn: Any, task: BenchmarkTask
    ) -> list[TurnResult]:
        """Drive a multi-turn task turn-by-turn and return per-turn results."""
        if not task.is_multi_turn:
            raise ValueError("Task has no turns defined")
        results: list[TurnResult] = []
        history: list[dict[str, Any]] = []
        for i, turn in enumerate(task.turns):
            response = agent_fn({"instruction": turn["instruction"], "history": history})
            tr = TurnResult(
                turn_index=i,
                predicted_call=response.get("call", {}),
                predicted_output=response.get("output", ""),
            )
            results.append(tr)
            history.append({"turn": turn, "result": tr})
        return results

    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self.tasks),
            "by_vertical": dict(Counter(t.vertical for t in self.tasks)),
            "by_difficulty": dict(Counter(t.difficulty for t in self.tasks)),
            "multi_turn_count": sum(1 for t in self.tasks if t.is_multi_turn),
        }
