<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0096 — A Bug-Fix Path That Separates Diagnosis, Repair and Verification

**Status:** Proposed
**Date:** 2026-10-31
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — delivery process; the defect rule it applies is `spec_for_defect` in `docs/process/gates/phase-gates.yaml`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0090](ADR-0090-adopt-spec-kit-workflow-primitives.md) (adopted spec-kit primitives; this adds a category), [ADR-0058](ADR-0058-agentic-spec-driven-delivery-workflow.md) (the 15 phases), [ADR-0064](ADR-0064-delivery-right-sizing-tiers.md) (tiers), [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation)

---

## Context

This corpus gives a defect a risk class (`small_bug_fix`, minimum tier TRIVIAL) and a rule for its
spec (`spec_for_defect`: a regression cites the spec it violates; unspecified behaviour gets the
missing spec section first, or a `REM-NNN`). It does not say how an agent should work a bug, and
no artefact is owed between the bug report and the pull request. In practice, the agent that
reads the report also edits the code and runs the tests in one pass:

- **The diagnosis is never reviewed before the code changes.** A wrong root cause is discovered
  in code review, after the repair has been built on it.
- **Scope grows silently.** A fix that meets a second problem tends to fix that one too, and the
  PR no longer traces to the report (CLAUDE.md §7).
- **"Tests pass" stands in for "the bug is gone."** A green suite says nothing about a bug whose
  reproduction was never run, and the existing suite is exactly what missed it.

github/spec-kit added a bundled `bug` extension in 2026 (`docs/guides/bugfix.md`,
`docs/reference/agentic-bugfix.md`) that separates the work into assess → fix → test. Each
stage writes its own record, and only the fix stage edits code. spec-kit-sync §2.5 requires an ADR
when a new _category_ of primitive is adopted. ADR-0090 §4 refuses extensions as a mechanism,
so the process is adopted here as a command, not as an extension.

## Decision

We will work every defect through **`/sdd-bugfix`**, one command with three stages, each writing
one record under `docs/bugs/BUG-{issue}/`:

| Stage    | Writes          | May edit code | Ends with                                                                   |
| -------- | --------------- | ------------- | --------------------------------------------------------------------------- |
| `assess` | `assessment.md` | No            | Reproduction, root cause with evidence, the spec it violates, a remediation |
| `fix`    | `fix.md`        | **Only this** | The change, its regression test, and every deviation from the assessment    |
| `test`   | `test.md`       | No            | `verified` · `partial` · `failed`, with the reproduction re-run             |

1. **The spec comes first, from `spec_for_defect`.** `assess` must name the approved spec the
   behaviour violates. When there is none, it stops and emits `[HITL-ESCALATE]`, because writing
   the missing spec section or choosing a `REM-NNN` is a product decision. Article I is protected,
   and this path does not waive it in any tier.
2. **A human accepts the diagnosis before any code changes.** `fix` refuses to start until the
   assessment's decision row reads `accepted`. A rejected diagnosis goes back to `assess`, not
   forward to a patch.
3. **Scope is the assessment.** Evidence that the repair needs work outside the assessed scope
   is recorded as a deviation in `fix.md`, and `fix` stops for a decision. It never widens the
   repair on its own initiative.
4. **The original reproduction decides the verdict.** `test` re-runs it and the relevant suites.
   `verified` requires the reproduction to pass. `test` never edits code to make a check pass
   (Constitution II): a failure goes back to `assess` or `fix` with its evidence.
5. **Nothing else changes.** The tier (ADR-0064) still decides which phases apply. Code review
   (Phase 7) is still a mandatory human gate, and the CLAUDE.md §14.1 escalation triggers apply to
   every stage. The command does not create branches, commits or PRs.

## Consequences

### Positive

- A wrong diagnosis is rejected before the patch is built on it.
- Reviewers get a trace from symptom to evidence: the assessment, the fix record and the test
  report, each linked from the PR.
- `small_bug_fix` gains the artefact chain it lacked, without a new tier or risk class.

### Negative / Trade-offs

- Three records for a one-line fix. The records are short by design, and a trivial bug pays a
  few minutes for the diagnosis review, which is the step this ADR adds.
- The preconditions (an approved cited spec, an accepted diagnosis) are enforced by the command's
  own procedure, not by a hook. `sdd-gate.py` gates only feature commands, whose spec it resolves
  from the feature directory. A bug's spec is named inside its assessment. A deterministic
  gate is a follow-up if the procedure turns out to be skipped in practice.
- `docs/bugs/` is a new directory that an adopting repository has to keep.

## Alternatives Considered

- **Do nothing.** It keeps the single-pass behaviour and the three failure modes above.
- **Three commands** (`/sdd-bug-assess`, `-fix`, `-test`), as upstream has them. Rejected:
  `sdd-gate.py` matches commands with `sdd-[a-z]+`, so a hyphenated name would be read as
  `sdd-bug`. One command with a stage argument also keeps the rendered command set small.
- **Adopt spec-kit's `bug` extension directly.** Rejected by ADR-0090 §4: extensions are a
  mechanism this corpus does not run.
- **Fold the stages into `/sdd-implement`.** Rejected: implement works a feature's `tasks.md`
  against a feature spec, and a bug has neither.

## Compliance & Risk

Constitution I (spec first: the cited spec, or an escalation), II (a regression test, and no test
weakened to pass), V (the diagnosis acceptance is a human decision) and IX (the root cause has to
cite evidence, not plausibility). A bug whose cause lies in a guardrail or the HITL gateway
triggers CLAUDE.md §14.1 at the `assess` stage, before any edit.
