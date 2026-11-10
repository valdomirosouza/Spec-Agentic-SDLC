<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0103 — Reconciliation Controls for Batch Runs

**Status:** Proposed
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — data controls for the `batch-data` adoption profile
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0101](ADR-0101-batch-run-record-and-run-slos.md) (run record), [ADR-0102](ADR-0102-ipe-data-evidence-for-batch-runs.md) (IPE evidence), [ADR-0098](ADR-0098-adoption-profiles-and-declared-not-applicable.md) (adoption profiles)

---

## Context

A reconciliation compares two sides of the same data and decides whether they agree. Examples:
the rows extracted against the rows loaded, or the total of the invoices in the ERP against the
total in the receivables report. For a pipeline whose outputs a close relies on, reconciliations
are the controls an auditor tests. They are how completeness and accuracy are shown, run after
run.

ADR-0098 §1 left reconciliation to a separate ADR. ADR-0101 records each run and ADR-0102
describes each output, but neither decides whether two sides agree. The 2026-11-06 audit of an
adopting Order-to-Cash pipeline found **no reconciliation controls with tolerances or an
exception path**. That means three things:

- **no declared tolerance.** When a check allows a difference, the allowance sits in code. A
  reviewer cannot see it, and it can change without anyone deciding to change it.
- **no shared verdict.** Each check reports in its own words, so "ok", "warning" and a log line
  cannot be counted or compared across runs.
- **no exception path.** A difference that is understood and accepted either stops the close or
  is waved through with no trace. Neither leaves evidence of who accepted what.

## Decision

Under the `batch-data` profile, every reconciliation is **declared, judged in one vocabulary, and
excepted only on the record, for one run at a time**.

1. **A reconciliation is declared.** The pipeline's spec declares each reconciliation it runs.
   Each declaration gives:
   - an ID that is unique within the pipeline;
   - the two sides, each one a step output or an external source with its query path;
   - the measure: a row count, the sum of a named column, or a count of keys present on one side
     only;
   - the tolerance;
   - an owner.

   The tolerance is **zero unless declared**. A non-zero tolerance is either absolute (in the
   measure's unit) or relative (a share of the source side), never both. It states its reason.
   Changing a tolerance is a change to the spec, reviewed like any other.

2. **One verdict vocabulary.** Each reconciliation ends a run with exactly one verdict:

   | Verdict            | Meaning                                                           |
   | ------------------ | ----------------------------------------------------------------- |
   | `match`            | the difference is zero                                            |
   | `within_tolerance` | the difference is not zero and is within the declared tolerance   |
   | `break`            | the difference is outside the declared tolerance                  |
   | `not_run`          | the measure could not be computed, for example a side was missing |

   The verdict, both measured values and the difference are written to the run record
   (ADR-0101 §2) and to the manifest of the step that ran the check (ADR-0102 §1). They are
   aggregates. The keys behind a `break` are never written to the record. When they are needed
   to investigate, they go into an output of the run under the pipeline's data classification.

3. **A `break` or `not_run` fails the run**, unless an exception covers it. The step that ran the
   check ends `failed`, so the run ends `failed` and its outputs are not relied on. `not_run`
   counts as a failure because a missing check proves nothing.
4. **An exception covers one reconciliation in one run.** It is recorded before the run's outputs
   are relied on, and it holds:
   - the run ID and the reconciliation ID;
   - the observed difference and the reason it is accepted;
   - the approver, who is not the run's operator.

   With an exception, the verdict stays `break` or `not_run`, and the record adds a reference to
   the exception. A verdict is never rewritten to `match`. An exception does not carry over to the
   next run. If the same reconciliation needs one again in the next scheduled run, the difference
   is no longer an exception: it needs either a fix or a reviewed change to the tolerance (§1).
   The exception is evidence. It is appended to the run's ledger and copied write-once with the
   run's outputs (ADR-0102 §2–§3).

5. **The IPE evidence-map section includes reconciliations.** The "Data processing evidence (IPE)"
   section of ADR-0102 §6 maps the auditor's completeness and accuracy requests to the declared
   reconciliations, their verdicts per run, and their exceptions.

Implementation, once accepted, is a separate change:

- the schema for a declaration, a verdict and an exception;
- a stdlib checker that computes the verdict from the declared tolerance;
- a reconciliation section in the spec template;
- the reconciliation rows of the evidence-map section;
- what the phase gates check under `batch-data` in `phase-gates.yaml`.

## Consequences

### Positive

- A tolerance is visible and reviewed, and changing it is a decision with an author.
- Verdicts can be counted across runs, so a run SLO (ADR-0101 §4) or a review can ask how often
  a reconciliation broke.
- An accepted difference leaves evidence of who accepted it and why, and it cannot quietly
  become the normal state.

### Negative / Trade-offs

- Every reconciliation already running in code has to be declared before adoption, and its
  implicit tolerance written down.
- The approver must be a second person. For a one-person team, every exception waits for
  someone else.
- An exception limited to one run is strict for a difference that will recur for a known reason
  until a fix ships. The ADR chooses that strictness: the way out is a reviewed tolerance, which
  is visible, instead of a series of exceptions, which is not.

## Alternatives Considered

- **Do nothing.** Each check keeps its own vocabulary and its tolerance stays in code, so neither
  can be reviewed.
- **Warnings instead of failures.** Rejected: a warning nobody must act on does not stop a close
  from relying on data that does not agree.
- **Standing exceptions with an expiry date**, like the `n/a` declarations of ADR-0098 §4.
  Rejected for data: an `n/a` says a check does not apply to the repository, but an exception
  accepts a specific difference in specific data. Each run's data is new, so each difference
  needs its own decision.
- **Rewriting the verdict to `match` once excepted.** Rejected: it erases the fact that the data
  disagreed, which is what an auditor asks about.

## Compliance & Risk

Constitution II (a reconciliation is a test the data must pass, every run), VII (traceability:
verdict → run → commit, exception → approver) and III (records hold aggregates; keys stay under
the pipeline's classification). For financial data in SOX scope, the second-person approver
gives segregation of duties for exceptions (`skills/compliance/sox.md` CC3). There is no autonomy
change. Control matrices change only through the evidence-map section, at implementation.
