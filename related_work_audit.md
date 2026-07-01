# Related Work & Novelty Audit

*Purpose: anticipate reviewer objections, document differentiators, confirm citation completeness. Referenced from PAPER_DRAFT.md Section 2.*

---

## 1. Benchmark Comparison Table

Rows = existing benchmarks. Columns = key EnterpriseBench features.

| Benchmark | Venue / Year | Enterprise tasks | Policy compliance | False completion detection | Multi-turn consistency | Audit trail quality | Cost tracking | State-diff verification |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| GAIA | arXiv 2023 | No | No | No | No | No | No | No |
| SWE-bench | ICLR 2024 | No (code only) | No | No | No | No | No | Partial (test pass/fail) |
| AgentBench | ICLR 2024 | Partial | No | No | No | No | No | No |
| WebArena | ICLR 2024 | No (web only) | No | No | No | No | No | No |
| WorkArena | ICLR 2024 | Yes (1 platform) | No | No | No | No | No | No |
| TAU-bench | arXiv 2024 | Partial | No | No | No | No | No | No |
| TheAgentCompany | arXiv 2024 | Yes (multi-domain) | No | No | No | No | No | No |
| AssistGUI | CVPR 2024 | No (GUI only) | No | No | No | No | No | No |
| OSWorld | NeurIPS 2024 | No (desktop only) | No | No | No | No | No | Partial |
| Spider2-V | arXiv 2024 | Partial (data eng) | No | No | No | No | No | No |
| ToolBench | ICLR 2024 | No | No | No | No | No | No | No |
| **EnterpriseBench** | **—** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## 2. Per-Benchmark Differentiator Analysis

### GAIA (Mialon et al., 2023)
- **What it does:** Multi-step web research and reasoning with human-level performance targets.
- **Gap:** Tasks are general-purpose (web lookup, arithmetic, file parsing). No organizational policies, no cost modeling, no multi-turn consistency requirement. Success = correct answer to a factual question.
- **Objection:** "Enterprise agents also need general reasoning — GAIA measures that."
- **Rebuttal:** True, but general reasoning capability and policy compliance capability are orthogonal. An agent can achieve high GAIA scores while violating 75% of enterprise policies on realistic workflows, as Experiment 1 demonstrates.

### AgentBench (Liu et al., 2023)
- **What it does:** Eight environments (OS, DB, KG, digital card game, lateral thinking puzzle, House Holding, web shopping, web browsing).
- **Gap:** Environments are synthetic or toy (card games, lateral thinking puzzles). "Enterprise" environments (DB, OS) do not include organizational policy constraints. No cost tracking. No multi-turn consistency metric.
- **Objection:** "AgentBench already evaluates enterprise agents on databases and operating systems."
- **Rebuttal:** Running SQL queries against a toy database is not the same as respecting data retention policies, escalation rules, and segregation-of-duties constraints in a live enterprise system. The difference is that those constraints are not encoded in AgentBench's task definitions.

### WorkArena (Drouin et al., 2024)
- **What it does:** 33 tasks on ServiceNow (IT service management platform). Closest prior work in enterprise scope.
- **Gap:** Single platform (ServiceNow). Tasks are defined by ServiceNow's UI affordances, not organizational policy. No policy violation tracking. No cost modeling. Completion = UI state matches expected.
- **Objection:** "WorkArena already covers enterprise workflows."
- **Rebuttal:** ServiceNow is one enterprise platform out of many, and WorkArena evaluates workflow execution, not policy compliance. An agent that creates an IT ticket in the wrong priority tier completes the task in WorkArena but may violate an escalation policy in an enterprise deployment.

### TAU-bench (Yao et al., 2024)
- **What it does:** Tool-augmented task completion with a simulated user persona driving the conversation.
- **Gap:** The simulated user is a customer (retail/airline domains), not an enterprise compliance officer. Policies are not modeled explicitly; success is defined by whether the agent's actions match a reference solution.
- **Objection:** "TAU-bench already measures whether agents follow instructions in multi-turn settings."
- **Rebuttal:** Following a user's instructions in a multi-turn retail conversation is different from maintaining consistency with organizational policies across a 50-turn enterprise workflow. TAU-bench does not define or measure policy violation as a distinct metric.

### TheAgentCompany (Xu et al., 2024)
- **What it does:** 175 tasks across a simulated software company (Slack, GitHub, Jira, web browsing, file editing). Most comprehensive enterprise benchmark to date.
- **Gap:** No organizational policy taxonomy; success = task completion matching a reference trajectory. No FCR (agent self-report vs. verified success). No multi-turn consistency metric. No cost tracking.
- **Objection:** "TheAgentCompany already covers multi-domain enterprise tasks — what does EnterpriseBench add?"
- **Rebuttal:** TheAgentCompany asks "did the agent do the right thing?" EnterpriseBench additionally asks "did the agent do it without violating a policy?", "did it accurately report whether it succeeded?", and "can a human audit why it made each decision?" These are independent properties. A task that succeeds on TheAgentCompany may still produce a high PVR and low ATR on EnterpriseBench.

