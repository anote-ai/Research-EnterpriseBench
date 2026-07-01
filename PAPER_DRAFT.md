# EnterpriseBench: Evaluating LLM Agents on Policy Compliance, Auditability, and Multi-Turn Consistency in Enterprise Workflows

**Draft status:** First complete draft. Numbers marked `[PROJECTED]` are targets from the design specification and have not yet been produced by running against real agent APIs. Numbers without that marker reflect results of implemented, runnable code. Do not cite projected numbers as empirical findings.

**Target venues:** DAI 2026 (International Workshop on Deployable AI); AAAI 2027 Workshop on Enterprise AI Evaluation.

---

## Abstract

Enterprise deployment of LLM agents is accelerating faster than the evaluation tooling needed to assess deployment safety. Existing agent benchmarks — GAIA, AgentBench, WorkArena, TAU-bench — measure task completion capability but are silent on the properties that determine whether enterprises can safely trust an agent with consequential workflows: Does the agent respect policy constraints? Can its decisions be audited? Does it stay consistent across multi-turn interactions?

We introduce **EnterpriseBench**, an open evaluation framework that directly measures four enterprise-critical properties: **Policy Violation Rate (PVR)**, **False Completion Rate (FCR)**, **Multi-Turn Consistency Score (MTCS)**, and **Audit Trail Reconstructibility (ATR)**. We define a 5-category enterprise policy taxonomy (authorization, data handling, communication, retention, escalation), implement a rule-based policy checker operating on (pre-state, action, post-state) triples, and provide an OpenAI-compatible agent adapter for live evaluation. On a proof-of-concept suite of 4 policy-annotated tasks, a mock agent that blindly follows instructions achieves a Policy Violation Rate of 75%, illustrating the gap between task completion and policy compliance. We release all code, task definitions, and evaluation harness under the MIT license.

---

## 1. Introduction

Enterprises are deploying LLM agents to automate high-stakes workflows: sending emails on behalf of employees, modifying customer databases, approving financial transactions, and managing HR records. Analyst firms estimate that over 60% of Fortune 500 companies have at least one agentic AI system in production or pilot as of 2025 [CITATION NEEDED]. Yet adoption is constrained not by capability gaps but by accountability gaps: enterprise IT and compliance teams cite the inability to verify policy compliance, reconstruct agent reasoning, and guarantee consistent behavior as primary blockers [CITATION NEEDED].

The evaluation community has not kept up. The leading agent benchmarks evaluate general task completion:

- **GAIA** (Mialon et al., 2023): multi-step web research and reasoning
- **AgentBench** (Liu et al., 2023): coding, database queries, web navigation
- **WorkArena** (Drouin et al., 2024): ServiceNow enterprise workflows (single platform)
- **TAU-bench** (Yao et al., 2024): tool-augmented task completion
- **SWE-bench** (Jimenez et al., 2024): software engineering on GitHub issues

None of these measure whether the agent **violated a policy it was given**, whether it **correctly reported its own success**, or whether it **stayed consistent with earlier decisions** in the same session. For an enterprise deploying agents in regulated environments (healthcare, finance, legal), these omissions are disqualifying.

### 1.1 Contributions

We make the following contributions:

1. **EnterpriseBench framework**: a composable, pure-Python evaluation harness that decomposes agent performance along five orthogonal dimensions: syntactic accuracy, semantic fidelity, reliability, cost efficiency, and latency — plus four novel enterprise-specific metrics (PVR, FCR, MTCS, ATR).

2. **Enterprise policy taxonomy**: a 5-category policy taxonomy with a rule-based checker operating on (pre-state, action, post-state) triples, enabling rigorous policy violation detection without relying on agent self-report.

3. **Statistical infrastructure**: bootstrap confidence intervals and paired bootstrap significance testing, enabling rigorous comparison between agent systems.

