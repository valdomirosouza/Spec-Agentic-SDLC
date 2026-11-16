---
id: SPEC-SDLC-002
kind: threat-model
status: draft # draft | in-review | approved | implemented | superseded (ADR-0085)
owner: Security Lead
issue: 199
governing_adrs: [ADR-0011, ADR-0034, ADR-0035, ADR-0070, ADR-0104]
implemented_by: []
verified_by: []
related_specs: [SPEC-AI-008]
last_updated: 2026-11-15
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Threat Model — SPEC-SDLC-002 Dev-time Judge and Advisor (STRIDE)

**Status:** Proposed | **Owner:** Security Lead | **Last updated:** 2026-11-15
**Method:** STRIDE | **Scope:** the dev-time Judge (`asdd-judge`) before the Phase 7 gate, and the
Advisor (`asdd-advisor`) on its two triggers, both invoked by `asdd-orchestrator`
**Sources:** `specs/features/SPEC-SDLC-002-judge-advisor-roles/spec.md` (FR and AC ids below),
[ADR-0104](../../docs/adr/ADR-0104-judge-advisor-roles-and-judge-independence.md) (§ references below)

> **Agent disclosure.** Drafted by an AI agent (Claude) at Phase 5 from the spec and ADR-0104 at
> `35093a2`. The two agents do not exist yet. Every control below is a requirement or decision to
> be built at Phase 6, not a control in place. `uncertain — verify` marks what neither source
> settles.

This model covers dev-time delivery agents, not the runtime product. The runtime STRIDE model in
`specs/security/threat-model.md` is unchanged.

---

## System Boundary

```
producing phase (Phase 7 agent) ──handoff: artefacts, notes, human_gate──▶ asdd-orchestrator
   (writes the artefact: untrusted to the Judge)                 │ ci_checks green? (FR-01/02)
                                                                 │ builds allow-listed envelope (FR-03)
                                                                 ▼ own invocation, isolated (FR-11)
                                     asdd-judge ──judge_verdict_v1──▶ orchestrator ──▶ per-run state
                                     (read-only, FR-07)                    │       .agent/delivery/<id>/
                                                                           ▼
                                                  human gate (Phase 7, tech_lead) — always presented (FR-08)

orchestrator ──question, options (blocked retry · converge round 2, FR-14)──▶ asdd-advisor
                                     ◀── advice record (FR-15) ── caller decides, records `followed` (FR-16)
```

**Trust boundaries:**

- producer ↔ Judge. The artefact crosses it. The producer's notes, session and reasoning must not
  cross it.
- Judge or Advisor ↔ per-run state. Each writes only its own record.
- agent output ↔ human gate. No agent output clears the gate.

---

## STRIDE Analysis

### S — Spoofing

| #   | Threat                                                                                                                         | Component      | Likelihood | Impact | Controls                                                                                                                                                                                                                                                                                                  | Residual |
| --- | ------------------------------------------------------------------------------------------------------------------------------ | -------------- | ---------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1   | **Forged verdict.** A producing agent with write access writes a `pass` record into the per-run state as if the Judge had run. | per-run state  | Medium     | Medium | A verdict never satisfies an approval or a gate, and never changes routing in report mode (FR-08, FR-09). A forged `pass` therefore gains only reviewer bias. Recommended for the plan: the orchestrator persists the record from the Judge invocation's return value, so the producer is not the writer. | Medium   |
| 2   | **Misreported producer model.** `producer_model` comes from the producer's own claim, hiding a same-model verdict.             | verdict record | Low        | Low    | Both models are recorded (FR-12). Who records `producer_model` is not settled by the spec or ADR-0104 (`uncertain — verify`). Recommended for the plan: the orchestrator records it from the invocation it made, not from the producer's handoff.                                                         | Low      |

### T — Tampering

| #   | Threat                                                                                                                                                                           | Component    | Likelihood | Impact | Controls                                                                                                                                                                                                                                                                                                                                                                                                 | Residual |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ---------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 3   | **An artefact written to persuade its judge** (OWASP LLM01, indirect). The producer controls the artefact, so comments, docstrings or text in it can instruct the Judge to pass. | `asdd-judge` | Medium     | High   | Several controls limit what such text can achieve: the Judge is read-only, so injected text cannot make it write (FR-07). Every finding cites evidence, a path and line or a test (spec Key Entities). A criterion it cannot confirm is `unverified` and the verdict is not `pass` (FR-05). The human gate is always presented (FR-08). The spec names this channel as one that cannot be removed (§11). | Medium   |
| 4   | **Producer reasoning leaks into the envelope**, so the Judge inherits the producer's conclusions.                                                                                | orchestrator | Medium     | Medium | The envelope is allow-listed and excludes the producer's handoff `notes`, session and reasoning, and any Advisor output (FR-03, ADR-0104 §2). The Judge runs as its own invocation in isolated context (FR-11). The envelope is recorded with the verdict, so a reviewer can see what the Judge saw (AC-03, SC-04).                                                                                      | Low      |
| 5   | **Rubric weakened.** Criteria are dropped from the Phase 7 rubric so the Judge stops checking them.                                                                              | rubric file  | Low        | Medium | The rubric has no criteria of its own: it is built from the spec's ACs and the Phase 7 `exit_criteria` (ADR-0104 §4). Each verdict names the rubric version. A change to the rubric is a reviewed corpus change. A criterion the rubric does not cover makes the verdict `escalate` (FR-06).                                                                                                             | Low      |

