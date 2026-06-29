# Experiment status tracker

This tracks the gap between what `DESIGN_DOC.md` describes and what is
actually implemented and runnable in this repository, so that claims in any
future paper/blog draft stay honest. Update this file whenever an experiment
moves between states.

Status values: `not started`, `partial`, `implemented (unrun)`,
`run (results in results/)`.

| DESIGN_DOC.md section | Experiment | Status | Notes |
|---|---|---|---|
| 6.1 | Baseline: self-report vs. verified success | not started | Requires real agent integration; no agent framework adapters exist in `src/` yet. |
| 6.2 | Experiment 1: Policy Violation Rate across frameworks | partial | Policy rule engine + PVR metric implemented in `src/enterprisebench/policy.py` (3 reference rules, not the full 250-task/5-category set). No agent systems wired up, so PVR has never been computed against a real agent. |
| 6.3 | Experiment 2: Multi-turn consistency degradation | not started | `BenchmarkTask.turns` / `run_agent_multi_turn` exist in `core.py` as plumbing, but no MTCS metric, no consistency-graph/DAG formalism, and no 40-task consistency dataset exist. |
| 6.4 | Experiment 3: Audit trail quality | not started | No audit log schema, no rubric, no rater tooling. |
| 6.5 | Experiment 4: Graceful degradation on ambiguous inputs | not started | No ambiguous-task dataset, no classifier for safe-stop/unsafe-proceed/error outcomes. |
| 5 | Agent framework adapters (AutoGen, LangGraph, CrewAI, OpenAI Assistants, Claude Computer Use, rule-based baseline) | not started | `src/enterprisebench` currently only supports a generic Python callable `agent_fn(task) -> dict`; no framework-specific adapters exist. |
| 3.1 | 8-category task taxonomy (250 tasks) | partial | Only 4 of 8 categories have any task implementation (finance, healthcare, legal, devops in `data.py`), and those tasks are simple tool-call-matching tasks without policy annotations or pre/post state -- not the policy-bearing tasks the design doc specifies. CRM, HR, calendar, document management, and IT support categories: not started. |

## What `results/` should contain once experiments run

There is currently no `results/` directory because no experiment has been
run end-to-end against a real agent system. Once Experiment 1 (the most
tractable next step, since the policy engine already exists) is run against
at least one real agent integration, results should be saved as:

```
results/
  exp1_policy_violation_rate/
    <agent_name>_<date>.json   # raw per-task PolicyCheckResult dumps
    summary.csv                # one row per agent: PVR, violations by category
```

Until such a directory with real output exists, treat every number in
`PAPER_DRAFT.md` and `DESIGN_DOC.md`'s "Expected Results" tables as a
projection, not a finding.
