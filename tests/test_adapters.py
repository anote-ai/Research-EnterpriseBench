"""Tests for the OpenAI adapter (mocked — no real API calls)."""
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from enterprisebench.adapters import OpenAIAdapter, _estimate_cost
from enterprisebench.core import BenchmarkTask


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="fin_001",
        vertical="finance",
        instruction="Retrieve the account balance for account ID ACC-001.",
        tool_schema={
            "name": "get_account_balance",
            "description": "Get the balance for a given account.",
            "parameters": {
                "type": "object",
                "properties": {"account_id": {"type": "string"}},
                "required": ["account_id"],
            },
        },
        expected_call={"name": "get_account_balance", "arguments": {"account_id": "ACC-001"}},
        expected_output="The balance for ACC-001 is $5,000.",
    )


def _fake_openai_response(tool_name: str, tool_args: dict, content: str = "") -> MagicMock:
    """Build a minimal mock that matches the openai ChatCompletion response shape."""
    tool_call = SimpleNamespace(
        function=SimpleNamespace(name=tool_name, arguments=str(tool_args).replace("'", '"')),
    )
    message = SimpleNamespace(content=content, tool_calls=[tool_call])
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(prompt_tokens=50, completion_tokens=20)
    return SimpleNamespace(choices=[choice], usage=usage)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_adapter_requires_api_key():
    with pytest.raises(ValueError, match="API key"):
        OpenAIAdapter(api_key="")


def test_adapter_stores_model_and_key():
    adapter = OpenAIAdapter(model="gpt-4o", api_key="sk-test")
    assert adapter.model == "gpt-4o"
    assert adapter.api_key == "sk-test"


def test_adapter_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    adapter = OpenAIAdapter()
    assert adapter.api_key == "sk-env-key"


def test_adapter_call_returns_expected_format():
    task = _make_task()
    fake_response = _fake_openai_response(
        tool_name="get_account_balance",
        tool_args={"account_id": "ACC-001"},
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake_response

    with patch("enterprisebench.adapters.OpenAI", return_value=mock_client):
        adapter = OpenAIAdapter(model="gpt-4o-mini", api_key="sk-test")
        result = adapter(task)

    assert result["call"]["name"] == "get_account_balance"
    assert result["call"]["arguments"] == {"account_id": "ACC-001"}
    assert result["agent_name"] == "openai/gpt-4o-mini"
    assert isinstance(result["cost_usd"], float)
    assert result["cost_usd"] > 0


def test_adapter_handles_no_tool_call():
    """If the model returns plain text instead of a tool call, call should be empty."""
    task = _make_task()
    message = SimpleNamespace(content="I cannot help with that.", tool_calls=[])
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(prompt_tokens=30, completion_tokens=10)
    fake_response = SimpleNamespace(choices=[choice], usage=usage)

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake_response

    with patch("enterprisebench.adapters.OpenAI", return_value=mock_client):
        adapter = OpenAIAdapter(api_key="sk-test")
        result = adapter(task)

    assert result["call"] == {}
    assert result["output"] == "I cannot help with that."


def test_estimate_cost_known_model():
    # gpt-4o-mini: $0.15/1M input, $0.60/1M output
    cost = _estimate_cost("gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=0)
    assert abs(cost - 0.15) < 1e-9


def test_estimate_cost_unknown_model_falls_back():
    # Unknown model falls back to gpt-4o pricing
    cost_unknown = _estimate_cost("gpt-99-turbo", 1_000_000, 0)
    cost_4o = _estimate_cost("gpt-4o", 1_000_000, 0)
    assert cost_unknown == cost_4o
