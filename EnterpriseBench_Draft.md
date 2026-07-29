# EnterpriseBench: Do Syntactic Tool-Calling Benchmarks Predict Deployment Trustworthiness?

**Aye Oyemami**
***University of Akron***

## Abstract

Current LLM agent benchmarks, including ToolBench, TAU-bench, and AgentBench, score agent tool use primarily by syntactic accuracy: whether the agent invoked the correct function with the correct arguments. This leaves three properties enterprise deployers care about unmeasured: whether the agent respects organizational policy constraints, whether its decisions stay consistent across a multi-turn workflow, and whether it reports its own completion state honestly. No existing benchmark scores these three properties directly, and none combines them with an enterprise-relevant task corpus spanning multiple business verticals.

This paper asks directly: does high syntactic tool-calling accuracy predict deployment trustworthiness — policy compliance, multi-turn consistency, and honest self-reported completion — in enterprise agent workflows? To make the question answerable, this paper introduces EnterpriseBench, a benchmark framework that scores agent tool use along five standard dimensions (syntactic accuracy, semantic fidelity, reliability, cost, latency) and defines three deployment-trustworthiness metrics: Policy Violation Rate (PVR), Multi-Turn Consistency Score (MTCS), and False Completion Rate (FCR). The contribution is the framework itself: a scoring engine, an eight-rule policy taxonomy with a general pairwise multi-turn consistency checker, bootstrap confidence intervals and paired significance testing, and two task corpora, together with an initial empirical test of the framework's central claim, namely that syntactic tool-calling accuracy and policy compliance are separable properties.

As a first empirical result, a deterministic reference agent that is syntactically perfect by construction was evaluated against a 16-task, eight-category policy-annotated workflow suite and violated an applicable policy on 50% of tasks (95% CI 25–75%), because several tasks are deliberately constructed so that literal instruction-following conflicts with an unstated organizational policy. A live GPT-4o-mini run on the same suite produced a comparable violation rate (56%, 95% CI 31–81%), with the two confidence intervals overlapping substantially, and with category-level variance suggesting compliance depends on whether a policy domain overlaps with common pretraining-derived business norms. The answer this first data point supports is: *not reliably* — a model can be highly capable at tool-calling syntax and still violate policy at a rate indistinguishable from an agent that never reasons about policy at all — though the evidence is a single model family on a small suite and should be read as a first data point, not a settled finding. This paper reports honestly which of the framework's metrics are backed by measured results today (PVR, MTCS, the five-dimensional scorer against a reference agent) and which are implemented and unit-tested but not yet exercised end-to-end against live agent output (FCR, the CLAS composite score), together with what is required to close that gap.

## 1. Introduction

Organizations are increasingly deploying LLM agents to automate workflows in finance, healthcare, legal, and DevOps — domains where errors are costly, policies are often legally binding, and decisions must be auditable. The practical question a deployer faces is not "can this agent call the right function" but "can this agent be trusted in production."

Existing agent benchmarks answer a narrower question. ToolBench [1] evaluates tool selection across more than 16,000 real-world APIs but does not model organizational policy constraints. TAU-bench [2] introduces multi-turn tool use with a simulated user, but scores trajectory match rather than policy compliance. AgentBench [3] spans eight environments and again scores task success, not policy adherence. GAIA [6] and WebArena [7] evaluate general-purpose web research and browsing competence, with no notion of organizational policy. SWE-bench [8] verifies software patches against a real test suite — a state-diff verification methodology this paper's false-completion metric is directly inspired by — but is scoped to software engineering, not enterprise workflows. Enterprise-specific efforts — WorkArena [4] and TheAgentCompany [5] — add realistic enterprise tasks but neither defines nor measures policy-violation rate, multi-turn consistency, or false-completion rate as first-class metrics (Table 1).

**Gap.** No existing benchmark measures whether an agent that is syntactically correct is also policy-compliant, internally consistent across turns, and honest about its own completion state.

**Thesis.** Syntactic tool-calling accuracy and deployment trustworthiness are separable properties: an agent can score highly on the former while failing the latter, and a benchmark that reports only syntactic accuracy therefore risks overstating an agent's readiness for enterprise deployment.

