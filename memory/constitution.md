# Spec-Agentic-SDLC Constitution

> The constitution is the root of authority for every artefact in this repository. Specs, plans,
> tasks, ADRs, skills and agent prompts are evaluated against it; when they conflict with it, the
> artefact changes, never the principle. It condenses the inviolable rules of `CLAUDE.md` §3 into
> nine articles so that an agent can load one file and know what is non-negotiable.
> Pattern adopted from github/spec-kit (`/speckit.constitution`); content is this template's own.

## Core Principles

### I. Specification First (NON-NEGOTIABLE)

No code, migration, prompt or infrastructure change exists without an **approved** spec that names
it. A spec is a file under `specs/` with ADR-0085 frontmatter (`id`, `kind`, `status`,
`governing_adrs`, `implemented_by`, `verified_by`). Code may only reference a spec whose status is
`approved` or `implemented`. If a spec cannot be found after two searches, the agent stops and
emits `[HITL-ESCALATE]` instead of inventing one.

**Rationale:** The spec is the contract between intent and implementation. Every downstream gate
(traceability, coverage, audit evidence) keys on the spec id.

### II. Test-Backed Change

Every behavioural change ships with automated tests that reference the requirement they prove
(`@pytest.mark.requirement("SPEC-…/FR-NN")` or the language equivalent). Unit coverage stays at or
above **the declared floor** and never below the per-package floors; **the floor never decreases**;
the abuse-case count never decreases; a test is never weakened, skipped or deleted to make a gate
pass (ADR-0050, ADR-0065). The floor is a single number declared in ADR-0022 — currently **85%**,
ratcheted from 80% by RFC-0020 — and is not restated here, so raising it needs no amendment to this
article and cannot leave a stale copy behind. Tests are written
so that they **fail before** the implementation exists.

### III. Privacy by Design

No real personal data in any file. PII is classified L1–L4 (`docs/privacy/pii-inventory.md`),
masked before every log write, broker publish and LLM call, and encrypted at rest for L1/L2.
Any new PII processing triggers a DPIA/RIPD (LGPD + GDPR) before the spec is approved.

### IV. Security Gates Are Not Optional

SAST, SCA, secret scanning, container and IaC scanning, DAST in staging, SBOM and signed
artefacts run on every change; a gate is never bypassed (`--no-verify` is prohibited). The OWASP
ASVS 5.0 and OWASP LLM Top 10 control matrices under `specs/security/` are the authoritative,
machine-verified mapping from control to code, test and CI job. New gates enter in report mode
and are promoted to blocking only after a documented burn-in (ADR-0070).

### V. Human Oversight of Agents (HITL/HOTL)

Agents draft, analyse, test and recommend. Humans approve, own and operate. Every agent action
with a real-world effect routes through the HITL gateway; autonomy is granted only through
feature flags under governance review (ADR-0011, ADR-0015). Delivery agents stop at the nine
mandatory human gates of the 15-phase lifecycle and never merge, deploy, release or change
autonomy flags on their own.

### VI. Observability Is Part of Done

A feature is production-ready only when the team can observe, diagnose and roll it back. Every
production-impacting feature defines its critical user journey, the four Golden Signals
(Traffic, Errors, Saturation, Latency), SLIs/SLOs, required logs, traces and metrics, dashboard
and runbook updates, and rollback indicators — before the Production Readiness Review.

### VII. Traceability and Auditability

Every artefact carries the identifiers that let an auditor walk the chain
issue → spec → ADR → code → test → CI gate → release evidence without asking anyone. Commits
carry `Refs: #issue, SPEC-…, ADR-…`; releases produce the eleven-item evidence package; audit
records are immutable and retained per policy (ISO 27001 3 years, SOX 7 years where applicable).
Documents are superseded, never deleted.

### VIII. Simplicity and No Gold-Plating

Implement what the spec says and nothing more. Additional abstraction, projects, or "might need"
features require a justification recorded in the plan's Complexity Tracking table. Every task
loads at most two skills; a task that needs a third is not atomic and is split (ADR-0060).

### IX. Grounding and Non-Fabrication

Every factual or API-level claim is grounded down the chain codebase → specs/docs → Context7 →
web → `uncertain — verify`. An agent never invents an API, config key, file path, ADR number or
behaviour. Ambiguities are recorded as `[NEEDS CLARIFICATION: …]` markers in the spec (at most
three per spec) or as Open Questions resolved at a human gate, never as silent assumptions.

## Governance

- **Authority.** These articles are binding gates. The `## Constitution Check` section of every
  plan is evaluated against them; `/sdd-analyze` and `/sdd-converge` treat a conflict with a MUST
  as CRITICAL. Violations are resolved by changing the spec, plan or tasks, not by diluting the
  article.
- **Relationship to CLAUDE.md.** `CLAUDE.md` remains the detailed operating contract (commands,
  skills, escalation protocol). This constitution is its normative core; if the two ever diverge,
  the constitution wins and `CLAUDE.md` is amended in the same change.
- **Amendments.** A change to this file requires a PR with rationale, Tech Lead + Security Lead
  approval, a version bump, and propagation to the templates and skills that cite the amended
  article, recorded in the Sync Impact Report comment at the top of the file.
- **Versioning.** MAJOR = an article removed or redefined; MINOR = an article or section added or
  materially expanded; PATCH = wording and clarifications.
- **Compliance review.** Every PR review verifies compliance. Added complexity or any deviation is
  justified in the PR and, for plans, in Complexity Tracking. Unjustified violations block merge.

**Version**: 1.0.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-12
