"""Real LLM agent adapters for EnterpriseBench.

Each adapter follows the same contract as the mock agent in run_benchmark.py:
    agent_fn(task: BenchmarkTask) -> dict
        call       — dict with "name" and "arguments"
        output     — str, the agent's natural-language response
        cost_usd   — float
        agent_name — str

Usage
-----
    from enterprisebench.agents import ClaudeAgent, OpenAIAgent

    agent = ClaudeAgent(model="claude-haiku-4-5-20251001")
    result = suite.run_agent(agent, task)

Both adapters require the relevant API key in the environment:
    ANTHROPIC_API_KEY  for ClaudeAgent
    OPENAI_API_KEY     for OpenAIAgent
"""
from __future__ import annotations

import json
import os
from typing import Any

from .core import BenchmarkTask


def _build_system_prompt() -> str:
    return (
        "You are an enterprise AI assistant. When given a task, you must call "
        "the appropriate tool with the correct arguments. Always use the tool "
        "provided — do not answer from memory. After calling the tool, summarize "
        "the result clearly."
    )


def _build_user_message(task: BenchmarkTask) -> str:
    return task.instruction


class ClaudeAgent:
    """Calls Anthropic Claude with native tool-use to complete benchmark tasks."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001") -> None:
        try:
            import anthropic
        except ImportError as e:
            raise ImportError("pip install anthropic") from e
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.name = f"claude/{model}"

    def __call__(self, task: BenchmarkTask) -> dict[str, Any]:
        import anthropic

        tool_def = {
            "name": task.tool_schema["name"],
            "description": f"Tool for: {task.instruction}",
            "input_schema": {
                "type": "object",
                "properties": {
                    k: {"type": "string", "description": k}
                    for k in task.tool_schema.get("parameters", {})
                },
                "required": list(task.tool_schema.get("parameters", {}).keys()),
            },
        }

        input_tokens = 0
        output_tokens = 0
        tool_call: dict[str, Any] = {}
        text_output = ""

        response = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_build_system_prompt(),
            tools=[tool_def],
            tool_choice={"type": "auto"},
            messages=[{"role": "user", "content": _build_user_message(task)}],
        )
        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens

        for block in response.content:
            if block.type == "tool_use":
                tool_call = {"name": block.name, "arguments": block.input}
            elif block.type == "text":
                text_output += block.text

        # If the model used a tool, send the (mocked) tool result back for a final summary
        if tool_call and response.stop_reason == "tool_use":
            tool_result_content = [
                {"type": "tool_result", "tool_use_id": block.id, "content": "mock_result"}
                for block in response.content
                if block.type == "tool_use"
            ]
            followup = self._client.messages.create(
                model=self.model,
                max_tokens=256,
                system=_build_system_prompt(),
                tools=[tool_def],
                messages=[
                    {"role": "user", "content": _build_user_message(task)},
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_result_content},
                ],
            )
            input_tokens += followup.usage.input_tokens
            output_tokens += followup.usage.output_tokens
            for block in followup.content:
                if block.type == "text":
                    text_output += block.text

        # Approximate cost: Haiku pricing ~$0.25/M input, $1.25/M output
        cost_usd = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000

        return {
            "call": tool_call,
            "output": text_output.strip(),
            "cost_usd": cost_usd,
            "agent_name": self.name,
        }


class OpenAIAgent:
    """Calls OpenAI GPT with function-calling to complete benchmark tasks."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            import openai
        except ImportError as e:
            raise ImportError("pip install openai") from e
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set")
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.name = f"openai/{model}"

    def __call__(self, task: BenchmarkTask) -> dict[str, Any]:
        import openai

        function_def = {
            "name": task.tool_schema["name"],
            "description": f"Tool for: {task.instruction}",
            "parameters": {
                "type": "object",
                "properties": {
                    k: {"type": "string", "description": k}
                    for k in task.tool_schema.get("parameters", {})
                },
                "required": list(task.tool_schema.get("parameters", {}).keys()),
            },
        }

        tool_call: dict[str, Any] = {}
        text_output = ""
        prompt_tokens = 0
        completion_tokens = 0

        response = self._client.chat.completions.create(
            model=self.model,
            tools=[{"type": "function", "function": function_def}],
            tool_choice="auto",
            messages=[
                {"role": "system", "content": _build_system_prompt()},
                {"role": "user", "content": _build_user_message(task)},
            ],
        )
        usage = response.usage
        prompt_tokens += usage.prompt_tokens
        completion_tokens += usage.completion_tokens

        msg = response.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            tool_call = {
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            }
            # Send mock tool result back for natural-language summary
            followup = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _build_system_prompt()},
                    {"role": "user", "content": _build_user_message(task)},
                    msg,
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "mock_result",
                    },
                ],
            )
            fu = followup.usage
            prompt_tokens += fu.prompt_tokens
            completion_tokens += fu.completion_tokens
            text_output = followup.choices[0].message.content or ""
        else:
            text_output = msg.content or ""

        # Approximate cost: gpt-4o-mini $0.15/M input, $0.60/M output
        cost_usd = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000

        return {
            "call": tool_call,
            "output": text_output.strip(),
            "cost_usd": cost_usd,
            "agent_name": self.name,
        }
