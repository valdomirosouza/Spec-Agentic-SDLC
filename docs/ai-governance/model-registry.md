<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Model registry and AI component inventory

> **Owner:** Tech Lead · **Co-owner:** AI Governance Lead · **Last reviewed:** 2026-09-13
> **Satisfies:** EU AI Act `ART-11`, `ART-51-55` (deployer retention) · ISO/IEC 42001 A.4 and A.10
> · NIST AI RMF GOVERN 6 and MANAGE 3
> **Source of truth for versions:** [`../dependency-manifest.yaml`](../dependency-manifest.yaml)

## What this adds

The dependency manifest pins model versions and records contract-test results. It is the source of
truth for *what is running* and it is not a registry: it has no promotion history, no provenance,
no approver, and it says nothing about the other AI components — prompts, retrieval indices, tools,
memory — that shape behaviour as much as the model does.

"Model registry" and "AI component inventory" both had zero occurrences. Without them, two
questions have no answer: *which model version was live when this decision was made*, and *what
else changed that could explain this behaviour*.

**This page does not duplicate the manifest.** Versions are read from it; what is recorded here is
the governance layer around them.

## 1. Model registry

| Model                        | Role                         | State        | Contract | Promoted   | Approved by        | Provenance                                   |
| ---------------------------- | ---------------------------- | ------------ | -------- | ---------- | ------------------ | ---------------------------------------------- |
| `claude-sonnet-4-6`          | Primary reasoning            | **Active**   | v1.1, 16/16 on 2026-09-12 | 2026-05-01 | AI Governance Lead | Anthropic PBC, hosted API, US region          |
| `claude-haiku-4-5-20251001`  | Low-latency classification   | **Approved fallback** — nothing selects it | v1.1, passing | 2026-05-01 | AI Governance Lead | Anthropic PBC, hosted API                     |
| `claude-sonnet-5`            | Candidate                    | **Blocked**  | v1.1, 15/16 — PII non-leakage test failed on 2026-09-12 | — | — | Anthropic PBC; tracking issue in the manifest |

**States.** `candidate` → `approved` → `active` → `deprecated` → `blocked` | `retired`. A model
moves to `active` only when the full contract suite passes; a failing test is a finding and never a
reason to loosen the test.

**The blocked row is the most useful one here.** It records a real refusal with its evidence, which
is what makes the registry credible: a registry that only ever records approvals is a list, not a
control.

## 2. AI component inventory

Everything that shapes agent behaviour, not only the model.

| Component                    | Type              | Owner              | Class | Where it is defined                                   | Change control                                    |
| ---------------------------- | ----------------- | ------------------ | ----- | ------------------------------------------------------- | --------------------------------------------------- |
| Primary reasoning model      | Model             | AI Governance Lead | —     | `docs/dependency-manifest.yaml`                        | Contract suite + residency check (ADR-0094)       |
| Orchestrator prompts         | Prompt            | AI Governance Lead | —     | Prompt registry (ADR-0079 — no inline prompts)         | Versioned; evaluated before promotion             |
| Evaluator prompts            | Prompt            | AI Governance Lead | —     | Prompt registry                                        | Changing these changes every quality judgement    |
| Retrieval and memory corpus  | Dataset           | AI platform domain | L2    | `docs/data/datasheets/agent-memory-documents.md`       | **Not cleared for model use** — datasheet is draft |
| Embedding model              | Model             | AI platform domain | —     | Retrieval pipeline (ADR-0081)                          | A change invalidates every stored vector          |
| Tool registry                | Capability set    | Security Lead      | —     | `specs/ai/tool-registry.md` (ADR-0048)                 | Zero-trust: unregistered is uncallable            |
| Action types                 | Capability set    | AI Governance Lead | —     | `docs/ai-governance/dual-use-registry.md`              | No entry, no activation                           |
| Autonomy flags               | Configuration     | AI Governance Lead | —     | Feature flags (ADR-0015)                               | Governance sign-off; red team before an increase  |
| Guardrails                   | Control           | Security Lead      | —     | `specs/ai/guardrails.md`                               | Dual approval; never weakened                     |
| Session memory               | Dataset           | AI platform domain | L2    | `specs/ai/agent-memory.md` (ADR-0017)                  | Governance controls documented, **not implemented** |

**Prompts belong in this inventory and are the component most often left out.** A prompt change can
alter behaviour more than a model change, it usually ships without a contract test, and ADR-0079
exists precisely because inline prompts are invisible to governance.

## 3. Promotion record

Every promotion records: model and version, contract suite version and result, residency
verification (ADR-0094 §2), the approver, the date, and the version it replaced.

| Date       | From | To                  | Contract result | Residency verified | Approver           | Note                          |
| ---------- | ---- | ------------------- | --------------- | ------------------ | ------------------ | ------------------------------- |
| 2026-05-01 | —    | `claude-sonnet-4-6` | v1.1 passing    | US (recorded)      | AI Governance Lead | Initial onboarding             |
| 2026-09-12 | —    | *refused* `claude-sonnet-5` | 15/16 — PII non-leakage failed | — | — | Candidate blocked; tracking issue open |

A promotion with no row here did not happen, whatever the manifest says.

## 4. Provenance a deployer must retain

For a general-purpose model consumed from a provider, the deployer's duty is to obtain and retain
what the provider publishes, not to produce it (ADR-0093 §3). Retained per model:

| Item                                              | State                                    |
| ------------------------------------------------- | ------------------------------------------ |
| Provider identity and contract                    | Recorded — manifest and sub-processor register |
| Processing region                                 | Recorded — US                             |
| Terms on training with submitted data             | Recorded — no training on submitted data  |
| Provider's systemic-risk determination (Art. 51)  | **Not retained** — gap, `ART-51-55`       |
| Provider's training-content summary (Art. 53)     | **Not retained** — gap, `ART-51-55`       |
| Published model documentation                     | **Not retained as evidence** — linked only |

Three gaps, all the same kind: the provider publishes, and we have not captured a dated copy. That
is the deployer's half of the GPAI obligation and it is open.

## 5. Retirement

A model moves to `retired` only after nothing references it: no configuration default, no fallback,
no evaluation baseline. The row stays, with its dates and its contract history, because the
question "what was running when this decision was made" must remain answerable after retirement.

## 6. Review

| When                     | What                                                                  |
| ------------------------ | ----------------------------------------------------------------------- |
| On every promotion       | Rows in §1 and §3; residency re-verified; model card updated           |
| Monthly                  | Provider announcements against the active version                      |
| Quarterly                | Whole inventory: owners still correct, unclassified components, gaps in §4 |
| On an AI incident        | Which component versions were live (this page is the answer)           |

## 7. Open items

| # | Item                                                                 | Owner              | Resolve by            |
| - | ---------------------------------------------------------------------- | ------------------ | --------------------- |
| 1 | Retain dated copies of the provider's Art. 51 and Art. 53 publications | AI Governance Lead | 2027-01-15            |
| 2 | Prompt registry entries listed here by id once populated               | AI Governance Lead | on-event: With the prompt registry |
| 3 | Embedding model version pinned in the manifest beside the reasoning model | AI platform domain | on-event: Next model change |

## Related

- [`../dependency-manifest.yaml`](../dependency-manifest.yaml) — versions and contract results
- [`model-card.md`](model-card.md) · [`system-card.md`](system-card.md)
- [`../ai/model-lifecycle.md`](../ai/model-lifecycle.md) — the promotion path
- [`../ai/prompt-registry.md`](../ai/prompt-registry.md) — the prompt component
