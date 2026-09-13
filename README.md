# Spec-Agentic-SDLC

> The documentation, governance and agent-operating layer of an enterprise Agentic
> Spec-Driven SDLC, extracted from **Repository-Template-v2** (Waves 11–15) and upgraded with
> the best of **github/spec-kit**: a constitution, a feature-directory bundle, clarify /
> checklist / analyze / converge quality gates, and executable templates for spec, plan and
> tasks. No application code lives here — the corpus is meant to be dropped into, or referenced
> from, any product repository.

**What it covers**

| Area                                                                                                                    | Where                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Harness (Claude Code PR-review gates: code, doc, release, staging, business value)                                      | `harness/*.yml`                                                                                                |
| Guardrails & AI governance (HITL/HOTL, autonomy levels, OWASP LLM Top 10, EU AI Act, NIST AI RMF, model card)           | `specs/ai/`, `docs/ai-governance/`, `skills/ai/`, `.claude/hooks/`                                             |
| Spec-Driven Development (spec grammar ADR-0085, registry, templates, lifecycle skill)                                   | `specs/`, `templates/`, `skills/sdlc/`, `docs/governance/spec-registry.md`                                     |
| Agentic SDLC (15 phases, nine human gates, delivery agents, `/deliver`, `/sdd-*` commands)                              | `docs/sdlc/`, `docs/process/`, `.claude/agents/`, `.claude/skills/`                                            |
| Compliance — LGPD, GDPR, ISO 27001, SOX, SOC 2                                                                          | `docs/compliance/`, `docs/privacy/`, `docs/sox/`, `specs/compliance/`, `skills/privacy/`, `skills/compliance/` |
| Security — OWASP ASVS 5.0 & LLM Top 10 control matrices, threat model, SAST/SCA/DAST pipeline, secure development       | `specs/security/`, `skills/devsecops/`, `SECURITY.md`                                        |
| Observability — Golden Signals (Traffic, Errors, Saturation, Latency), logs, metrics, traces, SLOs, PRR, runbooks, DORA | `specs/observability/`, `docs/sre/`, `skills/sre/`, `skills/observability/`                                    |
| Audit & governance — traceability matrix, release evidence package, change log, RACI, Big Four evidence map             | `docs/governance/`, `docs/change-log/`, `docs/audit/`                                                          |
| ADRs (90, all binding)                                                                                                  | `docs/adr/`                                                                                                    |
| Root of authority                                                                                                       | `memory/constitution.md`                                                                                       |

## The workflow

```text
/sdd-constitution   once per project → memory/constitution.md
/sdd-specify        feature description → specs/features/<SPEC-ID>-<slug>/spec.md (+ checklists/requirements.md)
/sdd-clarify        ≤ 5 targeted questions, answers encoded into the spec
        ▼  human gate: Spec-as-PR approval (status: approved)
/sdd-plan           plan.md with Constitution Check + research / data-model / contracts / quickstart (+ ADR, threat model, DPIA decisions)
/sdd-checklist      reviewer-owned "unit tests for the requirements" (security, privacy, observability, audit …)
/sdd-tasks          tasks.md — Setup → Foundational → per user story (tests first) → Polish
/sdd-analyze        read-only cross-artifact consistency report (constitution & ADR conflicts = CRITICAL)
/sdd-implement      execute tasks phase by phase, scoped runs, hard stops at every HITL trigger
/sdd-converge       append remaining gaps as tasks; repeat until "Converged"
        ▼  human gates: code review (Phase 7) → testing, DevSecOps, AI safety, PRR, release, post-deploy (Phases 8–14, driven by /deliver)
```

Each command is a Claude Code skill under `.claude/skills/sdd-*/SKILL.md`; the phase and gate
mapping is in [`docs/sdlc/spec-kit-comparison.md`](docs/sdlc/spec-kit-comparison.md) §5.
The persistence rules for specs are in
[`docs/sdlc/spec-persistence-model.md`](docs/sdlc/spec-persistence-model.md).

## Repository map

```text
memory/constitution.md          nine binding articles; every plan and analysis is checked against them
templates/                      spec, plan, tasks, checklist, roadmap, constitution templates
scripts/bash/                   create-new-feature.sh · check-prerequisites.sh · setup-plan.sh (JSON output for agents)
specs/                          system, api, ai, privacy, security (control matrices), compliance, observability, features/
docs/adr/                       ADR-0001 … ADR-0090 (index in docs/adr/README.md)
docs/process/                   WORKFLOW (15 phases), RACI, HITL-GOVERNANCE, DoR / DoD / DoR-Release, gates/phase-gates.yaml
docs/sdlc/                      agentic-spec-driven-delivery.md (canonical model), handoff schema, spec-kit comparison
docs/governance/                traceability matrix, release evidence package, gate lifecycle, spec registry, RACI/RBAC matrices
docs/audit/                     Big Four / SOX / SOC 2 / ISO 27001 evidence map — what an auditor asks for and where it lives
docs/compliance/ docs/privacy/  ISO 27001 Annex A, SOC 2 TSC, dependency policy, PII inventory, DPIA/RIPD, retention
docs/sre/ docs/runbooks/        SLOs, CUJs, PRR, runbooks, capacity, backup/recovery, on-call
docs/ai-governance/             AI safety checklist, autonomy boundaries, EU AI Act, NIST AI RMF, model card
skills/                         plain-Markdown skills (load ≤ 2 per task — ADR-0060); .claude/skills/ is the /-command layer
.claude/agents/                 asdd-orchestrator + 15 phase agents + phase-executor
harness/                        code / doc / release / staging / business-value check specs
CLAUDE.md · AGENTS.md           the detailed operating contract for agents (the constitution is its normative core)
```

## Using it

1. Read `memory/constitution.md`, then `CLAUDE_SESSION_INIT.md` and `CLAUDE.md`.
2. Start a feature with `/sdd-specify <description>` (or run `scripts/bash/create-new-feature.sh --json "<description>"`).
3. Follow the workflow above; every command tells you the human gate it stops at.
4. For a full governed dry-run of the 15 phases use `/deliver dry-run <spec.md>`.

## Provenance and known limits

- Source: Repository-Template-v2 on branch `feat/W15-test-depth` (2026-09-12) — Markdown,
  harness YAML, control-matrix YAML/JSON and the `.claude/` operating layer only. The original
  README is kept at `docs/reference/repository-template-v2-README.md`.
- Documents still reference source-code paths (`src/…`, `scripts/governance/…`,
  `.github/workflows/…`, `services.yaml`) that live in the source template, not here. They
  describe where a control is implemented in a product repository that adopts this corpus.
- spec-kit reference: github/spec-kit `d848fb4` (2026-09-11). What was adopted, adapted or
  deliberately left out is recorded in `docs/sdlc/spec-kit-comparison.md`.
