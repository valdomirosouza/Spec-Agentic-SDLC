<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ISO/IEC 42001 Annex A — control matrix

> Objective-by-objective assessment of the **38 controls in A.2–A.10**. Scope, applicability
> decisions and certification posture are in
> [`iso42001-scope-and-soa.md`](iso42001-scope-and-soa.md); gaps are tracked in
> [`remediation-register.md`](remediation-register.md).
> **Owner:** AI Governance Lead · **Assessed:** 2026-09-13 · **Against:** `main`
>
> **Copyright and non-fabrication.** ISO/IEC 42001 is licensed. The **titles of the individual
> controls are not reproduced here** and are deliberately not paraphrased one by one: doing so
> from memory would risk inventing control text, which Constitution IX forbids. Each row records
> the objective, the count of controls it contains, our evidence and our gap. Completing the
> per-control rows requires the licensed standard text and is tracked as a remediation item.

## Summary

| Objective | Controls | Coverage   | Evidence in this corpus                                                                                     | Gap                                                                          |
| --------- | -------- | ---------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| **A.2** Policies related to AI | 2–3 | **Strong** | `memory/constitution.md` (nine binding articles, five protected), `specs/ethics/ethical-ai-principles.md`, `CLAUDE.md` §3 | The AI policy is not labelled as such; an auditor looking for "the AI policy" finds a constitution |
| **A.3** Internal organisation | 2–3 | **Strong** | `docs/governance/raci-matrix.md`, `docs/process/RACI.md`, ADR-0034 escalation, named leads per path in `CLAUDE.md` §8 | No management-system owner distinct from the AI Governance Lead |
| **A.4** Resources for AI systems | 4–5 | Partial | Per-feature resources in `templates/plan-template.md`; `docs/dependency-manifest.yaml` pins the model; `specs/ai/tool-registry.md` | No organisation-wide inventory of AI resources: models, prompts, indices, tools, memory (#42) |
| **A.5** Assessing impacts of AI systems | 4–5 | **Strong** | `specs/privacy/dpia-ripd.md` with a release gate, three DPIA/RIPD instances, `skills/ethics/ethical-ai-review.md`, Phase 10 checklist | Impact assessment covers privacy and ethics; societal and environmental impact are not assessed |
| **A.6** AI system life cycle | 9 | **Strong** | The 15-phase lifecycle (ADR-0058), the `/sdd-*` commands, `docs/ai/model-lifecycle.md`, `docs/ai/eval-scorecard.md`, abuse-case ratchet (ADR-0050), model behavioural contracts (ADR-0051) | Verification and validation are defined; a declared accuracy metric per intended purpose is missing (EU AI Act Art. 15 shares this gap) |
| **A.7** Data for AI systems | 4–5 | Partial | `specs/privacy/pii-inventory.md`, `specs/privacy/data-retention.md`, encryption specs, `docs/data/data-model-catalog.md` | Provenance, quality, lineage and acquisition of AI data: issues #29, #32, #33, #34 |
| **A.8** Information for interested parties | 3–4 | Partial | `docs/ai-governance/autonomy-boundaries.md`, `docs/ai-governance/model-card.md` (template), reporting channels in the ethics skill | System card (#38), user-facing disclosure for EU AI Act Art. 50, and a published point of contact |
| **A.9** Use of AI systems | 3–4 | **Strong** | `specs/ai/hitl-hotl.md`, `specs/ai/autonomous-mode-levels.md`, `docs/ai-governance/dual-use-registry.md`, the `PreToolUse` guard | The dual-use registry is empty (#39); intended-use statements live per spec, not centrally |
| **A.10** Third-party and customer relationships | 3–4 | Partial | `docs/dependency-manifest.yaml`, `docs/compliance/dependency-policy.md`, `docs/privacy/data-processing-register.md` | Sub-processor register (#37); supplier assessment criteria for AI providers are not written |

Control counts per objective are approximate where the licensed text is needed to confirm them;
the total of 38 across A.2–A.10 and the identity of A.6 as the largest objective are the published
facts this table relies on.

## What an audit would find first

1. **No internal audit programme and no management review** (clauses 9.2 and 9.3). The corpus
   reviews artefacts constantly and the management system never.
2. **No single AI risk register** (clause 6.1). Risks are real and documented, but spread across
   DPIAs, threat models and ADR consequence sections, so no one can answer "what are our top AI
   risks and who accepted the residual" from one place.
3. **The AI policy is not named as a policy** (A.2). The content is there and is stronger than most
   policies; the artefact is called a constitution and an auditor will not find it by name.
4. **No AI resource inventory** (A.4) and **no sub-processor register** (A.10).

## Remediation

Each gap above is an entry in [`remediation-register.md`](remediation-register.md) with an owner
and a target. Four of them close with issues already open (#29, #32, #33, #34, #37, #38, #39, #42);
the clause 6, 9 and 10 gaps need their own issues and are recorded as such.

## Related

- [`iso42001-scope-and-soa.md`](iso42001-scope-and-soa.md) — scope, clauses, applicability
- [`iso27001-annex-a-control-matrix.md`](iso27001-annex-a-control-matrix.md) — the security counterpart
- [`../ai-governance/eu-ai-act-compliance.md`](../ai-governance/eu-ai-act-compliance.md) — the regulatory counterpart