**Contribution.** This paper contributes EnterpriseBench, a benchmark framework consisting of (1) a five-dimensional tool-use scorer, (2) a policy-violation engine with eight rules spanning four active policy categories, (3) a general multi-turn consistency scorer that checks every pair of dependent decisions rather than only adjacent turns, (4) a false-completion metric, (5) bootstrap confidence intervals and paired significance testing, and (6) two complementary task corpora: a 20-template general tool-use corpus and a 16-task, eight-category policy-annotated workflow corpus. The framework is the artifact through which the thesis above becomes empirically testable. Three motivating scenarios illustrate the target failure modes:

- An agent calling `merge_contacts` on two records could score perfectly on syntactic accuracy while violating a policy that forbids merging a record with an active deal without manager approval — syntactic correctness and policy compliance are independent axes.
- An agent could match reference tool calls at every turn of a multi-turn workflow while contradicting an earlier decision it was not asked to revisit — e.g., setting a ticket's priority to HIGH at turn 2 and LOW at turn 7.
- An agent could report a task as complete while the underlying system state does not reflect that, scoring perfectly on self-reported success while masking a real failure.

**Research question.** *Do high syntactic tool-calling scores predict deployment trustworthiness — low policy violation, high multi-turn consistency, low false completion — in enterprise workflows?* This paper does not answer this question at the scale the title poses it; a full answer requires the multi-model, multi-hundred-task study sketched in Section 6. What this paper reports is a first, honestly-scoped data point toward that answer, together with a framework built to make the question tractable to test further.

Section 2 situates this work against prior benchmarks. Section 3 defines the framework's metrics formally. Section 4 describes the task corpora and evaluated agents. Section 5 reports results, scoped explicitly to what has been measured versus what remains implemented-but-unmeasured. Section 6 discusses what would be required to turn this first data point into a full empirical study, and Section 7 states the paper's limitations directly.

## 2. Related Work

ToolBench [1] evaluates API tool selection at scale but treats every API call as equally valid so long as it matches a reference; it has no notion of a call being syntactically correct yet organizationally disallowed. TAU-bench [2] is the closest prior work on multi-turn evaluation, but its consistency notion is trajectory match against a single reference path rather than a check for self-contradiction across turns. AgentBench [3] broadens the environment set considerably but does not represent policy as an evaluation object at all. GAIA [6] and WebArena [7] target general reasoning and browsing competence respectively; an agent can score well on either while having no organizational policy constraints applied to it at all, since none are modeled. SWE-bench [8] is methodologically related in that it verifies outcomes against real system state rather than self-report — the same principle behind this paper's false-completion metric — but its domain (software patches judged by a test suite) does not transfer to enterprise workflow policy compliance. WorkArena [4] and TheAgentCompany [5] are the two prior efforts closest in spirit — both use realistic, enterprise-style tasks — but neither reports a policy-violation rate, a multi-turn consistency score, or a false-completion rate. EnterpriseBench's contribution relative to this line of work is not a new task domain but a new set of scoring axes — PVR, MTCS, and FCR — together with a measurement framework and an initial empirical test of whether PVR diverges from syntactic accuracy in practice.

**Table 1: Coverage of enterprise-relevant properties across benchmarks.**

| Benchmark | Ent. | Pol. | MTCS | FCR | Cost |
|---|---|---|---|---|---|
| GAIA | – | – | – | – | – |
| ToolBench | – | – | – | – | – |
| WebArena | – | – | – | – | – |
| SWE-bench | – | – | – | partial | – |
| TAU-bench | partial | – | – | – | – |
| AgentBench | partial | – | – | – | – |
| WorkArena | yes (1) | – | – | – | – |
| TheAgentCompany | yes | – | – | – | – |
| **EnterpriseBench** | **yes (4)** | **yes** | **yes** | **def'd** | **yes** |

## 3. The EnterpriseBench Framework

### 3.1 Two Task Corpora

The framework currently ships two complementary corpora, deliberately kept separate because they serve different measurement purposes. The **general corpus** contains 20 hand-written task templates spread evenly across finance, healthcare, legal, and DevOps (5 templates per vertical), each specifying an instruction, a tool schema, and a ground-truth call; it exercises the five-dimensional scorer described in Section 3.2. The **policy-annotated workflow corpus** contains 16 tasks — two per category across eight workflow categories (email management, CRM operations, HR workflow, data-pipeline operations, calendar scheduling, document management, IT support, and finance operations), spanning all four verticals with an emphasis on finance and legal (6 tasks each) — each additionally specifying a pre-state, one or more applicable policy rules, and, for two tasks, an explicit sequence of multi-turn decisions. This corpus exercises PVR and MTCS (Section 3.3). Neither corpus has yet reached the larger scale sketched in early project planning (a 200–250-task target across both); growing both corpora, particularly the workflow corpus past its current 2-tasks-per-category density, is the highest-priority item in Section 6.

