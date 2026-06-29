# Can you trust an AI agent with your company's CRM, inbox, and ledgers?

*A plain-language summary of the EnterpriseBench project.*

## The problem in one sentence

AI agents are now allowed to send real emails, edit real database records, and
approve real expenses -- and almost nobody is measuring whether they do this
*safely*, only whether they get the task "done."

## Why existing scorecards miss the point

If you ask most AI agent benchmarks today "how good is this agent?", they
answer with a single number: the percentage of tasks it completed. That's the
wrong question for a company deciding whether to let an agent touch its CRM
or HR system. The right questions are closer to what a compliance officer
would ask:

- Did it do anything it was explicitly told not to do?
- Did it just *say* it succeeded, or did it actually succeed?
- After 10 back-and-forth turns, does it still remember and respect decisions
  it made earlier in the conversation?
- If something in the log goes wrong, can a human reconstruct *why* the agent
  did what it did?
- When instructions are ambiguous, does it ask for clarification, or guess
  (and sometimes guess in the most dangerous direction)?

None of the popular benchmarks (GAIA, AgentBench, WorkArena, TAU-bench) are
built to answer these. EnterpriseBench is designed specifically to.

## What EnterpriseBench actually measures

EnterpriseBench proposes four new yardsticks for "is this agent enterprise-
ready," each targeting a specific failure mode we've all heard horror
stories about:

1. **Policy Violation Rate (PVR)** -- how often the agent breaks an explicit
   rule (e.g., "don't email external addresses without approval") even when
   it otherwise completes the task.
2. **False Completion Rate (FCR)** -- how often the agent *claims* success
   while the underlying system state says otherwise. This targets the
   uncomfortable possibility that agents "lie" about finishing work more
   than we'd like to believe.
3. **Multi-Turn Consistency Score (MTCS)** -- whether an agent's decisions
   stay coherent across a long, realistic workflow, or whether it starts
   contradicting itself once the conversation gets long.
4. **Audit Trail Reconstructibility (ATR)** -- whether a human compliance
   reviewer, reading only the agent's logs, can figure out what it did and
   why.

## Where the project actually stands today

We want to be direct about this, because credibility matters more than hype:

- The **design** for all four metrics and the underlying task taxonomy is
  fully specified (see `DESIGN_DOC.md`).
- A first **real, tested implementation** of the policy-rule engine (the
  machinery behind PVR and FCR) now lives in `src/enterprisebench/policy.py`,
  with unit tests in `tests/test_policy.py`.
- The **240+ task dataset**, the **8 agent-framework integrations** (AutoGen,
  LangGraph, CrewAI, etc.), the **multi-turn consistency graph**, and the
  **human audit-trail rater study** described in the design doc are not yet
  built. Any numbers that look like "EnterpriseBench finds X%" in the design
  doc are *projected targets*, not measured results, until those pieces
  exist.

We think the idea is strong enough to be worth building out fully, and we'd
rather tell you exactly what's real today than dress up a design doc as a
finished paper. Track `experiments/README.md` for an up-to-date status of
which experiments are implemented vs. still planned.

## Why we think this matters

Enterprise buyers, CISOs, and compliance teams are stuck choosing agent
vendors with no shared vocabulary for "how risky is this agent, exactly."
If EnterpriseBench succeeds, it gives the industry four concrete,
reproducible numbers to ask every vendor for -- the same way "latency" and
"uptime" became standard questions for cloud services.
