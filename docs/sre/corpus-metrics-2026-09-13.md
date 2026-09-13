<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Corpus metrics — 2026-09-13

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
| Commits on the default branch | 59 | git log over the full history; a day is active when it carries >= 1 commit |
| Active days | 2 (span 2 days) | — |
| Commits per active day | 29.5 | — |
| First / last commit | 2026-09-12T23:14:09 → 2026-09-13T09:57:03 | — |

**Reading it honestly.** A commit is the unit that reaches the default branch here, so
commits per active day is the deployment-frequency analogue and nothing more. The history
is short, so no trend can be claimed from it — only a baseline that a later run can compare
against.

## 2. Change quality

| Metric | Value | Method |
| --- | --- | --- |
| Completed CI runs | 43 | the last 100 workflow runs; failure rate is failed/completed; recovery is the wall-clock gap from a failed run to the next successful one |
| Failed runs | 4 | — |
| Change failure rate | 9.3% | failed ÷ completed |
| Median run duration | 26 s | — |
| Recoveries observed | 4, median 94 s | gap from a failed run to the next success |

## 3. Corpus shape

| Metric | Value |
| --- | --- |
| Markdown files | 530 |
| Markdown lines | 60019 |
| Executable lines (scripts + hooks) | 2591 |
| Test lines | 904 |
| Prose to executable ratio | 23.2 : 1 |
| Check families in `check-corpus.sh` | 11 |
| ADRs | 95 |

**Why the ratio is a metric and not trivia.** The maturity assessment named governance mass
outgrowing verification as a structural risk. Tracking the ratio makes that visible: it
should fall when verification is added and rise when documents are. A rising ratio across
two reports is the signal to stop writing and start checking.

## 4. Not measurable here, and why

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
