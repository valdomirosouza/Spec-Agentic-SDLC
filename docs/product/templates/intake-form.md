# Intake — FEAT-{id}

> **Owner:** Product Lead | **Phase:** 0 (Intake & Prioritization) | **Status:** Draft | Decided
> Copy to `docs/product/FEAT-{id}/intake-form.md`. When agent-generated, prepend the
> Agent-Disclosure Header (see `docs/product/README.md`).
>
> Intake answers one question: **is this request worth a GitHub Issue?** It is a decision, not a
> design. Solutions here stay at concept level; architecture, tasks and code belong to Phases 4–6.
> Adapted from the `assess` process of github/spec-kit (intake → research → define → shape →
> decide), compressed into the single Phase 0 artefact this lifecycle already has.

---

## 1. Problem statement

{Who is affected, what fails or is missing for them today, and how we know. One paragraph.}

## 2. Value hypothesis

{The expected value and how it will be measured. Phase 2 expands it with
`templates/value-hypothesis.md`.}

## 3. Evidence

The research has to **challenge** the request as well as support it. A claim with no source is an
assumption, not evidence (Constitution IX).

| #   | Claim | For / Against | Source (link, ticket, metric, interview) | Confidence (high / medium / low) |
| --- | ----- | ------------- | ---------------------------------------- | -------------------------------- |
| E1  | {…}   | For           | {…}                                      | {…}                              |
| E2  | {…}   | Against       | {…}                                      | {…}                              |

## 4. Cost of doing nothing

{What happens if this is never built: who keeps paying, how much, and how often. "Nothing much"
is a valid answer and argues for `kill`.}

## 5. Concept options

| Option      | Appetite (S / M / L) | Trade-off |
| ----------- | -------------------- | --------- |
| Do nothing  | —                    | {…}       |
| {concept A} | {…}                  | {…}       |

## 6. Risk class and owner

- **Risk class:** {one of the `risk_classes` labels in `docs/process/gates/phase-gates.yaml`}
- **Proposed owner:** {…}
- **Related specs / ADRs:** {…}

## 7. Recommended verdict (agent)

**Verdict:** `go` | `needs-clarification` | `kill`

| Verdict               | Meaning                                                     | Next step                                        |
| --------------------- | ----------------------------------------------------------- | ------------------------------------------------ |
| `go`                  | Problem and evidence are adequate; a concept is recommended | Phase 1 opens the Issue                          |
| `needs-clarification` | Named unknowns block a defensible decision                  | Answer them in this file; do not regenerate it   |
| `kill`                | Not worth pursuing now                                      | Keep this file as the record; stopping succeeded |

**Rationale:** {two or three sentences that cite the evidence rows above}

**Blocking unknowns** (only for `needs-clarification`): `[NEEDS CLARIFICATION: …]`

## 8. Handoff summary (only for `go`)

{Five lines at most. Phase 1 and `/sdd-specify` take this as their input: problem, persona,
recommended concept, success signal, risk class.}

## 9. Decision (human)

| Decided by | Date | Decision                        | Note |
| ---------- | ---- | ------------------------------- | ---- |
| {…}        | {…}  | go / needs-clarification / kill | {…}  |

The agent recommends; the Product Lead decides (`docs/process/WORKFLOW.md` Phase 0, step 3). A
`kill` is recorded here and in the backlog, not deleted: the reasoning stays useful when the same
request comes back.
