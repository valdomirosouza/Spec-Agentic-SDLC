<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Monitoring note — 2026-09-13 (first cycle)

> The cycle defined in
> [`../../../specs/compliance/ai-post-market-monitoring.md`](../../../specs/compliance/ai-post-market-monitoring.md),
> executed for the first time. That plan's own open item 2 said it had never been executed; this
> note closes it.
> **Owner:** SRE Lead · **Co-owner:** AI Governance Lead · **Cadence:** weekly, scheduled in
> [`.github/workflows/corpus-measure.yml`](../../../.github/workflows/corpus-measure.yml)

## What this cycle could observe

The plan monitors four signal families. Three of them need a running agent, a model and a HITL
gateway, none of which exist in a documentation corpus. Rather than record four families as
"no data", this note states which are observable **here** and which belong to the adopting
repository's first cycle.

| Family                    | Observable here?                       | Why                                                                  |
| ------------------------- | -------------------------------------- | ---------------------------------------------------------------------- |
| Behavioural conformity    | **No**                                 | Needs evaluator and groundedness scores from a running agent          |
| Guardrail effectiveness   | **Partly** — the two hooks, not the runtime guardrails | The PreToolUse guard and sdd-gate run here; `src/guardrails/` does not |
| Human-oversight health    | **No**                                 | Needs the HITL gateway of an adopting product repository              |
| Model conformity          | **No**                                 | No model is called from this repository                               |
| _Corpus integrity_ (added) | **Yes**                               | The checks, the generated artefacts and the CI history are the signal this repository actually has |

## Observations

**Corpus integrity.** 15 check families run on every push. All green at the time of this note.
Two generated artefacts are now byte-compared against their source rather than trusted: the spec
registry (C13) and the per-agent command copies (C9). Before this week the registry had drifted to
50 of 58 entries with nothing noticing, which is the failure this signal exists to catch.

**Guardrail effectiveness.** The first red-team exercise (RT-2026-09-13) ran twelve attempts
against the two live hooks and found one real bypass: command substitution resolving to a binary
evaded the high-risk guard, so a subagent could have pushed. Fixed, and all twelve attempts are now
regression tests. Two low findings were accepted with reasons rather than fixed.

**Change quality.** Across 45 completed CI runs the change failure rate is 8.9%. Every
failure was caught by the corpus check before reaching the default branch in a broken state, and
each was followed by a green run. Full numbers: [`../corpus-metrics-2026-09-13.md`](../corpus-metrics-2026-09-13.md).

**Data quality.** Fourteen rules now run over the corpus's own datasets. One open major finding:
a spec marked `implemented` with nothing named in `verified_by`. Reported on every run until closed.

## Threshold review

The plan's §3 thresholds are written for runtime signals and none could be evaluated. No threshold
is changed on the basis of a cycle that could not test it. What this cycle does change: the plan's
§2 gains corpus integrity as a fifth family for repositories with no runtime, so a corpus-only
adoption has something real to monitor rather than four empty rows.

## Decisions

1. **Cadence is now scheduled, not described.** It was written here as "monthly" and nothing
   anywhere fired: five assessment rounds produced exactly one data point per control, which is a
   snapshot, not a trend. `corpus-measure.yml` runs the measurement every Monday, compares the
   structural numbers against the last published report, and opens an issue when one moves by 2%
   or more. Weekly rather than monthly because the comparison is cheap and a month is long enough
   for the reason a number moved to be forgotten. Three of five families stay unobservable here
   until an adopting repository runs the agents; that is unchanged and honest.
2. **No threshold changed**, for the reason above.
3. **One item carried forward:** the open `DQ-REG-006` finding, owner Tech Lead.

## Next cycle

The next measurement fires on its own, on the first Monday after this note. It compares this
note's numbers rather than starting from nothing, which is the whole point of having taken a first
measurement: the prose-to-verification ratio, the executable-line count and the check-family count
become a trend the second time they are taken. The workflow measures and files; it does not commit
(Constitution V), so landing each report stays a human act.

A thing worth stating plainly, because five rounds of this work argue for it: **scheduling the
repetition is the only change in this wave that moves the maturity position.** Everything else
corrected defects in checks that already existed. A control with one observation is declared, not
measured, however well it is written.

> **Numbers in this note are derived from [`../corpus-metrics-2026-09-13.md`](../corpus-metrics-2026-09-13.md), not retyped.** The first version restated them by hand and drifted from its own source within a day (43 versus 44 runs, 9.3% versus 9.1%, fifteen families versus twelve). Regenerate with `scripts/python/corpus_metrics.py --json` before editing.
