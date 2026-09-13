<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Spec-Agentic-SDLC × github/spec-kit — comparison and adopted improvements

> **Compared on:** 2026-09-12 · spec-kit at commit `d848fb4` (2026-09-11, v1.0.x) ·
> this repository's documentation as copied from Repository-Template-v2 (Waves 11–15).
> Purpose: name what each side does better, then record exactly what was adopted here and how
> it was adapted to the 15-phase Agentic SDLC (ADR-0058), the HITL model (ADR-0011) and the
> compliance/audit obligations this repository carries.

## 1. What the two projects are

|                            | github/spec-kit                                                                                                                                                                 | Spec-Agentic-SDLC (this repo)                                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Shape                      | A CLI (`specify`) that scaffolds a spec-driven **workflow** into any project for 30+ coding agents: templates, scripts, slash commands, extensions, presets, bundles, workflows | A **governance and delivery corpus**: 15-phase lifecycle, 89 ADRs, control matrices, skills, harness gates, HITL governance, compliance (LGPD/GDPR/ISO 27001/SOX), SRE and audit documentation |
| Unit of work               | One feature = `specs/NNN-slug/{spec,plan,tasks}.md` + research/data-model/contracts/quickstart                                                                                  | One spec = `specs/<domain>/<id>.md` with ADR-0085 frontmatter, registry, gates, delivery report                                                                                                |
| Authority                  | `memory/constitution.md` (9 articles, SemVer, sync-impact report)                                                                                                               | `CLAUDE.md` §3 Inviolable Rules + binding ADRs + control matrices                                                                                                                              |
| Human gates                | `gate` steps in workflows; PR review                                                                                                                                            | Nine mandatory human gates across Phases 2–14; Spec-as-PR; runtime HITL gateway                                                                                                                |
| Ambiguity                  | `[NEEDS CLARIFICATION]` (≤ 3), `/clarify` (≤ 5 questions, one at a time, recommended answer)                                                                                    | Open Questions + Assumptions tables with owner and resolve-by phase; `check_open_questions.py` gate; §14.1 escalation on contradiction                                                         |
| Cross-artifact consistency | `/analyze` (read-only report), `/converge` (append-only gap tasks)                                                                                                              | Deterministic gates: spec registry S1–S7, doc-references, traceability, control matrix, delivery report                                                                                        |
| Testing stance             | Tests optional unless the spec asks for them                                                                                                                                    | Tests mandatory, coverage floors, abuse-case ratchet, test-integrity baseline                                                                                                                  |
| Compliance / audit         | Out of scope (left to presets)                                                                                                                                                  | SOX ITGC, SOC 2 TSC, ISO 27001 Annex A, LGPD/GDPR, release evidence package, change log                                                                                                        |
| Agent portability          | 30+ integrations, `$speckit-*`/`/speckit.*` forms                                                                                                                               | Claude Code first (`.claude/skills`, `.claude/agents`), `AGENTS.md` cross-tool contract                                                                                                        |

## 2. What spec-kit does better (and what was adopted)