### R — Repudiation

| #   | Threat                                                           | Component               | Likelihood | Impact | Controls                                                                                                                                                                                                                                                                           | Residual |
| --- | ---------------------------------------------------------------- | ----------------------- | ---------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 6   | **A `fail` is overridden without a recorded reason.**            | Phase 7 gate            | Medium     | Medium | Approving a gate whose verdict was `fail` requires a one-line rationale from the human (FR-20, AC-13).                                                                                                                                                                             | Low      |
| 7   | **The caller ignores advice and later denies it.**               | advice record           | Low        | Low    | Every advice record says whether the advice was followed and, if not, why (FR-16, SC-03).                                                                                                                                                                                          | Low      |
| 8   | **Records lost after the run.** The per-run state is gitignored. | `.agent/delivery/<id>/` | Medium     | Medium | The run's records are summarised in the committed FINAL-REPORT (ADR-0104 §4). The full records do not outlive the run unless the adopter keeps them. Whether the summary is enough for the audit trail is for the Security Lead to decide (`uncertain — verify` against ADR-0026). | Medium   |

### I — Information Disclosure

| #   | Threat                                                                                                                                   | Component       | Likelihood | Impact | Controls                                                                                                                                 | Residual |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ---------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 9   | **A verdict or advice record copies a secret or a data value** from the artefact into a record that is summarised in a committed report. | verdict, advice | Low        | High   | Records cite paths, lines and test names, not values (NFR-01). | Low      |

### D — Denial of Service

| #   | Threat                                                       | Component    | Likelihood | Impact | Controls                                                                                                                                                                                              | Residual |
| --- | ------------------------------------------------------------ | ------------ | ---------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 10  | **The Judge hangs or errors** and the gate waits for it.     | `asdd-judge` | Medium     | Low    | A fixed wall-clock limit, whose value is set in the plan (ADR-0104 §4, A4). Reaching it gives a recorded missing verdict, which is never read as `pass`, and the gate is presented (FR-10, AC-08).    | Low      |
| 11  | **Cost runaway** from repeated Judge or Advisor invocations. | both         | Low        | Medium | One Judge invocation per Phase 7 gate. Advice is given on two triggers only (FR-14), and the converge loop is bounded at three rounds (#196). Wall-clock and model are recorded per verdict (NFR-03). | Low      |

### E — Elevation of Privilege

| #   | Threat                                                                              | Component         | Likelihood | Impact   | Controls                                                                                                                                                                                                                                                                | Residual |
| --- | ----------------------------------------------------------------------------------- | ----------------- | ---------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 12  | **A verdict used as an approval**, so a `pass` clears the gate.                     | orchestrator      | Low        | Critical | No verdict satisfies a `required_approvals` entry or a gate (FR-08). In report mode, routing does not change (FR-09, AC-07). Promotion needs ADR-0070 burn-in and a `normal-change` (ADR-0104 §1).                                                                      | Low      |
| 13  | **Advice to bypass a gate is acted on**, or advice replaces a §14.1 escalation.     | caller            | Low        | High     | Advice to skip or weaken a gate, test or guardrail is recorded and not followed (FR-19, AC-12). When a §14.1 trigger fires, `[HITL-ESCALATE]` is emitted whatever the advice says (FR-17, AC-11; ADR-0034).                                                             | Low      |
| 14  | **Judge or Advisor granted write tools**, so a read-only role can change artefacts. | agent definitions | Low        | High     | Both are read-only apart from their own record (FR-07, FR-18, AC-09). Recommended for the plan: declare both agents without `Write` or `Edit`, as `asdd-phase-7-code-review.md` declares `Read, Grep, Bash`, and have the orchestrator persist their records (entry 1). | Low      |

---

## OWASP GenAI control matrix

`specs/security/owasp-genai-control-matrix.yaml` gets **no new rows in this change**.

- The matrix maps the adopting product's runtime controls, one row per OWASP LLM risk. Its LLM01
  row points at `adopter:src/guardrails/prompt_injection_guard.py`.
- The validator fails on any `implemented_by` or `verified_by` path that does not exist
  (ADR-0072). The Judge, its rubric and `tests/scripts/test_judge.py` do not exist until Phase 6.

Whether the matrix should also carry dev-time controls is a scope decision for the Security Lead.
Revisit it at Phase 6, once the paths exist. Until then the dev-time controls are traced through
this model to the spec's ACs.

---

## Summary

The model has 14 STRIDE entries across all six categories, over the producer ↔ Judge boundary, the
per-run state and the human gate.

**Highest residuals.** Three entries are Medium, and each is mitigated rather than removed:

- **Entry 3, the artefact written to persuade its judge.** The spec names this channel as one that
  cannot be removed (§11). Evidence-backed findings, `unverified` ⇒ not `pass` and the
  always-presented gate limit what persuasion can buy.
- **Entry 1, the forged verdict.**
- **Entry 8, records that do not outlive the run.**

**Entries 1 and 8 are bounded by report mode.** While no verdict changes routing or satisfies an
approval, a forged or lost verdict costs reviewer attention, not a gate. Both must be revisited
before the Judge is promoted to blocking.

**Questions for the plan.** These follow from entries 1, 2 and 14:

- Who writes the records?
- Who records `producer_model`?
- Which tools do the two agents declare?
