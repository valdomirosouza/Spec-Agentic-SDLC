<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# EU AI Act — compliance reading

> **Normative source:** [`specs/compliance/eu-ai-act-control-matrix.yaml`](../../specs/compliance/eu-ai-act-control-matrix.yaml).
> That file is the machine-verified obligation set; this page is the human reading of it and
> carries no obligation of its own. Where the two differ, the matrix wins.
> **Classification:** [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md).
> **Owner:** AI Governance Lead · **Last reviewed:** 2026-09-13

## Where this system stands

| Question                        | Answer                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------- |
| Which role does the organisation play? | **Provider** of the agentic AI system **and deployer** of a third-party general-purpose model |
| Which tier?                     | **High-risk** by default under Art. 6(2) with Annex III; narrowing requires a documented Art. 6(3) assessment |
| Does Art. 50 apply?             | **Assumed yes** — the system interacts directly with people                                     |
| Do the GPAI obligations bind us? | Not as provider. As deployer we **retain and record** what the model's provider publishes        |
| Is any Art. 5 practice implemented? | **No — and none may be.** Art. 5 is a refusal condition at the Phase 10 gate, not a risk to mitigate |

## Obligation status

Seventeen control entries cover Art. 5, Arts. 9–17 and 20, Arts. 43/47/48/49, Art. 50,
Arts. 51–55 and Arts. 72–73 with Annex IV. Current distribution:

| Status        | Count | Meaning                                                                    |
| ------------- | ----- | -------------------------------------------------------------------------- |
| `implemented` | 3     | Art. 12 record-keeping, Art. 14 human oversight, Art. 17 quality management |
| `partial`     | 11    | Artefact exists, a named gap remains                                       |
| `prohibited`  | 1     | Art. 5 — a refusal condition, never satisfied by a control                  |
| `n/a`         | 2     | Conformity assessment and CE marking, with a justification and a trigger    |

**Human oversight (Art. 14) is the system's strongest obligation** and the only one with an
executable enforcement point: the HITL gateway, autonomy only through governed feature flags, the
escalation protocol, and a `PreToolUse` guard that denies push, merge, release and deploy to
subagents. **Article 15 accuracy** is the weakest of the implemented set: thresholds exist for the
evaluator and for groundedness, but no accuracy metric has been declared per intended purpose.

## What binds, and from when

| Date           | What starts applying                                                     |
| -------------- | ------------------------------------------------------------------------- |
| 2 Feb 2025     | Art. 5 prohibited practices                                              |
| 2 Aug 2025     | General-purpose AI model obligations (on the model's provider)           |
| 2 Aug 2026     | Art. 50 transparency; governance and penalties regime                    |
| 2 Dec 2027     | Annex III high-risk obligations — Arts. 9–17, 20, 43, 47–49, 72, 73      |
| 2 Aug 2028     | Annex I high-risk obligations (not applicable to this system)            |

These dates were amended after the Regulation was first published. They are re-verified at every
review of ADR-0093 and the matrix carries `last_verified`.

## Reading the matrix

- `adopter:` before a path means the artefact lives in the product repository that adopts this
  corpus, not here.
- `planned:#<issue>:` before a path means the artefact is not written yet and names the open issue
  that will write it. The validator fails once that issue closes and the prefix remains.
- `gap:` on a `partial` control states in one sentence what is missing. A control with `partial`
  status and no `gap` is a defect.

## Related

- [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) — role, tier, triggers
- [`nist-ai-rmf.md`](nist-ai-rmf.md) — the risk-management framework mapping
- [`../compliance/iso42001-scope-and-soa.md`](../compliance/iso42001-scope-and-soa.md) — the management-system side
- [`ai-safety-checklist.md`](ai-safety-checklist.md) — the Phase 10 gate checklist
