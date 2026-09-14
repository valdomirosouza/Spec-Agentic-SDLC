<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Corpus metrics — 2026-09-14

> **Generated** by `scripts/python/corpus_metrics.py --report`. Every number below is
> measured from this repository's git history or its GitHub Actions runs, and every metric
> names its method. Nothing here is estimated: the metrics this repository cannot produce
> are listed in §4 with the reason, rather than filled in with a guess (Constitution IX).

This is the first measurement the corpus has ever taken of itself. It exists because the
maturity assessment of 2026-09-13 found every dimension stopping at *defined, never
measured*, and one data point is what separates the two.

## 1. Delivery

| Metric | Value | Method |
| --- | --- | --- |
| Commits on the default branch | 103 | git log over the full history; a day is active when it carries >= 1 commit |
| Active days | 3 (span 3 days) | — |
| Commits per active day | 34.33 | — |
| First / last commit | 2026-09-12T23:14:09 → 2026-09-14T07:53:43 | — |

**Reading it honestly.** A commit is the unit that reaches the default branch here, so
commits per active day is the deployment-frequency analogue and nothing more. The history
is short, so no trend can be claimed from it — only a baseline that a later run can compare
against.

## 2. Change quality

| Metric | Value | Method |
| --- | --- | --- |
| Completed CI runs | 54 | the last 100 workflow runs; failure rate is failed/completed; recovery is the wall-clock gap from a failed run to the next successful one |
| Failed runs | 4 | — |
| Change failure rate | 7.4% | failed ÷ completed |
| Median run duration | 27 s | — |
| Recoveries observed | 4, median 94 s | gap from a failed run to the next success |

## 3. Corpus shape

| Metric | Value |
| --- | --- |
| Markdown files | 533 |
| Markdown lines | 60609 |
| Executable lines (scripts + hooks) | 4607 |
| Test lines | 2546 |
| Verification lines (scripts + hooks + tests) | 7153 |
| Prose to verification ratio | 8.5 : 1 |
| Check families in `check-corpus.sh` | 15 |
| ADRs | 95 |

### What the periodic comparison can see

`--drift` reports a row when it moves by **1.0%** or more against a
baseline at least **7 days** old. A percentage means different
things on a count of 15 and a count of 4776, so the smallest visible move is published here
rather than left for the reader to work out. The threshold was previously 2%, chosen without
computing this table, and at 2% a newly added ADR was invisible (R6-T1).

| Metric | Value | Smallest move this threshold can see |
| --- | ---: | ---: |
| Markdown files | 533 | 5 |
| Executable lines (scripts + hooks) | 4607 | 46 |
| Test lines | 2546 | 25 |
| Verification lines (scripts + hooks + tests) | 7153 | 72 |
| Check families in `check-corpus.sh` | 15 | 1 |
| ADRs | 95 | 1 |

**Why the ratio is a metric and not trivia.** The maturity assessment named governance mass
outgrowing verification as a structural risk. Tracking the ratio makes that visible: it
should fall when verification is added and rise when documents are. A rising ratio across
two reports is the signal to stop writing and start checking.

## 4. Productivity — measured, and why there is no ratio

| Metric | Value | Method |
| --- | --- | --- |
| Commits on the default branch | 103 | wall-clock from the first to the last commit on the default branch; this is elapsed time, not effort, and includes every pause |
| Elapsed wall-clock | 32.7 h | first commit to last |
| Commits per elapsed hour | 3.2 | — |
| Cumulative diff | 467 files changed, 18384 insertions(+), 1530 deletions(-) | `git diff --shortstat` from the first commit |

**There is deliberately no speedup ratio here.** The corpus previously published a
withdrawn claim of ≈160× faster, by dividing a measured agent wall-clock by a sum of
t-shirt estimates — a confident figure nobody observed, which Constitution IX forbids.
That claim was
withdrawn (issue #55) and the instruction that generated it was removed from the
`/deliver` skill, because correcting the output while leaving the generator would have
produced the same claim on the next run.

*No human baseline exists for this work, so no speedup is computed. Elapsed time also is not effort: a figure that ignores pauses and review would overstate throughput in the other direction.*

**What a legitimate ratio would require**, none of which exists yet:

1. A **baseline**: the same scope delivered without agent assistance, timed, by a
   comparable team — not estimated from t-shirt sizes after the fact.
2. **Effort, not elapsed time**, on both sides, counted the same way.
3. A **defined scope boundary**: drafting artefacts and writing production code are
   different work, and the previous claim mixed them.
4. **More than one sample**, since a single run measures the run, not the method.

Until those exist, this section reports what was produced and stops.

## 5. Not measurable here, and why

| Metric | Why not |
| --- | --- |
| Lead time for changes (commit → production) | no production deployment exists; the corpus ships no runtime |
| MTTR for a production incident | no production incident has occurred; CI recovery is reported instead and is not the same thing |
| Evaluator score, groundedness, guardrail intervention rate | requires a running agent with a model; none runs here (post-market plan §2) |
| Approval latency and override rate | requires the HITL gateway of an adopting product repository |
| Time-to-spec and agent rework rate | not instrumented; would need per-command timing the skills do not yet emit |

Listing these is the point of the section. A metrics report that silently omits what it
cannot measure reads as complete; this one reads as partial, which is what it is.

## Related

- [`../../specs/compliance/ai-post-market-monitoring.md`](../../specs/compliance/ai-post-market-monitoring.md) — the cycle this feeds
- [`../../specs/observability/agent-performance.md`](../../specs/observability/agent-performance.md) — the agent metrics awaiting a runtime
- [`../../specs/observability/dora-metrics.md`](../../specs/observability/dora-metrics.md) — the DORA definitions this approximates for a corpus
