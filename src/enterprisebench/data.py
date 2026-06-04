from __future__ import annotations
import random
import uuid
from .core import BenchmarkTask, VERTICALS

SAMPLE_TOOLS: dict[str, dict] = {
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

# Richer task templates per vertical: (instruction, tool_name, arg_template)
TASK_TEMPLATES: dict[str, list[dict]] = {
    "finance": [
        {
            "instruction": "Retrieve the closing price of {ticker} on {date} for the earnings report.",
            "tool": "get_stock_price",
            "args": {"ticker": "AAPL", "date": "2024-03-31"},
        },
        {
            "instruction": "Calculate portfolio value: fetch prices for {ticker} as of {date}.",
            "tool": "get_stock_price",
            "args": {"ticker": "MSFT", "date": "2024-06-30"},
        },
        {
            "instruction": "Pull today's opening quote for {ticker} to compare with yesterday's close.",
            "tool": "get_stock_price",
            "args": {"ticker": "GOOGL", "date": "2024-09-01"},
        },
        {
            "instruction": "Fetch historical price for {ticker} on {date} for risk assessment.",
            "tool": "get_stock_price",
            "args": {"ticker": "TSLA", "date": "2023-12-31"},
        },
        {
            "instruction": "Get the adjusted closing price of {ticker} on {date} for dividend analysis.",
            "tool": "get_stock_price",
            "args": {"ticker": "AMZN", "date": "2024-01-15"},
        },
    ],
    "healthcare": [
        {
            "instruction": "Look up allergy history for patient {patient_id} before prescribing medication.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00123", "fields": ["allergies", "medications"]},
        },
        {
            "instruction": "Retrieve the latest lab results for patient {patient_id} for review.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00456", "fields": ["lab_results", "vitals"]},
        },
        {
            "instruction": "Fetch surgical history for patient {patient_id} ahead of a procedure.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00789", "fields": ["surgeries", "diagnoses"]},
        },
        {
            "instruction": "Pull insurance details for patient {patient_id} to verify coverage.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00321", "fields": ["insurance"]},
        },
        {
            "instruction": "Get contact information and next-of-kin for patient {patient_id}.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00654", "fields": ["contacts", "demographics"]},
        },
    ],
    "legal": [
        {
            "instruction": "Search for precedents on {query} in {jurisdiction} for contract dispute.",
            "tool": "search_case_law",
            "args": {"query": "breach of contract SaaS", "jurisdiction": "CA"},
        },
        {
            "instruction": "Find relevant case law on {query} in {jurisdiction} for IP litigation.",
            "tool": "search_case_law",
            "args": {"query": "trade secret misappropriation", "jurisdiction": "DE"},
        },
        {
            "instruction": "Look up employment discrimination rulings matching {query} in {jurisdiction}.",
            "tool": "search_case_law",
            "args": {"query": "wrongful termination retaliation", "jurisdiction": "NY"},
        },
        {
            "instruction": "Search for GDPR compliance precedents: {query} in {jurisdiction}.",
            "tool": "search_case_law",
            "args": {"query": "data breach notification obligations", "jurisdiction": "EU"},
        },
        {
            "instruction": "Retrieve case law on {query} in {jurisdiction} for merger review.",
            "tool": "search_case_law",
            "args": {"query": "antitrust horizontal merger", "jurisdiction": "FED"},
        },
    ],
    "devops": [
        {
            "instruction": "Check deployment status of {service} in {environment} before traffic shift.",
            "tool": "get_deployment_status",
            "args": {"service": "api-gateway", "environment": "production"},
        },
        {
            "instruction": "Verify {service} is healthy in {environment} after recent rollout.",
            "tool": "get_deployment_status",
            "args": {"service": "auth-service", "environment": "staging"},
        },
        {
            "instruction": "Poll {service} status in {environment} to decide on rollback.",
            "tool": "get_deployment_status",
            "args": {"service": "payment-processor", "environment": "production"},
        },
        {
            "instruction": "Fetch {service} deployment state in {environment} for incident report.",
            "tool": "get_deployment_status",
            "args": {"service": "data-pipeline", "environment": "prod"},
        },
        {
            "instruction": "Confirm {service} is running in {environment} post-maintenance window.",
            "tool": "get_deployment_status",
            "args": {"service": "recommendation-engine", "environment": "canary"},
        },
    ],
}


def make_task(
    vertical: str | None = None,
    difficulty: str = "medium",
    template_index: int | None = None,
) -> BenchmarkTask:
    vertical = vertical or random.choice(VERTICALS)
    templates = TASK_TEMPLATES[vertical]
    if template_index is None:
        tmpl = random.choice(templates)
    else:
        tmpl = templates[template_index % len(templates)]
    tool_schema = {
        "name": tmpl["tool"],
        "parameters": SAMPLE_TOOLS[vertical]["parameters"],
    }
    return BenchmarkTask(
        task_id=str(uuid.uuid4())[:8],
        vertical=vertical,
        instruction=tmpl["instruction"],
        tool_schema=tool_schema,
        expected_call={"name": tmpl["tool"], "arguments": tmpl["args"]},
        expected_output=f"Result from {tmpl['tool']}",
        difficulty=difficulty,
    )


def make_multi_turn_task(
    vertical: str = "finance",
    difficulty: str = "hard",
) -> BenchmarkTask:
    """Create a multi-turn task where each turn builds on the previous one."""
    templates = TASK_TEMPLATES[vertical]
    turns = [
        {"instruction": tmpl["instruction"], "expected_call": {"name": tmpl["tool"], "arguments": tmpl["args"]}}
        for tmpl in templates[:3]
    ]
    tool_schema = {
        "name": templates[0]["tool"],
        "parameters": SAMPLE_TOOLS[vertical]["parameters"],
    }
    return BenchmarkTask(
        task_id=str(uuid.uuid4())[:8],
        vertical=vertical,
        instruction=f"Multi-turn {vertical} workflow",
        tool_schema=tool_schema,
        expected_call={"name": templates[0]["tool"], "arguments": templates[0]["args"]},
        expected_output=f"Multi-turn result for {vertical}",
        difficulty=difficulty,
        turns=turns,
    )


def make_suite(n: int = 20, seed: int = 42) -> list[BenchmarkTask]:
    random.seed(seed)
    difficulties = ["easy", "medium", "hard"]
    return [
        make_task(
            vertical=VERTICALS[i % len(VERTICALS)],
            difficulty=difficulties[i % 3],
            template_index=i // len(VERTICALS),
        )
        for i in range(n)
    ]
