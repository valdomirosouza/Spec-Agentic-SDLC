#!/usr/bin/env python3
"""Every open item carries a date or a named trigger, and an overdue date fails (#78).

Forty-two open-item rows across the corpus, and not one carried a date. Eleven were deferred to a
"next quarterly review" that nothing convenes; the rest named an event in prose. So no item could
ever be overdue, because there was nothing to be late against, and the review that would resolve
them was not scheduled anywhere.

The fix is not to invent dates. Conditioning an item on a real event — before synthetic data is
used, before the first exception — is often more honest than a date somebody made up. The defect
was having no way to tell the two apart and no way to know when a deadline had passed. So the
vocabulary is explicit:

    2026-12-13            a date. Past today, it fails.
    on-event: <trigger>   a named condition. Never overdue, always visible.

    check_open_items.py            # list every item and its state
    check_open_items.py --check    # fail on overdue; report unmarked items
"""
import argparse
import datetime
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Every heading the corpus actually uses to record deferred governance work. The first version
# matched the literal `Open items`, and `docs/data/data-catalog.md` writes `### Open finding`,
# singular — so the one live open finding in the whole corpus, DQ-REG-006, fell outside the check
# written to stop undated deferrals (R7-T2).
#
# Deliberately NOT covered, each for a stated reason rather than to keep the count tidy:
#   `Open questions` — spec §15, with its own gate (check_open_questions.py); covering it here
#                      would double-report and the two vocabularies differ.
#   `Open Work`      — a shell snippet in the session primer, not a table.
#   `Open P2/P3 …`   — an on-call shift handover: operational, not deferred governance work.
# Numbered and prefixed headings count: the corpus writes `## 10. Open items` as well as
# `## Open items`. Anchoring "open" straight after the hashes dropped most of the tables,
# which the floors below caught immediately.
HEADING = re.compile(r"^#+\s+.*\bopen\s+(items?|findings?)\b", re.I)
ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
ON_EVENT = re.compile(r"^on-event:\s*\S")
# Rows that are the table's own furniture, not items.
FURNITURE = {"", "-", "—", "resolve by", "prazo", "when", "due", "suggested target",
             "target", "resolve when"}
DONE = ("✅", "~~")
_TABLES = set()


# Floors, raised deliberately. Renaming a covered heading makes its rows vanish from the count and
# every remaining item still passes, so a silent scope collapse would look exactly like success.
MIN_TABLES = 11
MIN_ITEMS = 30


def rows():
    """(path, line number, the last cell) for every open-item table row in the corpus."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel.startswith((".git/", "node_modules/")):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except (OSError, UnicodeDecodeError):
            continue
        inside = False
        for n, line in enumerate(lines, 1):
            if HEADING.match(line):
                inside = True
                _TABLES.add(rel)
                continue
            if inside and line.startswith("#"):
                inside = False
            if not inside or not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or set(cells[0]) <= set("-: "):
                continue          # separator row
            out.append((rel, n, cells[-1], cells))
    return out


def classify(cell):
    low = cell.strip().lower()
    if low in FURNITURE:
        return "furniture", None
    if any(d in cell for d in DONE):
        return "done", None
    m = ISO.match(cell.strip())
    if m:
        return "dated", datetime.date(*(int(x) for x in m.groups()))
    if ON_EVENT.match(cell.strip()):
        return "on-event", None
    return "unmarked", None


def audit(today=None):
    today = today or datetime.date.today()
    buckets = {"dated": [], "on-event": [], "unmarked": [], "done": [], "furniture": []}
    overdue = []
    for rel, n, cell, _cells in rows():
        kind, due = classify(cell)
        buckets[kind].append((rel, n, cell))
        if kind == "dated" and due < today:
            overdue.append((rel, n, cell, (today - due).days))
    return buckets, overdue


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    buckets, overdue = audit()
    dated, evented, unmarked = buckets["dated"], buckets["on-event"], buckets["unmarked"]

    if a.check:
        scope = []
        if len(_TABLES) < MIN_TABLES:
            scope.append(f"only {len(_TABLES)} open-item table(s) found, floor is {MIN_TABLES} — "
                         f"a heading was renamed and its rows left the check silently")
        items = len(dated) + len(evented) + len(unmarked)
        if items < MIN_ITEMS:
            scope.append(f"only {items} open item(s) found, floor is {MIN_ITEMS}")
        if scope:
            for line in scope:
                print(line, file=sys.stderr)
            print("  raise the floors in check_open_items.py deliberately if the shrink is real",
                  file=sys.stderr)
            return 1
        if overdue:
            print(f"{len(overdue)} open item(s) past their date:", file=sys.stderr)
            for rel, n, cell, days in overdue:
                print(f"  {rel}:{n}  due {cell}, {days} day(s) ago", file=sys.stderr)
            print("  resolve it, move the date deliberately, or restate it as "
                  "`on-event: <trigger>`", file=sys.stderr)
            return 1
        if unmarked:
            print(f"{len(unmarked)} open item(s) carry neither a date nor `on-event:` — "
                  f"they cannot become overdue, so nothing will ever surface them")
            for rel, n, cell in unmarked[:10]:
                print(f"  {rel}:{n}  {cell[:60]}")
            return 0
        if not a.quiet:
            print(f"open items: {len(dated)} dated, {len(evented)} on-event, none overdue, "
                  f"across {len(_TABLES)} table(s)")
        return 0

    print(f"dated:     {len(dated)}")
    print(f"on-event:  {len(evented)}")
    print(f"unmarked:  {len(unmarked)}")
    print(f"overdue:   {len(overdue)}")
    print(f"tables:    {len(_TABLES)}  ({', '.join(sorted(_TABLES))})")
    for rel, n, cell in unmarked:
        print(f"  UNMARKED  {rel}:{n}  {cell[:70]}")
    for rel, n, cell, days in overdue:
        print(f"  OVERDUE   {rel}:{n}  {cell} ({days} d)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
