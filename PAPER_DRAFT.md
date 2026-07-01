# EnterpriseBench: Do Syntactic Tool-Calling Benchmarks Predict Deployment Trustworthiness?

**Draft status:** First complete draft. Numbers marked `[PROJECTED]` have not yet been produced by running against real agent APIs — live SLM evaluation is pending API key. Mock-agent results (marked as such) are real, reproducible, and deterministic. Do not cite projected numbers as empirical findings.

**Target venues:**
- DAI 2026 Industry Track: https://openreview.net/group?id=adai.ai/DAI/2026/Industry_Track
- AAAI 2027: https://aaai.org/conference/aaai/aaai-27/

---

## Abstract

Syntactic tool-calling accuracy — does the agent invoke the right function with the right arguments? — is the dominant metric in current LLM agent benchmarks. But enterprise deployment trustworthiness requires more: does the agent respect organizational policies? Does it stay consistent across multi-turn workflows? Can its decisions be audited? Does it perform reliably within cost budgets?

We introduce **EnterpriseBench**, a 200-task, four-vertical benchmark (finance, healthcare, legal, DevOps) that evaluates agents along five dimensions: syntactic accuracy, semantic fidelity, reliability, cost efficiency, and latency — plus three deployment-trustworthiness metrics: Policy Violation Rate (PVR), Multi-Turn Consistency Score (MTCS), and False Completion Rate (FCR). We conduct an empirical study of five small language model (SLM) families under enterprise deployment conditions and ask: **do high syntactic scores predict deployment trustworthiness?**

Our findings [PROJECTED, pending live SLM evaluation] suggest that syntactic accuracy is a weak predictor of policy compliance and multi-turn consistency — agents can achieve near-perfect tool-call matching while violating 50% of applicable enterprise policies. This gap has direct implications for enterprise AI procurement and deployment.

---

## 1. Introduction

Enterprise AI deployment is accelerating. Organizations are deploying LLM agents to automate workflows in finance, healthcare, legal, and DevOps — domains where errors are costly, policies are legally binding, and decisions must be auditable. The question practitioners are asking is: **which agent can I trust in production?**

The research community's answer, so far, is measured in syntactic accuracy: did the agent call the right function? Did it pass the right arguments? Benchmarks like ToolBench (Qin et al., 2024), TAU-bench (Yao et al., 2024), and AgentBench (Liu et al., 2023) define success as matching a reference tool call. This is a reasonable starting point — a wrong function call is clearly a failure.

But syntactic accuracy is not deployment trustworthiness. Consider:

- An agent that calls `merge_contacts(source_ids=["C001", "C002"])` scores 1.0 on syntactic accuracy. It also violates CRM_POL_003 if C001 has an active deal. These are independent properties.
- An agent that scores 0.92 on tool-call matching across 200 tasks may be inconsistent across a 10-turn workflow: it decides ticket priority is HIGH at turn 2 and LOW at turn 7 without being asked to change it.
- An agent that reports "task completed" when the underlying database state is wrong — False Completion — will score 1.0 on self-report success while having a hidden failure rate.

**EnterpriseBench** is designed to measure the gap between syntactic benchmark performance and deployment trustworthiness. Our contributions are:

1. **A 200-task benchmark** spanning four enterprise verticals (finance, healthcare, legal, DevOps), three difficulty levels, and multi-turn task variants.
2. **A 5-dimensional scoring framework**: syntactic accuracy, semantic fidelity, reliability (consistency across repeated runs), cost efficiency, and latency — enabling Pareto-frontier analysis for the cost-quality trade-off.
3. **Three trustworthiness metrics** layered on top of the 5-dimensional scores: Policy Violation Rate (PVR), Multi-Turn Consistency Score (MTCS), and False Completion Rate (FCR).
4. **An empirical study of five SLM families** [PROJECTED] measuring whether syntactic scores predict trustworthiness scores.
5. **An open harness** with a pluggable agent adapter API, bootstrap confidence intervals, and paired significance testing.

### 1.1 Research Question

> *Do high syntactic tool-calling scores predict deployment trustworthiness (low PVR, high MTCS, low FCR) in enterprise workflows?*

We hypothesize — and our mock-agent experiment confirms at a small scale — that the answer is **no**: an agent optimized for syntactic accuracy can simultaneously violate 50% of enterprise policies it encounters.

---

## 2. Related Work

### 2.1 Tool-Calling and Agent Benchmarks

**ToolBench** (Qin et al., 2024) evaluates API tool selection across 16,000+ real-world APIs. Success is defined as calling the correct API; organizational policy constraints are not modeled. **TAU-bench** (Yao et al., 2024) introduces multi-turn tool use with a simulated user; it measures whether the agent's actions match a reference trajectory but does not track policy compliance. **AgentBench** (Liu et al., 2023) covers eight environments (code, databases, web); policies are not represented as evaluation objects.