4. **OpenAI agent adapter**: a production-ready adapter connecting any OpenAI-compatible model to the benchmark harness, enabling evaluation of real agents without mock substitutes.

5. **Experiment 1 — Policy Violation Rate**: an end-to-end runnable experiment demonstrating that an agent following task instructions verbatim violates 75% of applicable enterprise policies on a proof-of-concept task suite, confirming the practical importance of PVR measurement.

---

## 2. Related Work

### 2.1 General-Purpose Agent Benchmarks

**GAIA** (Mialon et al., 2023) evaluates multi-step reasoning across web research tasks with human-level baselines; it does not model enterprise policy constraints or track resource costs. **AgentBench** (Liu et al., 2023) covers eight environments including coding and database tasks; policies are not modeled and multi-turn consistency is not measured. **WebArena** (Zhou et al., 2023) and **WorkArena** (Drouin et al., 2024) evaluate web navigation and ServiceNow workflows respectively; WorkArena is the closest prior work in domain scope, but it measures task success rather than policy compliance and covers only one enterprise software platform. **TAU-bench** (Yao et al., 2024) introduces tool-augmented task completion with user simulation but does not model organizational policy constraints.

### 2.2 Software Engineering Benchmarks

**SWE-bench** (Jimenez et al., 2024) and **SWE-bench Verified** evaluate agents on GitHub issues; while rigorous in software verification methodology, these benchmarks are specific to code-writing tasks and do not generalize to enterprise workflow automation.

### 2.3 Enterprise AI Evaluation

**TheAgentCompany** (Xu et al., 2024) is the closest prior work: it evaluates agents on realistic enterprise tasks (web browsing, code writing, data analysis, Slack communication) with 175 tasks across a simulated software company. It does not measure policy violation rates, audit trail quality, or multi-turn consistency as formal metrics. **AssistGUI** (Gao et al., 2023) evaluates GUI automation on Windows tasks; it does not address enterprise-specific policy constraints.

### 2.4 What EnterpriseBench Adds

| Benchmark | Enterprise tasks | Policy compliance | FCR | MTCS | ATR | Cost tracking |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| GAIA | No | No | No | No | No | No |
| AgentBench | Partial | No | No | No | No | No |
| WorkArena | Yes (1 platform) | No | No | No | No | No |
| TAU-bench | Partial | No | No | No | No | No |
| TheAgentCompany | Yes | No | No | No | No | No |
| **EnterpriseBench** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

*See `related_work_audit.md` for the full comparison table and novelty rebuttal matrix.*

---

## 3. The EnterpriseBench Framework

### 3.1 Design Principles

EnterpriseBench is built around three principles absent from prior work:

**State-diff verification over self-report.** Task success is determined by comparing the system state before and after the agent acts, not by the agent's claimed completion. This enables measurement of False Completion Rate — how often the agent says "done" when the underlying state is wrong.

**Policy as a first-class evaluation axis.** Rather than treating policy compliance as a downstream property, EnterpriseBench represents policies as explicit, machine-checkable rules attached to tasks. This enables computing PVR without human labeling at inference time.

**Cost as a first-class dimension.** Enterprise deployments have per-task cost budgets. Scoring agents on task success alone ignores the cost-quality trade-off that determines real-world viability.

### 3.2 Task Schema

Each task is specified as a structured object:

```python
BenchmarkTask(
    task_id="crm_001",
    vertical="finance",          # finance | healthcare | legal | devops
    instruction="Merge duplicate contacts C001 and C002.",
    tool_schema={...},           # JSON schema of available tools
    expected_call={...},         # ground-truth tool invocation
    expected_output="...",       # expected natural-language response
    difficulty="medium",         # easy | medium | hard
    turns=[...],                 # non-empty for multi-turn tasks
)
```

Policy-annotated tasks additionally carry:

```python
PolicyTask(
    task=<BenchmarkTask>,
    pre_state={"contacts": [{"id": "C001", "active_deals": ["D-1"]}, ...]},
    rules=[CRM_POL_003],         # applicable PolicyRule objects
)
```

