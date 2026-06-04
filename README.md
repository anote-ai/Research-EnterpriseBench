# EnterpriseBench

[![CI](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml/badge.svg)](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Abstract

EnterpriseBench is a multi-dimensional evaluation framework for assessing large language model (LLM) agents on enterprise tool-use tasks across four industry verticals: finance, healthcare, legal, and DevOps. Unlike single-score benchmarks, EnterpriseBench decomposes agent performance along five orthogonal dimensions—syntactic accuracy, semantic fidelity, reliability, cost efficiency, and latency—enabling fine-grained capability profiling that mirrors real-world deployment constraints.

The benchmark provides a structured suite of tasks with well-defined tool schemas and expected outputs, a composable scoring API, and Pareto-frontier analysis for cost-performance trade-off visualization. EnterpriseBench is designed to support reproducible ablation studies and agent comparisons at scale, with a lightweight pure-Python implementation that requires no GPU or proprietary API access.

## Quick Start

```bash
pip install -e ".[dev]"
python scripts/run_benchmark.py
```

```python
from enterprisebench.data import make_suite
from enterprisebench.core import BenchmarkSuite
from enterprisebench.evaluate import evaluate_result, aggregate_scores, leaderboard

# Build suite
suite = BenchmarkSuite(tasks=make_suite(20))
print(suite.stats())
# {'total': 20, 'by_vertical': {'finance': 5, 'healthcare': 5, 'legal': 5, 'devops': 5}, ...}

# Run agent and score
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

print(leaderboard({"my-agent": scores}))
# [{'agent': 'my-agent', 'mean': 1.0, 'std': 0.0, 'min': 1.0, 'max': 1.0, 'n': 20}]
```

## Benchmark Schema

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique identifier for the task |
| `vertical` | `str` | Industry vertical (finance/healthcare/legal/devops) |
| `instruction` | `str` | Natural language instruction for the agent |
| `tool_schema` | `dict` | JSON schema of the available tool |
| `expected_call` | `dict` | Ground-truth tool call (name + arguments) |
| `expected_output` | `str` | Expected natural language response |
| `difficulty` | `str` | Task difficulty (easy/medium/hard) |

## Evaluation Dimensions

| Dimension | Description | Score Range |
|---|---|---|
| **Syntactic** | Tool name match + argument key Jaccard similarity | 0–1 |
| **Semantic** | Intent alignment between instruction and response | 0–1 |
| **Reliability** | Consistency across repeated runs | 0–1 |
| **Cost** | Normalized cost relative to per-task budget | 0–1 |
| **Latency** | Normalized latency relative to response budget | 0–1 |

## Leaderboard Format

```python
[
  {"agent": "gpt-4o",   "mean": 0.91, "std": 0.08, "min": 0.60, "max": 1.0, "n": 100},
  {"agent": "claude-3", "mean": 0.89, "std": 0.09, "min": 0.55, "max": 1.0, "n": 100},
]
```

## Target Venues

- DAI 2026 (International Workshop on Deployable AI)
- AAAI 2027 Workshop on Enterprise AI Evaluation

## Citation

```bibtex
@misc{enterprisebench2026,
  title        = {EnterpriseBench: Multi-Dimensional LLM Evaluation for Enterprise Tool-Use},
  author       = {Anote AI Research},
  year         = {2026},
  howpublished = {\url{https://github.com/anote-ai/research-enterprisebench}},
  note         = {Preprint}
}
```
