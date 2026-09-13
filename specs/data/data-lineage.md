---
id: SPEC-DATA-003
kind: spec
status: approved
owner: Tech Lead
issue: 32
governing_adrs:
  - ADR-0012
  - ADR-0013
  - ADR-0043
  - ADR-0044
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/data/data-contracts.md
  - specs/privacy/pii-inventory.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data lineage and impact analysis

> **Owner:** Tech Lead · **Accountable per dataset:** the data steward
> **Satisfies:** ISO/IEC 42001 A.7 · EU AI Act `ART-10` and `ART-12` · GDPR/LGPD data-subject rights

## 1. The two questions

Lineage exists to answer exactly two questions, and every design decision below serves one of them:

1. **Forward — impact.** *If this field changes or breaks, what breaks with it?* Asked before a
   contract change, during a quality incident, and when deciding whether a dataset may feed a model.
2. **Backward — provenance.** *Where did this value come from, and what happened to it on the way?*
   Asked during a data-subject request, an incident investigation, and any time an agent's output
   has to be justified.

The corpus could answer neither. "Data lineage" had zero occurrences, and the 26 mentions of
provenance all refer to artefact supply-chain provenance under SLSA, not to data.

**The backward question is the one with a legal deadline attached.** A data-subject erasure request
requires knowing every place a personal field reached, including an embedding in an agent's memory
and a masked copy in a log. Without lineage, the answer is a best effort, and a best effort is not
a defensible answer to a regulator.

## 2. Granularity

Lineage is recorded at **dataset level always, and field level for L1 and L2 fields**.

| Level     | Recorded                                       | Why this line                                                                 |
| --------- | ---------------------------------------------- | ------------------------------------------------------------------------------- |
| Dataset   | Always                                         | Enough for impact analysis and blast radius                                     |
| Field     | For L1 and L2 personal fields                  | Required to answer erasure and access requests precisely                        |
| Value     | Never, as a rule                               | Value-level lineage duplicates the data it describes and becomes a second copy of personal data to protect |

Recording field lineage for every field is the common over-engineering trap: it is expensive to
maintain, decays fastest, and the questions that need it are almost always about personal data.

## 3. What is captured

For each edge from a source to a target:

| Element        | Meaning                                                                     |
| -------------- | ----------------------------------------------------------------------------- |
| `source`       | Dataset (and field, where field-level) as named in the catalog               |
| `target`       | Dataset (and field) produced                                                 |
| `transform`    | What happened: `copy` · `mask` · `aggregate` · `derive` · `embed` · `join` · `enrich` |
| `owner`        | The component or job that performs it                                        |
| `classification_effect` | Whether the transform lowers, preserves or raises the class          |
| `contract`     | The data contract that governs the target, if any                            |

**`classification_effect` is the field that earns its place.** A `mask` transform lowers L1 to L2;
an `embed` transform **preserves** classification, because an embedding of personal text is still
personal data — a point teams get wrong routinely and which the agent memory DPIA already had to
address. A `join` can *raise* classification when two non-identifying fields become identifying
together.

## 4. Capture points

Lineage is declared, not inferred. Three points, in order of reliability:

| Point                | How                                                                        | Reliability |
| -------------------- | ---------------------------------------------------------------------------- | ----------- |
| **Data contract**    | The `Lineage` section of every contract names upstream, transform and downstream | Highest — reviewed by a human at every change |
| **Pipeline declaration** | The job declares its inputs and outputs where it is configured           | High — changes with the code that changes the flow |
| **Trace attributes** | Agent and request spans carry the dataset ids they read and write (ADR-0044) | Runtime truth, incomplete by nature |

The first two are the record. The third is the **reconciliation**: a dataset that appears in traces
and not in the declared lineage is a finding, because something is reading data no one declared.

**Do not derive lineage from database introspection alone.** It captures structure and misses
meaning — it cannot tell a masked copy from an unmasked one, which is the distinction the whole
privacy chain rests on.

## 5. Forward: impact analysis

Before any of these, the impact question is answered from the lineage graph:

| Trigger                              | Question                                                                  |
| ------------------------------------ | --------------------------------------------------------------------------- |
| Breaking contract change             | Which consumers must migrate, and is any of them an agent?                 |
| Quality incident (`critical`)        | Which downstream datasets are contaminated, and did any decision use them? |
| Schema or semantic change            | Which dashboards, SLOs and model inputs shift meaning without erroring?    |
| Retiring a dataset                   | What silently loses an input?                                              |
| Proposing a dataset for model use    | What feeds it, and is every upstream source datasheeted?                   |

The last one is the EU AI Act `ART-10` question. A dataset is only as governed as its least
governed upstream source.

## 6. Backward: provenance and data-subject requests

For an access or erasure request, lineage produces the list of places a subject's data reached:

1. Start from the personal field in the source dataset.
2. Walk forward through every edge, following `classification_effect`.
3. Split the result into three lists:
   - **Erasable** — copies that can be deleted or re-derived;
   - **Masked or aggregated beyond identification** — retained, with the transform as justification;
   - **Retained under a legal obligation** — audit records, with the retention rule that requires it.
4. Record which list each destination fell into. That record, not the deletion itself, is what
   demonstrates compliance.

**The hard case is the model.** If a personal value reached training or fine-tuning, deletion of
the source does not remove it from the model. The training-data policy (#34) governs what happens
then; lineage's job is to make sure the case is *detected* rather than missed.

## 7. Maintenance and decay

Lineage rots faster than any other governance artefact, because it changes whenever code changes
and nothing fails when it is wrong.

| Control                          | Effect                                                                    |
| -------------------------------- | --------------------------------------------------------------------------- |
| Lineage lives in the contract    | It is reviewed whenever the contract is, by the person who knows            |
| Trace reconciliation             | An undeclared read shows up as a finding rather than staying invisible      |
| Quarterly council review         | Every dataset's lineage confirmed current, or marked stale with an owner    |
| Incident feedback                | Any incident where lineage was wrong adds the missing edge in the postmortem |

A dataset whose lineage is marked stale **may not be proposed for model use** until it is refreshed.

## 8. What is enforced today

| Obligation                                  | Enforcement                                        |
| ------------------------------------------- | ---------------------------------------------------- |
| PII redaction before telemetry leaves       | ADR-0043 collector redaction — running control      |
| Contract lineage section present            | **Review only** — at contract approval              |
| Trace reconciliation                        | **Adopter** — needs the running system              |
| Lineage current before model use            | **Review only** — Phase 10 checklist                |

## 9. Open items

| # | Item                                                        | Owner        | Resolve by            |
| - | ------------------------------------------------------------- | ------------ | --------------------- |
| 1 | Lineage recorded for the datasets in the catalog             | Data stewards | Next quarterly cycle |
| 2 | Trace attributes carrying dataset ids (ADR-0044 extension)   | SRE Lead     | With the adopter      |
| 3 | Field-level lineage for the L1/L2 fields in the PII inventory | Data stewards | Before the next DSAR  |

## Related

- [`data-contracts.md`](data-contracts.md) — where lineage is declared
- [`data-quality.md`](data-quality.md) — blast radius during an incident
- [`../privacy/pii-inventory.md`](../privacy/pii-inventory.md) — which fields need field-level lineage
- [`../../skills/privacy/data-subject-rights.md`](../../skills/privacy/data-subject-rights.md) — the request workflow this feeds