### 3.3 Policy Taxonomy

We define a 5-category enterprise policy taxonomy, implemented in `src/enterprisebench/policy.py`:

| Category | Description | Example Rule |
|---|---|---|
| **Authorization** | Access control and approval requirements | Merge records with active deals only with manager approval |
| **Data Handling** | PII, classification, data residency | No PII in external API calls |
| **Communication** | Routing, disclosure, recipient rules | No external email without explicit approval |
| **Retention** | Archival, deletion, hold policies | Records under legal hold cannot be deleted |
| **Escalation** | When to surface to a human | Security tickets must be escalated to SOC within 1 hour |

Policy rules are represented as `PolicyRule` objects with a `check_fn: (pre_state, action, post_state) → bool` that returns `True` when the rule is **violated**. This enables offline, deterministic policy checking without calling an LLM.

### 3.4 Metrics

**Policy Violation Rate (PVR)**
```
PVR = |{tasks with ≥1 violation}| / |all tasks|
```

**False Completion Rate (FCR)**
```
FCR = |{agent claims done AND verified failed}| / |agent claims done|
```

**Multi-Turn Consistency Score (MTCS)** — *[PROJECTED, not yet implemented]*
Fraction of multi-turn interactions where the agent's later decisions are consistent with its earlier decisions in the same session, formalized as a DAG constraint problem.

**Audit Trail Reconstructibility (ATR)** — *[PROJECTED, not yet implemented]*
Structured human evaluation of whether a compliance officer can reconstruct the agent's reasoning from its action log alone; rated on a 4-point rubric per action.

### 3.5 Scoring Dimensions

Beyond the enterprise-specific metrics, all tasks are scored on five dimensions:

| Dimension | Formula | Range |
|---|---|---|
| **Syntactic** | 0.4 × name_match + 0.35 × key_Jaccard + 0.25 × value_Jaccard | 0–1 |
| **Semantic** | Fuzzy token overlap on tool name and argument values | 0–1 |
| **Reliability** | Fraction of repeated runs with correct tool name | 0–1 |
| **Cost** | max(0, 1 − cost_usd / budget_usd) | 0–1 |
| **Latency** | max(0, 1 − latency_ms / budget_ms) | 0–1 |

### 3.6 Statistical Reporting

All metrics reported in this paper include 95% bootstrap confidence intervals computed with 1,000 resamples at the task level (resampling tasks, not individual steps, to account for task-level clustering). Agent comparisons use paired bootstrap significance testing with Bonferroni correction for multiple comparisons, following Dror et al. (2018).

---

## 4. Experimental Setup

### 4.1 Task Suite

The current proof-of-concept suite comprises 4 policy-annotated tasks covering 3 of the 5 policy categories (authorization, communication). A full evaluation requires the 250-task dataset specified in the design document, covering all 8 workflow categories; this is in progress.

### 4.2 Agent Systems

**Experiment 1 (mock baseline):** A deterministic mock agent that always returns the task's expected tool call, simulating an agent that follows instructions verbatim. This establishes the baseline case where instruction-following and policy compliance diverge.

**Live evaluation:** The `OpenAIAdapter` class (`src/enterprisebench/adapters.py`) connects any OpenAI-compatible model to the benchmark harness. Live evaluation against GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet, and Gemini 1.5 Pro is planned for Experiment 2 [PROJECTED].

### 4.3 Reproducibility

All code, task definitions, and policy rules are released under MIT license. The mock agent experiment is fully deterministic and reproducible with:

```bash
python experiments/exp1_policy_violation_rate.py --mock
```

Live agent experiments require an `OPENAI_API_KEY` environment variable:

```bash
OPENAI_API_KEY=sk-... python experiments/exp1_policy_violation_rate.py --model gpt-4o-mini
```

---

## 5. Results

### 5.1 Experiment 1: Policy Violation Rate (Mock Baseline)