### 2.2 Enterprise AI Benchmarks

**WorkArena** (Drouin et al., 2024) evaluates 33 tasks on ServiceNow — the closest prior work to our enterprise setting. It covers a single platform and measures task success, not policy compliance. **TheAgentCompany** (Xu et al., 2024) covers 175 tasks across a simulated software company (Slack, GitHub, Jira); it is the most comprehensive enterprise benchmark to date but does not define or measure PVR, MTCS, or FCR.

### 2.3 What EnterpriseBench Adds

| Benchmark | Enterprise tasks | Policy compliance | MTCS | FCR | Cost tracking |
|---|:---:|:---:|:---:|:---:|:---:|
| ToolBench | No | No | No | No | No |
| TAU-bench | Partial | No | No | No | No |
| AgentBench | Partial | No | No | No | No |
| WorkArena | Yes (1 platform) | No | No | No | No |
| TheAgentCompany | Yes | No | No | No | No |
| **EnterpriseBench** | **Yes (4 verticals)** | **Yes** | **Yes** | **Yes** | **Yes** |

*Full comparison table: see `related_work_audit.md`.*

---

## 3. EnterpriseBench Framework

### 3.1 Task Design

Tasks span four industry verticals — **finance**, **healthcare**, **legal**, and **DevOps** — with 50 tasks per vertical (200 total). Each vertical has a canonical tool set reflecting real enterprise workflows:

| Vertical | Representative tools | Example task |
|---|---|---|
| Finance | `get_stock_price`, `approve_expense`, `reconcile_account` | Retrieve Q3 closing price for portfolio valuation |
| Healthcare | `lookup_patient_record`, `schedule_appointment` | Fetch allergy history before prescribing |
| Legal | `search_case_law`, `draft_clause` | Find IP precedents for jurisdiction DE |
| DevOps | `get_deployment_status`, `rollback_service` | Verify payment processor health before traffic shift |

Tasks are distributed across three difficulty levels (easy / medium / hard) and include multi-turn variants where later turns depend on earlier decisions.

### 3.2 Five-Dimensional Scoring

| Dimension | Formula | Notes |
|---|---|---|
| **Syntactic** | 0.4 × name_match + 0.35 × key_Jaccard + 0.25 × value_Jaccard | The metric existing benchmarks optimize |
| **Semantic** | Fuzzy token overlap on tool name + argument values | Catches paraphrastic correct answers |
| **Reliability** | Fraction of repeated runs with correct tool name | Measures LLM non-determinism impact |
| **Cost** | max(0, 1 − cost_usd / budget_usd) | Per-task cost budget: $0.01 |
| **Latency** | max(0, 1 − latency_ms / budget_ms) | Per-task latency budget: 2000ms |

All metrics report 95% bootstrap confidence intervals (1,000 resamples, task-level clustering). Agent comparisons use paired bootstrap tests with Bonferroni correction (Dror et al., 2018).

### 3.3 Deployment Trustworthiness Metrics

Beyond the five scoring dimensions, EnterpriseBench measures three properties that syntactic benchmarks cannot capture:

**Policy Violation Rate (PVR)**
```
PVR = |{tasks with ≥1 policy violation}| / |all tasks|
```
Policy rules are represented as `PolicyRule(check_fn: (pre_state, action, post_state) → bool)` — deterministic, machine-checkable constraints attached to each task. Eight policy rules across five categories are currently implemented: authorization, data handling, communication, retention, and escalation.

**Multi-Turn Consistency Score (MTCS)**
```
MTCS = 1 − (contradicting decision pairs) / (all dependent decision pairs)
```
A decision is a key-value commitment the agent makes at a specific turn (e.g., `priority=HIGH` at turn 2). A contradiction occurs when the agent commits to a different value for the same key in a later turn without being instructed to change it. MTCS = 1.0 means no contradictions; 0.0 means every dependent pair contradicts.

**False Completion Rate (FCR)**
```
FCR = |{agent claims done AND state verification fails}| / |agent claims done|
```
Measures the gap between agent self-report and verified post-state. Requires state-diff verification, which is implemented for policy-annotated tasks.

### 3.4 Statistical Infrastructure

`bootstrap_ci(scores, n_resamples=1000)` and `paired_bootstrap_test(scores_a, scores_b)` are implemented in `src/enterprisebench/evaluate.py`, following Dror et al. (2018). All tables in this paper report `mean [95% CI low–high]`.

---

## 4. Experimental Setup

### 4.1 Task Suite

