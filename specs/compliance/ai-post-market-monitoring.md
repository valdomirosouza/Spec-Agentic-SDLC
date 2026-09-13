---
id: SPEC-COMP-010
kind: policy
status: approved
owner: AI Governance Lead
issue: 27
governing_adrs:
  - ADR-0093
  - ADR-0011
  - ADR-0049
  - ADR-0051
  - ADR-0080
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/compliance/eu-ai-act-control-matrix.yaml
  - specs/ai/guardrails.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# AI post-market monitoring and serious-incident reporting

> Satisfies `ART-72` and `ART-73` of
> [`eu-ai-act-control-matrix.yaml`](eu-ai-act-control-matrix.yaml) and clause 9 of
> [`../../docs/compliance/iso42001-scope-and-soa.md`](../../docs/compliance/iso42001-scope-and-soa.md).
> **Owner:** AI Governance Lead · **Operational owner:** SRE Lead

## 1. Why a separate plan

Ordinary service monitoring answers "is the system up and fast". Post-market monitoring answers a
different question: **"is the system still behaving the way we said it would when we released it,
and is it causing harm we did not anticipate?"** An agentic system can be perfectly available,
within latency budget, and simultaneously drifting toward outputs its evaluator would have failed
three months ago. Golden Signals do not see that.

Article 72 of the EU AI Act requires the plan to be **proportionate to the risk** and to actively
collect and analyse performance data **across the lifetime** of the system. Article 73 requires
serious incidents to be reported once a causal link is established.

## 2. What is monitored

