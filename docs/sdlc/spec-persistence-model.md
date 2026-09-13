# Spec persistence model

> Adopted from spec-kit's _Spec Persistence Models_ concept (flow-back / flow-forward / living
> spec), made explicit here because auditability (Constitution VII) decides the answer.

## Decision

This repository uses **flow-forward for history** and **living spec for the contract**:

1. **`spec.md` is the contract.** When requirements change, the spec changes first; `plan.md`
   and `tasks.md` are regenerated or revised from it (`/sdd-plan`, `/sdd-tasks`). Rationale that
   would be lost by regeneration is preserved in `research.md` and in ADRs.
2. **Completed feature directories are historical records.** A change that alters an
   `implemented` spec's intent creates a **new** spec (new `SPEC-ID`) whose frontmatter points
   at the old one through `related_specs`; the old spec moves to `status: superseded` with a
   pointer forward. Nothing is deleted (see `skills/sdlc/spec-lifecycle.md`, "move, never
   delete"; `specs/deprecated/`).
3. **Small corrections** (typos, a clarified threshold, an added edge case) edit the spec in place
   with a `## Clarifications` session entry and a `last_updated` bump; they do not create a new id.

## Why

| Model                                               | Fit here                 | Reason                                                                               |
| --------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------ |
| Flow-back (edit any artefact, reconcile later)      | rejected                 | silent drift breaks the FR → AC → test chain auditors walk                           |
| Flow-forward (new directory per requirement change) | adopted for history      | ISO 27001 / SOX evidence needs the state of the contract at release time             |
| Living spec (spec first, regenerate the rest)       | adopted for the contract | the registry, gates and `requirement()` markers key on the spec id and its FR/AC ids |

## Rules the commands enforce

- `/sdd-implement` and `/sdd-tasks` refuse a spec that is not `approved` / `implemented`.
- `/sdd-converge` never edits `spec.md`; a gap that turns out to be a requirement change goes
  back to `/sdd-clarify` (in place) or to a new spec (superseding).
- The FR/AC identifiers of an `implemented` spec are **immutable**; a removed requirement is
  struck through and marked superseded, never renumbered.
