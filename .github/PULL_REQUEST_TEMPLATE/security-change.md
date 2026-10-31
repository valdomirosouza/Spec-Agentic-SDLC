<!-- Security change / vulnerability remediation. ?template=security-change.md -->

## Summary

<!-- What security issue this addresses and how. -->

## Linked issue / spec

Closes #
Threat model: `specs/security/threat-model.md`

## AI assistance

<!-- Disclose any AI involvement (CONTRIBUTING.md §5 "AI assistance", Constitution VII). Disclosure
     is provenance, not a lower bar: the same evidence and review apply. -->

- [ ] No AI tool was used for this change
- **Tool / agent:** <!-- e.g. Claude Code, GitHub Copilot, Cursor; or a delivery subagent from .claude/agents/ -->
- **Model and mode:** <!-- the model id and the mode or settings that shaped the output (plan mode, auto-accept, autonomy tier) -->
- **Extent:** <!-- what the agent drafted (code, tests, docs, PR text) and what a human wrote, rewrote or verified -->

## STRIDE category

- [ ] Spoofing · [ ] Tampering · [ ] Repudiation · [ ] Info disclosure · [ ] DoS · [ ] Elevation

## Finding reference

CVE / advisory / scanner finding: <!-- e.g. CVE-2026-xxxxx, Trivy/Bandit ID -->

## Remediation evidence

- [ ] Fix verified locally; before/after evidence in PR
- [ ] SAST rerun clean (`bandit` / `gosec` / `SpotBugs`)
- [ ] SCA rerun clean (`pip-audit` / OWASP dep-check)
- [ ] No new CRITICAL/HIGH findings (or documented risk acceptance)

## Rollback plan

<!-- How to revert safely if this regresses. -->

## Review

- [ ] Security Lead review requested
- [ ] `CHANGELOG.md` updated; no secrets/PII added
