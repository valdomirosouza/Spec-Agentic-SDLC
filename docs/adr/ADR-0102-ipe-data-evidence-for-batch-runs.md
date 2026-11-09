<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0102 — IPE Data Evidence for Batch Runs

**Status:** Proposed
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — audit evidence for the `batch-data` adoption profile
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0101](ADR-0101-batch-run-record-and-run-slos.md) (run ID and commit), [ADR-0098](ADR-0098-adoption-profiles-and-declared-not-applicable.md) (adoption profiles), [ADR-0026](ADR-0026-sox-audit-log-immutability.md) (immutable audit log), [ADR-0013](ADR-0013-data-retention-policy.md) (retention)

---

## Context

When an auditor relies on a report a company produced from its own systems, the report is
**information produced by the entity** (IPE). The auditor then tests it for completeness and
accuracy. Which query produced it, from which data, with which parameters? Was it altered
afterwards? A monthly Order-to-Cash pipeline produces exactly such reports: receivables ageing,
revenue cut-off, the extracts a close relies on.

The corpus has evidence for **program changes** (`docs/audit/big-four-evidence-map.md` §1–§4).
For the **data** a run produced, it has nothing. The 2026-11-06 audit of an adopting O2C pipeline
found:

- **no manifest** tying an output file to the query and parameters that produced it;
- **no write-once copy**: "WORM" does not appear anywhere in the corpus, and the outputs sat in a
  directory anyone with access could overwrite;
- **no audit package**: answering a sample request meant reassembling the code, the run and the
  files by hand, from the working tree rather than from the commit that ran.

ADR-0026 makes the application's audit log immutable (an insert-only table, cold-storage exports
with a SHA-256 manifest). It covers events, not the files a pipeline produces. ADR-0101 gives each
run an ID and the commit it executes, which this ADR keys on.

## Decision

Under the `batch-data` profile, every output a run produces that may be relied on as IPE is
**described, copied write-once, chained and packageable**.

1. **A manifest per step.** A step that produces data writes a manifest beside its output. The
   manifest records:
   - the run ID and commit (ADR-0101) and the step name;
   - its inputs: the source system, the query or script path and its SHA-256 at that commit, the
     parameters (period, filters), and the extraction time;
   - its outputs: path, SHA-256, row count, and a hash of the column list.

   A manifest holds metadata only, never data values. It is what makes completeness and accuracy
   testable: the query text is recoverable from the commit, and the counts and hashes are fixed
   at the time of the run.

2. **Write-once copies.** At the end of each step, its outputs and manifest are copied to
   write-once storage: an object store with a retention lock in compliance mode, or an
   equivalent the adopter declares. The corpus names the property, not a vendor. A directory on
   a shared drive, or an ordinary git repository, is not write-once.
3. **A hash-chained ledger.** Each copy appends one line to the run's evidence ledger: the run
   ID, step, path, SHA-256 of the file, and the hash of the previous ledger line. Deleting,
   editing or reordering an entry breaks the chain from that point on, so a verifier that
   recomputes it finds the break. The ledger is itself copied write-once when the run ends,
   including a failed run (ADR-0101 §2).
4. **An audit package built from the commit.** For a sampled run, a package is assembled from:
   - the code and queries **at the run's commit** (`git archive <commit>`), never from the
     working tree;
   - the run record (ADR-0101) and the step manifests;
   - the ledger, with the result of verifying its chain;
   - the write-once copies, checked against their recorded hashes.

   The package is reproducible: building it twice for the same run gives the same content.

5. **Personal data in write-once copies.** A write-once copy cannot be erased, and erasure is a
   data-subject right (LGPD, GDPR). Until a separate decision sets how retention above the
   classification cap is approved (audit proposal 0106, pending the DPO), a write-once copy holds
   only non-personal data or a pseudonymised extract. When the file itself cannot be kept, the
   hash of the full file is kept in the manifest and ledger. Retention of the copies follows the
   regime in scope in `applicability-matrix.yml`, for example SOX's seven years (ADR-0026).
6. **The evidence map gains a section.** `docs/audit/big-four-evidence-map.md` gets a
   "Data processing evidence (IPE)" section. It maps the auditor's requests (the query behind a
   report, the completeness and accuracy of the data, no alteration since the run, the run was
   authorised) to the artefacts above.

Implementation, once accepted, is a separate change:

- the manifest and ledger schemas;
- a stdlib ledger verifier;
- an audit-package builder template;
- the evidence-map section;
- the Phase 11 and Phase 12 readings under `batch-data` in `phase-gates.yaml`.

## Consequences

### Positive

- A sample request for a run's output is answered from one package, built from the commit that
  ran, instead of by hand.
- Tampering with an output or its record is detectable, not just forbidden.
- The O2C pattern (extract, transform, report) becomes reviewable by an external auditor using
  the same evidence map as the rest of the corpus.

### Negative / Trade-offs

- Write-once storage is infrastructure the adopter must provide and pay for. The corpus cannot
  provision it.
- A pseudonymised copy is weaker evidence than the original file. The kept hash proves what the
  original was, but cannot reproduce it.
- Every data-producing step owes a manifest, so the first adoption means instrumenting each step.

## Alternatives Considered

- **Do nothing.** IPE evidence is reassembled by hand per audit, from a working tree that may no
  longer match what ran.
- **Keep outputs in git.** Rejected: history can be rewritten by anyone who can force-push, data
  files bloat the repository, and personal data in history is close to impossible to erase.
- **Extend ADR-0026's audit log to carry the files.** Rejected: the audit log records events.
  Files belong in object storage, with the log recording that they were written.
- **Hashes without write-once storage.** Rejected as the whole answer: a hash proves a change
  only if the reference copy itself could not be changed.

## Compliance & Risk

Constitution VII (traceability: output → manifest → commit) and III (privacy by design: no
personal data in write-once copies until retention above the cap has a decided route). There is no
autonomy change. Control matrices change only through the evidence-map section, at
implementation. The pipeline's data classification (ADR-0064 §3) still applies to every output, as
for any spec.
