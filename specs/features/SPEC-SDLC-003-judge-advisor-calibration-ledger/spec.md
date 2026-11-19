---
id: SPEC-SDLC-003
kind: feature-spec # spec | policy | feature-spec | threat-model
status: draft # draft | in-review | approved | implemented | superseded (ADR-0085)
owner: Tech Lead
issue: 206
governing_adrs: [ADR-0011, ADR-0026, ADR-0058, ADR-0070, ADR-0104]
new_adrs_required: [calibration-ledger-persistence] # decided at Phase 5 (A2)
implemented_by: [] # filled at Phase 6
verified_by: [] # tests that prove the acceptance criteria
related_specs: [SPEC-SDLC-002, SPEC-COMP-010]
roadmap: null # specs/features/<epic>/roadmap.md → entry R<n>, when this spec is a slice of an epic
last_updated: 2026-11-17
---

# Feature Specification: Judge and Advisor calibration ledger

**Input**: the calibration of the dev-time Judge and Advisor (P6 of
`PROPOSAL-judge-advisor-graduated-oversight`, 2026-11-15), scored against later evidence and
measurement only. It is recorded in issue #206 with the Tech Lead's scoring decisions of
2026-11-16.
**Risk class**: ai _(it measures dev-time agents that judge and advise other agents; Phase 0
vocabulary)_

> **Agent disclosure.** Drafted by an AI agent (Claude) through `/sdd-specify` from issue #206, the
> proposal named above and a read of the corpus at `dbe228b`. Every corpus path, ADR and field cited
> here was checked against that commit. Anything not checked is marked `uncertain — verify`. The
> proposal is the author's working note under `temp/` and is not part of the corpus. Issue #206
> carries the decisions this spec relies on.

## Clarifications

<!-- Filled by /sdd-clarify. One "### Session YYYY-MM-DD" per run; "- Q: … → A: …" per answer. -->

### Session 2026-11-16 (scope decisions taken before drafting)

- Q: Should the ledger and the decision-delegation flow be one spec, two specs, or an amendment to
  SPEC-SDLC-002? → A: two specs. This one, the ledger, comes first. The delegation flow
  (SPEC-SDLC-004) is deferred until this ledger has data, because it conflicts with ADR-0104 (the
  Judge is on Phase 7 only, and the Advisor has two triggers). A simulated Judge and a simulated
  Advisor recommended the split, and the Tech Lead decided it.
- Q: What do the rewards and penalties score against? → A: later evidence, never agreement with
  the Tech Lead. A Tech Lead override is data, not ground truth. The values in FR-04 and FR-05 are
  the Tech Lead's decision, made after the Advisor pointed out that a first draft (+1 when
  confirmed, −1 when overridden) rewarded sycophancy.

### Session 2026-11-17 (decisions after independent Judge reviews)

- Q: Two rules in #206 conflict. "Never score for agreement with the Tech Lead" sits beside "−1 for a
  false block", and a false block exists only when the human overrides. → A (Tech Lead): a `fail`
  scores +1 when its cited evidence reproduces, whatever the human decided. The −1 applies only to
  an overridden `fail` whose evidence did not reproduce and that no defect, revert or CI failure
  followed. Agreement never yields a positive score (FR-04). An independent Judge review found that
  the two earlier drafts let agreement earn +1.
- Q: Being followed earned the Advisor +1 when nothing went wrong, which scores the calling agent's
  agreement. → A (Tech Lead): advice that was followed and borne out scores 0, because the
  alternative is unknown. Followed and failed scores −2. Not followed, with a human recording that
  the advice would have avoided the failure, scores +1. Being followed never earns a point (FR-05).
- Three Judge rounds did not converge, so per the `/sdd-specify` three-pass limit no fourth round
  was run. The remaining MEDIUM and LOW findings were fixed, and the Spec-as-PR review is the next
  check.

## 1. Context & Problem

### 1.1 Problem statement

