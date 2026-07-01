"""Real agent adapters for EnterpriseBench.

Each adapter wraps a live LLM API and returns the dict format expected by
BenchmarkSuite.run_agent():
    {"call": {...}, "output": "...", "cost_usd": float, "agent_name": "..."}

Usage example:
    from enterprisebench.adapters import OpenAIAdapter
    agent = OpenAIAdapter(model="gpt-4o-mini")
    result = suite.run_agent(agent, task)

The adapter uses OpenAI tool-calling: it passes the task's tool_schema as a
function definition and reads back the first tool_call from the response.
"""
from __future__ import annotations

import json
import os

try:
    from openai import OpenAI  # type: ignore[import]
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]


class OpenAIAdapter:
    """Calls the OpenAI Chat Completions API with tool-calling enabled.

    Args:
        model: OpenAI model name, e.g. "gpt-4o-mini" or "gpt-4o".
        api_key: OpenAI API key. Defaults to the OPENAI_API_KEY env var.

    The adapter sends the task instruction as a user message and registers
    the task's tool_schema as the only available function. It reads the first
    tool call from the response and maps it back to the benchmark format.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required: pass api_key= or set OPENAI_API_KEY env var."
            )

    def __call__(self, task: object) -> dict:
        """Run the task and return a result dict compatible with BenchmarkSuite."""
        if OpenAI is None:
            raise ImportError("openai package is required: pip install openai")

        client = OpenAI(api_key=self.api_key)

        # Build the tool definition from the task's tool_schema
        tool_schema = getattr(task, "tool_schema", {})
        function_def = {
            "name": tool_schema.get("name", "tool"),
            "description": tool_schema.get("description", ""),
            "parameters": tool_schema.get("parameters", {"type": "object", "properties": {}}),
        }

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": getattr(task, "instruction", "")}],
            tools=[{"type": "function", "function": function_def}],
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

        # Extract the tool call if the model used one
        predicted_call: dict = {}
        output_text = message.content or ""

        if message.tool_calls:
            tc = message.tool_calls[0]
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            predicted_call = {"name": tc.function.name, "arguments": args}
            output_text = output_text or f"Called {tc.function.name}"

        # Estimate cost from token usage (rough approximation)
        usage = response.usage
        cost_usd = _estimate_cost(self.model, usage.prompt_tokens, usage.completion_tokens)

        return {
            "call": predicted_call,
            "output": output_text,
            "cost_usd": cost_usd,
            "agent_name": f"openai/{self.model}",
        }


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Rough cost estimate in USD based on published OpenAI pricing (July 2026).

    These are approximations — use the OpenAI dashboard for accurate billing.
    """
    # Price per 1M tokens: (input, output)
    pricing: dict[str, tuple[float, float]] = {
        "gpt-4o":       (2.50, 10.00),
        "gpt-4o-mini":  (0.15,  0.60),
        "gpt-4-turbo":  (10.00, 30.00),
    }
    input_price, output_price = pricing.get(model, (2.50, 10.00))
    return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
