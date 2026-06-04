"""Tests for enterprisebench.core."""

import pytest

from enterprisebench.core import (
    BenchmarkSuite,
    BenchmarkTask,
    EvaluationDimension,
    VERTICALS,
)


# ---------------------------------------------------------------------------
# VERTICALS
# ---------------------------------------------------------------------------

def test_verticals_is_list() -> None:
    assert isinstance(VERTICALS, list)


def test_verticals_length() -> None:
    assert len(VERTICALS) == 4


def test_verticals_contains_expected() -> None:
    assert set(VERTICALS) == {"finance", "healthcare", "legal", "devops"}


# ---------------------------------------------------------------------------
# EvaluationDimension
# ---------------------------------------------------------------------------

def test_evaluation_dimension_values() -> None:
    assert EvaluationDimension.SYNTACTIC.value == "syntactic"
    assert EvaluationDimension.SEMANTIC.value == "semantic"
    assert EvaluationDimension.RELIABILITY.value == "reliability"
    assert EvaluationDimension.COST.value == "cost"
    assert EvaluationDimension.LATENCY.value == "latency"


def test_evaluation_dimension_count() -> None:
    assert len(EvaluationDimension) == 5


# ---------------------------------------------------------------------------
# BenchmarkTask
# ---------------------------------------------------------------------------

def _make_task(**kwargs):
    defaults = dict(
        task_id="t001",
        vertical="finance",
        instruction="Fetch latest stock price",
        tool_schema={"name": "get_stock_price", "parameters": {"symbol": "str"}},
        expected_call={"tool_name": "get_stock_price", "arguments": {"symbol": "AAPL"}},
        expected_output={"price": 182.5},
    )
    defaults.update(kwargs)
    return BenchmarkTask(**defaults)


def test_benchmark_task_creation() -> None:
    task = _make_task()
    assert task.task_id == "t001"
    assert task.vertical == "finance"


def test_benchmark_task_invalid_vertical() -> None:
    with pytest.raises(ValueError, match="vertical"):
        _make_task(vertical="marketing")


def test_benchmark_task_all_verticals() -> None:
    for v in VERTICALS:
        t = _make_task(vertical=v)
        assert t.vertical == v


# ---------------------------------------------------------------------------
# BenchmarkSuite
# ---------------------------------------------------------------------------

def test_benchmark_suite_instantiation_empty() -> None:
    suite = BenchmarkSuite()
    assert suite.tasks == []


def test_benchmark_suite_instantiation_with_tasks() -> None:
    tasks = [_make_task(task_id=f"t{i:03d}") for i in range(3)]
    suite = BenchmarkSuite(tasks=tasks)
    assert len(suite.tasks) == 3


def test_benchmark_suite_load_tasks_raises() -> None:
    suite = BenchmarkSuite()
    with pytest.raises(NotImplementedError):
        suite.load_tasks()


def test_benchmark_suite_run_agent_raises() -> None:
    suite = BenchmarkSuite()
    task = _make_task()
    with pytest.raises(NotImplementedError):
        suite.run_agent(task, agent_fn=lambda *a, **kw: None)


def test_benchmark_suite_score_task_raises() -> None:
    suite = BenchmarkSuite()
    task = _make_task()
    with pytest.raises(NotImplementedError):
        suite.score_task(task, {})
