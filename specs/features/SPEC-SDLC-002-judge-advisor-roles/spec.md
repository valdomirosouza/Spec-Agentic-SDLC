---
id: SPEC-SDLC-002
kind: feature-spec # spec | policy | feature-spec | threat-model
status: draft # draft | in-review | approved | implemented | superseded (ADR-0085)
owner: Tech Lead
issue: 199
governing_adrs: [ADR-0011, ADR-0034, ADR-0035, ADR-0058, ADR-0060, ADR-0070, ADR-0080, ADR-0095]
new_adrs_required: [judge-advisor-roles-and-judge-independence]
implemented_by: [] # filled at Phase 6
verified_by: [] # tests that prove the acceptance criteria
related_specs: [SPEC-AI-008, SPEC-AI-009, SPEC-AI-015, SPEC-COMP-010]
roadmap: null # specs/features/<epic>/roadmap.md → entry R<n>, when this spec is a slice of an epic
last_updated: 2026-11-15
---

# Feature Specification: Dev-time Judge and Advisor roles

**Input**: Dev-time Judge and Advisor roles for the Agentic Spec-Driven Delivery lifecycle
(P1, P2 and P3 of `PROPOSAL-judge-advisor-graduated-oversight`, 2026-11-15). The Judge is an
independent, read-only subagent that returns a structured verdict before a human gate and never
fixes or approves. The Advisor is a consultative, non-blocking subagent consulted on declared
triggers before a decision. Nothing removes or converts any of the nine human gates.
**Risk class**: ai _(dev-time agents that judge and advise other agents; Phase 0 vocabulary)_

> **Agent disclosure.** Drafted by an AI agent (Claude) through `/sdd-specify` from the proposal
> named above and a read of the corpus at `a698589`. Every path, ADR and field cited here was
> checked against that commit; anything not checked is marked `uncertain — verify`.

## Clarifications

<!-- Filled by /sdd-clarify. One "### Session YYYY-MM-DD" per run; "- Q: … → A: …" per answer. -->

### Session 2026-11-15

- Q1: Is the Judge a new agent with per-phase rubrics, or a responsibility added to `/sdd-analyze`
  and `/sdd-converge`? → A: a new agent, `asdd-judge`, with per-phase rubrics. Independence is the
  point of US2, and folding it into analyze or converge keeps the judging session next to the
  producer's. The added agent is justified in the plan's Complexity Tracking table (Article VIII).
- Q2: Is a different model class from the producer a requirement or a recommendation? → A: a
  recommendation. Both models are always recorded, and a same-model verdict says so (FR-12). An
  adopter with one approved model can comply. ADR-0035 is amended, not superseded (A5).
- Q3: When a human approves a gate whose verdict was `fail`, is a recorded rationale required?
  → A: yes, one line (FR-20). Phase 7 calibration (proposal P6) needs it to tell disagreement from
  rubber-stamping.

## 1. Context & Problem

### 1.1 Problem statement

The runtime side of the corpus already has a judge and an oversight model graduated by risk. The
harness `EvaluatorAgent` scores output with anti-leniency rules and escalates after
`harness_max_iterations` (SPEC-AI-008 §1.3, §1.4). HITL and HOTL are chosen by risk score
(SPEC-AI-009). The dev-time delivery lifecycle has neither:

- **No independent verdict precedes a human gate.** The Phase 7 agent opens the PR, verifies the
  Definition of Done and requests review itself (`.claude/agents/asdd-phase-7-code-review.md`).
  The human reviewer is the first independent check.
- **No consultation short of a human.** A delivery agent that is unsure has two options: proceed,
  or stop with `[HITL-ESCALATE]` (CLAUDE.md §14). Nothing sits between them.
- **Producer and reviewer share a model.** ADR-0035 pins the AI review to the producing session's
  model "for consistency", so a reviewer can share the producer's blind spots.

### 1.2 Why now

