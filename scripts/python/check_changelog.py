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

# Contracts an adopter can hold a file against. A word in prose depends on whoever writes it
# remembering to use it; the value of a versioned constant at the last release does not. Extend
# this list when a new contract is published — that is the explicit limit of what can be derived,
# stated rather than left as a silent blind spot (R8-T5).
CONTRACTS = (
    ("scripts/python/asdd_state.py", r'^SCHEMA_VERSION\s*=\s*"([^"]+)"'),
    ("scripts/python/build_spec_registry.py", r'^SCHEMA_VERSION\s*=\s*"([^"]+)"'),
)
NEXT_VERSION = re.compile(r"\*\*Next version:\*\*\s*v?(\d+)\.(\d+)\.(\d+)")
# A compatibility claim is a structured marker at the head of a bullet, not the word anywhere in
# the block. Scanning for the bare word fired on the three lines that EXPLAIN this rule — prose
# describing a claim is not a claim, and a checker that cannot tell them apart makes its own
# documentation unpublishable (R8-T5).
BREAKING = re.compile(r"^\s*[-*]\s+\*\*BREAKING\b", re.M)

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


def missing(path):
    """A file this corpus has and an adopting repository may not. Absent means the check does not
    apply here, which is a sentence to print — not a Python traceback, which is what a fresh
    adoption used to get (#106)."""
    return not os.path.isfile(os.path.join(ROOT, path))


def problems():
    """Two failures, deliberately independent of each other.

    The structural one is checked unconditionally. An earlier version only looked at the section
    when something was owing, which made the assertion depend on the state of the working tree: it
    passed or failed according to what happened to be edited, and could not be proved by mutation
    on a clean tree. An invariant that only holds sometimes is not an invariant."""
    errs = []
    if missing(CHANGELOG):
        return [f"no {CHANGELOG} in this repository — nothing to record against"], []
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


def release_commit():
    """The commit where version.txt last changed: the state an adopter on the current release has."""
    r = subprocess.run(["git", "log", "--format=%H", "-1", "--", VERSION_FILE],
                       capture_output=True, text=True, cwd=ROOT, timeout=60)
    return r.stdout.strip() or None


def _at(commit, path):
    r = subprocess.run(["git", "show", f"{commit}:{path}"],
                       capture_output=True, text=True, cwd=ROOT, timeout=60)
    return r.stdout if r.returncode == 0 else None


def derived_breaks():
    """Contracts that existed at the last release AND changed value since.

    A contract introduced after the release cannot break anyone on it: nobody holds a file written
    by a tool that did not ship. That is what makes this derivable rather than a matter of
    remembering a word."""
    commit = release_commit()
    if not commit:
        return [], ["no release commit found: version.txt has never been committed"]
    breaks, notes = [], []
    for path, pattern in CONTRACTS:
        rx = re.compile(pattern, re.M)
        then = _at(commit, path)
        if then is None:
            notes.append(f"{path} did not exist at the last release, so nothing held against it "
                         f"can break")
            continue
        now = open(os.path.join(ROOT, path), encoding="utf-8").read()
        a = rx.search(then)
        b = rx.search(now)
        if a and b and a.group(1) != b.group(1):
            breaks.append(f"{path}: {a.group(1)} → {b.group(1)}")
    return breaks, notes


def version_problems():
    """A BREAKING entry has to say what version it forces.

    ADR-0057 makes version.txt the version of record and says it follows SemVer. Nothing exercised
    that. The changelog now records a schema change as BREAKING under [Unreleased] while
    version.txt sits at 1.0.0, and in three months nobody will remember a break was pending — the
    rule was written and never made to act on anything (R7-T5)."""
    errs = []
    for needed in (CHANGELOG, VERSION_FILE):
        if missing(needed):
            return [f"no {needed} in this repository — no version of record to check against"]
    block = unreleased_block()
    cur = current_version()
    if cur is None:
        return [f"{VERSION_FILE} does not hold a SemVer version"]
    declared = NEXT_VERSION.search(block)
    nxt = tuple(int(x) for x in declared.groups()) if declared else None

    breaks, _notes = derived_breaks()
    claims_breaking = bool(BREAKING.search(block))

    if breaks:
        if nxt is None:
            errs.append(f"{UNRELEASED} breaks a published contract ({'; '.join(breaks)}) and "
                        f"declares no next version. Add: `> **Next version:** {cur[0] + 1}.0.0`")
        elif nxt[0] <= cur[0]:
            errs.append(f"a broken contract needs a major bump: declared "
                        f"{'.'.join(map(str, nxt))}, current is {'.'.join(map(str, cur))} "
                        f"({'; '.join(breaks)})")
    elif claims_breaking:
        # The case this rule was written for, and it was my own claim. `asdd_state.py` arrived
        # after 1.0.0, so nobody on that release holds a v1 state file and the v1→v2 change breaks
        # no published contract. The BREAKING label, and the 2.0.0 it forced, overstated the impact
        # exactly the way the withdrawn 160x claim did (Article IX).
        errs.append(
            f"{UNRELEASED} says BREAKING, but no contract published at the last release changed. "
            f"Either the label overstates the impact — a tool added after the release cannot break "
            f"anyone on it — or the contract is not in CONTRACTS and should be added.")
        if nxt is not None and nxt[0] > cur[0]:
            errs.append(f"and the declared {'.'.join(map(str, nxt))} follows from that label")
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
            brks, notes = derived_breaks()
            for n in notes:
                print(f"  {n}")
            print(f"version: {'.'.join(map(str, current_version()))}"
                  + (f", breaks {len(brks)} published contract(s)" if brks else
                     ", no published contract broken")
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
