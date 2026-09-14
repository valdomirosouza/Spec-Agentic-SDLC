#!/usr/bin/env python3
"""A live feature spec says something about its abuse surface (#97).

`templates/spec-template.md` carries an `Authn / abuse (auth, rate limit)` row in the security
posture table, and `docs/product/nfr-taxonomy.md` names retries, idempotency and graceful
degradation under Reliability. Both are section-filling, not barriers: nothing failed a spec that
omitted the table or left the cell blank. Two of the three feature specs in the corpus carried no
posture table at all.

What this checks, and why it is shaped this way. The obvious rule — demand the template's row —
would have forced duplication in the one spec that handles the concern best: SPEC-FEAT-001 has no
posture table and a *better* treatment, a threat-surface row naming label-cardinality exhaustion as
STRIDE DoS with its mitigation and residual risk. A gate that rejected that would be buying form at
the cost of substance, and would teach authors to paste a row rather than think. So either form
satisfies it.

What it cannot do, said here rather than discovered later: judge the answer. A gate can insist the
question is answered; only review can tell whether the answer is any good.

Scope is `kind: feature-spec` at `status: approved` or `implemented` — a spec describing an exposed
surface that someone is meant to build or has built. A superseded spec is history, and a policy has
no callers to abuse it.

    check_abuse_surface.py            # report
    check_abuse_surface.py --check    # fail when a live feature spec is silent
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIVE = ("approved", "implemented")

# Form (a): the template's posture row, with a control actually written in it.
POSTURE_ROW = re.compile(r'^\|\s*Authn / abuse[^|]*\|([^|]*)\|', re.M)
# Form (b): a threat-surface row naming the abuse category, mitigation in the same row. Searched
# ONLY inside the threat-surface section: over the whole document the same pattern matched an
# Assumptions row ("Route templates keep label cardinality bounded"), so a spec that said nothing
# about abuse passed on the strength of an unrelated sentence. Caught by mutating the real row away
# and watching the check stay green.
THREAT_SECTION = re.compile(r'^#{2,4}\s+.*threat surface.*$', re.I | re.M)
THREAT_ROW = re.compile(
    r'^\|[^|\n]*\|[^|\n]*\b(dos|denial[- ]of[- ]service|abuse|flood|rate[- ]?limit|throttl|'
    r'exhaust|cardinality)\b[^|\n]*\|([^|\n]*)\|', re.I | re.M)
EMPTY = {"", "-", "—", "n/a", "na", "tbd", "todo", "?"}


def frontmatter(text, field):
    m = re.search(rf'^{field}:\s*(\S+)', text, re.M)
    return m.group(1).strip() if m else None


def live_feature_specs():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "specs", "**", "*.md"), recursive=True)):
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
        if frontmatter(t, "kind") == "feature-spec" and frontmatter(t, "status") in LIVE:
            out.append((os.path.relpath(p, ROOT), t))
    return out


def addressed(text):
    """(ok, how). Either form counts; neither is preferred over the other."""
    m = POSTURE_ROW.search(text)
    if m and m.group(1).strip().lower() not in EMPTY:
        return True, "posture row"
    sec = THREAT_SECTION.search(text)
    if sec:
        rest = text[sec.end():]
        nxt = re.search(r'^#{2,4}\s', rest, re.M)
        block = rest[:nxt.start()] if nxt else rest
        m = THREAT_ROW.search(block)
        if m and m.group(2).strip().lower() not in EMPTY:
            return True, "threat-surface row"
    return False, None


def problems():
    errs, rows = [], []
    for rel, text in live_feature_specs():
        ok, how = addressed(text)
        rows.append((rel, how))
        if not ok:
            errs.append(f"{rel}: a live feature spec with nothing said about its abuse surface — "
                        f"fill the `Authn / abuse` posture row, or name the abuse threat and its "
                        f"mitigation in the threat-surface table")
    return errs, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    errs, rows = problems()

    if not rows:
        print("no live feature spec found to check", file=sys.stderr)
        return 1
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    if not a.quiet:
        print(f"abuse surface: {len(rows)} live feature spec(s), all addressed")
        for rel, how in rows:
            print(f"  {rel}  ({how})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
