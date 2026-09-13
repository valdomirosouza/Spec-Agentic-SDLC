<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Model card — claude-sonnet-4-6

> Instance of [`../../templates/model-card-template.md`](../../templates/model-card-template.md)
> for the model currently pinned in
> [`../dependency-manifest.yaml`](../dependency-manifest.yaml).
> **Owner:** AI Governance Lead · **Version:** 1.0 · **Date:** 2026-09-13
> **Satisfies:** EU AI Act `ART-11` and `ART-51-55` (deployer's retention duty) · ISO/IEC 42001 A.8

## Model details

| Field                    | Value                                                                 |
| ------------------------ | ----------------------------------------------------------------------- |
| Provider                 | Anthropic PBC                                                          |
| Model id                 | `claude-sonnet-4-6`                                                    |
| Our role                 | **Deployer**, not provider (ADR-0093 §1)                               |
| Selected by              | `LLM_MODEL` environment variable; default mirrors the dependency manifest |
| Modality                 | Text in, text out                                                      |
| Onboarded                | 2026-05-01                                                             |
| Behavioural contract     | Version 1.1 · suite `tests/model_contract/` · last run 2026-09-12, 16/16 pass |
| Approved fallback        | `claude-haiku-4-5-20251001` for low-latency classification (not currently selected by anything) |
| Processing region        | US (Anthropic cloud) — a governed fact under ADR-0094 §2               |
| Provider-side retention  | 30 days of API request logs, per the provider's policy                 |

**What we do not assert.** Training data, architecture, parameter count, context window and
benchmark results are the **provider's** facts. This card does not restate them, because restating
provider facts from memory is how a model card acquires errors that outlive it. Where the provider
publishes them, the adopter links to the published source rather than copying it.

## Intended use in this system

| Use                                                                 | Autonomy                                            |
| --------------------------------------------------------------------- | ----------------------------------------------------- |
| Reasoning over a request and proposing a structured action           | Proposal only — execution passes the HITL gateway    |
| Classifying request risk for HITL/HOTL routing                       | Advisory — the routing rule decides, not the model   |
| Drafting output for human review                                     | Draft only                                            |
| Evaluating another agent's output in the harness                     | Advisory — thresholds decide                          |

**Out of intended use.** Deciding anything about a person; executing an irreversible action
without an approval; producing content shown to a third party without disclosure; any Annex III
purpose the adopter has not assessed (ADR-0093 §2).

## Data that reaches this model

| Class | Reaches the model?                                       | Control                                                      |
| ----- | --------------------------------------------------------- | -------------------------------------------------------------- |
| L1    | **Never**                                                | PII filter before every call; also a residency control (ADR-0094 §2) |
| L2    | Masked                                                   | PII filter; retrieval corpus is L2 and encrypted at rest       |
| L3    | Yes                                                      | Prompt-injection guard on input, output sanitiser on output    |
| L4    | Yes                                                      | —                                                              |

Submitted data is **not used by the provider for training**, recorded as a contract term in the
dependency manifest and in the sub-processor register, row 2.

## Evaluation

| What is measured                        | Where                                                             | Current state                                        |
| --------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------ |
| Behavioural contract conformance        | `tests/model_contract/`, ADR-0051                                  | 16/16 at contract v1.1 on 2026-09-12                  |
| Groundedness                            | SLI, ADR-0080, target ≥ 0.9 with zero tolerance for fabrication    | Threshold defined; no production series recorded yet  |
| Evaluator quality across four dimensions | `docs/ai/eval-scorecard.md`, threshold 0.75                       | Threshold defined                                     |
| Adversarial robustness                  | `tests/abuse_cases/`, ADR-0050; [red-team programme](../../specs/ai/red-team-program.md) | Abuse-case ratchet in place; no red-team exercise recorded |
| Accuracy for the intended purpose       | —                                                                  | **Not declared.** Open gap, shared with EU AI Act `ART-15` |
| Fairness and bias                       | Quarterly procedure in `skills/ethics/ethical-ai-review.md`        | **No result recorded**                                |

The last two rows are the honest weaknesses of this card, and they match the gaps the EU AI Act
matrix and the NIST mapping independently identified.

## Known limitations

1. **Prompt-injection susceptibility is mitigated, not eliminated.** The guard reduces risk; the
   HITL gateway is what bounds the consequence.
2. **Groundedness is measured, not guaranteed.** The SLI detects fabrication after the fact; the
   evaluator and human review are what stop it reaching a decision.
3. **Provider-side change is outside our control.** A model can change behaviour without a version
   change on our side. The contract suite run at promotion detects it at promotion, not
   continuously — which is what post-market monitoring (`ART-72`) exists to cover.
4. **One candidate is blocked.** `claude-sonnet-5` failed the PII non-leakage contract test on
   2026-09-12 and is not promotable. Recorded in the manifest with its tracking issue; a failing
   test is a finding, never a reason to loosen the test.

## Oversight and escalation

Every action with a real-world effect routes through the HITL gateway (ADR-0011). Autonomy is
granted only by governed feature flag (ADR-0015). Escalation triggers are in CLAUDE.md §14, and the
`PreToolUse` guard denies push, merge, release and deploy to subagents regardless of what the model
proposes.

## Change control

| Event                          | What must happen                                                            |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Promoting a new model version  | Full contract suite passes; residency re-verified (ADR-0094 §2); this card updated; registry entry added |
| Provider announces a change    | Contract suite re-run; monitoring note records the outcome                    |
| Contract test fails in production | Model incident: [`../runbooks/RB-AI-001-ai-incident.md`](../runbooks/RB-AI-001-ai-incident.md); roll back by re-pinning |

## Related

- [`../../templates/model-card-template.md`](../../templates/model-card-template.md) — the template
- [`system-card.md`](system-card.md) — the system this model sits inside
- [`model-registry.md`](model-registry.md) — versions, provenance and promotion history
- [`../ai/model-lifecycle.md`](../ai/model-lifecycle.md) — the promotion path