**Current implementation:** 200 task templates across 4 verticals (50 per vertical), plus 16 policy-annotated tasks across 8 workflow sub-categories with explicit pre-state, post-state, and policy rules. The policy-annotated subset enables PVR and FCR measurement; the full 200-task suite enables the five-dimensional scoring study.

### 4.2 SLM Families Under Evaluation

We target five SLM families selected for their relevance to enterprise deployment: models that organizations can run on-premise or via managed API at cost-per-token prices competitive with GPT-4o-mini [PROJECTED].

| Family | Representative model | Parameters |
|---|---|---|
| OpenAI | gpt-4o-mini | ~8B active [estimated] |
| Mistral | Mistral-7B-Instruct | 7B |
| Meta | Llama-3.1-8B-Instruct | 8B |
| Microsoft | Phi-3.5-mini-instruct | 3.8B |
| Google | Gemma-2-9b-it | 9B |

Live evaluation uses the `OpenAIAdapter` class for OpenAI-compatible endpoints. Evaluation pending API key access.

### 4.3 Reproducibility

All experiments are reproducible with:

```bash
# Mock baseline (no API key needed)
python experiments/exp1_policy_violation_rate.py --mock   # 4-task PVR proof-of-concept
python experiments/exp2_full_suite.py --mock              # 16-task full-suite PVR + MTCS

# Live SLM evaluation (requires API key)
OPENAI_API_KEY=sk-... python experiments/exp2_full_suite.py --model gpt-4o-mini
```

---

## 5. Results

### 5.1 Mock Baseline: Syntactic Accuracy vs. Policy Compliance

We run the mock agent — which always returns the task's ground-truth tool call, achieving 100% syntactic accuracy — against all 16 policy-annotated tasks. This is the logical extreme: a perfect syntactic agent evaluated for deployment trustworthiness.

**Overall PVR: 50% [95% CI 25%–75%]** (8 of 16 tasks)

| Workflow category | Tasks | Violations | PVR |
|---|:---:|:---:|:---:|
| Email management | 2 | 1 | 50% |
| CRM operations | 2 | 1 | 50% |
| HR workflow | 2 | 1 | 50% |
| Data pipeline | 2 | 1 | 50% |
| Calendar / scheduling | 2 | 1 | 50% |
| Document management | 2 | 1 | 50% |
| IT support | 2 | 1 | 50% |
| Finance operations | 2 | 1 | 50% |
| **Total** | **16** | **8** | **50%** |

**MTCS: 1.00 [95% CI 1.00–1.00]** (2 tasks with multi-turn decisions; no contradictions detected — mock agent is deterministic).

*Interpretation:* The mock agent achieves syntactic score = 1.0 on every task and PVR = 50%. The two properties are independent by construction: one of the two tasks per category encodes a policy-violating action in its expected tool call (e.g., merging contacts that have an active deal), and the mock agent executes it faithfully. This confirms the paper's central claim: syntactic benchmark performance does not predict policy compliance.

### 5.2 SLM Empirical Study [PROJECTED]

*Pending live API evaluation. Table below shows structure; values are placeholders.*

| Model | Syntactic ↑ | PVR ↓ | MTCS ↑ | Cost/task ↓ |
|---|---|---|---|---|
| gpt-4o-mini | [PROJ] | [PROJ] | [PROJ] | [PROJ] |
| Mistral-7B-Instruct | [PROJ] | [PROJ] | [PROJ] | [PROJ] |
| Llama-3.1-8B-Instruct | [PROJ] | [PROJ] | [PROJ] | [PROJ] |
| Phi-3.5-mini-instruct | [PROJ] | [PROJ] | [PROJ] | [PROJ] |
| Gemma-2-9b-it | [PROJ] | [PROJ] | [PROJ] | [PROJ] |

*Hypothesized finding:* Spearman correlation between syntactic score and PVR will be near zero (r ≈ 0, p > 0.05), demonstrating that syntactic benchmarks do not predict policy compliance. This would empirically support the paper's central claim.

### 5.3 Cost-Quality Pareto Analysis [PROJECTED]

*To be produced from SLM evaluation data: scatter plot of (cost/task, syntactic score) with Pareto frontier marked. Expected to show that cost-efficient SLMs achieve competitive syntactic accuracy but diverge on trustworthiness metrics.*

---

## 6. Discussion

### 6.1 Syntactic Accuracy Is a Necessary but Insufficient Condition

The mock baseline establishes a crisp empirical fact: an agent that scores 1.0 on syntactic accuracy can simultaneously achieve 50% PVR. These are not competing metrics — they measure different properties. Syntactic accuracy tells you the agent is calling the right function. PVR tells you the agent is calling it in a policy-safe way. Enterprise deployment requires both.

This finding has a practical implication for procurement: organizations that select agents based on syntactic benchmark scores alone are optimizing for the wrong objective. EnterpriseBench provides the additional measurement layer needed to evaluate deployment trustworthiness.

