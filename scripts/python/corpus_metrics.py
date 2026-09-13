#!/usr/bin/env python3
"""Measure this corpus from its own git history and CI runs (issue #52).

The maturity assessment found every dimension stopping at "defined, never measured": zero DORA
reports, zero monitoring cycles, and a published speedup ratio whose denominator was an estimate.
This computes the numbers that CAN be measured here, and says plainly which cannot.

  --report        write docs/sre/corpus-metrics-<date>.md
  --json          print the measurements
  --quiet         only the summary line

Every metric names its source and its method. Nothing is estimated: a value that cannot be derived
from git or the GitHub API is reported as unavailable with the reason, never as a guess
(Constitution IX).
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def sh(*args, default=""):
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT, timeout=90)
        return r.stdout.strip() if r.returncode == 0 else default
    except Exception:
        return default


def git_metrics():
    log = sh("git", "log", "--format=%H|%ad|%s", "--date=iso-strict")
    commits = [l.split("|", 2) for l in log.split("\n") if l]
    dates = sorted(datetime.fromisoformat(c[1]) for c in commits)
    days = sorted({d.date().isoformat() for d in dates})
    # Calendar span, not elapsed 24h periods: two commits 10 hours apart across midnight are
    # two active days in a one-day span, which made active_days exceed span_days.
    span_days = (dates[-1].date() - dates[0].date()).days + 1 if dates else 0
    types = Counter()
    for _, _, subject in commits:
        t = subject.split("(")[0].split(":")[0].strip()
        types[t if t and t.isalpha() else "other"] += 1
    return {
        "commits": len(commits),
        "active_days": len(days),
        "span_days": span_days,
        "first_commit": dates[0].isoformat() if dates else None,
        "last_commit": dates[-1].isoformat() if dates else None,
        "commits_per_active_day": round(len(commits) / len(days), 2) if days else 0,
        "conventional_types": dict(types.most_common()),
        "method": "git log over the full history; a day is active when it carries >= 1 commit",
    }


def ci_metrics():
    """Deployment-frequency and change-failure analogues. In a documentation corpus the unit that
    reaches main is a commit, and the gate that can reject it is the corpus-check workflow."""
    raw = sh("gh", "run", "list", "--limit", "100", "--json",
             "conclusion,status,headSha,createdAt,updatedAt,workflowName")
    if not raw:
        return {"available": False,
                "reason": "gh CLI unavailable or unauthenticated; CI history not readable"}
    try:
        runs = json.loads(raw)
    except json.JSONDecodeError:
        return {"available": False, "reason": "gh returned unparseable JSON"}
    done = [r for r in runs if r.get("status") == "completed"]
    fails = [r for r in done if r.get("conclusion") == "failure"]
    durations = []
    for r in done:
        try:
            a = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
            b = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
            durations.append((b - a).total_seconds())
        except Exception:
            pass
    # Recovery: for each failure, the time until the next completed success.
    ordered = sorted(done, key=lambda r: r["createdAt"])
    recoveries = []
    for i, r in enumerate(ordered):
        if r.get("conclusion") != "failure":
            continue
        for later in ordered[i + 1:]:
            if later.get("conclusion") == "success":
                try:
                    a = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
                    b = datetime.fromisoformat(later["updatedAt"].replace("Z", "+00:00"))
                    recoveries.append((b - a).total_seconds())
                except Exception:
                    pass
                break
    return {
        "available": True,
        "runs_completed": len(done),
        "failures": len(fails),
        "change_failure_rate_pct": round(100 * len(fails) / len(done), 1) if done else None,
        "median_duration_s": round(sorted(durations)[len(durations) // 2]) if durations else None,
        "recoveries_observed": len(recoveries),
        "median_recovery_s": round(sorted(recoveries)[len(recoveries) // 2]) if recoveries else None,
        "method": ("the last 100 workflow runs; failure rate is failed/completed; recovery is the "
                   "wall-clock gap from a failed run to the next successful one"),
    }


def corpus_metrics():
    md_files = md_lines = 0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in (".git", ".serena", ".sdd", "node_modules", ".agent")]
        for f in files:
            if f.endswith(".md"):
                md_files += 1
                try:
                    md_lines += sum(1 for _ in open(os.path.join(d, f), encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    def count_lines(patterns):
        n = 0
        for pat in patterns:
            base = os.path.join(ROOT, pat)
            if os.path.isdir(base):
                for d, _, files in os.walk(base):
                    for f in files:
                        if f.endswith((".sh", ".py")):
                            n += sum(1 for _ in open(os.path.join(d, f), encoding="utf-8", errors="replace"))
        return n
    exec_lines = count_lines(["scripts", ".claude/hooks"])
    test_lines = count_lines(["tests"])
    checks = sh("grep", "-c", "^say \"C", os.path.join(ROOT, "scripts", "bash", "check-corpus.sh"), default="0")
    return {
        "markdown_files": md_files,
        "markdown_lines": md_lines,
        "executable_lines": exec_lines,
        "test_lines": test_lines,
        "prose_to_code_ratio": round(md_lines / exec_lines, 1) if exec_lines else None,
        "check_families": int(checks or 0),
        "adrs": len([f for f in os.listdir(os.path.join(ROOT, "docs", "adr"))
                     if f.startswith("ADR-") and f[4:8].isdigit()]),
        "method": "file walk excluding .git, .serena, .sdd, .agent and node_modules",
    }


def session_throughput():
    """What an agent-assisted session actually produced, measured — with no comparison attached.

    The corpus previously published "≈160× faster" by dividing a measured wall-clock by a sum of
    t-shirt estimates. This reports only the measured side. A ratio needs a baseline nobody has
    collected, and §Productivity of the report says what collecting one would require.
    """
    log = sh("git", "log", "--format=%H|%ad", "--date=iso-strict")
    rows = [l.split("|") for l in log.split("\n") if l]
    if not rows:
        return {"available": False, "reason": "no commit history"}
    dates = sorted(datetime.fromisoformat(r[1]) for r in rows)
    hours = (dates[-1] - dates[0]).total_seconds() / 3600
    first = rows[-1][0]
    stat = sh("git", "diff", "--shortstat", f"{first}..HEAD")
    return {
        "available": True,
        "commits": len(rows),
        "elapsed_hours": round(hours, 1),
        "commits_per_hour": round(len(rows) / hours, 1) if hours else None,
        "diff_since_first_commit": stat,
        "method": ("wall-clock from the first to the last commit on the default branch; this is "
                   "elapsed time, not effort, and includes every pause"),
        "not_a_ratio": ("No human baseline exists for this work, so no speedup is computed. "
                        "Elapsed time also is not effort: a figure that ignores pauses and "
                        "review would overstate throughput in the other direction."),
    }


def unavailable():
    """Stated, not omitted: a metric the corpus defines and this repository cannot produce."""
    return [
        {"metric": "Lead time for changes (commit → production)",
         "reason": "no production deployment exists; the corpus ships no runtime"},
        {"metric": "MTTR for a production incident",
         "reason": "no production incident has occurred; CI recovery is reported instead and is not the same thing"},
        {"metric": "Evaluator score, groundedness, guardrail intervention rate",
         "reason": "requires a running agent with a model; none runs here (post-market plan §2)"},
        {"metric": "Approval latency and override rate",
         "reason": "requires the HITL gateway of an adopting product repository"},
        {"metric": "Time-to-spec and agent rework rate",
         "reason": "not instrumented; would need per-command timing the skills do not yet emit"},
    ]


def build():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": sh("git", "config", "--get", "remote.origin.url"),
        "git": git_metrics(),
        "ci": ci_metrics(),
        "corpus": corpus_metrics(),
        "session": session_throughput(),
        "unavailable": unavailable(),
    }


def render(m):
    g, c, k = m["git"], m["ci"], m["corpus"]
    date = m["generated_at"][:10]
    L = [
        "<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->",
        "",
        f"# Corpus metrics — {date}",
        "",
        "> **Generated** by `scripts/python/corpus_metrics.py --report`. Every number below is",
        "> measured from this repository's git history or its GitHub Actions runs, and every metric",
        "> names its method. Nothing here is estimated: the metrics this repository cannot produce",
        "> are listed in §4 with the reason, rather than filled in with a guess (Constitution IX).",
        "",
        "This is the first measurement the corpus has ever taken of itself. It exists because the",
        "maturity assessment of 2026-09-13 found every dimension stopping at *defined, never",
        "measured*, and one data point is what separates the two.",
        "",
        "## 1. Delivery",
        "",
        "| Metric | Value | Method |",
        "| --- | --- | --- |",
        f"| Commits on the default branch | {g['commits']} | {g['method']} |",
        f"| Active days | {g['active_days']} (span {g['span_days']} days) | — |",
        f"| Commits per active day | {g['commits_per_active_day']} | — |",
        f"| First / last commit | {(g['first_commit'] or '')[:19]} → {(g['last_commit'] or '')[:19]} | — |",
        "",
        "**Reading it honestly.** A commit is the unit that reaches the default branch here, so",
        "commits per active day is the deployment-frequency analogue and nothing more. The history",
        "is short, so no trend can be claimed from it — only a baseline that a later run can compare",
        "against.",
        "",
        "## 2. Change quality",
        "",
    ]
    if c.get("available"):
        L += [
            "| Metric | Value | Method |",
            "| --- | --- | --- |",
            f"| Completed CI runs | {c['runs_completed']} | {c['method']} |",
            f"| Failed runs | {c['failures']} | — |",
            f"| Change failure rate | {c['change_failure_rate_pct']}% | failed ÷ completed |",
            f"| Median run duration | {c['median_duration_s']} s | — |",
            f"| Recoveries observed | {c['recoveries_observed']}"
            + (f", median {c['median_recovery_s']} s" if c.get("median_recovery_s") is not None else "")
            + " | gap from a failed run to the next success |",
        ]
    else:
        L += [f"CI history unavailable: {c.get('reason')}."]
    L += [
        "",
        "## 3. Corpus shape",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Markdown files | {k['markdown_files']} |",
        f"| Markdown lines | {k['markdown_lines']} |",
        f"| Executable lines (scripts + hooks) | {k['executable_lines']} |",
        f"| Test lines | {k['test_lines']} |",
        f"| Prose to executable ratio | {k['prose_to_code_ratio']} : 1 |",
        f"| Check families in `check-corpus.sh` | {k['check_families']} |",
        f"| ADRs | {k['adrs']} |",
        "",
        "**Why the ratio is a metric and not trivia.** The maturity assessment named governance mass",
        "outgrowing verification as a structural risk. Tracking the ratio makes that visible: it",
        "should fall when verification is added and rise when documents are. A rising ratio across",
        "two reports is the signal to stop writing and start checking.",
        "",
        "## 4. Productivity — measured, and why there is no ratio",
        "",
    ]
    t = m.get("session", {})
    if t.get("available"):
        L += [
            "| Metric | Value | Method |",
            "| --- | --- | --- |",
            f"| Commits on the default branch | {t['commits']} | {t['method']} |",
            f"| Elapsed wall-clock | {t['elapsed_hours']} h | first commit to last |",
            f"| Commits per elapsed hour | {t['commits_per_hour']} | — |",
            f"| Cumulative diff | {t['diff_since_first_commit']} | `git diff --shortstat` from the first commit |",
            "",
            "**There is deliberately no speedup ratio here.** The corpus previously published a",
            "withdrawn claim of ≈160× faster, by dividing a measured agent wall-clock by a sum of",
            "t-shirt estimates — a confident figure nobody observed, which Constitution IX forbids.",
            "That claim was",
            "withdrawn (issue #55) and the instruction that generated it was removed from the",
            "`/deliver` skill, because correcting the output while leaving the generator would have",
            "produced the same claim on the next run.",
            "",
            f"_{t['not_a_ratio']}_",
            "",
            "**What a legitimate ratio would require**, none of which exists yet:",
            "",
            "1. A **baseline**: the same scope delivered without agent assistance, timed, by a",
            "   comparable team — not estimated from t-shirt sizes after the fact.",
            "2. **Effort, not elapsed time**, on both sides, counted the same way.",
            "3. A **defined scope boundary**: drafting artefacts and writing production code are",
            "   different work, and the previous claim mixed them.",
            "4. **More than one sample**, since a single run measures the run, not the method.",
            "",
            "Until those exist, this section reports what was produced and stops.",
            "",
        ]
    else:
        L += [f"Session throughput unavailable: {t.get('reason')}.", ""]
    L += [
        "## 5. Not measurable here, and why",
        "",
        "| Metric | Why not |",
        "| --- | --- |",
    ]
    L += [f"| {u['metric']} | {u['reason']} |" for u in m["unavailable"]]
    L += [
        "",
        "Listing these is the point of the section. A metrics report that silently omits what it",
        "cannot measure reads as complete; this one reads as partial, which is what it is.",
        "",
        "## Related",
        "",
        "- [`../../specs/compliance/ai-post-market-monitoring.md`](../../specs/compliance/ai-post-market-monitoring.md) — the cycle this feeds",
        "- [`../../specs/observability/agent-performance.md`](../../specs/observability/agent-performance.md) — the agent metrics awaiting a runtime",
        "- [`../../specs/observability/dora-metrics.md`](../../specs/observability/dora-metrics.md) — the DORA definitions this approximates for a corpus",
        "",
    ]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    m = build()
    if a.json:
        json.dump(m, sys.stdout, indent=2)
        print()
        return 0
    if a.report:
        rel = os.path.join("docs", "sre", f"corpus-metrics-{m['generated_at'][:10]}.md")
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
            fh.write(render(m))
        print(f"wrote {rel}")
    g, k, c = m["git"], m["corpus"], m["ci"]
    if not a.quiet:
        print(f"commits {g['commits']} over {g['active_days']} active days "
              f"({g['commits_per_active_day']}/day) · "
              f"CI failure rate {c.get('change_failure_rate_pct', 'n/a')}% · "
              f"prose:code {k['prose_to_code_ratio']}:1 · {k['check_families']} check families")
    return 0


if __name__ == "__main__":
    sys.exit(main())