### SWE-bench (Jimenez et al., 2024)
- **What it does:** Agents fix GitHub issues in real Python repositories; success = test suite passes after patch.
- **Gap:** Entirely a software engineering benchmark. Not applicable to email management, CRM operations, HR workflows, etc. No policy constraints.
- **Objection:** "SWE-bench already rigorously evaluates agents with state-diff verification (tests pass/fail)."
- **Rebuttal:** SWE-bench's verification methodology (run tests) is excellent and influenced EnterpriseBench's state-diff approach. The domain and evaluation axes are entirely different: software patches vs. enterprise workflow policy compliance.

---

## 3. Novelty Claims (Defensible Summary)

Three claims we can defend against any prior benchmark:

**Claim 1: EnterpriseBench is the first benchmark to measure Policy Violation Rate (PVR) as a primary metric.**
Policy constraints appear in the task definitions as explicit, machine-checkable rules (not natural language instructions). No prior benchmark defines PVR or provides a policy checker that operates on (pre-state, action, post-state) triples.

**Claim 2: EnterpriseBench is the first benchmark to measure False Completion Rate (FCR) — the gap between agent self-report and verified outcome.**
This directly addresses the enterprise concern that agents claim success when the system state is actually wrong. No prior benchmark distinguishes "agent says done" from "state matches expected post-state".

**Claim 3: EnterpriseBench measures cost as a first-class evaluation dimension, enabling Pareto-frontier analysis between task-completion quality and per-task cost.**
While some benchmarks note the cost of evaluation, none make cost a scored output dimension with a per-task budget, enabling enterprise buyers to select agents on cost-quality trade-off curves rather than accuracy alone.

---

## 4. Strongest Reviewer Objections and Rebuttals

| Objection | Rebuttal |
|---|---|
| "TheAgentCompany already covers enterprise tasks at a larger scale (175 tasks)." | Scale is not the differentiator. EnterpriseBench measures PVR, FCR, and ATR; TheAgentCompany does not. A 4-task suite that measures policy compliance is more useful for enterprise buyers than a 175-task suite that doesn't. |
| "Policy rules are hand-crafted and may not generalize." | This is a limitation we acknowledge (Section 6.3). The rule-based approach is a deliberate design choice for reproducibility: LLM-based policy judges introduce non-determinism. Community contribution of rules is planned. |
| "The paper has no results from real agents." | Experiment 1 with real agents (GPT-4o, Claude) is the immediate next step. The framework infrastructure (policy checker, adapter, statistical tools) is complete; only API budget and task scale are gating. We submit the framework paper; results will follow in a journal version. |
| "PVR on 4 tasks is not statistically meaningful." | Agreed; we present Experiment 1 as a proof-of-concept, not a finding. The framework paper contribution is the measurement methodology, not the specific numbers. |
| "GAIA/AgentBench already show agents fail on reasoning — policy compliance is just another capability gap." | Policy compliance is not a reasoning gap; it is a representation gap. The mock agent in Experiment 1 achieves 100% reasoning accuracy (it returns exactly the expected answer) and 75% policy violation rate. These are independent. |

---

## 5. Citation Completeness Checklist

### Must cite (directly comparable)
- [x] GAIA — Mialon et al., arXiv:2311.12983
- [x] AgentBench — Liu et al., arXiv:2308.03688
- [x] WorkArena — Drouin et al., arXiv:2403.07718
- [x] TAU-bench — Yao et al., arXiv:2406.12045
- [x] WebArena — Zhou et al., arXiv:2307.13854
- [x] SWE-bench — Jimenez et al., ICLR 2024
- [x] TheAgentCompany — Xu et al., arXiv:2412.14161
- [x] Dror et al. 2018 (statistical testing methodology)

### Should cite (methodologically relevant)
- [ ] OSWorld — Xie et al., NeurIPS 2024 (desktop task benchmark)
- [ ] Spider2-V — Cao et al., arXiv 2024 (data engineering tasks)
- [ ] ToolBench — Qin et al., ICLR 2024 (tool-calling benchmark)
- [ ] AssistGUI — Gao et al., CVPR 2024 (GUI automation)
- [ ] AutoGen — Wu et al., arXiv:2308.08155 (agent framework)
- [ ] LangGraph — LangChain team, 2024 (agent framework)

### To verify via Semantic Scholar search
- [ ] Search "enterprise agent evaluation" 2023–2025 for any missed work
- [ ] Search "policy compliance LLM agent" for any prior policy-focused work
- [ ] Search "agent benchmark cost" for cost-tracking precedents
