---
id: SPEC-PRIV-010
kind: policy
status: approved
owner: DPO
issue: 34
governing_adrs:
  - ADR-0012
  - ADR-0013
  - ADR-0093
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/privacy/pii-inventory.md
  - specs/privacy/data-retention.md
  - specs/data/data-lineage.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Training and fine-tuning data governance

> **Owner:** DPO · **Co-owner:** AI Governance Lead
> **Satisfies:** EU AI Act `ART-10` · ISO/IEC 42001 A.7 · GDPR Arts. 5, 6, 17 and LGPD Arts. 7, 18
> **Prerequisite for every dataset named here:** an approved datasheet
> ([`../../templates/datasheet-template.md`](../../templates/datasheet-template.md))

## 1. Where this applies

Today the organisation **does not train or fine-tune models**. Its only control on the subject is
negative: the provider contract states that submitted data is not used for training. That control
protects against the provider training on our data. It says nothing about what happens the day the
organisation decides to train or tune a model itself, and by then the data has usually already been
collected under assumptions nobody wrote down.

This policy exists so that the decision to train is a **governed** decision rather than a technical
one, and so that data collected today does not quietly foreclose it or, worse, make it unlawful.

**Scope.** Any dataset used to train, fine-tune, distil, align or continuously update model weights,
and any dataset used to *evaluate* such a model where the evaluation set shapes the result.

**Out of scope.** Retrieval corpora and prompt context, which do not alter weights. They are
governed by the datasheet and the data contract, and by
[`../../docs/data/datasheets/agent-memory-documents.md`](../../docs/data/datasheets/agent-memory-documents.md)
for the existing corpus. The distinction matters because the irreversibility below does not apply
to retrieval: removing a document from an index removes its influence.

## 2. Principles

1. **Training is a purpose, not a side effect.** Data collected for operating a service is not
   thereby available for training. A new purpose needs its own basis and its own record.
2. **No dataset trains a model without an approved datasheet.** Draft is not approved.
3. **Irreversibility is assumed.** Once a value has influenced weights, deleting the source does not
   remove it. Every decision is made as if it cannot be undone, because in practice it cannot.
4. **Minimise before you train, not after.** Fields that are not needed for the task are removed
   before training, not masked in the output.
5. **Provenance beats volume.** A smaller dataset with clear origin, licence and basis is preferred
   to a larger one with gaps. A gap in provenance is a blocking defect, not a quality issue.

## 3. Lawful basis

| Basis                        | Usable for training?                       | Conditions                                                                          |
| ---------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| **Consent**                  | Yes                                        | Specific to training as a purpose, freely given, and **withdrawable** — see §5         |
| **Legitimate interest**      | Sometimes                                  | Requires a documented balancing test; fails where individuals would not reasonably expect it |
| **Contract performance**     | Rarely                                     | Only where training is genuinely necessary to perform the contract, which it seldom is |
| **Legal obligation / vital interests** | No                               | Neither supports training                                                             |
| **Special-category data**    | **Prohibited** by this policy              | Even where a GDPR Art. 9 condition might exist, this corpus does not permit it         |

**The balancing test is written before collection, not after.** A legitimate-interest assessment
produced to justify a decision already taken is not an assessment.

## 4. Data sources

| Source                              | Permitted            | Conditions                                                                      |
| ----------------------------------- | -------------------- | --------------------------------------------------------------------------------- |
| Organisation's own operational data | With a new basis     | Datasheet, minimisation, DPIA where personal data is involved                     |
| Synthetic data                      | Yes, preferred       | §6                                                                                |
| Purchased or licensed datasets      | Yes                  | Licence explicitly permits model training; supplier assessed; sub-processor registered |
| Publicly available data             | Case by case         | Public does not mean licensed or lawful. Terms of service and copyright apply     |
| Scraped data                        | **No**               | Not permitted without a licence and a basis, both recorded before collection      |
| User-submitted content              | Only with consent    | Specific consent for training, separate from the service's own terms              |
| Another model's output              | With disclosure      | Recorded in the datasheet; the upstream model's terms must permit it              |

**Data derived from production.** Operational data used for training is minimised, pseudonymised
where the task allows, and carries the same classification as its source. Production data that has
merely been copied to another environment has not been minimised.

