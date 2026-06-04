from __future__ import annotations
import random
import uuid
from .core import BenchmarkTask, VERTICALS

SAMPLE_TOOLS = {
    "finance": {
        "name": "get_stock_price",
        "parameters": {"ticker": "string", "date": "string"},
    },
    "healthcare": {
        "name": "lookup_patient_record",
        "parameters": {"patient_id": "string", "fields": "array"},
    },
    "legal": {
        "name": "search_case_law",
        "parameters": {"query": "string", "jurisdiction": "string"},
    },
    "devops": {
        "name": "get_deployment_status",
        "parameters": {"service": "string", "environment": "string"},
    },
}


def make_task(vertical: str | None = None, difficulty: str = "medium") -> BenchmarkTask:
    vertical = vertical or random.choice(VERTICALS)
    tool = SAMPLE_TOOLS[vertical]
    args = {k: f"sample_{k}" for k in tool["parameters"]}
    return BenchmarkTask(
        task_id=str(uuid.uuid4())[:8],
        vertical=vertical,
        instruction=f"Use the {tool['name']} tool with sample arguments.",
        tool_schema={"name": tool["name"], "parameters": tool["parameters"]},
        expected_call={"name": tool["name"], "arguments": args},
        expected_output=f"Result from {tool['name']}",
        difficulty=difficulty,
    )


def make_suite(n: int = 20, seed: int = 42) -> list[BenchmarkTask]:
    random.seed(seed)
    difficulties = ["easy", "medium", "hard"]
    return [
        make_task(
            vertical=VERTICALS[i % len(VERTICALS)],
            difficulty=difficulties[i % 3],
        )
        for i in range(n)
    ]
