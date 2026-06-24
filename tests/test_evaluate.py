import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.evaluate import (
    score_syntactic,
    score_semantic,
    score_reliability,
    score_latency,
    score_cost,
    aggregate_scores,
    pareto_frontier,
    task_complexity_score,
    agent_leaderboard,
    claims_success,
    verify_post_state,
    score_false_completion,
)
from enterprisebench.core import BenchmarkTask, TaskResult


def test_score_syntactic_perfect_match():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_syntactic(pred, exp)
    assert result.score == 1.0


def test_score_syntactic_name_mismatch():
    pred = {"name": "wrong_tool", "arguments": {"ticker": "AAPL"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    result = score_syntactic(pred, exp)
    assert result.score <= 0.6


def test_score_syntactic_empty_dicts():
    result = score_syntactic({}, {})
    assert result.score == 0.0


def test_score_syntactic_includes_value_jaccard():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "wrong-date"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_syntactic(pred, exp)
    assert 0.5 < result.score < 1.0
    assert "value_jaccard" in result.details


def test_score_syntactic_key_jaccard_in_details():
    pred = {"name": "tool", "arguments": {"a": "1"}}
    exp = {"name": "tool", "arguments": {"a": "1", "b": "2"}}
    result = score_syntactic(pred, exp)
    assert "key_jaccard" in result.details
    assert result.details["key_jaccard"] < 1.0


def test_score_semantic_perfect_match():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_semantic(pred, exp)
    assert result.score >= 0.9


def test_score_semantic_fuzzy_value_tolerance():
    pred = {"name": "get_stock_price", "arguments": {"ticker": "aapl", "date": "2024-01-01"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-01-01"}}
    result = score_semantic(pred, exp)
    assert result.score > 0.7


def test_score_semantic_name_mismatch_penalised():
    pred = {"name": "wrong_tool", "arguments": {"ticker": "AAPL"}}
    exp = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    result = score_semantic(pred, exp)
    assert result.score < 0.8


def test_score_semantic_empty():
    result = score_semantic({}, {})
    assert result.score == 0.0


def test_score_semantic_details_keys():
    pred = {"name": "tool", "arguments": {"x": "1"}}
    exp = {"name": "tool", "arguments": {"x": "1"}}
    result = score_semantic(pred, exp, instruction="call tool x")
    for key in ("name_similarity", "arg_similarity", "instruction_boost"):
        assert key in result.details


def test_score_latency_under_budget():
    result = score_latency(500.0, budget_ms=2000.0)
    assert result.score > 0.5


def test_score_cost_over_budget():
    result = score_cost(0.05, budget_usd=0.01)
    assert result.score == 0.0


def test_aggregate_scores():
    agg = aggregate_scores([1.0, 0.0, 0.5])
    assert abs(agg["mean"] - 0.5) < 1e-9
    assert agg["min"] == 0.0
    assert agg["max"] == 1.0
    assert agg["n"] == 3
    assert agg["std"] > 0


def test_pareto_frontier():
    points = [
        {"cost": 0.1, "score": 0.9},
        {"cost": 0.2, "score": 0.8},
        {"cost": 0.3, "score": 0.95},
    ]
    frontier = pareto_frontier(points)
    assert len(frontier) >= 1
    assert frontier[0]["cost"] == 0.1


def test_task_complexity_simple():
    score = task_complexity_score(n_required_tools=1, n_dependencies=0, has_conditional=False)
    assert 0.0 <= score <= 1.0
    assert score < 0.3


def test_task_complexity_complex():
    score = task_complexity_score(n_required_tools=5, n_dependencies=4, has_conditional=True)
    assert score > 0.7


def test_agent_leaderboard_sorted():
    results = {"agent_a": [0.9, 0.8], "agent_b": [0.4, 0.5]}
    board = agent_leaderboard(results)
    assert board[0]["agent"] == "agent_a"
    assert board[0]["mean"] > board[1]["mean"]


def test_agent_leaderboard_weights_change_ranking():
    # agent_a: strong syntactic, weak semantic; agent_b: the reverse
    results = {"agent_a": [0.9, 0.2], "agent_b": [0.2, 0.9]}
    board = agent_leaderboard(results, weights={"syntactic": 0.1, "semantic": 0.9})
    assert board[0]["agent"] == "agent_b"
    board = agent_leaderboard(results, weights={"syntactic": 0.9, "semantic": 0.1})
    assert board[0]["agent"] == "agent_a"


def test_score_reliability_perfect():
    calls = [{"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}] * 5
    expected = [{"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}]
    result = score_reliability(calls, expected)
    assert result.score == 1.0
    assert result.details["hits"] == 5


def test_score_reliability_partial():
    predicted = [
        {"name": "get_stock_price"},
        {"name": "wrong_tool"},
        {"name": "get_stock_price"},
        {"name": "get_stock_price"},
    ]
    expected = [{"name": "get_stock_price"}]
    result = score_reliability(predicted, expected)
    assert abs(result.score - 0.75) < 1e-9
    assert result.details["total"] == 4


def test_score_reliability_zero():
    predicted = [{"name": "wrong_tool"}, {"name": "also_wrong"}]
    expected = [{"name": "get_stock_price"}]
    result = score_reliability(predicted, expected)
    assert result.score == 0.0


def test_score_reliability_empty_inputs():
    result = score_reliability([], [])
    assert result.score == 0.0
    assert "reason" in result.details


def test_score_reliability_single_hit():
    pred = [{"name": "lookup_patient_record"}]
    exp = [{"name": "lookup_patient_record"}]
    result = score_reliability(pred, exp)
    assert result.score == 1.0
    assert result.details["expected_name"] == "lookup_patient_record"


# --- FCR: claims_success ---

def test_claims_success_positive_phrases():
    assert claims_success("Done. Successfully retrieved the stock price.")
    assert claims_success("I have fetched the record for patient P-00123.")
    assert claims_success("Here is the deployment status you requested.")
    assert claims_success("The result has been retrieved.")
    assert claims_success("Confirmed: api-gateway is running in production.")

def test_claims_success_negative():
    assert not claims_success("")
    assert not claims_success("An error occurred while querying the API.")
    assert not claims_success("Unable to find matching case law.")

def test_claims_success_case_insensitive():
    assert claims_success("SUCCESSFULLY completed the task.")
    assert claims_success("RETRIEVED the patient record.")


# --- FCR: verify_post_state ---

def test_verify_post_state_exact_match():
    call = {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-03-31"}}
    post = {"ticker": "AAPL", "date": "2024-03-31"}
    assert verify_post_state(call, post) is True

def test_verify_post_state_wrong_value():
    call = {"name": "get_stock_price", "arguments": {"ticker": "MSFT", "date": "2024-03-31"}}
    post = {"ticker": "AAPL", "date": "2024-03-31"}
    assert verify_post_state(call, post) is False

def test_verify_post_state_missing_key():
    call = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    post = {"ticker": "AAPL", "date": "2024-03-31"}
    assert verify_post_state(call, post) is False

def test_verify_post_state_empty_expected():
    # No constraints means any call passes
    call = {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
    assert verify_post_state(call, {}) is True

def test_verify_post_state_case_insensitive():
    call = {"name": "get_stock_price", "arguments": {"ticker": "aapl", "date": "2024-03-31"}}
    post = {"ticker": "AAPL", "date": "2024-03-31"}
    assert verify_post_state(call, post) is True


# --- FCR: score_false_completion ---

def _make_task(expected_post_state=None):
    return BenchmarkTask(
        task_id="t-fcr",
        vertical="finance",
        instruction="Get AAPL price",
        tool_schema={"name": "get_stock_price", "parameters": {}},
        expected_call={"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-03-31"}},
        expected_output="150.0",
        expected_post_state=expected_post_state or {"ticker": "AAPL", "date": "2024-03-31"},
    )

def _make_result(predicted_call, output):
    return TaskResult(
        task_id="t-fcr",
        vertical="finance",
        predicted_call=predicted_call,
        predicted_output=output,
        latency_ms=100.0,
        cost_usd=0.001,
        agent_name="test-agent",
    )

def test_score_false_completion_genuine_success():
    # Correct call + success claim → not a false completion → score 1.0
    result = _make_result(
        {"name": "get_stock_price", "arguments": {"ticker": "AAPL", "date": "2024-03-31"}},
        "Successfully retrieved the closing price.",
    )
    ds = score_false_completion(result, _make_task())
    assert ds.score == 1.0
    assert ds.details["false_completion"] is False
    assert ds.details["claimed_success"] is True
    assert ds.details["state_verified"] is True

def test_score_false_completion_wrong_call_but_claims_success():
    # Wrong ticker + "done" in output → FALSE COMPLETION → score 0.0
    result = _make_result(
        {"name": "get_stock_price", "arguments": {"ticker": "MSFT", "date": "2024-03-31"}},
        "Done. I have retrieved the stock price.",
    )
    ds = score_false_completion(result, _make_task())
    assert ds.score == 0.0
    assert ds.details["false_completion"] is True
    assert ds.details["claimed_success"] is True
    assert ds.details["state_verified"] is False

def test_score_false_completion_wrong_call_no_claim():
    # Wrong call but agent doesn't claim success → not a false completion → score 1.0
    result = _make_result(
        {"name": "get_stock_price", "arguments": {"ticker": "MSFT", "date": "2024-03-31"}},
        "An error occurred.",
    )
    ds = score_false_completion(result, _make_task())
    assert ds.score == 1.0
    assert ds.details["false_completion"] is False

def test_score_false_completion_no_post_state_defined():
    # Task with no expected_post_state — any call passes verification
    task = BenchmarkTask(
        task_id="t-nostate",
        vertical="devops",
        instruction="Check status",
        tool_schema={},
        expected_call={},
        expected_output="ok",
    )
    result = _make_result({}, "Successfully checked.")
    ds = score_false_completion(result, task)
    assert ds.score == 1.0
    assert ds.details["state_verified"] is True
