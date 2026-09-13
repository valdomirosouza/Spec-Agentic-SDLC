# Keeping the spec-kit primitives in sync with upstream

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

> **Owner:** Tech Lead · **Cadence:** quarterly (next review in `docs/sdlc/spec-kit-upstream.json`)
> · **ADRs:** ADR-0090 (what was adopted and why), ADR-0091 (adoption script, per-agent copies)

The `/sdd-*` commands, the feature-bundle templates and the helper scripts were adapted from
[github/spec-kit](https://github.com/github/spec-kit) at the revision pinned in
`docs/sdlc/spec-kit-upstream.json`. Upstream moves fast (eight releases between 2026-08-19 and
2026-09-10); this page is the procedure that keeps the corpus deliberately, not accidentally,
behind or ahead of it.

## 1. What is tracked

`spec-kit-upstream.json` lists the upstream files whose local counterparts exist here:

| Upstream                          | Local counterpart                              | Adaptation rule                                                        |
| --------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| `templates/commands/<name>.md`    | `.claude/skills/sdd-<name>/SKILL.md`           | Same procedure shape; this repository's gates, Refs grammar and escalation are kept |
| `templates/<name>-template.md`    | `templates/<name>-template.md`                 | Section additions are considered; §7 governance, §8 Golden Signals, §9 AC table and the coverage footer never leave |
| `scripts/bash/<name>.sh`          | `scripts/bash/<name>.sh`                       | Ported to bash 3.2, SPEC-ID grammar, no git side effects              |
| `docs/reference/integrations.md`  | `scripts/python/render_commands.py`            | New agent layouts are added to the renderer, not hand-written          |
| `spec-driven.md`                  | `docs/sdlc/spec-kit-comparison.md`             | Philosophy changes are discussed in the comparison, not copied         |

Deliberately **not** tracked: extensions, presets, bundles, the workflow engine and the
`specify` CLI (ADR-0090 §4, ADR-0091).

## 2. Quarterly procedure

1. **Diff.** Run `scripts/bash/spec-kit-diff.sh` (needs `gh`). It lists the tracked files that
   changed between the pinned commit and upstream `main`, and the latest release tag. Use
   `--show <path>` for a unified diff of one file; `--ref vX.Y.Z` to compare against a release.
2. **Classify each change** with one of three verdicts and record it in the table of §3:
   - **adopt** — a pure improvement with no conflict with the constitution or an ADR (a clearer
     clarify taxonomy, a better checklist item, a new integration layout);
   - **adapt** — useful but must be reshaped (e.g. anything that makes tests optional, creates
     branches, or bypasses the approval gate is reshaped to Constitution II and V);
   - **refuse** — conflicts with a binding ADR or the constitution; write one sentence why.
3. **Apply** adopted/adapted changes as ordinary PRs against the local counterparts, one PR per
   command or template (ADR-0060: one artefact per task). Re-render the per-agent copies
   (`scripts/bash/render-commands.sh`) and run `scripts/bash/check-corpus.sh`.
4. **Re-pin.** Update `commit`, `release`, `release_date`, `compared_on` and `next_review_due`
   in `spec-kit-upstream.json`; add a `### Upstream reference` line to `CHANGELOG.md` under
   `[Unreleased]`; update the "Compared on" header of `docs/sdlc/spec-kit-comparison.md`.
5. **Amend ADR-0090** only if a *category* of primitive changes (something new adopted or something
   previously adopted removed). Wording changes inside a command do not need an ADR.

## 3. Review log

| Date       | Upstream range        | Files changed | Adopted | Adapted | Refused | PRs / notes                        |
| ---------- | --------------------- | ------------- | ------- | ------- | ------- | ---------------------------------- |
| 2026-09-12 | — → `d848fb4` (v1.0.6) | (baseline)    | 14 rows of `spec-kit-comparison.md` §2 | see §2 | ADR-0090 §4 | initial adoption, ADR-0090; `/sdd-taskstoissues` added (#10) |

## 4. What a reviewer checks before merging a sync PR

- [ ] No protected constitution article weakened (I, II, V, VII, IX); tests still mandatory in `tasks-template.md`
- [ ] Scripts still create no branch and run no git command (`check-corpus.sh` C8)
- [ ] Rendered copies regenerated (C9), example bundle still passes `check-prerequisites.sh`
- [ ] `spec-kit-upstream.json` re-pinned and `CHANGELOG.md` updated in the same PR