| spec-kit strength                                                                                                                | Adopted here as                                                                                    | Adaptation notes                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Constitution** as a single, versioned root of authority that plans and analyses are checked against                            | `memory/constitution.md` (9 articles) + `templates/constitution-template.md` + `/sdd-constitution` | Articles condense `CLAUDE.md` §3; five articles are protected (can only be strengthened); a constitution FAIL in a plan blocks the phase                          |
| **Feature-directory bundle** (`spec / plan / tasks / research / data-model / contracts / quickstart / checklists`)               | `specs/features/<SPEC-ID>-<slug>/` with the same files                                             | Directory name carries the ADR-0085 spec id; `plan.md` = Phase 5 artefact, `tasks.md` = Phase 6                                                                   |
| **Prioritised, independently testable user stories** (P1 = MVP) and Given/When/Then scenarios                                    | `templates/spec-template.md` §2                                                                    | Kept EARS FR table and canonical AC table (machine-traceable); stories organise `tasks.md`                                                                        |
| **`[NEEDS CLARIFICATION]` budget** (≤ 3) with informed defaults recorded as assumptions                                          | Spec template + `/sdd-specify` step 3                                                              | Assumptions table keeps owner + resolve-by phase (this repo); markers must be gone before `approved`                                                              |
| **`/clarify`**: taxonomy-driven coverage scan, ≤ 5 questions, one at a time, recommended answer, answers encoded into the spec   | `/sdd-clarify`                                                                                     | Adds compliance categories (LGPD/GDPR/SOX/ISO), observability; a conflict with an ADR/approved spec is escalated (`[HITL-ESCALATE]`), never decided by preference |
| **Constitution Check gate + Complexity Tracking** in the plan                                                                    | `templates/plan-template.md`                                                                       | Rows are the nine articles; adds Phase 5 obligations (ADR, threat model, DPIA, Phase 10) and an Observability Design table                                        |
| **Tasks format** `- [ ] T001 [P] [US1] … path` with Setup → Foundational → per-story → Polish, dependency and MVP-first strategy | `templates/tasks-template.md`, `/sdd-tasks`                                                        | Tests are mandatory and precede code; every task carries `Refs: FR/AC`; ≤ 2 skills per task (ADR-0060)                                                            |
| **Checklists as "unit tests for requirements"** (reviewer-owned, never tick by agent, implement reads them as a gate)            | `templates/checklist-template.md`, `/sdd-checklist`                                                | Built-in rows for privacy, security, observability and audit traceability                                                                                         |
| **`/analyze`**: read-only, severity-graded, coverage table, constitution conflicts CRITICAL                                      | `/sdd-analyze`                                                                                     | Also checks ADR conflicts, control-matrix ids, `services.yaml` topics, AC → named test                                                                            |
| **`/converge`**: append-only gap closure loop after implement                                                                    | `/sdd-converge`                                                                                    | Also verifies frontmatter `implemented_by`/`verified_by` and the abuse-case ratchet; feeds Phase 7                                                                |
| **Scoped implementation runs** to survive context compaction (per phase / story / task range, sub-agent delegation)              | `/sdd-implement` usage line and tasks-template "Implementation Strategy"                           | Same guidance; hard stops from CLAUDE.md §14.1 added                                                                                                              |
| **Spec of specs / roadmap** for epics too large for one cycle                                                                    | `templates/roadmap-template.md`; `roadmap:` frontmatter field                                      | Bidirectional plain-text links; immutable R-ids as traceability anchors                                                                                           |
| **Spec persistence models** made explicit (flow-back / flow-forward / living)                                                    | `docs/sdlc/spec-persistence-model.md`                                                              | This repo chooses **flow-forward + living spec**: supersede, never delete (audit)                                                                                 |
| **Helper scripts** (`create-new-feature`, `check-prerequisites`, `setup-plan`) with JSON output for agents                       | `scripts/bash/*.sh`                                                                                | Rewritten for the SPEC-ID grammar and bash 3.2; they never create git branches (human decision)                                                                   |
| **`/taskstoissues`**: one GitHub issue per task, deduplicated by task id                                                          | `/sdd-taskstoissues` + `scripts/bash/tasks-to-issues.sh`                                            | gh CLI instead of the GitHub MCP server; refuses unapproved specs; `Refs:` grammar; issue number written back to the task line                    |
| **Sync Impact Report** on constitution amendments                                                                                | `/sdd-constitution` step 4                                                                         | Lists dependent templates/skills that must change in the same PR                                                                                                  |

## 3. What this repository does better (kept, and now wired to the spec-kit flow)

