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
            "pre_state": {"ticker": "AAPL", "price_fetched": False},
            "expected_post_state": {"ticker": "AAPL", "date": "2024-03-31"},
        },
        {
            "instruction": "Calculate portfolio value: fetch prices for {ticker} as of {date}.",
            "tool": "get_stock_price",
            "args": {"ticker": "MSFT", "date": "2024-06-30"},
            "pre_state": {"ticker": "MSFT", "price_fetched": False},
            "expected_post_state": {"ticker": "MSFT", "date": "2024-06-30"},
        },
        {
            "instruction": "Pull today's opening quote for {ticker} to compare with yesterday's close.",
            "tool": "get_stock_price",
            "args": {"ticker": "GOOGL", "date": "2024-09-01"},
            "pre_state": {"ticker": "GOOGL", "price_fetched": False},
            "expected_post_state": {"ticker": "GOOGL", "date": "2024-09-01"},
        },
        {
            "instruction": "Fetch historical price for {ticker} on {date} for risk assessment.",
            "tool": "get_stock_price",
            "args": {"ticker": "TSLA", "date": "2023-12-31"},
            "pre_state": {"ticker": "TSLA", "price_fetched": False},
            "expected_post_state": {"ticker": "TSLA", "date": "2023-12-31"},
        },
        {
            "instruction": "Get the adjusted closing price of {ticker} on {date} for dividend analysis.",
            "tool": "get_stock_price",
            "args": {"ticker": "AMZN", "date": "2024-01-15"},
            "pre_state": {"ticker": "AMZN", "price_fetched": False},
            "expected_post_state": {"ticker": "AMZN", "date": "2024-01-15"},
        },
        {
            "instruction": "Fetch intraday high for {ticker} on {date} for volatility report.",
            "tool": "get_stock_price",
            "args": {"ticker": "NVDA", "date": "2024-02-20"},
            "pre_state": {"ticker": "NVDA", "price_fetched": False},
            "expected_post_state": {"ticker": "NVDA", "date": "2024-02-20"},
        },
        {
            "instruction": "Get closing price of {ticker} on {date} for quarterly rebalancing.",
            "tool": "get_stock_price",
            "args": {"ticker": "META", "date": "2024-03-15"},
            "pre_state": {"ticker": "META", "price_fetched": False},
            "expected_post_state": {"ticker": "META", "date": "2024-03-15"},
        },
        {
            "instruction": "Retrieve price of {ticker} on {date} for options expiry analysis.",
            "tool": "get_stock_price",
            "args": {"ticker": "SPY", "date": "2024-04-19"},
            "pre_state": {"ticker": "SPY", "price_fetched": False},
            "expected_post_state": {"ticker": "SPY", "date": "2024-04-19"},
        },
        {
            "instruction": "Pull {ticker} price on {date} for year-end tax-loss harvesting.",
            "tool": "get_stock_price",
            "args": {"ticker": "QQQ", "date": "2023-12-29"},
            "pre_state": {"ticker": "QQQ", "price_fetched": False},
            "expected_post_state": {"ticker": "QQQ", "date": "2023-12-29"},
        },
        {
            "instruction": "Get {ticker} share price on {date} before earnings call.",
            "tool": "get_stock_price",
            "args": {"ticker": "NFLX", "date": "2024-07-17"},
            "pre_state": {"ticker": "NFLX", "price_fetched": False},
            "expected_post_state": {"ticker": "NFLX", "date": "2024-07-17"},
        },
        {
            "instruction": "Fetch closing price for {ticker} on {date} for sector rotation model.",
            "tool": "get_stock_price",
            "args": {"ticker": "XOM", "date": "2024-05-01"},
            "pre_state": {"ticker": "XOM", "price_fetched": False},
            "expected_post_state": {"ticker": "XOM", "date": "2024-05-01"},
        },
        {
            "instruction": "Retrieve {ticker} price on {date} for index rebalancing calculation.",
            "tool": "get_stock_price",
            "args": {"ticker": "BRK.B", "date": "2024-06-03"},
            "pre_state": {"ticker": "BRK.B", "price_fetched": False},
            "expected_post_state": {"ticker": "BRK.B", "date": "2024-06-03"},
        },
        {
            "instruction": "Pull closing price for {ticker} on {date} for margin call assessment.",
            "tool": "get_stock_price",
            "args": {"ticker": "TSLA", "date": "2024-08-05"},
            "pre_state": {"ticker": "TSLA", "price_fetched": False},
            "expected_post_state": {"ticker": "TSLA", "date": "2024-08-05"},
        },
        {
            "instruction": "Get price of {ticker} on {date} for ESG fund compliance check.",
            "tool": "get_stock_price",
            "args": {"ticker": "MSFT", "date": "2024-09-30"},
            "pre_state": {"ticker": "MSFT", "price_fetched": False},
            "expected_post_state": {"ticker": "MSFT", "date": "2024-09-30"},
        },
    ],
    "healthcare": [
        {
            "instruction": "Look up allergy history for patient {patient_id} before prescribing medication.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00123", "fields": ["allergies", "medications"]},
            "pre_state": {"patient_id": "P-00123", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00123"},
        },
        {
            "instruction": "Retrieve the latest lab results for patient {patient_id} for review.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00456", "fields": ["lab_results", "vitals"]},
            "pre_state": {"patient_id": "P-00456", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00456"},
        },
        {
            "instruction": "Fetch surgical history for patient {patient_id} ahead of a procedure.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00789", "fields": ["surgeries", "diagnoses"]},
            "pre_state": {"patient_id": "P-00789", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00789"},
        },
        {
            "instruction": "Pull insurance details for patient {patient_id} to verify coverage.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00321", "fields": ["insurance"]},
            "pre_state": {"patient_id": "P-00321", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00321"},
        },
        {
            "instruction": "Get contact information and next-of-kin for patient {patient_id}.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00654", "fields": ["contacts", "demographics"]},
            "pre_state": {"patient_id": "P-00654", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00654"},
        },
        {
            "instruction": "Retrieve immunization records for patient {patient_id} for school enrollment.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-00987", "fields": ["immunizations"]},
            "pre_state": {"patient_id": "P-00987", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-00987"},
        },
        {
            "instruction": "Fetch prescription history for patient {patient_id} to check for drug interactions.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01010", "fields": ["medications", "allergies"]},
            "pre_state": {"patient_id": "P-01010", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01010"},
        },
        {
            "instruction": "Look up prior diagnoses for patient {patient_id} ahead of specialist referral.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01122", "fields": ["diagnoses"]},
            "pre_state": {"patient_id": "P-01122", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01122"},
        },
        {
            "instruction": "Pull emergency contact for patient {patient_id} for post-op notification.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01234", "fields": ["contacts"]},
            "pre_state": {"patient_id": "P-01234", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01234"},
        },
        {
            "instruction": "Retrieve radiology results for patient {patient_id} for oncology review.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01357", "fields": ["radiology", "lab_results"]},
            "pre_state": {"patient_id": "P-01357", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01357"},
        },
        {
            "instruction": "Get advance directive for patient {patient_id} before surgery.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01470", "fields": ["advance_directive"]},
            "pre_state": {"patient_id": "P-01470", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01470"},
        },
        {
            "instruction": "Fetch discharge summary for patient {patient_id} for follow-up scheduling.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01598", "fields": ["discharge_summary"]},
            "pre_state": {"patient_id": "P-01598", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01598"},
        },
        {
            "instruction": "Pull mental health history for patient {patient_id} for crisis assessment.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01612", "fields": ["mental_health", "medications"]},
            "pre_state": {"patient_id": "P-01612", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01612"},
        },
        {
            "instruction": "Retrieve genetic screening results for patient {patient_id} for risk counseling.",
            "tool": "lookup_patient_record",
            "args": {"patient_id": "P-01789", "fields": ["genetics", "diagnoses"]},
            "pre_state": {"patient_id": "P-01789", "record_accessed": False},
            "expected_post_state": {"patient_id": "P-01789"},
        },
    ],
    "legal": [
        {
            "instruction": "Search for precedents on {query} in {jurisdiction} for contract dispute.",
            "tool": "search_case_law",
            "args": {"query": "breach of contract SaaS", "jurisdiction": "CA"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "breach of contract SaaS", "jurisdiction": "CA"},
        },
        {
            "instruction": "Find relevant case law on {query} in {jurisdiction} for IP litigation.",
            "tool": "search_case_law",
            "args": {"query": "trade secret misappropriation", "jurisdiction": "DE"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "trade secret misappropriation", "jurisdiction": "DE"},
        },
        {
            "instruction": "Look up employment discrimination rulings matching {query} in {jurisdiction}.",
            "tool": "search_case_law",
            "args": {"query": "wrongful termination retaliation", "jurisdiction": "NY"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "wrongful termination retaliation", "jurisdiction": "NY"},
        },
        {
            "instruction": "Search for GDPR compliance precedents: {query} in {jurisdiction}.",
            "tool": "search_case_law",
            "args": {"query": "data breach notification obligations", "jurisdiction": "EU"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "data breach notification obligations", "jurisdiction": "EU"},
        },
        {
            "instruction": "Retrieve case law on {query} in {jurisdiction} for merger review.",
            "tool": "search_case_law",
            "args": {"query": "antitrust horizontal merger", "jurisdiction": "FED"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "antitrust horizontal merger", "jurisdiction": "FED"},
        },
        {
            "instruction": "Find rulings on {query} in {jurisdiction} for securities fraud defense.",
            "tool": "search_case_law",
            "args": {"query": "securities fraud materiality standard", "jurisdiction": "FED"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "securities fraud materiality standard", "jurisdiction": "FED"},
        },
        {
            "instruction": "Search for {query} precedents in {jurisdiction} for landlord-tenant dispute.",
            "tool": "search_case_law",
            "args": {"query": "constructive eviction commercial lease", "jurisdiction": "NY"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "constructive eviction commercial lease", "jurisdiction": "NY"},
        },
        {
            "instruction": "Look up {query} rulings in {jurisdiction} for class-action certification.",
            "tool": "search_case_law",
            "args": {"query": "class action predominance commonality", "jurisdiction": "FED"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "class action predominance commonality", "jurisdiction": "FED"},
        },
        {
            "instruction": "Retrieve {query} case law in {jurisdiction} for product liability claim.",
            "tool": "search_case_law",
            "args": {"query": "strict liability design defect", "jurisdiction": "CA"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "strict liability design defect", "jurisdiction": "CA"},
        },
        {
            "instruction": "Find case law on {query} in {jurisdiction} for non-compete enforcement.",
            "tool": "search_case_law",
            "args": {"query": "non-compete enforceability blue pencil", "jurisdiction": "TX"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "non-compete enforceability blue pencil", "jurisdiction": "TX"},
        },
        {
            "instruction": "Search {query} precedents in {jurisdiction} for patent infringement defense.",
            "tool": "search_case_law",
            "args": {"query": "obviousness prior art patent", "jurisdiction": "FED"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "obviousness prior art patent", "jurisdiction": "FED"},
        },
        {
            "instruction": "Retrieve {query} rulings in {jurisdiction} for insurance coverage dispute.",
            "tool": "search_case_law",
            "args": {"query": "duty to defend ambiguity insurance", "jurisdiction": "IL"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "duty to defend ambiguity insurance", "jurisdiction": "IL"},
        },
        {
            "instruction": "Find {query} precedents in {jurisdiction} for corporate veil piercing.",
            "tool": "search_case_law",
            "args": {"query": "alter ego liability piercing corporate veil", "jurisdiction": "DE"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "alter ego liability piercing corporate veil", "jurisdiction": "DE"},
        },
        {
            "instruction": "Search {query} in {jurisdiction} for environmental compliance defense.",
            "tool": "search_case_law",
            "args": {"query": "CERCLA innocent landowner defense", "jurisdiction": "FED"},
            "pre_state": {"search_executed": False},
            "expected_post_state": {"query": "CERCLA innocent landowner defense", "jurisdiction": "FED"},
        },
    ],
    "devops": [
        {
            "instruction": "Check deployment status of {service} in {environment} before traffic shift.",
            "tool": "get_deployment_status",
            "args": {"service": "api-gateway", "environment": "production"},
            "pre_state": {"service": "api-gateway", "status_checked": False},
            "expected_post_state": {"service": "api-gateway", "environment": "production"},
        },
        {
            "instruction": "Verify {service} is healthy in {environment} after recent rollout.",
            "tool": "get_deployment_status",
            "args": {"service": "auth-service", "environment": "staging"},
            "pre_state": {"service": "auth-service", "status_checked": False},
            "expected_post_state": {"service": "auth-service", "environment": "staging"},
        },
        {
            "instruction": "Poll {service} status in {environment} to decide on rollback.",
            "tool": "get_deployment_status",
            "args": {"service": "payment-processor", "environment": "production"},
            "pre_state": {"service": "payment-processor", "status_checked": False},
            "expected_post_state": {"service": "payment-processor", "environment": "production"},
        },
        {
            "instruction": "Fetch {service} deployment state in {environment} for incident report.",
            "tool": "get_deployment_status",
            "args": {"service": "data-pipeline", "environment": "prod"},
            "pre_state": {"service": "data-pipeline", "status_checked": False},
            "expected_post_state": {"service": "data-pipeline", "environment": "prod"},
        },
        {
            "instruction": "Confirm {service} is running in {environment} post-maintenance window.",
            "tool": "get_deployment_status",
            "args": {"service": "recommendation-engine", "environment": "canary"},
            "pre_state": {"service": "recommendation-engine", "status_checked": False},
            "expected_post_state": {"service": "recommendation-engine", "environment": "canary"},
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
        instruction=tmpl["instruction"].format(**tmpl["args"]),
        tool_schema=tool_schema,
        expected_call={"name": tmpl["tool"], "arguments": tmpl["args"]},
        expected_output=f"Result from {tmpl['tool']}",
        difficulty=difficulty,
        pre_state=tmpl.get("pre_state", {}),
        expected_post_state=tmpl.get("expected_post_state", {}),
    )


def make_multi_turn_task(
    vertical: str = "finance",
    difficulty: str = "hard",
) -> BenchmarkTask:
    """Create a multi-turn task where each turn builds on the previous one."""
    templates = TASK_TEMPLATES[vertical]
    turns = [
        {"instruction": tmpl["instruction"].format(**tmpl["args"]), "expected_call": {"name": tmpl["tool"], "arguments": tmpl["args"]}}
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
