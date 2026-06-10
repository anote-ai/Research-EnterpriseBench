# EnterpriseBench — Research Design Document

## Goal

Create the first benchmark that evaluates AI agents on realistic enterprise workflows with specific focus on policy compliance, auditability, and multi-turn consistency: the three dimensions that determine whether an enterprise organization can actually trust and deploy an AI agent.

## Objective

1. Build a suite of 200+ enterprise workflow tasks (CRM, HRIS, ERP, data pipeline, email management) with clear success criteria and policy constraints
2. Evaluate 6+ leading agent frameworks (AutoGen, LangGraph, CrewAI, OpenAI Assistants, Claude Computer Use) on this suite
3. Publish findings that give enterprise buyers a principled basis for agent selection and deployment

## Background / Motivation

The enterprise AI agent market crossed $5B ARR in 2025. Every major vendor claims their agent is "enterprise-ready." But existing benchmarks (GAIA, AgentBench) evaluate agents on general tasks — not enterprise workflows. Enterprise buyers need to know: does the agent send emails it shouldn't? Does it delete records it wasn't authorized to delete? Does it remain consistent across a 50-turn workflow? No existing benchmark measures this.

## Experimental Design

### Baseline Experiment

**Evaluate GPT-4o (OpenAI Assistants API) on 20 representative enterprise tasks using pass/fail outcome scoring**

- Metric: binary task success rate
- Purpose: establish baseline capability and confirm task difficulty calibration
- Expected result: ~65–75% task success rate

### Test Experiment 1: Policy Violation Rate

For each agent framework, run 50 enterprise tasks that include a policy constraint (e.g., "do not send external emails without approval").

- Metric: policy violation rate = violated tasks / tasks with applicable policy
- Evaluate: GPT-4o, Claude, Gemini, AutoGen, LangGraph

**Expected result:** violation rates vary 2–5x across frameworks; agents without policy grounding violate policies on 20–40% of applicable tasks

### Test Experiment 2: Multi-Turn Consistency

Design 30 tasks requiring 10+ turns. At turn k, introduce information consistent or contradicting turn-1 decisions. Measure consistency rate and degradation curve.

**Expected result:** consistency degrades sharply after turn 8 for all tested agents

### Test Experiment 3: State-Diff Outcome Verification

Record world state before and after task execution. Success = post-task state matches expected state (not "agent reported success").

- Measure: false success rate = agent reports success but state is wrong

**Expected result:** false success rates of 15–25% for current SOTA agents

## Expected Results

1. A benchmark of 200+ enterprise workflow tasks with policy constraints and state-diff verification
2. Published violation rates, consistency curves, and false success rates for 6+ frameworks
3. **Key finding:** "Enterprise agents violate policies on 1 in 4 applicable tasks on average"
4. Leaderboard at `enterprisebench.anote.ai`

## Why This Matters / Why People Would Care

- **Enterprise buyers:** first principled basis for comparing AI agent platforms on policy compliance and auditability — influences $B+ procurement decisions
- **ML researchers:** policy violation and consistency findings motivate new research directions
- **AI safety:** enterprise agent deployment at scale is a major near-term safety concern; this benchmark raises the bar
- **Vendors:** credible third-party benchmark is the most effective product differentiation tool

## Timeline

| Month | Milestone |
|---|---|
| 1–2 | Task construction (200 tasks across 8 enterprise categories) |
| 3 | Infrastructure setup (state recording, policy constraint specification) |
| 4 | Baseline + test experiments across all frameworks |
| 5 | Analysis + leaderboard launch |
| 6 | Submission to NeurIPS 2026 D&B track |

## Related Issues

- Design doc GitHub issue: #19
- Target conferences: see issues labeled `conference-prep`
- Reproducibility package: see issues labeled `artifact-release`