Five families, each with a source that already exists in the corpus. The fifth was added after the
first cycle (#54): in a repository with no runtime, the first four are unobservable, and a plan
that records four empty rows is not a monitoring plan. Corpus integrity is what such a repository
can actually watch.

| Family                        | Signals                                                                                                    | Source                                                    | Review |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------ |
| **Behavioural conformity**    | Evaluator score distribution, groundedness score, refusal rate, escalation rate, share of actions auto-executed vs. approved | `docs/ai/eval-scorecard.md`, agent spans (ADR-0044, ADR-0045) | Weekly |
| **Guardrail effectiveness**   | Prompt-injection blocks, output-sanitiser interventions, PII filter hits, tool calls denied by the registry | `specs/ai/guardrails.md`, `adopter:src/guardrails/`         | Weekly |
| **Human-oversight health**    | Approval latency, expiry rate, override rate, share of approvals with no comment, reopened decisions        | HITL gateway records, ADR-0086                              | Monthly |
| **Model conformity**          | Model contract pass rate, drift indicators, provider-announced model changes, deprecation notices           | `docs/ai/model-lifecycle.md`, `docs/dependency-manifest.yaml` | On change, and monthly |
| **Corpus integrity** _(added 2026-09-13, #54)_ | Check results, drift in generated artefacts, CI failure rate, data-quality violations | `scripts/bash/check-corpus.sh`, `scripts/python/corpus_metrics.py` | Weekly |

**Two of these are leading indicators and must not be dropped when metrics are pruned:** the
override rate (humans disagreeing with the agent more often is the earliest sign of behavioural
drift) and the approval latency (humans approving faster over time is the earliest sign of
automation bias, which Article 14 explicitly requires the system to counter).

## 3. Thresholds and what each one triggers

| Condition                                                            | Severity | Action                                                                                 |
| -------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------- |
| Evaluator score below its threshold for two consecutive review cycles | Medium   | Open a finding; run the model contract suite; consider lowering autonomy                 |
| Groundedness below its SLI target                                     | High     | Treat as a model incident: `docs/runbooks/RB-AI-001-ai-incident.md`                      |
| Guardrail intervention rate rises sharply with no release to explain it | High   | Suspected attack or model change; notify Security Lead, preserve evidence                |
| Override rate rises across a review cycle                             | Medium   | Behavioural review: is the spec wrong, the model changed, or the context degraded?       |
| Approval latency falls while override rate falls                      | Medium   | Suspected automation bias; sample approvals for genuine review                           |
| Model contract suite fails on a pinned version                        | High     | The version is BLOCKED for promotion; if already in production, roll back by re-pinning  |
| Any harm to a person, or a near miss                                  | Critical | Serious-incident procedure, §5                                                            |

Thresholds are proportionate to the high-risk classification recorded in ADR-0093; a system that
narrows to non-high-risk under Article 6(3) may relax the cadence, never the harm trigger.

## 4. Cadence and ownership

| Cycle       | Who                                          | Output                                                                     |
| ----------- | -------------------------------------------- | -------------------------------------------------------------------------- |
| Weekly      | SRE Lead                                     | Behavioural and guardrail dashboard read; findings opened                  |
| Monthly     | AI Governance Lead + SRE Lead                | Written monitoring note: what moved, what was decided, what stays watched  |
| Quarterly   | AI Governance Lead + Security Lead + DPO     | Full review: thresholds, bias audit result, red-team findings, risk register |
| On release  | Phase 11 and Phase 14 of the lifecycle       | Baseline refreshed; the release records the values it starts from          |
| On model change | AI Governance Lead                        | Model contract re-run before promotion (ADR-0051); registry updated        |

The monthly note is the artefact an auditor asks for. A cycle with nothing to report still
produces a note saying so, dated — silence is not evidence of monitoring.

## 5. Serious incidents

### 5.1 What counts

A **serious incident** is an incident or malfunction of the AI system that directly or indirectly
leads to any of: the death of a person or serious harm to health; a serious and irreversible
disruption of critical infrastructure; an infringement of obligations under Union law intended to
protect fundamental rights; or serious harm to property or the environment.

Two clarifications this corpus adds, because they are the realistic cases for an agentic delivery
system:

- **A near miss that only a human gate prevented is treated as a serious incident for internal
  purposes.** It is investigated with the same rigour and recorded, even when no external report is
  required. The gate working is not evidence that the system is safe; it is evidence that the gate
  is load-bearing.
- **An agent action that caused irreversible effect without the required approval** is a serious
  incident regardless of the size of the effect, because the control that failed is the one the
  whole classification depends on.

### 5.2 Procedure

1. **Detect and contain.** Follow [`../../docs/runbooks/RB-AI-001-ai-incident.md`](../../docs/runbooks/RB-AI-001-ai-incident.md): disable the action
   type, lower autonomy, roll back the model version if implicated.
2. **Establish the causal link.** The reporting clock under Article 73 starts when the link
   between the system and the incident is established, or when it is reasonably suspected.
   Record the moment of establishment explicitly — it is what every deadline is measured from.
3. **Classify.** Serious incident, internal-only near miss, or ordinary defect. The AI Governance
   Lead classifies; the SRE Lead may escalate but not downgrade.
4. **Report.** For a serious incident: notify the market surveillance authority of the Member
   State concerned within the deadline the Article sets for that incident class, and no later.
   Where the full investigation cannot complete in time, submit an **initial report** and complete
   it afterwards — an incomplete report on time beats a complete report late.
5. **Inform the chain.** Deployers, distributors and, where the model is implicated, the model
   provider.
6. **Investigate and correct.** Postmortem within 48 hours using
   `docs/postmortems/POSTMORTEM-TEMPLATE.md`; corrective action under Article 20; every finding
   that can be expressed as a test becomes an abuse case, so the ratchet of ADR-0050 rises.
7. **Record.** The incident, its classification, the causal-link timestamp, what was reported and
   to whom, and the corrective action, retained per the audit retention policy.

### 5.3 What the adopter must fill in

Two fields are jurisdiction-specific and cannot be written here:

- the **market surveillance authority** for each Member State where the system is placed on the
  market or put into service;
- the **reporting channel and format** that authority requires.

Until an adopter fills these in, the `ART-73` control stays `partial` in the matrix. This is a
deliberate refusal to invent a contact (Constitution IX), not an oversight.

## 6. How this feeds back

Post-market monitoring is not a filing cabinet. Each cycle ends by asking which of these changes:

- a **threshold** in §3, when the current one produced noise or silence;
- an **abuse case**, when a finding can be expressed as a test;
- the **risk register**, when a new failure mode appeared;
- the **classification** in ADR-0093, when the system's use or autonomy changed;
- the **spec**, when the system is behaving as built but the requirement was wrong.

The last one is the most common and the easiest to miss.

## 7. Open items

| # | Item                                                                     | Owner              | Resolve by            |
| - | ------------------------------------------------------------------------ | ------------------ | --------------------- |
| 1 | Market surveillance authority and reporting channel per Member State     | Adopting organisation | First Union deployment |
| 2 | ~~First monthly monitoring note~~ — done 2026-09-13, [`../../docs/sre/monitoring/2026-09-13-first-cycle.md`](../../docs/sre/monitoring/2026-09-13-first-cycle.md) (#54) | SRE Lead | ✅ |
| 3 | Drift thresholds for the behavioural anomaly metric (ADR-0049)           | AI Governance Lead | Next quarterly review |

## Related

- [`eu-ai-act-control-matrix.yaml`](eu-ai-act-control-matrix.yaml) — `ART-72`, `ART-73`, `ART-20`
- [ADR-0093](../../docs/adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) — classification and triggers
- [`../../docs/runbooks/RB-AI-001-ai-incident.md`](../../docs/runbooks/RB-AI-001-ai-incident.md) — containment
- [`../../docs/ai/model-lifecycle.md`](../../docs/ai/model-lifecycle.md) — promotion and rollback