SPEC-SDLC-002 introduces a Judge, which gives a verdict before the Phase 7 gate in report mode, and
an Advisor, which advises on two triggers. Nothing measures whether either one is right:

- **The value of a verdict is unknown.** The human at the gate sees a `pass` or a `fail`, but no
  record says how often a `pass` was later contradicted by a defect or a revert. Promoting the
  Judge out of report mode under ADR-0070 would rely on run counts alone.
- **Automation bias cannot be seen.** SPEC-COMP-010 §2 names two leading indicators: the override
  rate and the approval latency. Its §3 treats "approval latency falls while override rate falls"
  as suspected automation bias. Neither is yet collected for the Judge's gates.
- **The obvious scoring would be harmful.** If an agent scores by agreeing with the human, it
  learns sycophancy and hides automation bias. If it scores by agreeing with the other agent, the
  two learn to collude, which undoes ADR-0104 §2. Penalising escalation discourages the
  "uncertain — verify" state that Constitution IX requires.

### 1.2 Why now

SPEC-SDLC-002 and ADR-0104 are approved and accepted. SPEC-SDLC-002 §3 deferred calibration to "its
own spec", and the proposal's §6 (the author's working note, outside the corpus) orders measurement before anything that depends on the Judge. The
deferred delegation flow (SPEC-SDLC-004) is waiting on this ledger's data.

## 2. User Scenarios & Testing _(mandatory)_

### User Story 1 — Every verdict and every piece of advice is scored by what happened next (Priority: P1) 🎯 MVP

The Tech Lead can look up any Judge verdict or Advisor advice. The record shows what the agent said,
what the human decided, and what happened afterwards: a CI failure, a revert, or a defect traced to
that decision. A score is derived from that later evidence by fixed rules, not from whether the
human agreed.

**Why this priority**: every other use of the ledger depends on its entries existing and being
scored correctly.

**Independent Test**: record a Judge `pass` that a human approved, then record a revert traced to
that gate. The entry's Judge score is −3, and it is the same whether or not the human agreed with
the verdict.

**Acceptance Scenarios**:

1. **Given** a Judge verdict or an Advisor advice record exists, **When** the related human
   decision is made, **Then** a calibration entry pairs them, with the human's rationale when there
   is one.
2. **Given** an open entry, **When** later evidence is recorded against it, **Then** the entry is
   scored by the FR-04 or FR-05 rules.
3. **Given** a verdict of `escalate` or "uncertain — verify", **When** the entry is scored, **Then**
   the score is 0, whatever happened next.

### User Story 2 — The release retrospective shows whether the Judge can be trusted (Priority: P2)

At the Phase 14 release retrospective, the Tech Lead sees per gate and per release: the agreement
rate, the false-pass rate, the override-with-rationale rate and the approval latency. When the
sample is too small, the report says so instead of showing a number. When latency falls while
overrides fall, the report flags suspected automation bias.

**Why this priority**: this gives the humans who decide promotion under ADR-0070, and SPEC-SDLC-004,
evidence beyond run counts. People read the report, and no score is an automated input (FR-10). It
needs US1's entries to exist.

**Independent Test**: build a release with nine scored entries, then with ten. With nine, the report
shows "insufficient sample" in place of the totals. With ten, it shows them.

**Acceptance Scenarios**:

1. **Given** a release with at least 10 closed entries for a gate, **When** the retrospective is
   drafted, **Then** the four metrics appear for that gate.
2. **Given** fewer than 10 closed entries, **When** the retrospective is drafted, **Then** totals
   and rates are withheld and the sample size is shown.
3. **Given** approval latency fell and the override rate fell against the previous release,
   **When** the report is drafted, **Then** it flags suspected automation bias (SPEC-COMP-010 §3).

### User Story 3 — Scores cannot steer the agents or the gates (Priority: P3)

A Security Lead auditing a delivery can show two things. No Judge or Advisor input carried a score.
No score changed autonomy, review depth, a gate or the Judge's mode.

