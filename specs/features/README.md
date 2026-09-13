<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Feature Specs

> **Owner:** Tech Lead | **Phase:** 4 (Specification) → 6 (Development)
> **ADRs:** ADR-0085 (id and status grammar), ADR-0090 (feature bundle) | **Workflow:** `docs/process/WORKFLOW.md §Phase 4`

This directory holds the machine-readable, human-approved feature specifications that bound
agent implementation, one **bundle per feature**. No code may be written for a feature without
an `approved` spec here (Constitution I; CLAUDE.md §2, §3.4).

---

## Directory layout (ADR-0090)

```text
specs/features/
└── <SPEC-ID>-<slug>/              e.g. SPEC-FEAT-002-cursor-pagination/
    ├── spec.md                    Phase 4 — /sdd-specify, /sdd-clarify   (WHAT and WHY)
    ├── checklists/
    │   ├── requirements.md        built-in spec-quality gate (agent-maintained)
    │   └── <domain>.md            reviewer-owned checklists — /sdd-checklist
    ├── plan.md                    Phase 5 — /sdd-plan                    (HOW: stack, design, Constitution Check)
    ├── research.md                Phase 5 / Phase 0 research — decisions, rationale, alternatives
    ├── data-model.md              Phase 5 / Phase 1 design — entities, validation, transitions
    ├── contracts/                 OpenAPI / AsyncAPI / Avro deltas
    ├── quickstart.md              runnable validation scenarios (one per AC)
    └── tasks.md                   Phase 6 — /sdd-tasks, executed by /sdd-implement, closed by /sdd-converge
```

- The directory name carries the spec id (`SPEC-<DOMAIN>-NNN`, ADR-0085) and a ≤ 4-word slug.
  The GitHub issue number lives in the frontmatter `issue:` field, not in the path.
- `spec.md` is created from `templates/spec-template.md` by
  `scripts/bash/create-new-feature.sh --json "<description>"` (called by `/sdd-specify`).
- `plan.md` is created from `templates/plan-template.md` by `scripts/bash/setup-plan.sh`.
- The active feature is resolved by `scripts/bash/check-prerequisites.sh` from
  `SDD_FEATURE_DIRECTORY`, `.sdd/feature.json` or the branch `feature/<SPEC-ID>-<slug>`.

## Worked examples

| Directory                                      | Status        | What it shows                                                                 |
| ---------------------------------------------- | ------------- | ----------------------------------------------------------------------------- |
| `SPEC-LGS-001-log-based-golden-signals/`       | `draft`       | Full bundle: spec, plan, research, data-model, contracts, quickstart, tasks; two checklist items deliberately left to the DPO and Security Lead |
| `SPEC-FEAT-001-http-golden-signals/`           | `implemented` | Spec-only, small, back-filled from a delivered feature (legacy section numbering) |

`SPEC-LGS-001-golden-signals-feature-spec.md` (flat file) is `superseded` by the bundle and kept
for history.

## Spec lifecycle (ADR-0085)

```text
draft → in-review (Spec-as-PR open) → approved (PR merged) → implemented → superseded
```

Same five lower-case values as every other spec, in the frontmatter `status:` field. Only a
human sets `approved` (Tech Lead + Security Lead review, `docs/process/HITL-GOVERNANCE.md`);
`check-prerequisites.sh --require-approved` refuses anything else before Phase 6.

## Creating a new feature spec

```bash
scripts/bash/create-new-feature.sh --json "Add cursor pagination to the requests list"
# → {"SPEC_ID":"SPEC-FEAT-002","FEATURE_DIR":".../specs/features/SPEC-FEAT-002-cursor-pagination-requests-list", ...}
```

Or run `/sdd-specify <description>` in Claude Code, which calls the script and fills the spec.
Add `--domain <CODE>` for a non-FEAT domain and `--issue <N>` when the GitHub issue exists. The
script never creates a git branch; create `feature/<SPEC-ID>-<slug>` yourself.

## Review requirements

| Reviewer      | Required when                                                                              |
| ------------- | ------------------------------------------------------------------------------------------ |
| Tech Lead     | Always                                                                                     |
| Security Lead | New PII processing, new attack surface, or anything touching guardrails / the HITL gateway |
| Product Owner | User stories and acceptance criteria (spec §2, §9)                                         |
| DPO           | DPIA/RIPD decision (spec §7, checklist CHK on privacy)                                     |

In the adopting repository the `feature-spec-lint` gate (`harness/doc-check.yml`) verifies that
the SPEC-ID named in the PR body has a `spec.md`, that every ADR it cites exists, and that a spec
touching `src/agents/` declares its allowed action types.

## Superseding a spec

Never delete. Set `status: superseded` and `superseded_by: <path>` in the old file's frontmatter,
add a banner pointing to the replacement, and keep the old id out of new directories
(`create-new-feature.sh` scans frontmatter ids when numbering).

## Related

- Templates: `templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`
- Legacy template (section numbering used by SPEC-FEAT-001): `.github/FEATURE_SPEC_TEMPLATE.md`
- Discovery artefacts: `docs/product/FEAT-{issue}/` (keyed by issue; unchanged)
- Lifecycle skill: `skills/sdlc/spec-lifecycle.md` · Commands: `.claude/skills/sdd-*/SKILL.md`
- Comparison with spec-kit: `docs/sdlc/spec-kit-comparison.md`
