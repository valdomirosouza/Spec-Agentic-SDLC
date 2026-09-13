<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Datasheet: [DATASET NAME]

<!--
  Required before a dataset feeds or evaluates a model (EU AI Act Art. 10; ISO/IEC 42001 A.7).
  Structure follows "Datasheets for Datasets" (Gebru et al.), extended with the licence, lawful
  basis and exclusion criteria this corpus requires. Written by the data owner, approved by the
  DPO and the AI Governance Lead. "Unknown" is a valid answer and is more useful than a guess —
  an unknown provenance is itself a finding (Constitution IX).
-->

**Dataset:** `[name as in docs/data/data-catalog.md]` · **Version:** [n] · **Status:** draft | approved | superseded
**Data owner:** [role] · **Approved by:** [DPO] + [AI Governance Lead] on [YYYY-MM-DD]
**Used by:** [model / retrieval index / evaluation suite]

## 1. Motivation

- **Why was this dataset created?** [purpose it serves; the decision it supports]
- **Who created it, and who funded it?** [team; external source]
- **What task is it for?** [training · fine-tuning · retrieval · evaluation · benchmarking]

## 2. Composition

| Question | Answer |
| -------- | ------ |
| What does each record represent? | |
| How many records? | |
| Is it a sample or the whole population? If a sample, how was it drawn? | |
| What does each record contain (fields)? | |
| Are there labels or targets? Who produced them? | |
| Is any information missing, and why? | |
| Are relationships between records made explicit? | |
| Are there recommended splits (train / validation / test)? | |
| Are there errors, noise or redundancies you know about? | |
| Does it rely on external resources that could change or disappear? | |

## 3. Personal data and sensitivity

| Question | Answer |
| -------- | ------ |
| Does it contain personal data? Which fields, and at what class (L1–L4)? | |
| Does it contain special-category data (health, biometrics, beliefs, orientation)? | |
| Could an individual be identified, directly or by combination? | |
| **Lawful basis** for processing (GDPR Art. 6 / LGPD Art. 7) | |
| Was consent obtained? For this purpose specifically? | |
| Can a data subject's records be located and removed? How? | |
| Does it contain data that could be offensive, distressing or harmful? | |

_Answering "no personal data" here requires it to be true after joins, not only field by field
(see `specs/data/data-lineage.md` §3 on classification-raising joins)._

## 4. Collection

| Question | Answer |
| -------- | ------ |
| How was the data acquired? [observed · reported · derived · inferred · purchased · scraped] | |
| Over what time window was it collected? | |
| What does the window exclude, and does that bias it? | |
| Were people notified, and did they have a way to object? | |
| Was an ethical or privacy review conducted? [DPIA/RIPD reference] | |

## 5. Licence and rights

| Question | Answer |
| -------- | ------ |
| **Licence** of the underlying content | |
| Does that licence permit this use, including model training? | |
| Third-party rights: copyright, database rights, terms of service | |
| Restrictions passed on to anything derived from it | |
| Who verified this, and when? | |

_A dataset whose licence does not clearly permit the intended use is **not approved**, whatever its
technical quality. This row is the most common reason a datasheet is rejected._

## 6. Preprocessing

| Question | Answer |
| -------- | ------ |
| What cleaning, filtering, normalisation or tokenisation was applied? | |
| **Exclusion criteria** — what was deliberately removed, and why? | |
| Is the raw data retained alongside the processed form? | |
| Is the processing code available and versioned? | |
| Was any masking or pseudonymisation applied? At which point? | |

_Exclusion criteria are mandatory. What was removed shapes the model as much as what was kept, and
undocumented exclusion is how a dataset quietly acquires a bias no one can later explain._

## 7. Known biases and limitations

| Dimension | What is over- or under-represented | Effect on the model | Mitigation |
| --------- | ---------------------------------- | ------------------- | ---------- |
|           |                                    |                     |            |

_"None known" is only acceptable when an examination was actually performed; say who performed it
and when. Not having looked is different from having looked and found nothing._

## 8. Uses

| Question | Answer |
| -------- | ------ |
| What has it been used for so far? | |
| What should it **not** be used for? | |
| Is there anything about its composition that could cause unfair treatment of a group? | |
| What should a future user know before using it? | |

## 9. Distribution

| Question | Answer |
| -------- | ------ |
| Will it be shared outside the organisation? With whom, under what terms? | |
| Is it subject to export controls or residency constraints? | |
| Does a sub-processor hold a copy? [`docs/privacy/sub-processor-register.md`] | |

## 10. Maintenance

| Question | Answer |
| -------- | ------ |
| Who maintains it? | |
| How often is it refreshed, and what triggers a refresh? | |
| **Retention** — how long is it kept, and what deletes it? | |
| How are erasure requests applied to it and to anything trained on it? | |
| How are changes communicated to consumers? | |
| Is there a contract governing it? [`specs/data/data-contracts.md`] | |

## 11. Approval

| Role | Name/role | Date | Decision |
| ---- | --------- | ---- | -------- |
| Data owner | | | proposed |
| DPO | | | approved / rejected |
| AI Governance Lead | | | approved / rejected |

**A rejected datasheet blocks the dataset from model use.** The dataset may still exist and serve
other purposes; it simply may not feed or evaluate a model until the rejection is resolved.
