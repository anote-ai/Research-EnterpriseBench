# EnterpriseBench

[![CI](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml/badge.svg)](https://github.com/anote-ai/research-enterprisebench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **Do Syntactic Tool-Calling Benchmarks Predict Deployment Trustworthiness?**

## Abstract

EnterpriseBench is a 200-task, 4-vertical benchmark designed to evaluate small language model (SLM) families on tool-calling under realistic enterprise deployment conditions. Unlike existing benchmarks that measure syntactic accuracy alone, EnterpriseBench assesses five orthogonal dimensions — accuracy, reliability, latency, cost, and hallucination rate — across four enterprise verticals: **finance**, **healthcare**, **legal**, and **devops**.

Our central finding is that syntactic accuracy is a poor predictor of deployment trustworthiness: models that score highly on syntactic benchmarks can exhibit significant reliability and hallucination failures in production-like settings.

## Quickstart

```bash
git clone https://github.com/anote-ai/research-enterprisebench
cd research-enterprisebench
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v
```

## Benchmark Schema

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Unique task identifier (e.g. `fin_001`) |
| `vertical` | `str` | One of `finance`, `healthcare`, `legal`, `devops` |
| `instruction` | `str` | Natural-language instruction given to the agent |
| `tool_schema` | `dict` | JSON Schema describing the available tool |
| `expected_call` | `dict` | Ground-truth tool call (`tool_name` + `arguments`) |
| `expected_output` | `Any` | Expected tool return value |

## Evaluation Dimensions

| Dimension | Description | Metric |
|-----------|-------------|--------|
| **Syntactic** | Tool name and parameter key correctness | Exact match F1 |
| **Semantic** | Output value correctness relative to intent | BERTScore / custom |
| **Reliability** | Consistency across repeated runs | Variance @ N=10 |
| **Cost** | Token usage per task | USD per task |
| **Latency** | End-to-end response time | Median ms |

## Repository Structure

```
src/enterprisebench/
    __init__.py        # public API
    core.py            # BenchmarkTask, BenchmarkSuite, EvaluationDimension
    evaluate.py        # scoring functions and Pareto analysis
tests/
    test_core.py
    test_evaluate.py
```

## Citation

```bibtex
@misc{anoteai2025enterprisebench,
  title        = {EnterpriseBench: Do Syntactic Tool-Calling Benchmarks Predict Deployment Trustworthiness?},
  author       = {Anote AI Research},
  year         = {2025},
  howpublished = {\url{https://github.com/anote-ai/research-enterprisebench}},
}
```

## License

MIT
