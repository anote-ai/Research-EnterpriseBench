import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.core import (
    BenchmarkTask, BenchmarkSuite, TaskResult, EvaluationDimension, VERTICALS
)
from enterprisebench.data import make_suite


def _simple_task():
    return BenchmarkTask(
        task_id="t001",
        vertical="finance",
        instruction="Get AAPL stock price",
        tool_schema={"name": "get_stock_price", "parameters": {"ticker": "string"}},
        expected_call={"name": "get_stock_price", "arguments": {"ticker": "AAPL"}},
        expected_output="150.0",
    )


def test_benchmark_task_creation():
    t = _simple_task()
    assert t.task_id == "t001"
    assert t.vertical == "finance"
    assert t.difficulty == "medium"


def test_vertical_validation():
    with pytest.raises(ValueError, match="vertical"):
        BenchmarkTask(
            task_id="bad", vertical="unknown",
            instruction="x", tool_schema={}, expected_call={}, expected_output=""
        )


def test_difficulty_validation():
    with pytest.raises(ValueError, match="difficulty"):
        BenchmarkTask(
            task_id="bad", vertical="finance",
            instruction="x", tool_schema={}, expected_call={}, expected_output="",
            difficulty="impossible"
        )


def test_filter_by_vertical():
    suite = BenchmarkSuite(tasks=make_suite(20))
    finance_tasks = suite.filter_by_vertical("finance")
    assert all(t.vertical == "finance" for t in finance_tasks)
    assert len(finance_tasks) > 0


def test_filter_by_difficulty():
    suite = BenchmarkSuite(tasks=make_suite(20))
    easy_tasks = suite.filter_by_difficulty("easy")
    assert all(t.difficulty == "easy" for t in easy_tasks)


def test_run_agent_with_lambda():
    suite = BenchmarkSuite()
    task = _simple_task()
    suite.add_task(task)

    def agent(t):
        return {"call": t.expected_call, "output": "ok", "cost_usd": 0.001, "agent_name": "test"}

    result = suite.run_agent(agent, task)
    assert isinstance(result, TaskResult)
    assert result.task_id == "t001"
    assert result.latency_ms >= 0
    assert result.agent_name == "test"


def test_stats_structure():
    suite = BenchmarkSuite(tasks=make_suite(20))
    stats = suite.stats()
    assert "total" in stats
    assert stats["total"] == 20
    assert "by_vertical" in stats
    assert "by_difficulty" in stats


def test_add_task():
    suite = BenchmarkSuite()
    assert len(suite.tasks) == 0
    suite.add_task(_simple_task())
    assert len(suite.tasks) == 1


def test_verticals_has_four_items():
    assert len(VERTICALS) == 4
    assert "finance" in VERTICALS
    assert "healthcare" in VERTICALS


def test_evaluation_dimension_values():
    assert EvaluationDimension.SYNTACTIC == "syntactic"
    assert EvaluationDimension.LATENCY == "latency"
    assert EvaluationDimension.COST == "cost"
    assert EvaluationDimension.SEMANTIC == "semantic"
    assert EvaluationDimension.RELIABILITY == "reliability"