**Why this priority**: an agent that is scored by evidence but can see its score can learn to game
it (Goodhart). The ledger must measure, not steer.

**Independent Test**: inspect the recorded Judge input envelopes and Advisor inputs for a run, and
the gate records. No ledger content appears in any input, and no gate or routing record cites a
score.

**Acceptance Scenarios**:

1. **Given** the ledger has entries, **When** the Judge or the Advisor is invoked, **Then** its input
   contains no ledger entry, score or total.
2. **Given** any score, **When** routing, autonomy or review depth is decided, **Then** the score is
   not an input.

### Edge Cases

- **Evidence arrives after the entry closed.** A defect is traced to a gate after the release
  retrospective. The entry is reopened with the evidence appended, and the next retrospective shows
  the correction. Nothing is overwritten.
- **Evidence never arrives.** An entry closes at its release retrospective. A shipped `pass` with no contrary evidence by
  then scores +1, and followed advice scores 0. A `fail` scores by FR-04 only: +1 if its
  evidence reproduces, −1 for a false block, otherwise 0. A human accepting the `fail` is not
  evidence.
- **The human overrides a `fail`, and a defect, revert or CI failure follows.** This is not a false
  block. The `fail` scores +1 if its evidence reproduces and 0 otherwise. The override is recorded
  with its rationale (SPEC-SDLC-002 FR-20). No one is scored for disagreeing.
- **The Judge's verdict is missing** (error or timeout, SPEC-SDLC-002 FR-10). No entry is scored.
  The missing verdict is counted in the error signal (§8).
- **Two defects are traced to the same gate.** The gate's entry is scored once, as a false `pass`.
  The second defect is appended as evidence.
- **Unadvised path fails.** The Advisor's advice was not followed, and the path taken failed in a
  way the advice would have avoided. Whether the advice would have avoided it is a human judgement
  recorded at the retrospective. The agent never decides it.

## 3. Non-Goals / Out of Scope

- **Any path from a score to autonomy, review depth, gate routing or the Judge's mode.** This is
  measurement only, and FR-10 states it as a SHALL NOT.
- **Demoting the Judge or resetting its burn-in** on a false `pass`. That would amend ADR-0070,
  which resets burn-in only on false positives. It is a later decision that would use this ledger's
  data.
- **The decision-delegation flow** (Judge and Advisor on every non-mechanical decision, SPEC-SDLC-004).
  It is deferred, as recorded in §Clarifications.
- **Removing or converting any human gate** (Constitution V).
- **Scoring humans.** The ledger scores agents. A human override is recorded as data, and no human
  gets a score.
- **The interim session ledger** kept by an agent session while SPEC-SDLC-004 is deferred. That is
  a working convention, not this feature.

## 4. Functional Requirements _(mandatory)_

