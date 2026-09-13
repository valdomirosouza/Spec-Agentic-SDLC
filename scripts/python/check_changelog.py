#!/usr/bin/env python3
"""A change to executable or normative files must be recorded in the changelog (#77).

`CLAUDE.md` §7 lists "CHANGELOG.md updated" on the PR checklist and §7.1 describes the gate that
makes it blocking — in the *adopting* repository. Nothing enforced it here, and the result was
seven commits, including a breaking schema change, reaching main with no entry. An adopter reading
the changelog had no way to learn their state files had stopped loading.

This runs against the working tree, which is where check-corpus runs: at the moment before a
commit, when the entry can still be written. Untracked files count too — a new script is exactly
the kind of change that owes an entry.

    check_changelog.py            # report
    check_changelog.py --quiet    # report only on failure
    CHANGELOG_WAIVER="reason"     # declare an exemption; it is printed, never silent
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHANGELOG = "CHANGELOG.md"
UNRELEASED = "## [Unreleased]"

# What owes an entry: things that execute, and things that bind. Prose that documents an unchanged
# behaviour does not, which is why `docs/` and `specs/` are absent.
WATCHED = ("scripts/", ".github/workflows/", ".claude/hooks/", "memory/", "CLAUDE.md", "AGENTS.md")

VERSION_FILE = "version.txt"
NEXT_VERSION = re.compile(r"\*\*Next version:\*\*\s*v?(\d+)\.(\d+)\.(\d+)")
BREAKING = re.compile(r"\bBREAKING\b")

# Generated on nearly every run as a side effect of measuring; an entry for each would be noise
# that teaches people to ignore the gate.
EXEMPT = ("docs/sre/corpus-metrics-", "docs/governance/spec-registry.", "tests/.mutation-coverage-baseline.json")


def changed_paths():
    """Every path the working tree touches relative to HEAD, staged or not, tracked or not."""
    out = subprocess.run(["git", "status", "--porcelain", "-z"], capture_output=True, text=True,
                         cwd=ROOT, timeout=60)
    paths = set()
    fields = [f for f in out.stdout.split("\0") if f]
    i = 0
    while i < len(fields):
        entry = fields[i]
        status, path = entry[:2], entry[3:]
        # A rename carries its source in the next field; both sides count as touched.
        if "R" in status and i + 1 < len(fields):
            paths.add(fields[i + 1])
            i += 1
        paths.add(path)
        i += 1
    return {p for p in paths if p}


def problems():
    """Two failures, deliberately independent of each other.

    The structural one is checked unconditionally. An earlier version only looked at the section
    when something was owing, which made the assertion depend on the state of the working tree: it
    passed or failed according to what happened to be edited, and could not be proved by mutation
    on a clean tree. An invariant that only holds sometimes is not an invariant."""
    errs = []
    with open(os.path.join(ROOT, CHANGELOG), encoding="utf-8") as fh:
        if UNRELEASED not in fh.read():
            errs.append(f"{CHANGELOG} has no `{UNRELEASED}` section, so nothing can be recorded "
                        f"under it")

    changed = changed_paths()
    owing = sorted(p for p in changed if p.startswith(WATCHED) and not p.startswith(EXEMPT))
    if owing and CHANGELOG not in changed:
        errs.append(f"{len(owing)} executable or normative file(s) changed with no "
                    f"{CHANGELOG} entry")
    return errs, owing


def unreleased_block():
    with open(os.path.join(ROOT, CHANGELOG), encoding="utf-8") as fh:
        text = fh.read()
    if UNRELEASED not in text:
        return ""
    rest = text.split(UNRELEASED, 1)[1]
    # Up to the next release heading, so a BREAKING note in an older release does not count.
    return re.split(r"\n## \[", rest, maxsplit=1)[0]


def current_version():
    with open(os.path.join(ROOT, VERSION_FILE), encoding="utf-8") as fh:
        raw = fh.read().strip()
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", raw)
    return tuple(int(x) for x in m.groups()) if m else None


def version_problems():
    """A BREAKING entry has to say what version it forces.

    ADR-0057 makes version.txt the version of record and says it follows SemVer. Nothing exercised
    that. The changelog now records a schema change as BREAKING under [Unreleased] while
    version.txt sits at 1.0.0, and in three months nobody will remember a break was pending — the
    rule was written and never made to act on anything (R7-T5)."""
    errs = []
    block = unreleased_block()
    cur = current_version()
    if cur is None:
        return [f"{VERSION_FILE} does not hold a SemVer version"]
    declared = NEXT_VERSION.search(block)
    nxt = tuple(int(x) for x in declared.groups()) if declared else None

    if BREAKING.search(block):
        if nxt is None:
            errs.append(f"{UNRELEASED} records a BREAKING change and does not declare the next "
                        f"version. Add a line: `> **Next version:** {cur[0] + 1}.0.0`")
        elif nxt[0] <= cur[0]:
            errs.append(f"a BREAKING change needs a major bump: declared "
                        f"{'.'.join(map(str, nxt))}, current is {'.'.join(map(str, cur))}")
    if nxt is not None and nxt <= cur:
        errs.append(f"declared next version {'.'.join(map(str, nxt))} is not ahead of "
                    f"{'.'.join(map(str, cur))}")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="store_true", dest="version_mode",
                    help="check that a BREAKING entry declares the next version")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if a.version_mode:
        verrs = version_problems()
        if verrs:
            for e in verrs:
                print(e, file=sys.stderr)
            return 1
        if not a.quiet:
            block = unreleased_block()
            d = NEXT_VERSION.search(block)
            print(f"version: {'.'.join(map(str, current_version()))}"
                  + (f", next declared {d.group(1)}.{d.group(2)}.{d.group(3)}" if d else
                     ", no next version declared and none required"))
        return 0

    errs, owing = problems()
    waiver = (os.environ.get("CHANGELOG_WAIVER") or "").strip()

    if errs and waiver:
        print(f"changelog waived: {waiver}")
        for p in owing:
            print(f"  {p}")
        return 0
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        for p in owing:
            print(f"  {p}", file=sys.stderr)
        print(f"  add the entry under `{UNRELEASED}`, or declare CHANGELOG_WAIVER=\"<reason>\"",
              file=sys.stderr)
        return 1
    if not a.quiet:
        print(f"changelog: {len(owing)} watched file(s) changed"
              + (f", {CHANGELOG} updated" if owing else ", nothing owing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