The implement ↔ converge loop is now bounded (#196), and the nine human gates are now listed once
(#191). An independent check can therefore be placed at a known boundary, in front of a known
gate, without first settling what the gates are.

## 2. User Scenarios & Testing _(mandatory)_

### User Story 1 — Independent verdict before code review (Priority: P1) 🎯 MVP

A Tech Lead opening the Phase 7 gate sees, beside the PR, a verdict from an agent that did not
write the code. The verdict names each acceptance criterion it checked, the evidence, and the
criteria it could not confirm. The Tech Lead still decides. The verdict changes what they look at
first, not who approves.

**Why this priority**: Phase 7 is the gate every code change crosses, and the one where the
producer currently checks its own work (§1.1).

**Independent Test**: run a Phase 7 delivery on a spec whose implementation misses one acceptance
criterion. The gate packet carries a `fail` verdict naming that criterion, the gate still stops for
the human, and no approval is recorded on the human's behalf.

**Acceptance Scenarios**:

1. **Given** Phase 7 emitted its handoff with `human_gate: true` and its `ci_checks` are green,
   **When** the orchestrator reaches the gate, **Then** it invokes the Judge and attaches the
   verdict to the gate before asking the human.
2. **Given** the Judge returns `pass`, **When** the gate is presented, **Then** the human approval
   is still required and the `required_approvals` entry (`tech_lead`) is still open.
3. **Given** the Judge cannot confirm a criterion, **When** it returns, **Then** that criterion is
   listed as unverified and the verdict is not `pass`.
4. **Given** the phase's `ci_checks` are red, **When** the phase hands off, **Then** the Judge does
   not run, and the phase is blocked as it is today.

### User Story 2 — The Judge cannot be steered by the producer (Priority: P2)

A Security Lead auditing a delivery can show that the Judge's input held no reasoning from the
agent whose work it judged, and can tell which model judged and which model produced.

**Why this priority**: a judge that reads the producer's reasoning, or shares its context, inherits
the producer's conclusions. Independence is what makes US1 worth having.

**Independent Test**: inspect a recorded verdict and its input envelope. The envelope holds only
allow-listed items, and the verdict names both models.

**Acceptance Scenarios**:

1. **Given** a producing phase wrote `notes` in its handoff, **When** the Judge is invoked, **Then**
   its input contains neither those notes, nor the producer's session, nor any Advisor output.
2. **Given** a verdict, **When** it is read, **Then** it records `judge_model` and `producer_model`.

### User Story 3 — Advice before a retry or another round (Priority: P3)

An orchestrator about to retry a blocked phase, or a run entering its second implement ↔ converge
round, first asks an Advisor what is likely wrong and what the options are. The Advisor recommends.
The caller decides, records whether it followed the advice, and stays accountable for the outcome.

**Why this priority**: retries and extra rounds are where runs spend the most for the least. A
second opinion before them is cheaper than a third failed attempt. It depends on nothing in US1
or US2.

**Independent Test**: block a phase on a missing input. Before the first retry the orchestrator
records an advice entry: question, options, recommendation, and whether it was followed.

**Acceptance Scenarios**:

1. **Given** a phase returned `blocked`, **When** the orchestrator is about to retry it, **Then** it
   consults the Advisor first and records the advice.
2. **Given** a `CLAUDE.md` §14.1 trigger has fired, **When** the Advisor has been consulted, **Then**
   `[HITL-ESCALATE]` is still emitted, whatever the advice says.
3. **Given** advice was given, **When** the caller acts, **Then** the record shows whether the
   advice was followed and, if not, why.

### Edge Cases

- The Judge times out or errors. The gate is presented without a verdict, and the missing verdict
  is recorded as such. A missing verdict is never read as `pass`.
- The rubric for the phase is missing or does not cover a criterion in the spec. The Judge returns
  `escalate`, naming the gap.
- The spec has no acceptance criteria for the changed behaviour. The Judge returns `escalate`; it
  does not invent criteria.
- The Judge and the producer resolve to the same model. The verdict is still recorded, with both
  model ids, so the overlap is visible.
- The Advisor recommends skipping or weakening a gate or a test. The recommendation is recorded and
  never acted on: gates and tests are outside the caller's discretion (Constitution II, IV, V).
- A human overrides a Judge `fail` at the gate. The override is the human's decision. They record a one-line rationale (FR-20).

## 3. Non-Goals / Out of Scope

- **Converting any human gate to HOTL, or removing one.** Article V fixes the nine. That would be a
  constitutional amendment, not this feature.
- **Blocking mode.** The Judge enters in report mode. Promotion follows ADR-0070 and is a later
  `normal-change`.
- **Phases other than 7** for the Judge. Extending it is a later change, one phase at a time, each
  with its own rubric and burn-in.
- **Advisor triggers other than the two in FR-14.** The proposal lists more (ADR drafting, tier
  promotion, ambiguous intake). They are deferred.
- **Risk-graduated review depth** (proposal P5) and **Judge calibration metrics** (P6). Each gets
  its own spec. P5 waits for P6 data.
- **The runtime `EvaluatorAgent`** (SPEC-AI-008) is unchanged.

## 4. Functional Requirements _(mandatory)_

| ID    | Requirement (EARS: WHEN … the system SHALL …)                                                                                                                                                                                                                        | Story | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------- |
| FR-01 | WHEN a phase in the Judge's scope hands off with `human_gate: true` and its `ci_checks` are green, the orchestrator SHALL invoke the Judge before presenting the gate to the human.                                                                                  | US1   | must     |
| FR-02 | WHEN a phase's `ci_checks` are not green, the Judge SHALL NOT run, and the phase SHALL be blocked as it is without the Judge.                                                                                                                                        | US1   | must     |
| FR-03 | The Judge SHALL receive only the phase's artefacts, the spec sections in scope and the phase rubric at a stated version. It SHALL NOT receive the producer's handoff `notes`, the producer's session or reasoning, the orchestrator's history or any Advisor output. | US2   | must     |
| FR-04 | WHEN the Judge finishes, it SHALL return exactly one `judge_verdict_v1` record (Key Entities).                                                                                                                                                                       | US1   | must     |
| FR-05 | WHEN the Judge cannot confirm a rubric criterion, it SHALL list the criterion under `unverified`, and the verdict SHALL NOT be `pass`.                                                                                                                               | US1   | must     |
| FR-06 | WHEN the rubric, the spec's acceptance criteria or the artefact is insufficient to judge a criterion, the Judge SHALL return `escalate`, naming what is missing, and SHALL NOT invent a criterion.                                                                   | US1   | must     |
| FR-07 | The Judge SHALL NOT modify any artefact, code, spec or state other than recording its own verdict.                                                                                                                                                                   | US1   | must     |
| FR-08 | A Judge verdict of any value SHALL NOT satisfy a `required_approvals` entry or a human gate. The gate SHALL be presented to the human in every case.                                                                                                                 | US1   | must     |
| FR-09 | WHILE the Judge is in report mode, the orchestrator SHALL attach the verdict to the gate and record it, and SHALL NOT change routing because of it.                                                                                                                  | US1   | must     |
| FR-10 | WHEN the Judge errors or times out, the orchestrator SHALL present the gate with the verdict recorded as missing, and SHALL NOT treat a missing verdict as `pass`.                                                                                                   | US1   | must     |
| FR-11 | The Judge SHALL run as its own invocation, in isolated context, separate from the producing phase and from any Advisor invocation.                                                                                                                                   | US2   | must     |
| FR-12 | Every verdict SHALL record `judge_model` and `producer_model`. A different model class from the producer is recommended, not required; WHEN the two are the same, the verdict SHALL say so.                                                                                             | US2   | must     |
| FR-13 | The Judge SHALL be introduced in report mode, scoped to Phase 7 only, with an entry in `docs/governance/gate-lifecycle.md` (ADR-0070).                                                                                                                               | US1   | must     |
| FR-14 | WHEN a phase returned `blocked` and the orchestrator is about to retry it, or WHEN the implement ↔ converge loop is entering its second round, the caller SHALL consult the Advisor before deciding.                                                                 | US3   | must     |
| FR-15 | WHEN consulted, the Advisor SHALL return one advice record: the question, the options considered, a recommendation and its rationale.                                                                                                                                | US3   | must     |
| FR-16 | WHEN the caller acts after advice, it SHALL record whether it followed the advice and, if it did not, why.                                                                                                                                                           | US3   | must     |
| FR-17 | The Advisor SHALL NOT clear a gate, satisfy a `required_approvals` entry or replace a `CLAUDE.md` §14.1 escalation. WHEN a §14.1 trigger has fired, `[HITL-ESCALATE]` SHALL be emitted whatever the advice.                                                          | US3   | must     |
| FR-18 | The Advisor SHALL NOT modify any artefact, code, spec or state other than recording its advice.                                                                                                                                                                      | US3   | must     |
| FR-19 | WHEN advice recommends skipping, weakening or bypassing a gate, test or guardrail, the caller SHALL record the advice and SHALL NOT act on that recommendation.                                                                                                      | US3   | must     |
| FR-20 | WHEN a human approves a gate whose Judge verdict was `fail`, the approval record SHALL carry a one-line rationale from that human. | US1 | must |

### Key Entities

- **Judge verdict (`judge_verdict_v1`)**: one per Judge invocation.
  - `phase`, and `verdict` (`pass` · `fail` · `escalate`).
  - `rubric`: the rubric's identity and version.
  - `findings`: each has a criterion id (an AC or FR key), a severity (CRITICAL · HIGH · MEDIUM ·
    LOW, the `/sdd-converge` step 5 scale), the evidence (a path and line, or a test), and a
    one-line statement.
  - `unverified`: the criteria it could not confirm.
  - `groundedness`: a separate score, in the sense of ADR-0080.
  - `judge_model`, `producer_model` and a timestamp.
- **Rubric**: per phase and versioned. It lists the criteria the Judge checks, each traceable to the
  spec's ACs or the phase's exit criteria in `phase-gates.yaml`. The rubric for Phase 7 is the
  first and only one in scope.
- **Advice record**: one per consultation.
  - the trigger, and the caller (the orchestrator or a phase);
  - the question, the options considered, the recommendation and its rationale;
  - `followed` (yes or no), and the caller's reason when it is no;
  - the Advisor's model id and a timestamp.

## 5. Non-Functional Requirements

| ID     | Requirement                                                                                                                    | Category (taxonomy) | Evidence / gate                      |
| ------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------- | ------------------------------------ |
| NFR-01 | A Judge verdict and an advice record carry no PII and no secret. They cite paths and lines, not data values.                   | Privacy             | AC-09                                |
| NFR-02 | Each Judge and Advisor task declares at most two skills (ADR-0060).                                                            | Maintainability     | agent definitions; review at Phase 7 |
| NFR-03 | The Judge's wall-clock and the model it ran on are recorded per verdict, so its cost can be read in the delivery FINAL-REPORT. | Cost (FinOps)       | AC-10                                |
| NFR-04 | Every verdict and advice record is traceable to the run, phase, spec id and issue it belongs to.                               | Compliance          | AC-04, AC-08                         |
| NFR-05 | Agents propose and humans decide: no Judge or Advisor output changes a gate, an approval or an autonomy flag.                  | Human-oversight     | AC-02, AC-07                         |

## 6. Success Criteria _(mandatory, measurable, technology-agnostic)_

| ID    | Measurable outcome                                                                                  | Measurement                                                                   |
| ----- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| SC-01 | Every Phase 7 gate reached in report mode carries a verdict, or a recorded missing verdict.         | count of Phase 7 gates vs verdict records, per release retrospective          |
| SC-02 | Zero gates opened, and zero approvals recorded, on the strength of a Judge or Advisor output alone. | audit of the gate and approval records against the verdict and advice records |
| SC-03 | Every advice record says whether the advice was followed.                                           | share of advice records with `followed` set: 100%                             |
| SC-04 | No Judge input envelope contains producer notes, producer reasoning or Advisor output.              | inspection of recorded envelopes, sampled per release                         |

## 7. Governance, Privacy & Security _(gate: threat & privacy review)_

| Concern                                  | Control in this spec                                                                                                                                                                                                                                | Maps to                                        |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Human oversight (HITL/HOTL)              | Additive only. The nine gates and every `required_approvals` entry are unchanged. Judge and Advisor output never clears either (FR-08, FR-17). The Advisor never replaces a §14.1 escalation.                                                       | ADR-0011, ADR-0034, Constitution V             |
| PII (classify L1–L4; mask at boundaries) | No new personal data. Verdicts and advice cite paths, lines and test names, not values (NFR-01).                                                                                                                                                    | ADR-0012, specs/privacy/                       |
| DPIA / RIPD required?                    | no. No new processing of personal data.                                                                                                                                                                                                             | docs/privacy/dpia/                             |
| Auditability (immutable trail)           | Every verdict and advice record is kept with the run and summarised in the FINAL-REPORT (A3). Overrides of a `fail` carry a rationale (FR-20).                                                                                                              | ADR-0026, Constitution VII                     |
| Authn / abuse (auth, rate limit)         | The Judge and the Advisor are read-only (FR-07, FR-18). The producer cannot reach the Judge's input (FR-03, FR-11). That is the injection path: an artefact written to persuade its judge.                                                          | specs/security/threat-model.md                 |
| OWASP controls touched                   | LLM01: the Judge reads artefacts written by another agent, so an artefact is untrusted input to it. LLM09: a verdict is advisory and a human decides. Mapping these rows into `owasp-genai-control-matrix.yaml` is `uncertain — verify` at Phase 5. | specs/security/owasp-genai-control-matrix.yaml |

## 8. Golden Signals & SLO _(gate: observability)_

Dev-time agents. These signals are read per run and per release retrospective, not from a
production dashboard.

| Signal     | Derivation                                                                                      | Exposed as                  |
| ---------- | ----------------------------------------------------------------------------------------------- | --------------------------- |
| Traffic    | Judge invocations per gate, and Advisor consultations per trigger                               | counts in the FINAL-REPORT  |
| Latency    | Judge wall-clock from invocation to verdict                                                     | P50 / P95 / P99 per release |
| Errors     | Judge errors and timeouts (FR-10), and `escalate` verdicts                                      | error_rate per release      |
| Saturation | Judge tokens per verdict, against the phase's context budget (`docs/process/context-budget.md`) | share of budget used        |

### Reconciliations _(only under the `batch-data` profile — ADR-0103)_

N/A. This feature runs no batch pipeline.

## 9. Acceptance Criteria _(gate: canonical, machine-traceable)_

The test paths below are planned for Phase 6 and do not exist yet.

| ID    | Given / When / Then (one line)                                                                                                                                                                                  | Covers FR(s)        | Verified by (test path or `requirement` marker)                        |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------- |
| AC-01 | Given Phase 7 hands off with `human_gate: true` and green `ci_checks`, when the gate is reached, then a verdict is attached before the human is asked.                                                          | FR-01, FR-13        | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-01")`   |
| AC-02 | Given red `ci_checks`, when the phase hands off, then no verdict is produced and the phase is blocked.                                                                                                          | FR-02               | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-02")`   |
| AC-03 | Given a handoff with producer `notes` and an Advisor record for the run, when the Judge is invoked, then its input envelope holds neither, and the invocation is separate from both.                            | FR-03, FR-11        | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-03")`   |
| AC-04 | Given any verdict, when it is validated, then it matches `judge_verdict_v1` and names both models.                                                                                                              | FR-04, FR-12        | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-04")`   |
| AC-05 | Given a criterion the Judge could not confirm, when the verdict is validated, then the criterion is under `unverified` and the verdict is not `pass`.                                                           | FR-05               | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-05")`   |
| AC-06 | Given a spec with no AC for the changed behaviour, or a rubric missing a criterion, when the Judge runs, then it returns `escalate` naming the gap.                                                             | FR-06               | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-06")`   |
| AC-07 | Given a `pass` verdict, when the gate is presented, then the human approval and the `required_approvals` entry are still open, and routing is unchanged.                                                        | FR-08, FR-09        | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-08")`   |
| AC-08 | Given a Judge error or timeout, when the gate is presented, then the verdict is recorded as missing and nothing reads it as `pass`.                                                                             | FR-10               | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-10")`   |
| AC-09 | Given a Judge or Advisor run, when its files are compared before and after, then only its own record was written.                                                                                               | FR-07, FR-18        | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-07")`   |
| AC-10 | Given a blocked phase about to be retried, or a converge entering round 2, when the caller decides, then one advice record exists with the question, options, recommendation and rationale, and `followed` set. | FR-14, FR-15, FR-16 | `tests/scripts/test_advisor.py` — `requirement("SPEC-SDLC-002/FR-14")` |
| AC-11 | Given a §14.1 trigger and advice to proceed, when the caller acts, then `[HITL-ESCALATE]` is emitted and no gate or approval is cleared.                                                                        | FR-17               | `tests/scripts/test_advisor.py` — `requirement("SPEC-SDLC-002/FR-17")` |
| AC-12 | Given advice to skip a gate or weaken a test, when the caller acts, then the advice is recorded and not followed.                                                                                               | FR-19               | `tests/scripts/test_advisor.py` — `requirement("SPEC-SDLC-002/FR-19")` |
| AC-13 | Given a `fail` verdict, when the human approves the gate, then the approval record carries a one-line rationale, and an approval without one is refused. | FR-20 | `tests/scripts/test_judge.py` — `requirement("SPEC-SDLC-002/FR-20")` |

## 10. Requirement Coverage _(gate)_

| FR    | AC    |
| ----- | ----- |
| FR-01 | AC-01 |
| FR-02 | AC-02 |
| FR-03 | AC-03 |
| FR-04 | AC-04 |
| FR-05 | AC-05 |
| FR-06 | AC-06 |
| FR-07 | AC-09 |
| FR-08 | AC-07 |
| FR-09 | AC-07 |
| FR-10 | AC-08 |
| FR-11 | AC-03 |
| FR-12 | AC-04 |
| FR-13 | AC-01 |
| FR-14 | AC-10 |
| FR-15 | AC-10 |
| FR-16 | AC-10 |
| FR-17 | AC-11 |
| FR-18 | AC-09 |
| FR-19 | AC-12 |
| FR-20 | AC-13 |

**Coverage footer.** _20_ FRs total · _20_ mapped to ≥ 1 AC · **_0_ unmapped**

## 11. Risks & Limitations

- **Automation bias.** A `pass` may become a reason to review less. FR-08 keeps the gate, but it
  does not keep the attention. Measuring that is P6, out of scope here (§3), and P5 (review depth)
  must not ship before it.
- **Same blind spots.** A Judge on the producer's model may share its errors. FR-12 makes this
  visible. A different model class is recommended, not required (Q2).
- **An artefact can be written to persuade its judge.** The producer controls the artefact, so the
  artefact is untrusted input to the Judge (§7, LLM01). FR-03 and FR-11 remove the other channels.
  They cannot remove this one.
- **Cost.** One more model invocation per Phase 7 gate, plus one per advised retry or round. NFR-03
  makes it measurable. The budget belongs in `specs/sre/finops.md` (`uncertain — verify` its
  section).
- **Two new agents** against Constitution VIII. Justify in the plan's Complexity Tracking table (Q1).

## 12. Open Questions

None. Q1, Q2 and Q3 were answered on 2026-11-15 (§Clarifications).

## 13. Assumptions

| #   | Assumption                                                                                                                                                                                                                                                                        | Owner     | Resolve by (phase) | Status (open / confirmed / rejected) |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------ | ------------------------------------ |
| A1  | The Advisor triggers are exactly the two in FR-14: blocked retry and round 2. Both are cheap to detect from state that already exists: the `blocked` status, and the count of Convergence sections (#196).                                                                        | Tech Lead | 4 — Specification  | open                                 |
| A2  | The rubric for Phase 7 is built from the spec's ACs and the Phase 7 `exit_criteria` in `phase-gates.yaml`, with no criteria of its own.                                                                                                                                           | Tech Lead | 5 — Architecture   | open                                 |
| A3  | Verdict and advice records live in the per-run state under `.agent/delivery/<feature_id>/`, which is gitignored and per run (`asdd_state.py`). They are summarised in the committed FINAL-REPORT. The State Ledger (`specs/ai/agent-memory.md` §5b) was not read and is not used. | Tech Lead | 5 — Architecture   | open                                 |
| A4  | A Judge timeout is a fixed wall-clock limit set in the plan. FR-10 governs what happens at it.                                                                                                                                                                                    | Tech Lead | 5 — Architecture   | open                                 |
| A5  | The new ADR amends ADR-0035's "same model for consistency" clause: a different model class for the Judge is recommended and recorded, not required (Q2). | Tech Lead | 5 — Architecture | confirmed |

## 14. References

- `PROPOSAL-judge-advisor-graduated-oversight` (2026-11-15), P1, P2 and P3. Its P4 shipped as #196,
  and its P7 findings as #188 to #192.
- SPEC-AI-008 `specs/ai/harness-design.md` §1.3, §1.4 and §6.2: the runtime Evaluator and its
  bounded loop.
- SPEC-AI-009 `specs/ai/hitl-hotl.md`: runtime HITL and HOTL by risk.
- SPEC-COMP-010 `specs/compliance/ai-post-market-monitoring.md` §2 and §3: the oversight-health
  signals that P6 will extend to dev-time.
- `docs/sdlc/agent-handoff-schema.md`: the handoff message and the receive and return envelope.
- `docs/sdlc/agentic-spec-driven-delivery.md` §Required human gates: the nine (#191).
- `.claude/skills/sdd-converge/SKILL.md`: the severity scale and the round count (#196).
- `prompts/evaluator/evaluate.v2.md`: "cannot confirm counts as fail".
