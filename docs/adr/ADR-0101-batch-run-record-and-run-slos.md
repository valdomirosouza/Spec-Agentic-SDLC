<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0101 — A Batch Run Record and Run SLOs

**Status:** Proposed
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — observability and operations for the `batch-data` adoption profile
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0098](ADR-0098-adoption-profiles-and-declared-not-applicable.md) (adoption profiles), [ADR-0004](ADR-0004-observability-stack.md) (observability stack), [ADR-0068](ADR-0068-golden-signal-extraction-rules.md) (signal window semantics), [ADR-0013](ADR-0013-data-retention-policy.md) (retention)

---

## Context

ADR-0098 added the `batch-data` adoption profile for repositories that run scheduled or manual jobs
over data and expose no long-running endpoint. That profile switches off what a batch pipeline
does not have, such as the canary of `deploys_prod`. ADR-0098 §1 leaves open what a batch run owes
in its place, and gives it to separate ADRs. This ADR covers the first part: the record of a run
and the objectives a run is held to.

The corpus measures a service. Its Golden Signals, its SLOs (`docs/sre/slo/slo.yaml`) and its
error budgets count requests over a time window, and the observability stack of ADR-0004 assumes
a process that is up and exporting. A batch pipeline has neither. The 2026-11-06 audit of an
Order-to-Cash pipeline that adopted the corpus found:

- **no notion of a run.** Nothing tied a run to the code that ran. A rerun overwrote the evidence
  of the run before it.
- **no record of a failed run.** The adopter's history was written at the end of a successful run,
  so a run that stopped half-way left no trace.
- **no objective that a reviewer could hold a run to.** "Did this month's close finish, on time,
  with the rows it should have?" had no SLI, so it had no alert.

The adopter built its own run log to fill these gaps. Every batch adopter will need one, and
building it from scratch each time is what a corpus exists to prevent.

## Decision

Under the `batch-data` profile, a **run** is the unit that is recorded, measured and held to
objectives. A `service` adopter that also has batch jobs may opt in with the same contract.

1. **Every run has an ID and a commit.** A run gets an ID at its start:
   `<pipeline>-<UTC start, YYYYMMDDTHHMMSSZ>`. The ID is written in every log line, file name and
   evidence record of that run. The commit the run executes (`git rev-parse HEAD`) and whether the
   working tree was clean are recorded **before the first step**. A production run from a dirty
   tree is refused. A non-production run from a dirty tree is allowed, and the record marks it
   `dirty: true`.
2. **The run record is written even on failure.** The run is wrapped so that its record is
   appended whatever the outcome: a shell `trap … EXIT`, or `try/finally` in Python. The record is
   one line in an append-only run history, and it holds:
   - the run ID, the pipeline, the commit and `dirty`;
   - the operator, the start and end times;
   - `status`: `succeeded`, `failed` or `aborted`;
   - per step: name, status, duration, rows in, rows out and rows rejected.

   The record holds counts and identifiers, never data values, so it carries no personal data.
   A rerun is a new run with a new ID. It never rewrites an earlier record.

3. **Batch Golden Signals.** The four signals keep their names and are measured per run:

   | Signal     | For a run                                                                              |
   | ---------- | -------------------------------------------------------------------------------------- |
   | Traffic    | rows read and rows written, per step and in total                                      |
   | Errors     | failed steps, and rows rejected as a share of rows read                                |
   | Saturation | run duration as a share of the window the run is allowed (for example, a close window) |
   | Latency    | run duration, and **freshness**: from the end of the data period to data available     |

4. **Run SLOs.** A pipeline declares its objectives beside the services' objectives, in
   `docs/sre/slo/slo.yaml`, under a `pipelines:` key. There are three SLI types:
   - `run_success`: the share of scheduled runs that end `succeeded`;
   - `freshness`: data available by its deadline (for example, close day + 2 business days);
   - `duration`: the run finishes within its allowed window.

   The error budget is counted in **runs**, not minutes. A monthly pipeline has twelve runs a
   year, so its budget is stated as "at most N late or failed runs per year", and a breach is
   reviewed per run rather than by a burn rate.

5. **Nothing here changes the control floor.** The profile changes what is measured. It does not
   change which phases of ADR-0064 are control phases, and it does not allow any check that
   ADR-0098 refuses to be declared `n/a`.

Implementation, once accepted, is a separate change:

- a JSON schema for the run record and a stdlib run-wrapper template, for both shell and Python;
- the `pipelines:` schema in `slo.yaml`;
- a batch section in `skills/sre/golden-signals.md`;
- what Phase 11 (Observability & Operational Readiness) checks under `batch-data`, in
  `phase-gates.yaml`: the run record and the run SLOs in place of probes and dashboards.

## Consequences

### Positive

- A failed run leaves the same trace as a successful one, so "what ran, from which commit, and
  where did it stop" has an answer.
- Run evidence, reconciliation and audit packages (the next two ADRs) can key on one run ID and
  one commit.
- A batch pipeline gets objectives that can alert, in the same file and vocabulary as a service.

### Negative / Trade-offs

- A wrapper around every run is one more thing to maintain, and a step that bypasses it leaves no
  record. The wrapper template keeps it to a few lines.
- Refusing a production run from a dirty tree stops an urgent manual fix until it is committed.
  That is the intent: the run must be reproducible from its commit.
- Budgets counted in runs are coarse. A monthly pipeline has very few data points, so a single
  failure is a large share of the budget.

## Alternatives Considered

- **Do nothing.** Each batch adopter builds its own run log, as the audited one did, with
  incompatible formats and no shared SLI.
- **Treat a run as a service and export metrics through ADR-0004's stack.** Rejected as the
  requirement: a monthly job is not up to be scraped, and a push gateway is optional
  infrastructure many data teams do not run. An adopter that has the stack may still export the
  same four signals to it.
- **Time-window SLOs (minutes of budget) for batch.** Rejected: a monthly run is either late or
  not, and a minute budget over 30 days is meaningless for it.
- **Record only successful runs.** Rejected: the failure is the case the record exists for.

## Compliance & Risk

Constitution VI (observability is part of done) and VII (traceability: run → commit). No autonomy,
control-matrix or data-classification change. The run record holds counts and identifiers only.
If a pipeline ever needs a data value in it, the value goes through the pipeline's PII
classification first (ADR-0064 §3), and the record keeps its retention under ADR-0013.
