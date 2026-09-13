# Audit & Governance

> **Owner:** Tech Lead + Security Lead (internal controls) · **Status:** Living · **Last updated:** 2026-09-12
> This directory is the entry point for an **external auditor** (Big Four — PwC, Deloitte, EY,
> KPMG — or an internal-audit function) and for the engineers who have to answer them. It does
> not add new controls; it indexes the ones that already exist across `docs/`, `specs/` and
> `.claude/` and states, for each typical evidence request, exactly which artefact answers it.

| Document                                               | Purpose                                                                                                                                                            |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`big-four-evidence-map.md`](big-four-evidence-map.md) | SOX ITGC, SOC 2 TSC, ISO 27001 Annex A and LGPD/GDPR evidence requests → the artefact, gate or record that satisfies each, with the retention period and the owner |

## How the chain is walked

Every change in a repository that adopts this corpus can be traced without asking anyone:

```text
GitHub Issue ──► spec (SPEC-<DOMAIN>-NNN, status approved) ──► ADR(s) ──► commit (Refs: #issue, SPEC-…, ADR-…)
      ──► tests (requirement("SPEC-…/FR-NN")) ──► CI gates (harness/, pr-governance) ──► PR (≥ 1 human approval)
      ──► change-log record (docs/change-log/YYYY-MM-DD.yaml) ──► release evidence package (11 items) ──► DORA event
```

The identifiers that make the chain machine-checkable are defined in `docs/governance/spec-registry.md`
(spec ids), `docs/adr/README.md` (ADR ids), `docs/change-log/SCHEMA.md` (deploy records) and
`docs/governance/release-evidence-package.md` (release index). Constitution VII makes the chain
binding; `/sdd-converge` and the governance gates verify it before a PR is opened.

## Related

- `docs/governance/traceability-matrix.md` — service → spec/ADR/SLO/runbook/test matrix
- `docs/governance/release-evidence-package.md` — what every production release must produce
- `docs/compliance/` — ISO 27001 Annex A matrix, SOC 2 TSC mapping, SLSA assessment, remediation register
- `docs/sox/` and `specs/compliance/sox-controls.md` — SOX ITGC controls CC1–CC7 (SEC-listed organisations only)
- `docs/privacy/` — PII inventory, data-processing register (RoPA), DPIA/RIPD, retention policy
