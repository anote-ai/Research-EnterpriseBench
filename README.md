# EnterpriseBench

[![CI](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml/badge.svg)](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What this is

EnterpriseBench is a benchmark for measuring whether LLM agents behave **safely and compliantly** on enterprise workflows, not just whether they complete tasks.

Existing benchmarks (GAIA, AgentBench, WorkArena) ask "did the agent finish the task?" EnterpriseBench also asks:

- **Policy Violation Rate (PVR)**: did the agent do things it was explicitly told not to do?
- **False Completion Rate (FCR)**: did the agent claim success when the underlying state is wrong?
- **Multi-Turn Consistency (MTCS)**: did the agent contradict its own earlier decisions?
- **Audit Trail Quality (ATR)**: can a human reconstruct why each action was taken?

See [DESIGN_DOC.md](DESIGN_DOC.md) for the full research specification.

## Current implementation status

| Layer | Status |
|---|---|
| Task schema (4 industry verticals, tool-call format) | Implemented — `src/enterprisebench/core.py`, `data.py` |
| 5-dimension scoring (syntactic, semantic, reliability, cost, latency) | Implemented — `src/enterprisebench/evaluate.py` |
| Policy taxonomy + PVR/FCR metrics | Implemented — `src/enterprisebench/policy.py` |
| OpenAI agent adapter + Experiment 1 end-to-end | In progress |
| Full 250-task dataset with policy annotations | Future work |
| Multi-turn consistency graph (MTCS) | Future work |
| Audit trail quality rubric (ATR) | Future work |

For a detailed experiment readiness matrix, see [experiments/README.md](experiments/README.md).

## Quick Start

```bash
pip install -e ".[dev]"
python scripts/run_benchmark.py
```

```python
from enterprisebench.data import make_suite
from enterprisebench.core import BenchmarkSuite
from enterprisebench.evaluate import evaluate_result, aggregate_scores

# Build a task suite
suite = BenchmarkSuite(tasks=make_suite(20))
print(suite.stats())
# {'total': 20, 'by_vertical': {'finance': 5, 'healthcare': 5, 'legal': 5, 'devops': 5}, ...}

# Run any agent function and score it
def my_agent(task):
    return {"call": task.expected_call, "output": task.expected_output,
            "cost_usd": 0.002, "agent_name": "my-agent"}

scores = []
for task in suite.tasks:
    result = suite.run_agent(my_agent, task)
    dim_scores = evaluate_result(result, task)
    scores.append(dim_scores["syntactic"].score)

print(aggregate_scores(scores))
# {'mean': 1.0, 'std': 0.0, 'min': 1.0, 'max': 1.0, 'n': 20}
```

## Policy checking

```python
from enterprisebench.policy import check_policies, policy_violation_rate, CRM_POL_003

pre_state = {"contacts": [{"id": "C001", "active_deals": ["D-1"]}]}
action = {"type": "merge_contacts", "source_ids": ["C001"]}

result = check_policies("crm_001", [CRM_POL_003], pre_state, action, post_state={})
print(result.has_violation)          # True
print(result.violations[0].rule_id)  # 'CRM_POL_003'

# Aggregate across many tasks:
# pvr = policy_violation_rate(list_of_results)
```

## Task schema

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique identifier |
| `vertical` | `str` | Industry vertical (finance/healthcare/legal/devops) |
| `instruction` | `str` | Natural language instruction for the agent |
| `tool_schema` | `dict` | JSON schema of the available tool |
| `expected_call` | `dict` | Ground-truth tool call (name + arguments) |
| `expected_output` | `str` | Expected natural language response |
| `difficulty` | `str` | Task difficulty (easy/medium/hard) |

## Scoring dimensions

| Dimension | Description | Score Range |
|---|---|---|
| **Syntactic** | Tool name match + argument key Jaccard similarity | 0–1 |
| **Semantic** | Intent alignment between instruction and response | 0–1 |
| **Reliability** | Consistency across repeated runs | 0–1 |
| **Cost** | Normalized cost relative to per-task budget | 0–1 |
| **Latency** | Normalized latency relative to response budget | 0–1 |

## Citation

```bibtex
@misc{enterprisebench2026,
  title        = {EnterpriseBench: Evaluating AI Agents on Policy Compliance, Auditability, and Multi-Turn Consistency in Enterprise Workflows},
  author       = {Anote AI Research},
  year         = {2026},
  howpublished = {\url{https://github.com/anote-ai/research-enterprisebench}},
  note         = {Preprint}
}
```
