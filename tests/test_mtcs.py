import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from enterprisebench.core import BenchmarkTask, TurnResult
from enterprisebench.mtcs import score_mtcs


def _finance_task(turns=None):
    return BenchmarkTask(
        task_id="mt-01",
        vertical="finance",
        instruction="Multi-turn finance workflow",
        tool_schema={"name": "get_stock_price", "parameters": {"ticker": "string", "date": "string"}},
        expected_call={"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-03-31"}},
        expected_output="ok",
        turns=turns or [
            {"instruction": "step 1", "expected_call": {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-03-31"}}},
            {"instruction": "step 2", "expected_call": {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-06-30"}}},
            {"instruction": "step 3", "expected_call": {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-09-30"}}},
        ],
    )


def _turn(index, name, args):
    return TurnResult(turn_index=index, predicted_call={"name": name, "arguments": args}, predicted_output="ok")


# --- Fully consistent sequence ---

def test_mtcs_perfect_consistency():
    task = _finance_task()
    results = [
        _turn(0, "get_stock_price", {"ticker": "AAPL", "date": "2024-03-31"}),
        _turn(1, "get_stock_price", {"ticker": "AAPL", "date": "2024-06-30"}),
        _turn(2, "get_stock_price", {"ticker": "AAPL", "date": "2024-09-30"}),
    ]
    ds = score_mtcs(results, task)
    assert ds.score == 1.0
    assert ds.details["edges_evaluated"] == 2
    assert ds.details["violations"] == []


# --- Unauthorized tool introduced at turn 1 ---

def test_mtcs_unauthorized_tool():
    task = _finance_task()
    results = [
        _turn(0, "get_stock_price", {"ticker": "AAPL", "date": "2024-03-31"}),
        _turn(1, "lookup_patient_record", {"ticker": "AAPL", "date": "2024-06-30"}),
        _turn(2, "get_stock_price", {"ticker": "AAPL", "date": "2024-09-30"}),
    ]
    ds = score_mtcs(results, task)
    assert ds.score < 1.0
    assert any("unauthorized tool" in v for v in ds.details["violations"])


# --- Argument carry-through failure ---

def test_mtcs_argument_carrythrough_failure():
    task = _finance_task()
    results = [
        _turn(0, "get_stock_price", {"ticker": "AAPL", "date": "2024-03-31"}),
        # Turn 1 expected ticker=AAPL but agent passes MSFT
        _turn(1, "get_stock_price", {"ticker": "MSFT", "date": "2024-06-30"}),
        _turn(2, "get_stock_price", {"ticker": "AAPL", "date": "2024-09-30"}),
    ]
    ds = score_mtcs(results, task)
    assert ds.score < 1.0
    assert any("carry through" in v for v in ds.details["violations"])


# --- Fewer than 2 turns returns 1.0 (trivially consistent) ---

def test_mtcs_single_turn():
    task = BenchmarkTask(
        task_id="st-01",
        vertical="devops",
        instruction="Single turn",
        tool_schema={"name": "get_deployment_status", "parameters": {}},
        expected_call={"name": "get_deployment_status", "arguments": {}},
        expected_output="ok",
        turns=[{"instruction": "step", "expected_call": {}}],
    )
    results = [_turn(0, "get_deployment_status", {})]
    ds = score_mtcs(results, task)
    assert ds.score == 1.0
    assert ds.details["edges_evaluated"] == 0


# --- No turns defined ---

def test_mtcs_no_turns():
    task = BenchmarkTask(
        task_id="nt-01",
        vertical="legal",
        instruction="No turns",
        tool_schema={"name": "search_case_law", "parameters": {}},
        expected_call={"name": "search_case_law", "arguments": {}},
        expected_output="ok",
    )
    ds = score_mtcs([], task)
    assert ds.score == 1.0


# --- Partial consistency: 1 of 2 edges passes ---

def test_mtcs_partial_consistency():
    task = _finance_task()
    results = [
        _turn(0, "get_stock_price", {"ticker": "AAPL", "date": "2024-03-31"}),
        _turn(1, "bad_tool", {"ticker": "AAPL", "date": "2024-06-30"}),   # violation
        _turn(2, "get_stock_price", {"ticker": "AAPL", "date": "2024-09-30"}),  # ok
    ]
    ds = score_mtcs(results, task)
    assert 0.0 < ds.score < 1.0
    assert ds.details["edges_passed"] == 1
    assert ds.details["edges_evaluated"] == 2


# --- Per-turn details structure ---

def test_mtcs_details_structure():
    task = _finance_task()
    results = [
        _turn(0, "get_stock_price", {"ticker": "AAPL", "date": "2024-03-31"}),
        _turn(1, "get_stock_price", {"ticker": "AAPL", "date": "2024-06-30"}),
    ]
    ds = score_mtcs(results, task)
    assert "per_turn" in ds.details
    assert isinstance(ds.details["per_turn"], list)
    entry = ds.details["per_turn"][0]
    assert "turn" in entry and "passed" in entry and "violations" in entry
