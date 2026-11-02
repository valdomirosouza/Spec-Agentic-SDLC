<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

<!-- Infrastructure / pipeline / deploy change. ?template=infrastructure-change.md -->

## Summary

<!-- What infrastructure changed and why. -->

## Linked issue / RFC

Closes #
RFC: <!-- RFC-NNNN (required for Normal/Emergency changes) -->

## AI assistance

<!-- Disclose any AI involvement (CONTRIBUTING.md §5 "AI assistance", Constitution VII). Disclosure
     is provenance, not a lower bar: the same evidence and review apply. -->

- [ ] No AI tool was used for this change
- **Tool / agent:** <!-- e.g. Claude Code, GitHub Copilot, Cursor; or a delivery subagent from .claude/agents/ -->
- **Model and mode:** <!-- the model id and the mode or settings that shaped the output (plan mode, auto-accept, autonomy tier) -->
- **Extent:** <!-- what the agent drafted (code, tests, docs, PR text) and what a human wrote, rewrote or verified -->

## Change classification (ISO 27001)

- [ ] Standard · [ ] Normal (CAB-approved) · [ ] Emergency (retroactive RFC ≤ 24h)

## Canary / rollback plan

- [ ] Canary path documented (5% → 25% → 100%) with SLO gate
- [ ] Rollback tested in staging (`make rollback`); within MTTR target

## Cost impact

<!-- Expected change to infra/cloud cost, if any. -->

## Scans

- [ ] IaC scan (Checkov) passed on `infrastructure/` changes
- [ ] Container scan (Trivy) clean — zero CRITICAL CVEs (if images changed)

## Approvals

- [ ] CAB approval recorded (Normal/Emergency) — RFC_ID in merge commit
- [ ] DevOps Lead review requested
- [ ] `CHANGELOG.md` updated