## 5. Erasure, and what it can and cannot reach

This is the question the policy exists to answer, and the honest answer has three parts.

| Where the value is                          | On an erasure request                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------ |
| The **source dataset**                      | Deleted, and the deletion verified per `specs/privacy/data-retention.md`      |
| The **training snapshot** used for a run     | Deleted, or the record kept with the value removed and the change logged       |
| The **model weights**                        | **Not removable.** Deletion of the source does not unlearn the value           |

**What is therefore promised to a data subject:**

1. The source and every derived dataset are erased, and lineage
   ([`../data/data-lineage.md`](../data/data-lineage.md)) produces the list of where they were.
2. The value is **not used in any future training run**, which is enforced by re-deriving training
   sets from the live source rather than from archived snapshots.
3. Where the value has already influenced a deployed model, that fact is **recorded and disclosed**
   to the subject rather than glossed over, together with the conditions under which the model
   would be retrained.
4. Where the risk to the individual is material, the model is retrained or rolled back to a version
   that predates the data. That decision is the DPO's and is recorded.

Promising complete erasure from a trained model would be false. Saying so plainly, and describing
what actually happens, is the requirement (Constitution IX).

## 6. Synthetic data

Preferred wherever it works, with three conditions that stop it from becoming a loophole:

- **Generated from a governed source.** Synthetic data derived from personal data inherits the
  scrutiny of its source until the derivation is shown not to leak it.
- **Leakage tested, not assumed.** Memorisation and re-identification are tested before use; an
  untested generator is treated as carrying its source's classification.
- **Labelled as synthetic** in the datasheet and in any evaluation result that used it. A benchmark
  passed on synthetic data is a different claim from one passed on real data.

## 7. Evaluation data

Evaluation sets are governed as training data, with one addition: they are **held out and kept
separate**, and their contents are not fed back into training. A contaminated evaluation set makes
every downstream quality claim unfalsifiable, which is a governance failure and not only a
scientific one.

## 8. Decision path before any training run

1. Datasheet **approved** for every dataset in the run.
2. Lawful basis recorded per dataset; special-category data confirmed absent.
3. Minimisation applied and recorded.
4. DPIA completed or updated where personal data is involved.
5. Licences confirmed to permit training, including any upstream model's terms.
6. Evaluation set confirmed disjoint from training data.
7. Approval: **DPO and AI Governance Lead**, both required.
8. The run is recorded in the model registry
   (`docs/ai-governance/model-registry.md`, #42) with the exact dataset versions used.

A run that cannot complete step 1 does not start. There is no expedited path, because the
irreversibility in §2 makes an expedited path meaningless.

## 9. What is enforced today

| Obligation                                    | Enforcement                                                    |
| --------------------------------------------- | ---------------------------------------------------------------- |
| No real personal data in repository files     | Constitution Art. III; `pii-scan` gate — blocking               |
| Provider does not train on submitted data     | Contract term; recorded in `docs/dependency-manifest.yaml`      |
| Datasheet approved before model use           | **Review only** — Phase 10 checklist                            |
| Lawful basis recorded                         | **Review only** — DPO at the Discovery gate                     |
| Evaluation set disjoint                       | **Adopter** — test-side check                                   |

## 10. Open items

| # | Item                                                                     | Owner | Resolve by                      |
| - | -------------------------------------------------------------------------- | ----- | ------------------------------- |
| 1 | Legitimate-interest balancing test template                               | DPO   | Before any operational data is proposed for training |
| 2 | Leakage test procedure for synthetic data                                 | AI Governance Lead | Before synthetic data is used in a run |
| 3 | Position on retraining as a remedy for an erasure request                 | DPO   | Next quarterly review           |

## Related

- [`../../templates/datasheet-template.md`](../../templates/datasheet-template.md) — the prerequisite artefact
- [`../data/data-lineage.md`](../data/data-lineage.md) — where a value reached
- [`../../skills/privacy/data-subject-rights.md`](../../skills/privacy/data-subject-rights.md) — the request workflow
- [`../compliance/eu-ai-act-control-matrix.yaml`](../compliance/eu-ai-act-control-matrix.yaml) — `ART-10`