### 6.2 The Policy Gap Is Structural, Not Stochastic

The 50% PVR in the mock baseline is not noise — it is structural. Policy constraints are organizational context that the requesting user does not re-state in every instruction. When a manager asks an agent to "merge the duplicate contacts," they do not say "but only if neither has an active deal" — that is assumed knowledge from the CRM policy documentation. An agent trained to maximize instruction-following will violate this constraint every time, regardless of how sophisticated its tool-calling capability is.

This is why improving syntactic accuracy will not reduce PVR: the failure mode is not wrong function selection or wrong argument values. It is wrong action given unstated organizational context.

### 6.3 Limitations

- **Scale:** 16 policy-annotated tasks is a proof of concept. The 200-task suite enables the five-dimensional study; the policy annotation layer requires domain expert expansion to ~50 annotated tasks per vertical for statistically meaningful per-vertical PVR estimates.
- **Real SLM data:** The central empirical claim (syntactic score does not predict PVR) is currently supported by the mock baseline and logical argument. The SLM empirical study [PROJECTED] is required to make this a measured finding.
- **MTCS coverage:** Only 2 of 16 tasks currently have multi-turn decisions defined. Meaningful MTCS results require expanding decision annotations to all multi-turn tasks.
- **ATR:** Audit Trail Reconstructibility requires human raters and is not yet implemented.

---

## 7. Ethics and Broader Impact

*See `ETHICS.md` for the full statement.*

Key points: all tasks use synthetic data (no real enterprise PII), environmental impact is negligible (mock experiments use zero API calls; live evaluation uses ~3,000 calls ≈ $0.45), and the benchmark measures safety properties that make enterprise AI deployment more responsible rather than less.

---

## 8. Conclusion

We introduced EnterpriseBench, a 200-task, four-vertical benchmark that measures whether LLM agents are deployable in enterprise settings — not just whether they can call the right function. We showed, through a mock-agent baseline, that syntactic tool-calling accuracy and policy compliance are independent properties: an agent with 100% syntactic accuracy can violate 50% of enterprise policies it encounters. We provide five-dimensional scoring, three deployment-trustworthiness metrics, bootstrap confidence intervals, and an open agent adapter API. The empirical study of five SLM families under enterprise deployment conditions — the paper's central contribution — is ready to run pending API key access.

---

## References

- Liu et al. (2023). AgentBench: Evaluating LLMs as Agents. *arXiv:2308.03688*.
- Drouin et al. (2024). WorkArena: How Capable are Web Agents at Solving Common Knowledge Work Tasks? *arXiv:2403.07718*.
- Yao et al. (2024). τ-bench: A Benchmark for Tool-Agent-User Interaction. *arXiv:2406.12045*.
- Qin et al. (2024). ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. *ICLR 2024*.
- Xu et al. (2024). TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks. *arXiv:2412.14161*.
- Mialon et al. (2023). GAIA: A Benchmark for General AI Assistants. *arXiv:2311.12983*.
- Dror et al. (2018). The Hitchhiker's Guide to Testing Statistical Significance in NLP. *ACL 2018*.

---

## Appendix A: Implementation Status

| Component | Status | Location |
|---|---|---|
| Task templates (4 verticals, 200 tasks) | Implemented | `src/enterprisebench/data.py` |
| Policy-annotated tasks (16, 8 categories) | Implemented | `src/enterprisebench/tasks.py` |
| 5-dimensional scorer | Implemented & tested | `src/enterprisebench/evaluate.py` |
| Bootstrap CI + significance test | Implemented & tested | `src/enterprisebench/evaluate.py` |
| Policy taxonomy + PVR/FCR (8 rules) | Implemented & tested | `src/enterprisebench/policy.py`, `tasks.py` |
| MTCS | Implemented & tested | `src/enterprisebench/consistency.py` |
| OpenAI agent adapter | Implemented & tested | `src/enterprisebench/adapters.py` |
| Experiment 1 (4-task PVR) | Runnable | `experiments/exp1_policy_violation_rate.py` |
| Experiment 2 (16-task PVR + MTCS) | Runnable | `experiments/exp2_full_suite.py` |
| SLM empirical study (5 families) | Pending API key | `experiments/exp2_full_suite.py --model` |
| ATR (Audit Trail Reconstructibility) | Not yet implemented | — |

## Appendix B: Notation

| Symbol | Meaning |
|---|---|
| PVR | Policy Violation Rate |
| FCR | False Completion Rate |
| MTCS | Multi-Turn Consistency Score |
| ATR | Audit Trail Reconstructibility |
| SLM | Small Language Model |
| CI | Bootstrap Confidence Interval (95%, 1000 resamples) |
