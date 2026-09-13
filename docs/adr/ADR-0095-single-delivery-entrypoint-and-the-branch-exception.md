<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0095 — One Delivery Entrypoint, and the One Version-Control Exception Agents May Take

**Status:** Accepted
**Date:** 2026-09-13
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** `docs/sdlc/agent-handoff-schema.md` · `docs/process/WORKFLOW.md`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0058](ADR-0058-agentic-spec-driven-delivery-workflow.md) (the 15 phases), [ADR-0064](ADR-0064-delivery-right-sizing-tiers.md) (tiers), [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation), [ADR-0011](ADR-0011-hitl-hotl-model.md) (HITL/HOTL)

---

## Context

Two problems surfaced in the maturity assessment of 2026-09-13, and they turn out to be the same
problem seen from two sides.

**First, the delivery-agent layer did not run.** The orchestrator and all fifteen phase agents call
`scripts/asdd_state.py` and `scripts/vcs.sh`. Neither existed, neither was declared adopter-provided,
and thirty files referenced them. A team following `.claude/agents/README.md` failed at step 2, and
the handoff mechanism that README calls authoritative had never executed once.

**Second, a reader could not tell which entrypoint to use.** `.claude/agents/README.md` recommends
`asdd-orchestrator` "for actual delivery"; `SETUP.md` points at `/deliver`. The two were described
as if they competed. They do not compete on the whole surface — `asdd-orchestrator` drives real
issues and pull requests, `/deliver` is a governed simulation — but `/deliver` also has a `code`
mode that writes into the working tree, and that mode does overlap. On top of it, the two describe
phase-skipping with different words: risk class in one, tier in the other.

Implementing the two missing scripts forced a third question. `create-new-feature.sh` deliberately
refuses to create a git branch, on the grounds that it is a human decision, and the check-corpus
invariant C8 pinned that as "no script checks out, switches, pushes, merges or commits". But the
phase agents are specified to work on a short-lived feature branch, and `vcs.sh` is the script that
would create it. Either the agents' specified workflow is wrong, or the invariant is drawn in the
wrong place.

## Decision

### 1. `asdd-orchestrator` is the delivery entrypoint; `/deliver` is the assessment entrypoint

| Entrypoint          | Use it for                                                                 | Side effects                                   |
| ------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------ |
| `asdd-orchestrator` | Driving a feature through the 15 phases with real issues, branches and PRs   | Real, bounded by §3 and by the human gates      |
| `/deliver dry-run`  | Rehearsing a spec through the phases to find gaps before committing to it    | None                                            |
| `/deliver code`     | A single spec in a repository not driving the full lifecycle                 | Writes to the working tree; stops at every gate |

`/deliver code` is **not** a second delivery path for a team that has adopted the lifecycle. Where
the lifecycle is in use, the orchestrator owns delivery and `/deliver` owns rehearsal and
measurement. `SETUP.md` and `.claude/agents/README.md` say exactly this, in the same words.

### 2. Risk class and tier compose; they are not alternatives

ADR-0064 §164 already settles it: the risk class is the Phase 0 **input** and the tier is the
**process scope** it maps to — `small-fix` maps to `TRIVIAL`/`STANDARD`, `ai` and `security` force
`REGULATED`. What was missing is that the orchestrator and `/deliver` each used only one of the two
words, which read as two models. Both now state the composition, and `phase-gates.yaml` remains the
machine-readable arbiter of what a tier actually skips.

### 3. Agents may create a local feature branch, and nothing else

The invariant is redrawn, not relaxed. Two rules replace one:

- **Absolute:** no script in the corpus runs `git push`, `merge`, `commit`, `rebase`, `reset` or
  `switch`. These are outward or irreversible. C8 asserts it with no exceptions.
- **One named exception:** `scripts/bash/vcs.sh` may run `git checkout -b` to create a **local
  feature branch**, and only after `guard_branch_name` has rejected the default branch and every
  protected name. C8 asserts that no other script does it and that the guard is still there.

The line is drawn at **outward effect**. A local branch changes nothing outside the working tree
and can be deleted without trace; a push, a merge, a release and a deploy cannot. Constitution V
routes actions "with a real-world effect" through a human, and a local branch has none. Leaving
branch creation to a human while asking agents to work on a branch was not a stricter rule, it was
an unimplementable one.

`vcs.sh` enforces the same line at its own boundary rather than trusting the caller: `pr merge`,
`release create`, any deploy verb, pushing, and operating on a protected branch each exit 3 with a
message naming Constitution V. It is an allow-list, not a `gh` passthrough, because a passthrough
would hand agents exactly the verbs the PreToolUse guard exists to deny.

### 4. `asdd_state.py` implements an existing specification and touches no version control

`docs/sdlc/agent-handoff-schema.md` already specified the state object, the handoff message, the
fail-closed validation rules and the command surface. The implementation follows it and adds
nothing: validation on every write, an atomic replace so a crash cannot leave a half-written state,
exit code 2 on a blocked handoff so the orchestrator halts rather than advances, and a refusal to
append to a blocked pipeline without an explicit override. C8 asserts that it references neither
git nor gh — state and version control stay separate on purpose.

## Consequences

### Positive

- The delivery layer runs. `asdd-orchestrator` can complete step 1, and every phase handoff is
  recorded and validated against the schema that described it.
- The version-control boundary is enforced in code at the one place agents touch it, instead of
  being asserted in prose in 13 files.
- A reader has one answer to "which command do I run", and one model for phase skipping.

### Negative / Trade-offs

- C8 is now two assertions instead of one, and the exception must be re-justified whenever it is
  touched. That is the intended cost of naming an exception rather than widening a rule.
- `vcs.sh` is an allow-list, so a legitimate `gh` verb the agents later need must be added
  deliberately. Friction is the point.
- `/deliver code` and the orchestrator still overlap for a single-spec change. The rule above
  resolves which to use; it does not remove the overlap.

## Alternatives Considered

- **Declare the two scripts adopter-provided.** Rejected: thirty files would describe a workflow the
  adopter must reconstruct from nothing, and the handoff schema would remain a specification with no
  implementation anywhere.
- **Keep branch creation human and remove `vcs.sh branch create`.** Rejected: the phase agents are
  specified to work on a short-lived branch, so the rule would be violated at the first real run —
  and a rule violated at first use is worse than no rule.
- **Make `vcs.sh` a thin `gh` wrapper.** Rejected: it would be the one bypass around the PreToolUse
  guard, reachable by any subagent with Bash.
- **Retire one of the two entrypoints.** Rejected: rehearsal without side effects and delivery with
  them are genuinely different jobs, and the dry-run is what produced the findings that led here.

## Compliance & Risk

- **Controls affected:** extends C8 by one assertion; adds the `vcs.sh` refusal list as a checked
  invariant. Strengthens the enforcement of Constitution V from prose to code.
- **Data classification impact:** none. Delivery state is operational metadata, gitignored.
- **Autonomy impact:** none granted. The set of actions an agent may take is unchanged; what changes
  is that the boundary is now enforced by a script rather than assumed.
- **Review/expiry:** revisit when a phase agent needs a version-control verb the allow-list omits.

---

## Related

- `docs/sdlc/agent-handoff-schema.md` — the specification `asdd_state.py` implements
- `.claude/agents/README.md` — the entrypoint table this ADR fixes
- `.claude/hooks/README.md` — the PreToolUse guard `vcs.sh` reinforces