| ID    | Requirement (EARS: WHEN … the system SHALL …)                                                                                                                                                                                                                                                                                                   | Story | Priority |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------- |
| FR-01 | WHEN a human decides a gate that carried a Judge verdict, or a caller acts after Advisor advice, whether or not it follows the advice, the system SHALL record one calibration entry. The entry pairs the agent output with the human decision or the caller's action, and holds the human's rationale when one was given. | US1 | must |
| FR-02 | WHEN later evidence about a decision is recorded (a CI failure, a revert, or a defect traced to it), the system SHALL append it to that decision's entry and SHALL NOT overwrite earlier evidence.                                                                                                                                              | US1   | must     |
| FR-03 | Tracing a defect, a revert or a CI failure to a decision, and re-checking whether a `fail` verdict's cited evidence reproduces, SHALL be recorded at the retrospective and confirmed by a human. The re-check MAY be run by an agent other than the Judge that gave the verdict and the producer whose work it judged. An agent's proposal SHALL NOT be recorded as evidence until a human confirms it. | US1 | must |
| FR-04 | WHEN a Judge entry is scored and FR-06 does not apply, the system SHALL apply the first of these rules that matches. Every case they do not list scores 0. **`pass` that shipped:** −3 if a defect, revert or CI failure is traced to the gate by the entry's close (a false `pass`); otherwise +1. **`pass` the human rejected:** −3 if the rejection names a defect whose evidence reproduces; otherwise 0, because nothing shipped to bear it out. **`fail`:** +1 if the evidence the verdict cites reproduces (FR-03), whatever the human decided; −1 if the `fail` was overridden with a rationale, its evidence did not reproduce, and no defect, revert or CI failure is traced to the gate by the close (a false block); otherwise 0. The human decision enters only negative cases. Agreement with the human SHALL NOT yield a positive score. | US1 | must |
| FR-05 | WHEN an Advisor entry is scored and FR-06 does not apply, the system SHALL apply the first of these rules that matches. Every other case scores 0, including advice that was followed and borne out, because the alternative is unknown, and advice not followed where the path taken succeeded. **−2:** the advice was followed and a defect, revert or CI failure is traced to it by the close. **+1:** it was not followed and a human records that the path taken failed in a way the advice would have avoided. Being followed SHALL NOT earn a point. | US1 | must |
| FR-06 | WHEN an entry's agent output is `escalate`, or carries "uncertain — verify", the system SHALL score it 0, whatever later evidence shows. This rule takes precedence over FR-04 and FR-05. | US1 | must |
| FR-07 | The system SHALL NOT give any score for agreement, whether between the agent and the human or between the Judge and the Advisor.                                                                                                                                                                                                                | US1   | must     |
| FR-08 | WHEN the Phase 14 release retrospective is drafted, the system SHALL report per release. The metrics are reported, never scored. **Per Judge gate:** the agreement rate, which is the share of closed entries where the human decision matched the verdict; the false-pass rate, which is the share of `pass` entries scored −3 (a human rejection alone does not count, unlike the proposal's P6, which is outside the corpus, because that would measure agreement); the override-with-rationale rate, which is the share of human decisions that differ from the verdict and carry a rationale; and the approval latency from gate open to human decision, P50 and P95. **Per Advisor trigger:** the share of advice followed, the share of followed advice scored −2, and the count scored +1. | US2 | must |
| FR-09 | WHEN fewer than 10 entries for a gate or trigger are closed in the reporting period, the system SHALL withhold its totals, rates and automation-bias flag, and SHALL show the sample size instead. | US2 | must |
| FR-10 | No score, total or rate SHALL be an automated input to autonomy, review depth, gate routing, a `required_approvals` entry or the Judge's report or blocking mode. A human MAY read the report when deciding a promotion under ADR-0070. That decision stays the human's. | US3 | must |
| FR-11 | The Judge's input envelope and the Advisor's input SHALL NOT contain any ledger entry, score, total or rate.                                                                                                                                                                                                                                    | US3   | must     |
| FR-12 | WHEN approval latency falls and the override rate (1 − agreement rate, FR-08) falls for the same Judge gate between two consecutive releases, the report SHALL flag suspected automation bias (SPEC-COMP-010 §3). | US2 | must |
| FR-13 | WHEN evidence arrives for an entry that has already closed, the system SHALL reopen it, append the evidence, rescore it, and show the correction in the next retrospective.                                                                                                                                                                     | US1   | should   |

### Key Entities

- **Calibration entry**: one per Judge verdict or Advisor advice record.
  - **References**: the verdict or advice it scores, by run, phase, spec id and issue.
  - **Agent output**: the verdict (`pass` · `fail` · `escalate`) or the recommendation, including
    whether "uncertain — verify" was stated.
  - **Human side**: the human decision or the caller's action, with the rationale when given.
  - **Evidence**: append-only. Each item has a kind (CI failure · revert · traced defect ·
    reproduction re-check), a reference, who confirmed it and when.
  - **Score**: per FR-04 to FR-06.
  - **State**: open · closed · reopened.
- **Calibration report**: one per release retrospective.
  - The FR-08 metrics per Judge gate and per Advisor trigger, the sample size, the automation-bias flag (FR-12), and the
    corrections from reopened entries (FR-13).

## 5. Non-Functional Requirements

| ID     | Requirement                                                                                                           | Category (taxonomy) | Evidence / gate   |
| ------ | --------------------------------------------------------------------------------------------------------------------- | ------------------- | ----------------- |
| NFR-01 | Entries and reports carry no PII and no secret. They cite paths, run ids, PR and issue numbers, not data values. | Privacy | AC-12 |
| NFR-02 | The ledger is append-only. Evidence is added, never edited or removed, and a rescore keeps the earlier score visible. | Compliance | AC-02, AC-11 |
| NFR-03 | The ledger outlives a single run, so a release retrospective can read every entry for the release. | Reliability | AC-13 |
| NFR-04 | Each ledger task declares at most two skills (ADR-0060).                                                              | Maintainability     | review at Phase 7 |
| NFR-05 | Agents propose and humans decide. No score changes a gate, an approval or an autonomy flag.                           | Human-oversight     | AC-08             |

## 6. Success Criteria _(mandatory, measurable, technology-agnostic)_

| ID    | Measurable outcome                                                                              | Measurement                                                               |
| ----- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| SC-01 | Every Judge verdict and every Advisor advice record in a release has a calibration entry.       | entries vs verdict and advice records, per release: 100%                  |
| SC-02 | Every closed entry has a score that the FR-04 to FR-06 rules reproduce from its recorded evidence and human inputs. | recompute the scores at the retrospective: 0 mismatches |
| SC-03 | No Judge or Advisor input in a release contains ledger content.                                 | inspection of the recorded envelopes, sampled per release: 0 found        |
| SC-04 | No gate, approval, routing or mode record cites a score.                                        | audit of the gate and approval records per release: 0 found               |

## 7. Governance, Privacy & Security _(gate: threat & privacy review)_

| Concern                                  | Control in this spec                                                                                                                                                                    | Maps to                                                    |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Human oversight (HITL/HOTL)              | Measurement only. No score reaches a gate, an approval, routing, autonomy or the Judge's mode (FR-10). Traces are confirmed by a human (FR-03). No gate is added, removed or converted. | ADR-0011, Constitution V                                   |
| PII (classify L1–L4; mask at boundaries) | No new personal data. Entries cite references, not values (NFR-01). Human decisions are recorded by role, not by person.                                                                | ADR-0012, specs/privacy/                                   |
| DPIA / RIPD required?                    | no. No new processing of personal data.                                                                                                                                                 | docs/privacy/dpia/                                         |
| Auditability (immutable trail)           | Entries are append-only, and rescoring keeps the earlier score (NFR-02, FR-13).                                                                                                         | ADR-0026, Constitution VII                                 |
| Authn / abuse (auth, rate limit)         | Abuse here is an agent gaming its score. Two controls apply: agents never see the ledger in their input (FR-11), and only a human confirms an evidence trace (FR-03).                   | specs/security/threat-model-SPEC-SDLC-002-judge-advisor.md |
| OWASP controls touched                   | LLM09 (overreliance): the automation-bias flag (FR-12) makes overreliance visible. No new runtime control.                                                                              | specs/security/owasp-genai-control-matrix.yaml             |

## 8. Golden Signals & SLO _(gate: observability)_

The ledger serves dev-time agents. Its signals are read per release retrospective, not from a
production dashboard.

| Signal     | Derivation                                                                                             | Exposed as                  |
| ---------- | ------------------------------------------------------------------------------------------------------ | --------------------------- |
| Traffic    | Entries opened per release, per gate and per agent                                                     | counts in the retrospective |
| Latency    | Time from the human decision to the entry's close                                                      | P50 / P95 / P99 per release |
| Errors     | Missing verdicts (SPEC-SDLC-002 FR-10), and entries that cannot be scored for lack of a human decision | error_rate per release      |
| Saturation | Share of entries still open at the retrospective                                                       | share per release           |

### Reconciliations _(only under the `batch-data` profile — ADR-0103)_

N/A. This feature runs no batch pipeline.

## 9. Acceptance Criteria _(gate: canonical, machine-traceable)_

The test paths below are planned for Phase 6 and do not exist yet.

| ID    | Given / When / Then (one line)                                                                                                                                                  | Covers FR(s) | Verified by (test path or `requirement` marker)                            |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------------------------- |
| AC-01 | Given a verdict and a human gate decision, when the decision is recorded, then one entry pairs them with the rationale when given.                                              | FR-01        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-01")` |
| AC-02 | Given an entry with evidence, when more evidence is added, then both items are present and none was edited.                                                                     | FR-02        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-02")` |
| AC-03 | Given an agent-proposed trace, when it is not confirmed by a human, then it is not scored as evidence.                                                                          | FR-03        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-03")` |
| AC-04 | Given Judge entries for each FR-04 case, when scored, then each scores as listed. A shipped `pass` scores +1 when borne out and −3 when false. A rejected `pass` scores 0, or −3 when its named defect reproduces. A `fail` whose evidence reproduces scores +1, accepted or overridden. A false block scores −1. A `fail` accepted without reproduction scores 0, as does an overridden `fail` that did not reproduce but that a defect followed. Changing an accepted `fail` to an override never raises a score. | FR-04, FR-07 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-04")` |
| AC-05 | Given Advisor entries for each FR-05 case, when scored, then they score 0 for followed and borne out, −2 for followed and failed, +1 for not followed and vindicated, and 0 for not followed where the path succeeded. | FR-05 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-05")` |
| AC-06 | Given an `escalate` entry, or a `pass` or `fail` flagged "uncertain — verify", with contrary evidence, when scored, then it scores 0. | FR-06 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-06")` |
| AC-07 | Given 9 and then 10 closed entries for a gate, when the report is built, then totals, rates and the automation-bias flag are withheld at 9 and shown at 10, with the four FR-08 metrics computed as defined. | FR-08, FR-09 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-09")` |
| AC-08 | Given the orchestrator, gate, flag and agent definition files, when they are scanned, then none reads or references the ledger or a score. | FR-10 | `tests/scripts/test_calibration.py` (static scan) — `requirement("SPEC-SDLC-003/FR-10")` |
| AC-09 | Given a ledger with entries, when a Judge envelope or an Advisor input is built, then it holds no ledger content.                                                               | FR-11        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-11")` |
| AC-10 | Given two releases where latency and the override rate both fell for a gate, when the report is built, then the automation-bias flag is set. | FR-12        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-12")` |
| AC-11 | Given a closed entry, when evidence arrives, then it is reopened and rescored, the earlier score stays visible, and the correction is listed.                                   | FR-13        | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/FR-13")` |
| AC-12 | Given any entry and report, when inspected, then they hold references only: no data value, PII or secret. | NFR-01 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/NFR-01")` |
| AC-13 | Given entries written in one run, when a later run builds the release retrospective, then every entry for the release is read. | NFR-03 | `tests/scripts/test_calibration.py` — `requirement("SPEC-SDLC-003/NFR-03")` |

## 10. Requirement Coverage _(gate)_

| FR    | AC    |
| ----- | ----- |
| FR-01 | AC-01 |
| FR-02 | AC-02 |
| FR-03 | AC-03 |
| FR-04 | AC-04 |
| FR-05 | AC-05 |
| FR-06 | AC-06 |
| FR-07 | AC-04 |
| FR-08 | AC-07 |
| FR-09 | AC-07 |
| FR-10 | AC-08 |
| FR-11 | AC-09 |
| FR-12 | AC-10 |
| FR-13 | AC-11 |

**Coverage footer.** _13_ FRs total · _13_ mapped to ≥ 1 AC · **_0_ unmapped**

## 11. Risks & Limitations

- **Depends on SPEC-SDLC-002 being implemented.** Until the Judge and the Advisor produce records,
  there is nothing to score. This spec can be planned now, but its Phase 6 follows SPEC-SDLC-002's.
- **Human tracing is the bottleneck.** Scores are only as good as the traces humans confirm (FR-03).
  A retrospective that skips tracing leaves false passes unscored, so the Judge looks better than
  it is. The saturation signal (§8) shows how much was left open.
- **The ledger is readable in the repository.** FR-11 keeps it out of agent inputs, but an agent
  with read tools could still open it. The SPEC-SDLC-002 threat model recommends declaring the
  Judge without write tools. Whether its read access should exclude the ledger path is for the plan
  (`uncertain — verify` that the agent tooling can exclude a path).
- **Small samples.** At one Phase 7 gate per change, n ≥ 10 may take more than one release for a
  low-volume adopter. FR-09 withholds the numbers rather than show noise.
- **Weights are a judgement.** The −3 / −1 asymmetry makes a false `pass` costlier than a false
  block. That is a policy choice by the Tech Lead, not a derived value. Revisit it after the first
  report.

## 12. Open Questions

None. The scope and scoring decisions were taken on 2026-11-16 (§Clarifications, issue #206).

## 13. Assumptions

| #   | Assumption                                                                                                                                                                                                 | Owner     | Resolve by (phase) | Status (open / confirmed / rejected) |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------ | ------------------------------------ |
| A1  | An entry closes at the release retrospective that covers its change. "Borne out" means no contrary evidence by then. Later evidence reopens it (FR-13).                                                    | Tech Lead | 4 — Specification  | open                                 |
| A2  | The ledger is committed to the repository and append-only, because it must outlive a run (NFR-03). That differs from the gitignored per-run records of ADR-0104 §4, which this ledger references. Its path and format, and whether this needs an ADR (`new_adrs_required`), are decided at Phase 5. | Tech Lead | 5 — Architecture | open |
| A3  | A "defect traced to a gate" is the retrospective's own finding (`docs/process/RETROSPECTIVE-GUIDE.md`, release template, Incidents & Near-Misses). No new defect taxonomy is introduced.                   | Tech Lead | 5 — Architecture   | open                                 |
| A4  | The four metrics are added to the release retrospective template, and drafted by the Phase 14 agent (`.claude/agents/asdd-phase-14-post-deploy.md` step 3). Humans still review them at the terminal gate. | Tech Lead | 5 — Architecture   | open                                 |
| A5  | The scoring values in FR-04 and FR-05, and the n ≥ 10 floor, are the Tech Lead's decision of 2026-11-16 (issue #206). The `fail` rule was refined on 2026-11-17 (§Clarifications).                                                                                      | Tech Lead | 4 — Specification  | confirmed                            |

## 14. References

- `specs/features/SPEC-SDLC-002-judge-advisor-roles/spec.md`: the Judge verdict and the advice record
  scored here, FR-10 (missing verdict) and FR-20 (override rationale)
- `docs/adr/ADR-0104-judge-advisor-roles-and-judge-independence.md`: the roles and the Judge
  envelope (§2) that FR-11 extends
- `docs/adr/ADR-0070-governance-gate-enforcement-lifecycle.md`: the promotion whose human decision this ledger informs;
  its reset rule is unchanged
- `specs/compliance/ai-post-market-monitoring.md` (SPEC-COMP-010) §2 and §3: the leading indicators
  and the automation-bias threshold
- `specs/security/threat-model-SPEC-SDLC-002-judge-advisor.md`: entries 1, 8 and 14
- Issue #206 (the decisions), and the author's working note `PROPOSAL-judge-advisor-graduated-oversight`
  §P6 and §6 (under `temp/`, not part of the corpus)
