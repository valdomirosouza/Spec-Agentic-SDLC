# ADR-0090 — Adopt spec-kit Workflow Primitives (Constitution, Feature Bundle, Clarify/Analyze/Converge Gates)

**Status:** Accepted
**Date:** 2026-09-12
**Authors:** Tech Lead (drafted with Claude Code while creating the Spec-Agentic-SDLC corpus)
**Spec:** specs/sdlc/development-lifecycle.md · docs/sdlc/spec-kit-comparison.md
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0034](ADR-0034-agentic-escalation-protocol.md), [ADR-0058](ADR-0058-agentic-spec-driven-delivery-workflow.md), [ADR-0060](ADR-0060-task-atomicity-skill-budget.md), [ADR-0085](ADR-0085-unified-spec-identifier-and-status-grammar.md)

---

## Context

This corpus was extracted from Repository-Template-v2 and compared with
[github/spec-kit](https://github.com/github/spec-kit) at commit `d848fb4` (2026-09-11). The
comparison (`docs/sdlc/spec-kit-comparison.md`) found that the template already had the
stronger governance spine (15 phases, nine human gates, ADR-0085 spec grammar, deterministic
gates, control matrices, compliance and audit evidence) but lacked four things spec-kit does
well and that directly address the Seven-Axis Review findings on **ambiguity handling** and
**cross-artifact validation**:

1. a single, versioned **constitution** that plans and analyses are mechanically checked against
   (`CLAUDE.md` §3 is authoritative but 40 KB and not structured as checkable articles);
2. a **feature-directory bundle** (`spec / plan / tasks / research / data-model / contracts /
quickstart / checklists`) with executable templates, so the design artefacts of Phase 5 have a
   fixed home and shape;
3. explicit **clarification** discipline: a bounded `[NEEDS CLARIFICATION]` budget, a
   taxonomy-driven `/clarify` step with recommended answers encoded back into the spec, and
   reviewer-owned **checklists** that test the requirements rather than the code;
4. **cross-artifact gates** before and after implementation: a read-only `/analyze` report and an
   append-only `/converge` gap-closure loop.

Constraints: nothing may weaken CLAUDE.md §3, the HITL model (ADR-0011) or the test-integrity and
coverage rules (ADR-0050, ADR-0065); agents must not create branches, merge or deploy; the
ADR-0085 identifier grammar must be preserved; scripts must run on macOS bash 3.2.

## Decision

We adopt spec-kit's workflow primitives as **Claude Code skills and templates**, not as the
`specify` CLI or its extension/preset/workflow engine:

- `memory/constitution.md` — nine binding articles condensed from CLAUDE.md §3, with SemVer and a
  Sync Impact Report on amendment (`/sdd-constitution`). Articles I, II, V, VII and IX are
  protected: they may only be strengthened. If the constitution and CLAUDE.md diverge, the
  constitution wins and CLAUDE.md is amended in the same change.
- `specs/features/<SPEC-ID>-<slug>/` as the feature bundle; `templates/{spec,plan,tasks,checklist,
roadmap,constitution}-template.md` as its executable templates. The spec template keeps the EARS
  FR table, the canonical AC table and the coverage footer of `specs/SPEC-TEMPLATE.md`, and adds
  spec-kit's prioritised, independently testable user stories and `## Clarifications`.
- Ten commands `/sdd-constitution`, `/sdd-specify`, `/sdd-clarify`, `/sdd-plan`, `/sdd-checklist`,
  `/sdd-tasks`, `/sdd-analyze`, `/sdd-implement`, `/sdd-converge`, `/sdd-taskstoissues` (added 2026-09-12, #10) under
  `.claude/skills/sdd-*/`,
  each bound to an ADR-0058 phase and to the human gate it must stop at.
- `scripts/bash/{common,create-new-feature,check-prerequisites,setup-plan,tasks-to-issues}.sh` with JSON output;
  numbering is per `SPEC-<DOMAIN>`; `--require-approved` refuses a spec that is not
  `approved`/`implemented`; no script creates or switches git branches.
- Tests remain **mandatory** in `tasks.md` (spec-kit makes them optional); every task carries
  `Refs:` to its FR/AC ids and declares ≤ 2 skills (ADR-0060).
- Spec persistence is **flow-forward for history, living spec for the contract**
  (`docs/sdlc/spec-persistence-model.md`): supersede, never delete.

## Consequences

### Positive

- Ambiguity is bounded and visible: ≤ 3 markers per spec, ≤ 5 clarify questions per run, every
  answer encoded in the spec, contradictions escalated rather than silently resolved.
- Cross-artifact consistency is checked twice per feature (analyze before, converge after) in a
  form humans can read, alongside the deterministic gates.
- Design artefacts have one shape and one location, which makes the FR → AC → test → evidence
  chain (Constitution VII, `docs/audit/`) easier to walk.
- The corpus can be adopted by any product repository without the spec-kit CLI.

### Negative / Trade-offs

- Two sources of normative text exist (constitution and CLAUDE.md §3); drift is prevented by the
  amendment rule but must be reviewed.
- The `/sdd-*` skills are prompts, not code: their guarantees hold only as far as the deterministic
  gates from the source template are ported alongside them (tracked follow-up).
- Existing specs keep their `specs/<domain>/` location; only new feature work uses the bundle
  layout, so two layouts coexist until a migration is decided.

## Alternatives Considered

- **Install spec-kit as-is** (`specify init`) — rejected: its optional-tests stance, agent-created
  branches and `001-slug` ids conflict with Constitution II and V and with ADR-0085; its
  extension/preset/workflow engine duplicates `.claude/agents/` and `phase-gates.yaml`.
- **Keep CLAUDE.md as the only authority** — rejected: a 40 KB contract cannot be evaluated row by
  row in a plan; the constitution gives `/sdd-plan` and `/sdd-analyze` a checkable surface.
- **Write the commands as `.claude/agents/`** — rejected: they are per-artefact operations the
  existing phase agents and `/deliver` can call; skills are the right granularity.
