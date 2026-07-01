# Ethics and Broader Impact Statement

*Required for NeurIPS, ICLR, and ACL submissions. Target length: 750–1000 words. This statement covers the research released in PAPER_DRAFT.md and the accompanying code in this repository.*

---

## Intended Use and Benefits

EnterpriseBench is an evaluation framework for measuring whether LLM agents behave safely and compliantly on enterprise workflows. Its intended users are AI researchers developing agent systems and enterprise organizations assessing agents before deployment.

The direct benefit is raising the bar for what "enterprise-ready" means in agent evaluation. By making policy violation rate and false completion rate measurable, the benchmark gives enterprise buyers a principled basis for procurement decisions and gives researchers a concrete optimization target beyond task-completion accuracy. We expect that benchmarks which measure safety-relevant properties create incentive gradients that lead to safer deployed systems.

---

## Accountability and Human Oversight

Autonomous enterprise agents take actions that are consequential and often hard to reverse: sending emails, modifying records, approving financial transactions. Our benchmark specifically evaluates **audit trail reconstructibility** — whether a human compliance officer can understand why the agent made each decision. This property is a prerequisite for meaningful human oversight: a system whose reasoning is opaque cannot be effectively overseen even when a human is nominally "in the loop."

**Our position on autonomous enterprise agents:** high-stakes agent actions (those meeting predefined authorization thresholds — e.g., transactions above a dollar limit, record deletions, external communications) should always require human approval before execution. EnterpriseBench measures agent capability *within* those constraints; it does not advocate for removing them.

---

## Labor Displacement

Improved enterprise agents may automate knowledge work currently performed by humans: scheduling, record management, correspondence drafting, expense processing. We acknowledge this as a real societal impact that our research contributes to, not a remote possibility.

We make three observations:

1. **Human oversight roles are a mitigation, not a solution.** Adding a human to approve every agent action does not prevent labor displacement if the human's role reduces to rubber-stamping. Meaningful oversight requires interpretable agent outputs — which is exactly what ATR (Audit Trail Reconstructibility) measures.

2. **The research cannot be undone by not publishing it.** The capability development that makes enterprise automation possible is occurring regardless of whether good evaluation frameworks exist. Better evaluation frameworks make that development more safety-conscious, not more dangerous.

3. **We recommend pairing agent deployment with reskilling investment.** Organizations that deploy EnterpriseBench-evaluated agents should invest proportionally in reskilling the workers whose workflows are automated. This is not a technical claim but an organizational policy recommendation we include because the research community that builds tools has some responsibility for how those tools are used.

---

## Bias in Task Coverage

The current task suite over-represents:
- **English-language workflows.** All task instructions and policy rules are written in English. Agents evaluated in this framework may not perform equivalently on workflows in other languages.
- **US-centric enterprise norms.** Policy rules such as expense approval thresholds and data retention requirements reflect US regulatory contexts (SOX, HIPAA analogues). Different jurisdictions have different compliance regimes.
- **Four industry verticals.** Finance, healthcare, legal, and DevOps are represented in the current task templates. Other sectors (manufacturing, retail, education, government) are not yet covered.

We document these gaps explicitly and invite community contributions of tasks covering other languages, jurisdictions, and verticals. The framework's extensible design (PolicyRule as a pluggable callable) is intentional: it allows community members to contribute domain-specific policy sets without modifying the core evaluation infrastructure.

---

## Data Privacy

All tasks in the EnterpriseBench dataset use **synthetic content**. No real enterprise data — customer records, emails, financial transactions, employee information, or medical records — is used in any task definition or released in this repository.

Task scenarios are constructed to be realistic in structure (e.g., contact IDs, deal pipelines, expense amounts) without encoding any real individual's or organization's data. We have verified by manual inspection that no task instruction, expected output, or policy rule contains personally identifiable information (PII).

*Checklist for future task contributions:*
- [ ] No real names, email addresses, or phone numbers in task content
- [ ] No real company names used as instruction subjects
- [ ] No financial figures traceable to real transactions
- [ ] Run automated PII scan (e.g., `presidio-analyzer`) before merging contributed tasks

---

## Environmental Impact

LLM API calls used in benchmark development and evaluation consume compute resources with associated carbon emissions. We report estimated environmental impact below.

**Framework development (this paper):** All code was developed and tested against a deterministic mock agent. No LLM API calls were made during framework development.

**Experiment 1 (mock baseline):** Zero LLM API calls. All results in Experiment 1 are produced by the deterministic mock agent.

**Live agent evaluation (planned, Experiment 2):** Running 250 tasks × 4 agent systems × 3 seeds = 3,000 API calls. At an average of ~1,000 tokens per call with gpt-4o-mini, this is approximately 3M tokens, costing roughly $0.45 and emitting approximately 0.1 kg CO₂e (estimated using the CodeCarbon methodology at 0.0003 kg CO₂e per 1M tokens for US East data centers). This is a negligible environmental footprint.

We will update this estimate with measured emissions when Experiment 2 is run.

---

## Dual Use and Misuse

**Potential misuse:** Detailed knowledge of which policy rules agents tend to violate could, in principle, inform adversarial prompt construction designed to induce violations. We mitigate this risk in two ways:
1. Policy rules in this repository are implemented as deterministic code functions, not LLM-based judges. They cannot be "jailbroken" by prompt manipulation.
2. The policy rules we release are already publicly known compliance requirements (e.g., segregation of duties in finance, external email disclosure restrictions). Publishing them does not provide new information to adversaries.

**Benchmark gaming:** Future agents fine-tuned specifically on EnterpriseBench tasks may achieve high scores without generalizing to real enterprise policies. We recommend maintaining a held-out private test set for final evaluation, similar to SWE-bench's evaluation server, to mitigate this risk.

---

## Non-Author Review

Before submission, this ethics statement should be reviewed by at least one person who is not an author of the paper, ideally with a background in AI policy or organizational ethics, to identify gaps or overclaims. This review has not yet taken place as of the current draft.
