<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data governance charter

> **Status:** Active · **Version:** 1.0 · **Approved:** 2026-09-13
> **Owner:** Tech Lead · **Co-owner:** DPO
> **Related:** `docs/data/data-catalog.md` (#31) · `docs/data/business-glossary.md` (#31) ·
> [`../../specs/data/data-quality.md`](../../specs/data/data-quality.md) · [`../../specs/data/data-contracts.md`](../../specs/data/data-contracts.md) ·
> [`../../memory/constitution.md`](../../memory/constitution.md) Art. III and VII

## 1. Why this charter exists

Before it, the phrase "data governance" appeared twice in this entire corpus, both times as a
citation of Article 10 of the EU AI Act. The corpus protected **personal data** thoroughly — L1–L4
classification, a PII inventory, DPIAs with a release gate, retention with legal hold, encryption,
data-subject rights — and governed **data as an asset** not at all. There was exactly one data
role, the DPO, whose mandate is privacy. Everything that is not personal data had no named owner,
no quality expectation and no contract.

That asymmetry is a real risk for an agentic system: an agent reasons over whatever data it is
given, and undocumented, unowned, unmeasured data produces confidently wrong decisions that no
privacy control catches.

## 2. Scope

**In scope.** Every dataset the system produces, consumes, stores or exposes: operational stores,
event topics, the audit trail, agent memory, the retrieval corpus, telemetry, and any dataset used
to evaluate or tune a model.

**Out of scope.** The internal data of third-party services (governed by their provider and by the
contract), and personal data processing *purposes*, which remain the DPO's mandate under the
privacy specs rather than this charter's.

**Relationship to privacy.** Privacy governs *whether and why* personal data may be processed.
This charter governs *whether any data is fit to be used at all*. Where they meet — a personal
field with a quality rule — the privacy rule is the stricter one and wins.

## 3. Principles

1. **Every dataset has one accountable owner.** Not a team, a person in a role. No owner means the
   dataset is not fit for use and must not feed a decision or a model.
2. **Data is governed where it is produced.** The domain that creates a dataset owns its meaning,
   its quality and its contract. Central governance sets the rules and arbitrates; it does not own
   other people's data.
3. **A consumer-visible dataset is a product with a contract.** Its schema, semantics, quality
   expectations and deprecation path are promised, versioned and breakable only by process
   ([`../../specs/data/data-contracts.md`](../../specs/data/data-contracts.md)).
4. **Quality is declared before it is measured, and measured before it is trusted.** An undeclared
   quality expectation is an assumption (Constitution IX).
5. **Classification travels with the data.** A field's L1–L4 class, and the obligations that follow,
   apply wherever the field goes — including into a prompt, an embedding or an agent's memory.
6. **No dataset feeds a model without provenance.** Origin, licence, lawful basis and exclusion
   criteria are recorded in a datasheet before first use (EU AI Act Art. 10).
7. **Decisions are recorded where they bind.** A governance decision that is not in a spec, an ADR
   or the catalog did not happen.

## 4. Roles

| Role                        | Who                                    | Accountable for                                                                                                     | Not accountable for                        |
| --------------------------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **Data owner**              | The lead of the domain that produces it | The dataset's existence, purpose, classification, contract, quality targets and lifecycle. Signs off on breaking changes. | Running the infrastructure                   |
| **Data steward**            | An engineer in that domain, named       | Day-to-day accuracy: the catalog entry, the glossary terms, quality rules, incident triage for that dataset           | Approving changes to the contract            |
| **Data custodian**          | The platform or SRE owner of the store  | Storage, access control, encryption, backup, retention execution, availability                                       | The meaning or quality of the content        |
| **DPO**                     | As today                                | Lawful basis, DPIA/RIPD, data-subject rights, cross-border transfer, retention *policy* for personal data            | Non-personal data quality or contracts       |
| **Data governance council** | TL (chair), DPO, SEC, AIGOV, SRE, one steward per domain | Arbitration between domains, approving the charter and its amendments, accepting exceptions, quarterly review | Day-to-day dataset decisions |

**The split that matters.** Owner decides *what the data means and whether it is fit*. Steward
keeps that true day to day. Custodian keeps it safe and available. Conflating owner and custodian
is the most common failure: the team that runs the database is rarely the team that knows what the
field means.

**Naming.** Every dataset in `docs/data/data-catalog.md` (#31) names its owner, steward and
custodian by role. A dataset with an unnamed owner is a finding, not a gap to tolerate.

## 5. Council: cadence and decision rights

| Cadence      | Agenda                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| **Quarterly** | Catalog completeness, quality results, open contract deprecations, classification changes, exceptions granted and expiring, data incidents since last cycle |
| **On demand** | A breaking contract change two domains cannot resolve; a classification dispute; a request to use a dataset outside its declared purpose |

**Decision rights.**

- The **owner** decides within a dataset. The council does not overrule an owner on meaning.
- The **council** decides between datasets and between domains, and grants **time-boxed
  exceptions** with a recorded expiry. An exception with no expiry is refused.
- The **DPO has a veto** on anything touching personal data; the council cannot overrule it.
- The **Security Lead has a veto** on anything that weakens classification or access control.

## 6. How a dataset becomes governed

1. **Declare** it in `docs/data/data-catalog.md` (#31) with owner, steward, custodian, classification and purpose.
2. **Define** its terms in `docs/data/business-glossary.md` (#31) if it introduces business meaning.
3. **Contract** it if anyone outside the producing domain reads it.
4. **Measure** it: at least one quality rule per declared expectation ([`../../specs/data/data-quality.md`](../../specs/data/data-quality.md)).
5. **Trace** it: lineage from source to consumption, so impact analysis and data-subject requests
   can be answered.
6. **Datasheet** it if it will ever feed or evaluate a model.

Steps 1 and 2 are required before the dataset is used by anything. Steps 3 to 6 are required
before it crosses a domain boundary, feeds a decision, or feeds a model.

## 7. Exceptions

An exception is a written, time-boxed, council-approved deviation recording: what rule is not met,
why, the compensating control, the expiry date and the owner. Exceptions are listed in the council's
quarterly note. **An expired exception is a violation**, not a renewal by default.

## 8. How this is enforced

| Obligation                          | Enforcement today                                                          |
| ----------------------------------- | ---------------------------------------------------------------------------- |
| No real personal data in any file   | Constitution Art. III; `pii-scan` gate in `harness/code-check.yml` (blocking) |
| Masking before log, broker and LLM  | Constitution Art. III; `pii-validation` in `harness/staging-check.yml`       |
| DPIA current at release             | `dpia-ripd-current` in `harness/release-check.yml` (blocking)                |
| Schema compatibility                | Contract-drift gate                                                          |
| Owner, steward, custodian named     | **Review only** — no automated check yet                                     |
| Quality rules measured              | **Review only** — rules defined in `specs/data/data-quality.md`, run by the adopter |
| Datasheet before a model uses data  | **Review only** — Phase 10 checklist item                                    |

The last three rows are honest gaps, not oversights: they are review-enforced today and named as
such so no one mistakes this charter for a control that runs.

## 9. Amendment

This charter is amended by a PR approved by the Tech Lead and the DPO, with a version bump and a
row in the log below. An amendment that reduces an owner's accountability or removes a veto
requires full council approval.

| Version | Date       | Change                                                                |
| ------- | ---------- | ----------------------------------------------------------------------- |
| 1.0     | 2026-09-13 | Created. Roles, council, principles and enforcement recorded for the first time (#28) |

## Related

- `data-catalog.md` and `business-glossary.md` (#31) · [`data-model-catalog.md`](data-model-catalog.md)
- [`../governance/raci-matrix.md`](../governance/raci-matrix.md) §5 — Data governance
- [`../../specs/privacy/pii-inventory.md`](../../specs/privacy/pii-inventory.md) — the privacy side
- [`../../specs/compliance/eu-ai-act-control-matrix.yaml`](../../specs/compliance/eu-ai-act-control-matrix.yaml) — `ART-10`