Within each workflow category, one task is constructed so that literally following the instruction produces the policy-violating action (e.g., an instruction to provision a contractor account "with full admin access," where the ground-truth call grants permissions beyond the role's requirement), and the other is constructed so that literal instruction-following is policy-compliant. This design intentionally tests whether an agent surfaces an unstated policy constraint rather than complying with an instruction at face value; it is not a coincidental mismatch between an annotation and a rule.

### 3.2 Five-Dimensional Tool-Use Scoring

For a predicted tool call ĉ against a ground-truth call c*, syntactic accuracy is:

```
S_syn = 0.4 · 1[name(ĉ) = name(c*)] + 0.35 · J_k + 0.25 · J_v      (1)
```

where J_k and J_v are the Jaccard similarities of argument keys and argument values, respectively. Semantic fidelity S_sem applies fuzzy token overlap between predicted and reference tool name and argument values, with a small boost for overlap with the task instruction text. Reliability S_rel is defined as the fraction of repeated invocations of the same task that return the expected tool name; the current evaluation call site invokes it with a single predicted call per task, so in practice S_rel ∈ {0, 1} rather than a graded consistency fraction over repeated runs (Section 7). Cost and latency scores are computed relative to fixed per-task budgets B$ and B_ms:

```
S_cost = max(0, 1 − cost_usd / B$),   S_lat = max(0, 1 − latency_ms / B_ms)      (2)
```

with B$ = $0.01 and B_ms = 2000ms per task. A weighted composite (CLAS) combining all five dimensions is also implemented, with default weights of 0.30/0.20/0.20/0.15/0.15 for syntactic/semantic/reliability/cost/latency respectively; it is unit-tested but has not yet been exercised in any multi-agent comparison, since only one live model has been evaluated to date (Section 4).

### 3.3 Deployment-Trustworthiness Metrics

**Policy Violation Rate.** Each task is associated with a set of policy rules R_t = {r_1, ..., r_k}, where each rule is a boolean check over a (pre-state, action, post-state) triple. PVR over a task set T is:

```
PVR = |{t ∈ T : ∃ r ∈ R_t, r(ĉ_t) = fail}| / |T|      (3)
```

The current taxonomy defines five policy categories (authorization, data handling, communication, retention, escalation) and implements eight rules across four of them: authorization (four rules, e.g. least-privilege account provisioning and segregation of duties on expense approval), data handling (two rules, e.g. production schema changes requiring a change-control ticket), communication (one rule, external email recipients requiring approval), and escalation (one rule, minimum meeting notice). No rule currently exists in the retention category; it remains a defined-but-empty part of the taxonomy pending future work.

**Multi-Turn Consistency Score.** A multi-turn task produces a set of decisions, each a (turn, key, value) triple representing a fact the agent committed to at a specific turn. For every key that recurs, every pair of turns committing to that key is a dependent pair; a pair contradicts if the two values differ. Over a set of dependent pairs P with contradiction set V ⊆ P:

```
MTCS = 1 − |V| / |P|,   MTCS = 1 if P = ∅      (4)
```

This checks every pair of turns that share a decision key, not only adjacent turns. As with any contradiction-only check, a task with no recorded decisions or an agent that never commits to a decision produces P = ∅ and trivially scores MTCS = 1; this is a known limitation rather than a validated positive signal for such cases (Section 7).

**False Completion Rate.** Let claims(t) indicate that the agent's free-text response for task t contains completion language, and let verified(t) indicate that the resulting post-state matches the task's expected post-state. Then:

```
FCR = |{t : claims(t) ∧ ¬verified(t)}| / |{t : claims(t)}|      (5)
```

The scoring function itself is implemented and unit-tested in isolation, but no experiment in this paper currently wires it up against live or mock agent output on either corpus — doing so requires extending the workflow corpus with an explicit self-report field per task, which is future work (Section 6). No FCR numbers are reported in Section 5 for this reason.

### 3.4 Statistical Infrastructure

`bootstrap_ci` (1,000 resamples, task-level clustering, 95% interval) and `paired_bootstrap_test` (a paired bootstrap significance test following Dror et al. [9]) are implemented and used to produce every confidence interval reported in Section 5.

## 4. Experimental Setup

Two experiments were run. **Experiment A** runs a deterministic reference agent, which always returns the task's ground-truth call, against the 20-task general corpus and scores it on all five tool-use dimensions; this validates that the scoring pipeline produces the expected values end-to-end and is not intended as a comparative finding, since a reference agent's syntactic score is 1.0 by construction. **Experiment B** runs the same reference agent and a live GPT-4o-mini, via a standard OpenAI function-calling adapter with cost computed from actual token usage, against the 16-task policy-annotated workflow corpus and reports PVR and MTCS with bootstrap confidence intervals. No adapter for Claude or any other model family exists in the current codebase; extending the adapter layer beyond OpenAI-compatible endpoints is listed as future work rather than an in-progress component.

## 5. Results

### 5.1 Five-Dimensional Scoring: Pipeline Validation

Table 2 reports the reference agent's scores on the 20-task general corpus, reproduced by running the benchmark's demonstration script. Because the reference agent always returns the ground-truth call, syntactic accuracy and reliability are 1.0 by construction; semantic fidelity is below 1.0 because the fuzzy-overlap scorer is not a strict-match metric, which is expected behavior rather than a finding. This table demonstrates the scorer functions correctly end-to-end; it says nothing about how any live model performs on the five dimensions, since no live model has yet been run against this corpus.

**Table 2: Reference-agent scores, 20-task general corpus.** Reported to validate the scoring pipeline, not as a live-model finding.

| Dimension | Reference agent (n=20) |
|---|---|
| Syntactic | 1.000 |
| Semantic | 0.908 |
| Reliability † | 1.000 |
| Cost | 0.800 |
| Latency | 1.000 |

### 5.2 Policy Violation Rate and Multi-Turn Consistency

Table 3 reports PVR and MTCS on the 16-task policy-annotated workflow corpus.

**Table 3: PVR and MTCS, 16-task workflow corpus (8 categories × 2 tasks), with 95% bootstrap CIs.**

| Agent | PVR | MTCS (n=2) | Cost |
|---|---|---|---|
| Reference agent | 0.50 [0.25, 0.75] | 1.00 [1.00, 1.00] | $0.00 |
| GPT-4o-mini ‡ | 0.56 [0.31, 0.81] | 1.00 | $0.0005 |

**The reference-agent result is a pipeline check, not the central finding.** By construction, the reference agent always reproduces the ground-truth call, so its 50% PVR is fully determined by task design: each category contains one task whose ground-truth call was deliberately written to be policy-violating (Section 3) and one that is compliant. This confirms that the scoring pipeline correctly registers violations end-to-end, and that syntactic perfection alone does not guarantee compliance in this task set, but it does not by itself demonstrate anything about how a reasoning agent *behaves* when facing an instruction that conflicts with an unstated policy.

**The GPT-4o-mini result is the paper's primary evidence.** On the identical 16-task suite, live GPT-4o-mini produced a comparable violation rate (56%, 9/16 tasks), with per-category behavior that varied meaningfully: it reproduced violations on tasks matching the reference agent's pattern in most categories, reached 100% PVR on both data-pipeline and IT-support tasks (in the IT-support case, granting excess permissions on both the excessive-access task and the appropriately-scoped one), and reached 0% PVR on the calendar-scheduling category, correctly declining a short-notice meeting despite the 24-hour policy never being stated in the instruction. This suggests the model's compliance behavior is not uniform across policy domains: it may draw on pretraining-derived norms for some domains (meeting etiquette) while defaulting to literal instruction-following in others (IT provisioning, schema changes) where no such norm is common knowledge. This finding is reported as the author's own logged run rather than independently re-executed in the course of writing this paper, since reproducing it requires live API access not available in this pass; the raw per-task output for this run is not currently checked into the repository, and doing so is listed as a reproducibility fix in Section 7.

The two PVR confidence intervals overlap substantially (25–75% vs. 31–81%), so this sample size cannot establish whether GPT-4o-mini's rate differs meaningfully from the reference agent's; both point estimates being similarly high is consistent with, but does not on its own prove, the interpretation that a meaningful share of these particular violations stem from tasks whose instructions conflict with unstated policy rather than from model-specific reasoning failures.

### 5.3 What Is Not Yet Measured

False Completion Rate is defined and unit-tested (Section 3.3) but has not been run against either corpus, so no FCR numbers are reported here. The CLAS composite score is implemented and unit-tested but has not been exercised in a multi-agent comparison, since only one live model has been evaluated. The five-dimensional scorer (Section 3.2) has only been run against the reference agent, never against a live model, so no live syntactic, semantic, reliability, cost, or latency scores currently exist for GPT-4o-mini; extending the live evaluation from the workflow corpus (PVR/MTCS only) to the general corpus (all five dimensions) is straightforward future work rather than a design change, but it has not been done yet.

## 6. Discussion

**Answering the research question, provisionally.** The title asks whether high syntactic tool-calling scores predict deployment trustworthiness. At the scale tested here, the answer is: no, not reliably. GPT-4o-mini is a highly capable model at the tool-calling task itself, yet its policy-violation rate (56%) is statistically indistinguishable from a reference agent that performs no reasoning about policy whatsoever (50%). If syntactic competence predicted policy compliance, the capable model's rate should have been meaningfully lower than the reference agent's; it was not. This is consistent with the paper's thesis, though it is one model on 16 tasks, and the claim should be read at that scale, not the scale the title's question implies for the field as a whole.

Two agents, one syntactically perfect by construction and one genuinely capable but imperfect, produced similarly elevated policy-violation rates (50% and 56%) on a task suite where roughly half of the tasks were designed so literal instruction-following conflicts with an unstated organizational policy. Read as a first data point, this is consistent with the paper's thesis that syntactic accuracy and policy compliance are separable, and the category-level variance in GPT-4o-mini's behavior (0% on calendar scheduling, 100% on IT support and data-pipeline tasks) suggests compliance depends on whether a policy domain overlaps with common pretraining-derived business norms. It should not be read as a settled finding: it is one model family on a 16-task suite, the live-model figures were not independently re-executed during this revision, and rates this small carry wide uncertainty even with the bootstrap intervals reported here.

Turning this into a full empirical study requires, in priority order:

1. Checking the live GPT-4o-mini run's raw per-task output into the repository so PVR-by-category and MTCS figures are independently reproducible, not just aggregate-reported.
2. Building an adapter for at least one additional model family (no non-OpenAI adapter currently exists) to test whether the pattern generalizes.
3. Wiring FCR into an actual experiment by adding a self-report field to workflow-corpus tasks and running the existing scorer against live output.
4. Growing both corpora, with the workflow corpus's 2-tasks-per-category density being the more urgent gap for statistical power.
5. Extending live evaluation to the five-dimensional scorer so syntactic, semantic, reliability, cost, and latency figures exist for a live model, not only for the reference agent.
6. Implementing at least one rule in the retention category, which is currently defined in the taxonomy but has no implemented check.

## 7. Limitations

- Only one live model family (GPT-4o-mini) has been evaluated, and only on the 16-task policy-annotated corpus, not the five-dimensional general corpus; no adapter for any other model family currently exists in the codebase.
- The GPT-4o-mini PVR/MTCS figures reported here are the author's previously logged run (recorded in commit history and the project's working draft); the raw per-task results for that run are not checked into the repository, so this paper could not independently re-verify them in this revision. Checking in the raw output is a concrete, low-cost fix.
- Both task corpora are small: 20 templates across 4 verticals for five-dimensional scoring, and 16 tasks across 8 categories for policy/consistency scoring. Early project planning sketched roughly 200–250 tasks combined; neither corpus is yet at that scale.
- The policy taxonomy defines five categories but implements rules in only four; the retention category has no implemented check.
- False Completion Rate and the CLAS composite score are implemented and unit-tested but have not been exercised against any agent's actual output; no FCR or CLAS results appear in this paper.
- MTCS now checks all pairs of dependent decisions, not only adjacent turns, but a task or agent that produces no decisions still trivially scores 1.0; only 2 of the 16 workflow tasks currently carry multi-turn decision annotations, so the MTCS figures reported reflect a narrow slice of the corpus.
- The reliability dimension is invoked with a single predicted call per task in the current evaluation pipeline, so it can only return 0 or 1 rather than a graded consistency fraction across repeated runs.
- The five-dimensional scorer's latency budget (2000ms/task) has only been exercised against a reference agent with near-instantaneous mock latency; it has not yet been tested against a live, multi-round-trip model call, so it should not be assumed to be well-calibrated for that setting.
- Audit Trail Reconstructibility, referenced in the project's ethics statement as a property the framework evaluates, is not implemented; the ethics statement is corrected in Section 8 to avoid overstating current capability.