| This repository's strength                                                                                                                   | Where the spec-kit-style commands now rely on it                                                             |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 15-phase lifecycle with nine mandatory human gates and a risk-based path (ADR-0058, ADR-0064)                                                | Every `/sdd-*` skill names its phase and stops at the gate it must not cross                                 |
| Spec grammar, status vocabulary and registry (ADR-0085); `approved` before code                                                              | `check-prerequisites.sh --require-approved`; `/sdd-plan`, `/sdd-tasks`, `/sdd-implement` refuse a draft spec |
| Deterministic governance gates (registry, open questions, doc references, control matrices, test integrity, coverage floors, assertion lint) | `/sdd-analyze` is their human-readable twin, not a replacement                                               |
| HITL/HOTL runtime governance, escalation protocol, 2-skill budget                                                                            | Hard stops in `/sdd-implement`; ≤ 2 skills per task in `/sdd-tasks`                                          |
| Privacy by design (PII classes, DPIA/RIPD), LGPD/GDPR skills                                                                                 | Spec §7, plan Phase 5 obligations, checklist privacy rows                                                    |
| Security: OWASP ASVS 5.0 + LLM Top 10 control matrices, DevSecOps pipeline, threat model                                                     | Spec §7 controls row, plan Constitution Check IV, checklist security rows                                    |
| Observability: Golden Signals, SLOs, PRR, runbooks, DORA                                                                                     | Spec §8, plan Observability Design, checklist observability rows, Constitution VI                            |
| Audit & governance: release evidence package, change log, SOX ITGC, SOC 2, ISO 27001 Annex A, traceability matrix                            | `docs/audit/big-four-evidence-map.md` ties them to auditor requests; Constitution VII                        |
| Delivery agents (`asdd-orchestrator` + 15 phase agents, `/deliver` dry-run/code)                                                             | The `/sdd-*` commands are the per-artefact building blocks the orchestrator can call                         |

## 4. Deliberately not adopted

- **Command-lifecycle hooks** (`before_/after_<command>`): decided in ADR-0092 (Proposed) — the
  `before_` shape becomes a Claude Code `UserPromptSubmit` gate; the `after_` shape as a `Stop`
  hook is refused (Constitution V).
- **Extensions / presets / bundles / workflow engine.** Spec-kit's layered artifact resolution
  and its YAML workflow engine are tooling for a multi-agent CLI product. This repository keeps
  Claude Code skills and the harness YAML as the extension points; adopting the engine would
  duplicate `.claude/agents/` and the phase-gates YAML.
- **Optional tests.** Constitution II makes tests mandatory; spec-kit's "tests only if requested"
  rule is not compatible with the coverage floors and the test-integrity gate.
- **Agent-created git branches.** Spec-kit's git extension creates and switches branches in
  `before_specify` hooks. Here branch creation stays a human step (Constitution V); the script
  prints the branch name.
- **Numeric-only feature ids (`001-slug`).** The ADR-0085 grammar `SPEC-<DOMAIN>-NNN` is kept;
  numbering is per domain and scans both directory names and spec frontmatter.

## 5. The resulting flow

```text
/sdd-constitution ─┐ (once per project)
/sdd-specify → /sdd-clarify → [Spec-as-PR approval] → /sdd-plan → /sdd-checklist → /sdd-tasks
   → /sdd-analyze → /sdd-implement ⇄ /sdd-converge → PR (Phase 7) → Phases 8–14 via /deliver + human gates
```

| Command                                        | ADR-0058 phase                | Human gate it stops at                                                                  |
| ---------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------- |
| `/sdd-specify`, `/sdd-clarify`                 | 2–4 Discovery → Specification | Discovery approval; **Specification approval (Spec-as-PR)**                             |
| `/sdd-plan`                                    | 5 Architecture                | Architecture approval when an ADR / threat model is required                            |
| `/sdd-checklist`, `/sdd-tasks`, `/sdd-analyze` | 5 → 6 boundary                | — (read-only / preparatory)                                                             |
| `/sdd-implement`, `/sdd-converge`              | 6 Development                 | **Code review approval** (Phase 7); security and AI-governance approvals when triggered |

## 6. Open follow-ups

- Port the deterministic gate scripts (`scripts/governance/*.py`) from the source template so
  `/sdd-analyze` can cite their output instead of re-deriving it.
- ~~Add a `/sdd-taskstoissues` equivalent~~ — done 2026-09-12 (#10): `.claude/skills/sdd-taskstoissues/`
  backed by `scripts/bash/tasks-to-issues.sh` (gh CLI, approved specs only, `(#N)` written back).
- Decide whether `docs/delivery/<SPEC-ID>/FINAL-REPORT.md` should embed the `/sdd-converge`
  findings table as Phase 7 evidence.
