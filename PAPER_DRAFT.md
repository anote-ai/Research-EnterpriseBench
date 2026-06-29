# EnterpriseBench: Evaluating AI Agents on Policy Compliance, Auditability, and Multi-Turn Consistency in Enterprise Workflows

**Status: DRAFT SKELETON. This is not a submission-ready paper.** Sections
marked `[PROJECTED]` restate target numbers from `DESIGN_DOC.md`'s "Expected
Results" tables and have NOT been measured by running any code in this
repository. Sections marked `[TODO]` have no content yet. Do not cite any
number in this document as an empirical finding.

## Abstract

*[TODO: write after Experiment 1 produces real numbers.]*

Working draft: Enterprise deployment of LLM agents is accelerating faster
than the evaluation tooling needed to assess deployment safety. We introduce
EnterpriseBench, an evaluation framework targeting four properties existing
benchmarks do not measure: policy compliance, self-report reliability,
multi-turn consistency, and audit-trail reconstructibility. We define four
metrics -- Policy Violation Rate (PVR), False Completion Rate (FCR),
Multi-Turn Consistency Score (MTCS), and Audit Trail Reconstructibility
(ATR) -- and [PROJECTED] plan to evaluate 8 agent systems across 240+
enterprise workflow tasks spanning 8 categories.

## 1. Introduction

See `DESIGN_DOC.md` Sections 1-2 for the full problem statement and novelty
claims. Summary: general-purpose agent benchmarks (GAIA, AgentBench,
WorkArena, TAU-bench) measure task completion but not policy compliance,
auditability, or cross-turn consistency -- properties that determine whether
enterprises can safely deploy agents in regulated workflows.

## 2. Related Work

*[TODO: literature review. DESIGN_DOC.md Section 10 references an internal
"related work & novelty audit" issue (#17) -- pull its conclusions in here
once available.]*

## 3. The EnterpriseBench Framework

### 3.1 Task taxonomy

8 workflow categories (email, CRM, HR, data pipeline, calendar, document
management, IT support, finance) as specified in `DESIGN_DOC.md` Section 3.1.
**Implementation status:** task *templates* exist for 4 categories (finance,
healthcare, legal, devops) in `src/enterprisebench/data.py`, but these encode
simple tool-call matching tasks, not the policy-annotated, state-diff tasks
the design doc specifies. The other 4 categories (CRM, HR, calendar,
document management, IT support -- 5 of 8) have no task implementation yet.

### 3.2 Policy taxonomy and violation checking

Implemented in `src/enterprisebench/policy.py`: a 5-category taxonomy
(authorization, data handling, communication, retention, escalation) and a
rule-based `check_policies()` function operating on (pre_state, action,
post_state) triples, matching the spec in `DESIGN_DOC.md` Section 3.3. Three
reference rules are implemented (CRM merge-with-active-deal, external email
without approval, expense segregation of duties) as a proof of concept.
**This covers a small fraction of the full 250-task policy set envisioned in
the design doc** and has not yet been run against any real agent.

### 3.3 Metrics

`policy_violation_rate()` and `false_completion_rate()` are implemented and
unit-tested (`tests/test_policy.py`). `MTCS` (multi-turn consistency) and
`ATR` (audit trail reconstructibility) are specified in `DESIGN_DOC.md`
Section 4 but have **no implementation yet** -- see `experiments/README.md`
for status.

## 4. Experimental Setup

*[TODO]* No agent-framework adapters (AutoGen, LangGraph, CrewAI, OpenAI
Assistants, Claude Computer Use) are implemented in this repository yet.
`DESIGN_DOC.md` Section 5 lists the 8 systems under evaluation; none are
wired up to `src/enterprisebench` at the time of writing.

## 5. Results

### 5.1 Baseline: self-report vs. verified success [PROJECTED]

| Metric | Value |
|---|---|
| Self-report success rate | ~72% (projected, pending full experiment run) |
| Verified success rate | ~55% (projected, pending full experiment run) |
| Implied FCR | ~17pp gap (projected, pending full experiment run) |

### 5.2 Experiment 1: Policy Violation Rate [PROJECTED]

| Metric | Value |
|---|---|
| PVR range across systems | 12-38% (projected, pending full experiment run) |
| Most common violation category | Data handling, ~45% of violations (projected) |

### 5.3 Experiment 2: Multi-turn consistency degradation [PROJECTED]

Consistency(k) = alpha * e^(-beta*k) + gamma; no fitted parameters exist yet
-- this functional form is a modeling proposal, not a fitted result.

### 5.4 Experiment 3: Audit trail quality [PROJECTED]

ATR range 0.42-0.71 across systems (projected, pending human rater study;
no raters have been recruited or trained yet).

### 5.5 Experiment 4: Graceful degradation [PROJECTED]

Safe-stop rate 15-25% (projected, pending experiment implementation).

## 6. Discussion

*[TODO]*

## 7. Limitations

- No experiments in this draft reflect measured results; all numeric values
  are projections carried over from the design doc's expected-results
  tables.
- The currently implemented code (`src/enterprisebench`) evaluates a
  different, smaller scope (4 verticals x tool-call matching with
  syntactic/semantic/reliability/cost/latency scoring) than the policy /
  audit / consistency framework this paper describes. Reconciling these two
  is necessary before any experiment in Section 5 can be run for real.
- No statistical significance testing, human rater study, or agent-framework
  integration exists yet.

## 8. Conclusion

*[TODO: write last.]*

## Appendix: Status legend used in this document

- **Implemented & tested**: code exists in this repo and has passing unit
  tests.
- **[PROJECTED]**: a target number from `DESIGN_DOC.md`'s expected-results
  tables, not yet produced by running any code.
- **[TODO]**: no content yet.