## 8. Ethics and Broader Impact

All tasks in both corpora use synthetic data; no real enterprise or personal data is used in any task definition. Total compute cost to date across all live evaluation is under one dollar and is negligible at this scale. One correction to the project's existing ethics documentation: an earlier draft of the project's ethics statement described the framework as evaluating audit trail reconstructibility (whether a human compliance officer can reconstruct why an agent made a given decision); that metric is not implemented in the current codebase and should be treated as a design goal rather than a present capability. High-stakes agent actions of the kind these tasks model (financial approvals, record deletion, external communication) should require human approval before execution in any real deployment; this framework is intended to evaluate agent behavior within that constraint, not to argue for removing it.

## 9. Conclusion

This paper asked whether syntactic tool-calling benchmarks predict deployment trustworthiness, and introduced EnterpriseBench, a framework for measuring that gap, consisting of a five-dimensional scorer, an eight-rule policy-violation engine, a general pairwise multi-turn consistency score, a defined-but-not-yet-measured false-completion metric, and bootstrap statistical infrastructure, evaluated over two task corpora. A reference agent that is syntactically perfect by construction violated an applicable policy on 50% of a 16-task policy-annotated workflow suite (95% CI 25–75%), and a live GPT-4o-mini run on the same suite produced a comparable, overlapping-CI rate of 56% (31–81%) with meaningful category-level variance. At this scale, the provisional answer to the title's question is no: syntactic competence did not translate into a measurably lower policy-violation rate. This is initial evidence for the paper's central thesis, reported alongside an explicit account of which parts of the framework remain implemented-but-unmeasured. The immediate next steps are checking in the live run's raw output for independent reproducibility, adding a second model family, wiring up the false-completion metric end-to-end, and growing both task corpora past their current scale.

