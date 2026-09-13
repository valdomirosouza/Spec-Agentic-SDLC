<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Datasheet: agent_memory_documents

<!-- From templates/datasheet-template.md. This is the retrieval and memory corpus identified in
     docs/data/data-catalog.md as the one dataset that feeds a model. -->

**Dataset:** `agent_memory_documents` · **Version:** 1 · **Status:** draft
**Data owner:** AI platform domain · **Approved by:** _pending — DPO and AI Governance Lead_
**Used by:** the retrieval pipeline (ADR-0081) and agent session memory (ADR-0017)

> **Status note.** This datasheet is `draft` and the dataset is therefore **not cleared for model
> use** under EU AI Act `ART-10`. It is published in this state deliberately: the corpus is a
> template, several answers below depend on the adopting organisation's own corpus, and recording
> "unknown" is more useful than an invented answer (Constitution IX). The unresolved rows are
> listed in §12.

## 1. Motivation

- **Why created:** to give agents durable, searchable context beyond a single session — prior
  decisions, indexed documentation and bug history — so that answers are grounded in the
  organisation's own material rather than in the model's parametric memory.
- **Created by:** the AI platform domain. Not funded or sourced externally.
- **Task:** retrieval for grounding, and session memory. **Not** training or fine-tuning.

## 2. Composition

| Question | Answer |
| -------- | ------ |
| What does each record represent? | One document chunk with its embedding and source metadata |
| How many records? | Adopter-specific; unbounded and growing |
| Sample or population? | Population of whatever the adopter indexes |
| Fields | `content` (encrypted), embedding vector, source reference, timestamps, session scope |
| Labels? | None. There is no supervised target |
| Missing information | Source references may be absent for content ingested before the indexer recorded them |
| Relationships between records | Chunks of one source document are linked by source reference |
| Recommended splits | Not applicable — retrieval corpus, not a training set |
| Known errors or noise | Chunk boundaries can split a statement across records, which degrades retrieval precision |
| External dependencies | The embedding model. Changing it invalidates every stored vector |

## 3. Personal data and sensitivity

| Question | Answer |
| -------- | ------ |
| Personal data? | **Possibly.** Classified **L2** in the catalog. Indexed material may contain names, handles or identifiers depending on what the adopter indexes |
| Special-category data? | Must not be indexed. No control currently prevents it — see §12 |
| Re-identification risk | Real: an embedding of personal text remains personal data and the class is preserved through the `embed` transform (`specs/data/data-lineage.md` §3) |
| Lawful basis | Adopter-specific. Legitimate interest is the usual basis for internal documentation; **unknown** for this template |
| Consent | Not obtained. Not the basis relied on |
| Can a subject's records be located and removed? | Partially. Source-level deletion is possible; per-subject location requires field-level lineage, which is open item 3 of the lineage spec |
| Offensive or distressing content? | Possible where bug history or incident notes are indexed |

## 4. Collection

| Question | Answer |
| -------- | ------ |
| How acquired | Derived — indexed from the adopting organisation's own documents and records |
| Time window | Continuous from first indexing; no start boundary declared |
| What the window excludes | **Unknown.** No exclusion criteria are currently declared — see §6 |
| Were people notified? | Adopter-specific |
| Ethical or privacy review | `docs/privacy/dpia/dpia-agent-memory.md` |

## 5. Licence and rights

| Question | Answer |
| -------- | ------ |
| Licence of underlying content | The adopting organisation's own material; internal licence |
| Permits this use, including training? | Permits retrieval. **Training is out of scope** and is not authorised by this datasheet |
| Third-party rights | Any third-party document indexed carries its own terms. **Not verified** |
| Restrictions on derivatives | Embeddings inherit the source's restrictions |
| Verified by, when | **Not verified** — see §12 |

## 6. Preprocessing

| Question | Answer |
| -------- | ------ |
| Cleaning and chunking | Chunk → embed → store, per ADR-0081 |
| **Exclusion criteria** | **None declared.** This is the most significant gap in this datasheet |
| Raw data retained? | Yes, `content` retained encrypted alongside the vector |
| Processing code versioned? | Adopter-side |
| Masking or pseudonymisation | PII filter applies before LLM calls and log writes; **not** applied at index time |

_The gap between "masked before the LLM call" and "not masked at index time" matters: personal data
can be at rest in the corpus even when it never reaches a prompt unmasked._

## 7. Known biases and limitations

| Dimension | Over/under-represented | Effect | Mitigation |
| --------- | ---------------------- | ------ | ---------- |
| Recency | Recently indexed material dominates retrieval | Agents over-weight recent decisions | None currently |
| Coverage | Only what the adopter chose to index | Confident answers in indexed areas, silence elsewhere | Groundedness SLI catches ungrounded claims (ADR-0080) |
| Authorship | Material written by the most prolific authors dominates | Their conventions read as organisational norms | None currently |

**No bias examination has been performed.** The rows above are reasoned expectations, not
measurements, and are labelled as such.

## 8. Uses

| Question | Answer |
| -------- | ------ |
| Used for so far | Retrieval grounding; session memory |
| Should **not** be used for | Training or fine-tuning any model; any decision about a person; export outside the organisation |
| Could its composition cause unfair treatment? | Possible via the authorship bias above, if agent output is used in decisions about people |
| What a future user should know | Embeddings are tied to the embedding model version; the corpus is L2 and unmasked at rest |

## 9. Distribution

| Question | Answer |
| -------- | ------ |
| Shared externally? | No |
| Export controls or residency | Governed by the residency ADR (#36) |
| Sub-processor copy? | The vector store provider, if managed. See `docs/privacy/sub-processor-register.md` |

## 10. Maintenance

| Question | Answer |
| -------- | ------ |
| Maintainer | AI platform domain |
| Refresh trigger | On document change; full re-index on embedding-model change |
| Retention | 1 year (`docs/data/data-model-catalog.md`) |
| Erasure requests | Source-level deletion plus re-index. Nothing was trained on it, so no model carries the value |
| Change communication | Through the dataset's catalog entry |
| Contract | `internal` — no cross-domain consumer today |

## 11. Approval

| Role | Date | Decision |
| ---- | ---- | -------- |
| Data owner | 2026-09-13 | proposed |
| DPO | — | **pending** |
| AI Governance Lead | — | **pending** |

## 12. Unresolved

| # | Row | Why it matters |
| - | --- | -------------- |
| 1 | Lawful basis not stated | Required before any personal data is indexed (GDPR Art. 6 / LGPD Art. 7) |
| 2 | No exclusion criteria declared | Undocumented exclusion is how a corpus acquires an unexplainable bias |
| 3 | Third-party content rights not verified | A single third-party document can make the corpus unusable for its purpose |
| 4 | No control prevents special-category data being indexed | The highest-severity gap here |
| 5 | Not masked at index time | Personal data at rest even when prompts are clean |
| 6 | No bias examination performed | §7 is reasoning, not measurement |

Until these are resolved, the dataset stays `draft` and is **not cleared for model use**.

## Related

- [`../../../templates/datasheet-template.md`](../../../templates/datasheet-template.md)
- [`../data-catalog.md`](../data-catalog.md) — the dataset's governance row
- [`../../privacy/dpia/dpia-agent-memory.md`](../../privacy/dpia/dpia-agent-memory.md)
- [`../../../specs/compliance/eu-ai-act-control-matrix.yaml`](../../../specs/compliance/eu-ai-act-control-matrix.yaml) — `ART-10`
