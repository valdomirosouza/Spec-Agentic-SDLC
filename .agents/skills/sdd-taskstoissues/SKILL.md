---
name: sdd-taskstoissues
description: Create one GitHub issue per open task in the active feature's tasks.md, titled "<SPEC-ID> T010: …", with phase, story, Refs and bundle links in the body, and write the issue number back into tasks.md; skips [X] tasks and tasks that already have an issue; refuses a spec that is not approved. Trigger on "tasks to issues", "open issues for the tasks", "create issues from tasks.md". Usage — /sdd-taskstoissues [--dry-run] [--label <name>] [--assignee <login>] [--limit N].
---

<!-- generated from .claude/skills/sdd-taskstoissues/SKILL.md by scripts/python/render_commands.py — edit the source, then re-render (ADR-0091) -->

# /sdd-taskstoissues — tasks.md → GitHub issues

Adapted from spec-kit `/speckit.taskstoissues`. Differences: uses the `gh` CLI (no GitHub MCP
server), only runs against an `approved`/`implemented` spec (Constitution I), keeps the
repository's `Refs:` grammar (CLAUDE.md §6), and records the issue number on the task line so
`/sdd-implement` and `/sdd-converge` can cite it.

## User input

```text
$ARGUMENTS
```

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks`
   → `FEATURE_DIR`, `SPEC_ID`, `SPEC_STATUS`. Load `memory/constitution.md`.
2. **Preview first**: run `scripts/bash/tasks-to-issues.sh --dry-run` and show the user the
   table of issues it would create (task id, title, phase) and the counts of tasks skipped
   because they are `[X]` or already carry `(#N)`.
3. **Gate**: a spec that is not `approved`/`implemented` stops here — issues for unapproved work
   are premature (Constitution I). Report and suggest the Spec-as-PR.
4. **Confirm scope** with the user when the arguments do not already say: which labels
   (existing repository labels only — the script never creates labels), an assignee, a `--limit`
   for a first batch. Creating issues is an outward-facing action: ask before the real run
   unless the user's input explicitly says to proceed.
5. **Create**: `scripts/bash/tasks-to-issues.sh [--label …] [--assignee …] [--limit N]`. The script
   - resolves the repository from `git remote origin` (must be GitHub);
   - deduplicates against open **and** closed issues whose title contains the task id;
   - titles issues `<SPEC-ID> T010: <description>`; the body carries phase, story, `Refs:` ids,
     parallel flag, links to `spec.md`/`tasks.md`, and a "Done when" checklist;
   - appends `(#N)` to the task line in `tasks.md`.
6. **Order and dependencies**: issues are created in tasks.md order (Setup → Foundational →
   stories → Polish). Dependencies are stated in the body text ("depends on T012"); GitHub
   sub-issues or a project board are the adopting repository's choice — say so in the report.
7. **Never**: create issues for `[X]` tasks, rename or renumber tasks, or edit anything in
   `tasks.md` other than appending `(#N)`.

## Completion report

Repository, spec id and status, issues created (id → #number), skipped (done / existing),
labels applied, and the next command (`/sdd-implement`, citing the issue numbers in commit
trailers `Refs: #N, <SPEC-ID>, ADR-NNNN`).

## Done when

- [ ] Every open task without an issue has one, or the run was an explicit `--dry-run`
- [ ] `tasks.md` carries `(#N)` on each created task; nothing else changed
- [ ] No issue created for an unapproved spec