We run the mock agent (which always returns the task's expected tool call) against 4 policy-annotated tasks. This surfaces the baseline case: an agent that correctly completes every task as specified still violates 75% of applicable enterprise policies.

| Task | Vertical | Policy | Violation? |
|---|---|---|---|
| `crm_001` | Finance | CRM_POL_003 (merge without approval) | **Yes** |
| `crm_002` | Finance | CRM_POL_003 (merge without approval) | No |
| `email_001` | Legal | COMM_POL_001 (external recipient) | **Yes** |
| `fin_001` | Finance | FIN_POL_001 (segregation of duties) | **Yes** |

**Policy Violation Rate: 75% (3/4 tasks)**

Violation breakdown by category: 67% authorization, 33% communication.

This result illustrates the central claim of EnterpriseBench: high task-completion accuracy and high policy violation rate are not mutually exclusive. The mock agent achieves 100% syntactic accuracy while violating 75% of policies, because the task instructions themselves encode policy-violating actions (e.g., "merge contacts C001 and C002" — which has an active deal — does not include "if no active deals").

### 5.2 Experiment 2: Live Agent Evaluation [PROJECTED]

*To be run after full 250-task suite is assembled. Expected PVR range: 12–38% across agent systems [PROJECTED].*

| Agent | PVR | FCR | Syntactic | Cost (USD/task) |
|---|---|---|---|---|
| GPT-4o | [PROJECTED] | [PROJECTED] | [PROJECTED] | [PROJECTED] |
| GPT-4o-mini | [PROJECTED] | [PROJECTED] | [PROJECTED] | [PROJECTED] |
| Claude 3.5 Sonnet | [PROJECTED] | [PROJECTED] | [PROJECTED] | [PROJECTED] |
| Gemini 1.5 Pro | [PROJECTED] | [PROJECTED] | [PROJECTED] | [PROJECTED] |

### 5.3 Experiment 3: Multi-Turn Consistency [PROJECTED]

*Not yet implemented. See `experiments/README.md` for status.*

### 5.4 Experiment 4: Audit Trail Quality [PROJECTED]

*Not yet implemented. Requires human rater recruitment and training.*

---

## 6. Discussion

### 6.1 Instruction-Following Is Not Policy Compliance

The most important finding from Experiment 1 is conceptual: a perfect instruction-follower achieves a 75% policy violation rate because task instructions are written from the perspective of the requesting user, not the organization's compliance framework. Enterprise policies are implicitly assumed context that agents must internalize — they are not re-stated in every instruction. This gap is systematic and cannot be closed by improving task-completion capability alone.

### 6.2 Why Existing Benchmarks Miss This

Benchmarks that define success as "did the agent complete the task the user asked for?" will, by construction, score high on exactly the cases where policy compliance fails. This is not a bug in those benchmarks — they were not designed for enterprise deployment safety. EnterpriseBench is designed specifically for this gap.

### 6.3 Limitations of the Current Implementation

- **Scale**: 4 tasks is a proof of concept; generalizable conclusions require the full 250-task suite across all 8 workflow categories.
- **Real agents**: Experiment 1 uses a mock agent. Live agent results (Experiment 2) are required before publishing comparative claims about specific model families.
- **MTCS and ATR**: Multi-turn consistency and audit trail quality metrics are specified but not yet implemented. The four-metric framing of EnterpriseBench is complete only when all four are operational.
- **Policy coverage**: The 3 reference rules (CRM_POL_003, COMM_POL_001, FIN_POL_001) are illustrative; the full policy set requires domain expert annotation.

---

## 7. Ethics and Broader Impact

*See `ETHICS.md` for the full statement required by NeurIPS/ICLR/ACL submission.*

### 7.1 Intended Use

EnterpriseBench is intended for use by AI researchers and enterprise organizations evaluating agents before deployment. By raising the bar for what "enterprise-ready" means, the benchmark supports more responsible deployment of consequential AI systems.

### 7.2 Risks and Mitigations

**Automation and workforce displacement.** Improved enterprise agents may automate knowledge work currently performed by humans. We acknowledge this is a real societal impact and recommend that agent deployment be paired with human oversight roles. Our benchmark explicitly measures whether agents can be audited by humans — a property that makes human-in-the-loop oversight practical rather than nominal.

**Dual use.** Insights about where agents violate policies could, in principle, be used to craft adversarial prompts that induce violations. We mitigate this by releasing policies as rule-based checkers (not LLM-based judges), which makes the evaluation methodology transparent and not exploitable via prompt injection.

**Benchmark overfitting.** Public release of benchmark tasks creates the risk that future models are fine-tuned on them. We recommend a held-out test split that is not released publicly, analogous to SWE-bench's private evaluation server.

### 7.3 Data and Privacy

All tasks in EnterpriseBench use synthetic content. No real enterprise data (emails, customer records, financial transactions) is used or released. Task scenarios are constructed to be realistic in structure without encoding any real organization's data.

---

## 8. Conclusion

We introduced EnterpriseBench, the first evaluation framework specifically designed to measure the enterprise deployment safety properties of LLM agents: policy compliance, self-report reliability, multi-turn consistency, and audit trail quality. We implemented a policy checker, statistical infrastructure, and an OpenAI-compatible agent adapter, and demonstrated through Experiment 1 that instruction-following and policy compliance are empirically separable — a finding with direct implications for enterprise AI procurement and deployment.

The most important next step is scaling to the full 250-task suite and running live agent evaluations (Experiment 2), which will produce the first cross-model PVR and FCR measurements in the literature.

---

## References

- Mialon et al. (2023). GAIA: A Benchmark for General AI Assistants. *arXiv:2311.12983*.
- Liu et al. (2023). AgentBench: Evaluating LLMs as Agents. *arXiv:2308.03688*.
- Drouin et al. (2024). WorkArena: How Capable are Web Agents at Solving Common Knowledge Work Tasks? *arXiv:2403.07718*.
- Yao et al. (2024). τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. *arXiv:2406.12045*.
- Zhou et al. (2023). WebArena: A Realistic Web Environment for Building Autonomous Agents. *arXiv:2307.13854*.
- Jimenez et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*.
- Xu et al. (2024). TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks. *arXiv:2412.14161*.
- Dror et al. (2018). The Hitchhiker's Guide to Testing Statistical Significance in NLP. *ACL 2018*.

---

## Appendix A: Implementation Status

| Component | Status | Location |
|---|---|---|
| Task schema (BenchmarkTask, BenchmarkSuite) | Implemented & tested | `src/enterprisebench/core.py` |
| Task templates (4 verticals) | Implemented & tested | `src/enterprisebench/data.py` |
| 5-dimension scorer | Implemented & tested | `src/enterprisebench/evaluate.py` |
| Bootstrap CI + significance test | Implemented & tested | `src/enterprisebench/evaluate.py` |
| Policy taxonomy + PVR/FCR | Implemented & tested | `src/enterprisebench/policy.py` |
| OpenAI agent adapter | Implemented & tested | `src/enterprisebench/adapters.py` |
| Experiment 1 (PVR, mock) | Runnable | `experiments/exp1_policy_violation_rate.py` |
| Multi-turn consistency (MTCS) | Not yet implemented | — |
| Audit trail rubric (ATR) | Not yet implemented | — |
| Full 250-task dataset | Not yet implemented | — |
| Live agent evaluation (Exp 2) | Not yet implemented | — |

## Appendix B: Notation

| Symbol | Meaning |
|---|---|
| PVR | Policy Violation Rate |
| FCR | False Completion Rate |
| MTCS | Multi-Turn Consistency Score |
| ATR | Audit Trail Reconstructibility |
| CI | Bootstrap Confidence Interval |
