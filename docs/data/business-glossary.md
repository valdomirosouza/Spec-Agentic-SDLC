<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Business glossary

> **Owner:** Product Owner · **Accountable per term:** the data owner of the domain that owns it
> **Not** [`../glossary.md`](../glossary.md), which defines the *technical and governance* vocabulary
> of this corpus (HITL, SLO, DPIA, ADR). This page defines the **business meaning** of the things
> the system reasons about — the nouns that appear in specs, contracts, datasets and agent prompts.

## Why the two are separate

`docs/glossary.md` answers "what does this corpus mean by *autonomy level*". This page answers
"what does this business mean by *request*, and when is one *approved*". They drift for different
reasons and are owned by different people, and merging them is how a business glossary becomes a
dumping ground for acronyms.

A term belongs here when **two people in different roles could reasonably disagree about it**, and
that disagreement would show up as a defect, a wrong metric or a bad agent decision.

## How to use it

- A term used in a spec, a data contract or a prompt must resolve here if it carries business
  meaning. A spec inventing a synonym for an existing term is a review finding.
- Each term names the **data owner** accountable for its definition and where it is materialised.
- Synonyms are recorded and **deprecated**, not tolerated in parallel: one canonical name.
- Changing a definition is a **breaking change to every contract that uses the term**, and follows
  the process in [`../../specs/data/data-contracts.md`](../../specs/data/data-contracts.md) §4.

## Term shape

| Field            | Meaning                                                                   |
| ---------------- | --------------------------------------------------------------------------- |
| **Term**         | The canonical business name, singular                                       |
| **Definition**   | One sentence a non-engineer can act on; no implementation detail            |
| **Owner**        | The role accountable for the definition                                     |
| **Materialised in** | Where the term becomes data: table, topic, contract, field              |
| **Lifecycle**    | The states the thing can be in, if it has any                               |
| **Not to be confused with** | The near-miss term people actually confuse it with               |

## Terms

The corpus is a template: the terms below are the ones its own worked examples use. An adopting
organisation replaces them with its domain's vocabulary and keeps the shape.

### Request

| Field | Value |
| ----- | ----- |
| **Definition** | A unit of work submitted to the system for an agent to process, carrying the payload and the identity of whoever submitted it |
| **Owner** | Data owner, platform domain |
| **Materialised in** | `requests` table; `domain.request.created` topic; `SPEC-FEAT-001` |
| **Lifecycle** | `received` → `processing` → `waiting_for_human_approval` → `completed` \| `rejected` \| `expired` |
| **Not to be confused with** | **HITL request**, which is the *approval* item created when a request needs a human decision. One request can produce zero or many HITL requests |

### HITL request

| Field | Value |
| ----- | ----- |
| **Definition** | An item awaiting a named human's decision before an agent action with real-world effect may proceed |
| **Owner** | Data owner, AI platform domain |
| **Materialised in** | HITL store; `hitl_requests_archive`; `agent.action.approved` topic |
| **Lifecycle** | `pending` → `approved` \| `rejected` \| `expired` |
| **Not to be confused with** | **Escalation**, which raises a question to a human without an action waiting on it |

### Agent action

| Field | Value |
| ----- | ----- |
| **Definition** | A single effect an agent proposes to have on the world outside itself, of a registered `action_type` |
| **Owner** | Data owner, AI platform domain |
| **Materialised in** | Audit trail; the dual-use registry entry for its `action_type` |
| **Lifecycle** | `proposed` → `approved` \| `denied` → `executed` \| `failed` |
| **Not to be confused with** | A **tool call**, which is a mechanism. Several tool calls may serve one action; a tool call with no external effect is not an action |

### Approval

| Field | Value |
| ----- | ----- |
| **Definition** | A named human's recorded decision that a specific agent action may proceed, at a point in time |
| **Owner** | Data owner, AI platform domain |
| **Materialised in** | HITL decision record; audit trail |
| **Lifecycle** | Terminal — an approval is never edited. A changed mind is a new decision on a new item |
| **Not to be confused with** | **Autonomy**, which is a standing permission for a class of actions rather than a decision about one |

### Autonomy level

| Field | Value |
| ----- | ----- |
| **Definition** | The standing permission granted to agents for a class of actions, from none to full, changed only through a governed feature flag |
| **Owner** | AI Governance Lead |
| **Materialised in** | Feature-flag configuration; `specs/ai/autonomous-mode-levels.md` |
| **Lifecycle** | `NONE` → `READ_ONLY` → `TESTS_ONLY` → `LOW_RISK` → `MEDIUM_RISK` → `FULL`, raised only with governance approval |
| **Not to be confused with** | **Approval**, which is per action; autonomy is the rule that decides whether an approval is needed at all |

### Spec

| Field | Value |
| ----- | ----- |
| **Definition** | The approved statement of what will be built and how it will be proven, identified by a stable id |
| **Owner** | Product Owner with Tech Lead |
| **Materialised in** | `specs/**` with ADR-0085 frontmatter; the spec registry |
| **Lifecycle** | `draft` → `in-review` → `approved` → `implemented` → `superseded` |
| **Not to be confused with** | A **plan**, which is how it will be built, and a **task**, which is a unit of that work |

### Serious incident

| Field | Value |
| ----- | ----- |
| **Definition** | An incident or malfunction of the AI system that directly or indirectly leads to death or serious harm to health, serious disruption of critical infrastructure, infringement of fundamental-rights obligations, or serious harm to property or the environment |
| **Owner** | AI Governance Lead |
| **Materialised in** | Incident record; `specs/compliance/ai-post-market-monitoring.md` §5 |
| **Lifecycle** | `suspected` → `causal link established` → `reported` → `corrected` → `closed` |
| **Not to be confused with** | An **outage**, which is an availability event with no harm, and a **near miss**, which this corpus investigates with the same rigour but does not necessarily report externally |

## Adding a term

1. Check it is not an existing term under another name; if it is, record the synonym and use the canonical one.
2. Write the definition so that someone outside engineering could apply it to a real case.
3. Name the owner and where it is materialised.
4. Fill in **"not to be confused with"** — if nothing goes there, the term probably does not need an entry.
5. Register the affected datasets in [`data-catalog.md`](data-catalog.md).

## Related

- [`data-catalog.md`](data-catalog.md) — where these terms become datasets
- [`data-model-catalog.md`](data-model-catalog.md) — the physical tables and topics behind them
- [`../glossary.md`](../glossary.md) — the technical and governance vocabulary
- [`data-governance-charter.md`](data-governance-charter.md) — who owns a definition
