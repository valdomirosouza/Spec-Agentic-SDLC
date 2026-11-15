---
name: sdd-converge
description: After /sdd-implement, assess the codebase against the feature's spec, plan and tasks (and the constitution) and append every remaining gap as new, traceable tasks under a "Phase N: Convergence" section of tasks.md — append-only, never edits code, spec or plan. Repeat implement → converge until it reports Converged, for at most 3 rounds; a third round that still finds gaps escalates to a human instead. Trigger on "converge", "did we miss anything", "gap check". Usage — /sdd-converge.
---

<!-- generated from .claude/skills/sdd-converge/SKILL.md by scripts/python/render_commands.py — edit the source, then re-render (ADR-0091) -->

# /sdd-converge — close the gap between intent and code

Adapted from spec-kit `/speckit.converge`. It is the pre-PR self-check before Phase 7 (Code
Review) and the natural place to confirm the FR→AC→test chain that the audit evidence relies on.

## Operating constraints

- **APPEND-ONLY.** The only write is a new `## Phase N: Convergence` section at the end of
  tasks.md. Never rewrite, renumber or delete existing tasks; never touch spec.md, plan.md or
  application code. If nothing remains, tasks.md stays byte-for-byte unchanged.
- **Constitution and ADRs are non-negotiable**: code that violates a MUST is the first task.
- Not a diff tool: it assesses the present state of the code, not git history.
- **At most 3 rounds** (#196). A round is one `/sdd-implement` and the `/sdd-converge` after
  it. This run's round is the number of `## Phase N: Convergence` sections already in
  tasks.md, plus one. In round 3, findings are not appended: the loop stops and escalates
  (step 7). The limit is the same for every tier. Raising it is a change to this file, decided
  by the Tech Lead, never a choice made during a run.

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec --require-plan --require-tasks --include-tasks`.
   Load `memory/constitution.md` (skip constitution checks gracefully if it is still the
   unfilled template).
2. **Intent inventory**: FR-/SC- (buildable only) / `USn/ACm` keys from the spec; plan
   decisions and named touch-points; constitution articles with buildable obligations
   (tests with `requirement()` markers, PII masking, Golden Signals, audit records, HITL route).
   Every existing task enters the inventory, whatever its checkbox state or phase: a `[X]` is a
   completion claim, not evidence (Constitution IX). For a chain of corrective tasks, assess the
   behaviour that results, not the superseded implementation details.
3. **Code-scope map** from the file paths in plan.md and tasks.md plus keyword search for each
   requirement's concepts. Do not infer scope beyond the artefacts.
4. **Assess** each inventory item against the code and classify gaps: `missing` · `partial` ·
   `contradicts` · `unrequested` (work not called for — surfaced for review, never deleted).
   Also check: every AC's named test exists and asserts the outcome; spec frontmatter
   `implemented_by`/`verified_by` filled; topics registered; abuse-case count not reduced.
5. **Severity**: CRITICAL (constitution/ADR MUST, P1 baseline blocked) · HIGH (core FR/AC
   missing or partial) · MEDIUM (secondary partial, unclear unrequested) · LOW (polish).
6. **Findings summary** (in session, before any write): table
   `ID | Gap type | Severity | Source | Evidence | Remaining work` + counts by type/severity.
7. **Append or report**:
   - findings → `## Phase N: Convergence` with ids `T{max+1:03d}…`, CRITICAL first, each line
     `- [ ] T042 <imperative> per <FR-003 | US1/AC2 | plan: … | Constitution II> (<gap-type>)`.
   - findings in round 3 → do not touch tasks.md. Emit `[HITL-ESCALATE]` (CLAUDE.md §14.2)
     with reason `implement ↔ converge has not converged after 3 rounds`, then the findings
     table from step 6 and, for each earlier round, its Convergence section's task range. A
     human decides what follows: amend the spec or plan, accept the gaps as follow-up issues,
     or authorise one more round.
   - no findings → do not touch tasks.md; print
     `✅ Converged — the implementation satisfies the spec, plan and tasks.` with the counts.
8. **Next actions**: tasks appended → run `/sdd-implement` then `/sdd-converge` again (the next round);
   escalated → stop until the human decides;
   converged → open the PR (Phase 7), fill the PR template's spec/ADR/issue references, and
   hand over to the human gates (code review, security, AI governance, PRR).

## Done when

- [ ] Findings summary printed; tasks.md either appended or unchanged
- [ ] Round counted; in round 3, findings escalated instead of appended
- [ ] No code, spec or plan modified