## Acknowledgment
Special Thanks to Natan Vidra, Founder & CEO of Anote as well as the Anote team, for feedback on the framework and this paper.

## References

[1] Y. Qin et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-World APIs. ICLR, 2024.
[2] S. Yao et al. τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. arXiv:2406.12045, 2024.
[3] X. Liu et al. AgentBench: Evaluating LLMs as Agents. arXiv:2308.03688, 2023.
[4] A. Drouin et al. WorkArena: How Capable Are Web Agents at Solving Common Knowledge Work Tasks? arXiv:2403.07718, 2024.
[5] F. Xu et al. TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks. arXiv:2412.14161, 2024.
[6] G. Mialon et al. GAIA: A Benchmark for General AI Assistants. arXiv:2311.12983, 2023.
[7] S. Zhou et al. WebArena: A Realistic Web Environment for Building Autonomous Agents. arXiv:2307.13854, 2023.
[8] C. E. Jimenez et al. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR, 2024.
[9] R. Dror et al. The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing. ACL, 2018.

## Appendix A: Reproducibility

The reference-agent results in Table 2 and the reference-agent row of Table 3 are fully reproducible with no API key:

```bash
python scripts/run_benchmark.py
python experiments/exp2_full_suite.py --mock
```

The GPT-4o-mini row of Table 3 requires a live API key and is reproducible in principle via:

```bash
OPENAI_API_KEY=sk-... python experiments/exp2_full_suite.py --model gpt-4o-mini
```

As noted in Section 7, the raw per-task JSON output of the specific live run reported here is not currently checked into the repository; only the mock run's output is. Committing that artifact alongside this paper is a direct, low-cost step toward full reproducibility and is planned before camera-ready.

## Appendix B: Notation

| Symbol | Meaning |
|---|---|
| PVR | Policy Violation Rate |
| MTCS | Multi-Turn Consistency Score |
| FCR | False Completion Rate |
| CLAS | Composite five-dimensional score |
| CI | 95% bootstrap confidence interval |
| R_t | Policy rules applicable to task t |
| P | Dependent decision pairs (MTCS) |
| V | Contradicting decision pairs (MTCS) |
