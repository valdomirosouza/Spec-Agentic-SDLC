# ADR-0092 — spec-kit Command-Lifecycle Hooks vs Claude Code Hooks for the `/sdd-*` Gates

**Status:** Proposed
**Date:** 2026-09-13
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — agent-operating policy (`.claude/settings.json`, `.claude/hooks/`)
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation), [ADR-0090](ADR-0090-adopt-spec-kit-workflow-primitives.md) (primitives), [ADR-0091](ADR-0091-corpus-adoption-script-and-per-agent-skill-copies.md) (per-agent copies), [ADR-0011](ADR-0011-hitl-hotl-model.md) (HITL/HOTL)

---

## Context

spec-kit's extension system registers commands to run around its slash commands:
`hooks.before_<command>` / `hooks.after_<command>` in `.specify/extensions.yml`, each with
`enabled`, `optional` (prompt the user or run automatically), `priority` and `condition`
(spec-kit `docs/reference/extensions.md`, v1.0.6). Its `implement` command uses them, for
example, to run a checklist gate before and a validation step after implementation. ADR-0090 §4
declined the extension engine itself, so the corpus has no equivalent of these lifecycle hooks:
the gates inside `/sdd-implement` (approved spec, unchecked checklist items) and the post-run
check (`/sdd-converge`) are **prompt instructions** the agent follows, not mechanisms the
harness enforces.

Claude Code offers harness-level hooks (`code.claude.com/docs/en/hooks`, read 2026-09-13):
32 events, of which two match spec-kit's before/after shape —

- **`UserPromptSubmit`**: receives `user_prompt`; **exit 2** blocks the prompt (stderr becomes
  the message); plain-text stdout on exit 0 is added as context the agent sees. No
  `additionalContext` field on this event.
- **`Stop`**: receives `last_assistant_message` and `stop_reason`; **exit 2** prevents the agent
  from finishing and continues the conversation; `hookSpecificOutput.additionalContext` injects
  what to do next. The docs warn that a `Stop` hook must check `stop_hook_active` and not inject
  more context when it is `true`, or it creates an infinite loop.

This corpus already runs one Claude Code hook: the `PreToolUse` high-risk-action guard
(`.claude/hooks/high-risk-action-guard.py`, ADR-0034), which denies push/merge/release/deploy
for subagents and asks in the main session. spec-kit's integration code also shows Cursor
(`.cursor/hooks.json`) and Codex (`UserPromptSubmit`) exposing comparable events, so a
`UserPromptSubmit`-shaped gate is portable in principle; `Stop`-shaped continuation is not
documented for them.

Constraint: Constitution V — agents draft, analyse and recommend; humans approve. A hook that
makes the agent *keep working* without a human in the loop changes the autonomy model.

## Decision

1. **Adopt the `before_<command>` shape as a `UserPromptSubmit` hook, deterministic and
   read-only.** A script `.claude/hooks/sdd-gate.py` (to be implemented under a follow-up
   issue) inspects `user_prompt`; when it starts with `/sdd-plan`, `/sdd-tasks`,
   `/sdd-implement` or `/sdd-taskstoissues`, the hook runs
   `scripts/bash/check-prerequisites.sh --json` with the flags the command already documents and
   counts unchecked items in `checklists/*.md`. Outcome:
   - spec not `approved`/`implemented` for a code-producing command → **exit 2** with the same
     message the script prints (Constitution I becomes a harness rule, not only a prompt rule);
   - unchecked checklist items → exit 0 and print the checklist table to stdout so the agent
     sees the gate state before it starts (the prompt still asks "proceed anyway?").
   The hook never edits files and never runs git.
2. **Refuse the `after_<command>` shape as a `Stop` hook.** A `Stop` hook that blocks the end
   of the turn or injects "continue with `/sdd-converge`" would make the agent iterate without a
   human decision, which is exactly the autonomy Constitution V and ADR-0011 reserve for feature
   flags under governance review. `/sdd-converge` stays an explicitly invoked command; its
   findings are for a human to act on. At most, a `Stop` hook may emit a **`systemMessage`**
   (no `additionalContext`, no exit 2) reminding that converge has not been run — recorded here
   as permitted, not required.
3. **Scope.** This decision covers Claude Code only. The Cursor/Codex equivalents are noted
   as a portability path for the `UserPromptSubmit` gate; they are not adopted until the
   rendered-command layer (ADR-0091) has real users on those tools.
4. **Do not touch the PreToolUse guard.** The new hook is additive; `check-corpus.sh` C8
   continues to assert the guard is wired.

## Consequences

### Positive

- Constitution I ("no code without an approved spec") gains a mechanical enforcement point for
  the code-producing commands, independent of whether the model follows the prompt.
- The checklist gate becomes visible before work starts, the way spec-kit's mandatory
  `before_implement` hooks behave, without adopting the extension engine.
- No change to the autonomy model: nothing forces the agent to continue.

### Negative / Trade-offs

- A `UserPromptSubmit` hook runs on every prompt; the script must return in well under a
  second and exit 0 silently for non-`/sdd-*` prompts.
- Prompt-prefix detection is brittle (a prompt that merely *mentions* `/sdd-implement` must
  not be blocked); the hook must match only a leading command token.
- Two enforcement layers (prompt text and hook) must be kept consistent; the hook's messages
  are generated by the same script the skills call, which limits drift.

## Alternatives Considered

- **Adopt spec-kit's `.specify/extensions.yml` hook engine** — rejected (ADR-0090 §4): it
  would add a second hook system beside Claude Code's, executed by the model rather than the
  harness.
- **`Stop` hook that blocks until `/sdd-converge` reports Converged** — rejected: autonomous
  iteration without a human gate (Constitution V); loop risk documented by Claude Code itself.
- **`PreToolUse` gate on `Edit`/`Write` under `src/`** instead of `UserPromptSubmit` —
  considered and deferred: it would enforce "approved spec before code" at the file level,
  but in this documentation corpus there is no `src/`; revisit with the adopting repository.
- **Do nothing** — rejected: the gates exist only as prompt text, which the spec-kit comparison
  scored as the weakest form of enforcement.

## Compliance & Risk

- **Controls affected:** none new; strengthens LLM08 (agent action guarded) in
  `specs/security/owasp-genai-control-matrix.yaml` once implemented.
- **Data classification impact:** none — the hook reads spec frontmatter and checklist files.
- **Autonomy impact:** none by design (decision 2); any future `Stop`-based continuation
  requires its own ADR and ADR-0015 governance review.
- **Review/expiry:** revisit when the hook is implemented (follow-up issue) or when Cursor /
  Codex hook events are adopted.

---

## Related

- `.claude/hooks/README.md` — the existing PreToolUse guard
- `docs/sdlc/spec-kit-comparison.md` §4 — what was deliberately not adopted
