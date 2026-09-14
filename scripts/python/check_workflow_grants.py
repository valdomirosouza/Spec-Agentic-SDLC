#!/usr/bin/env python3
"""A workflow may not use an elevated verb this corpus has not written down (#100).

`corpus-measure.yml` declared `pull-requests: write` and its first scheduled run still could not
open a pull request: that grant is a repository setting, decided outside the repository. ADR-0071
argues precisely that about branch protection and was scoped to branch protection, so it did not
cover the setting that stopped the corpus's own automation three months after it was written.

What this verifies is that the dependency is **declared** — that ADR-0071's table carries every
elevated verb the workflows use. It cannot verify the grant is switched on: reading that needs an
administrative credential the corpus does not have and should not hold. Discovering a missing grant
still happens on the first run, which is how this one was found, and saying so is more useful than
implying otherwise.

    check_workflow_grants.py            # report
    check_workflow_grants.py --check    # fail on an undeclared elevated verb
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADR = "docs/adr/ADR-0071-repository-settings-as-code.md"
WORKFLOWS = ".github/workflows/*.yml"

# Verbs that need something granted beyond reading the repository. Deliberately a closed list: a
# pattern broad enough to catch "anything that writes" would fire on every `echo` and `grep`, which
# is the widening this corpus has rejected five times. Add a verb here when a workflow needs one.
ELEVATED = (
    re.compile(r'\bgh\s+pr\s+create\b'),
    re.compile(r'\bgh\s+pr\s+merge\b'),
    re.compile(r'\bgh\s+issue\s+create\b'),
    re.compile(r'\bgh\s+issue\s+comment\b'),
    re.compile(r'\bgh\s+label\s+create\b'),
    re.compile(r'\bgh\s+release\s+create\b'),
    re.compile(r'\bgit\s+push\b'),
)


def _uncommented(text):
    """Comments explain; they do not use. A verb named in a comment is prose about a verb."""
    return "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("#"))


def used_verbs():
    found = {}
    for path in sorted(glob.glob(os.path.join(ROOT, WORKFLOWS))):
        body = _uncommented(open(path, encoding="utf-8").read())
        for rx in ELEVATED:
            m = rx.search(body)
            if m:
                found.setdefault(" ".join(m.group(0).split()), set()).add(
                    os.path.relpath(path, ROOT))
    return found


def declared_verbs():
    with open(os.path.join(ROOT, ADR), encoding="utf-8") as fh:
        text = fh.read()
    out = set()
    # The whole first cell, backticks and all. Stopping at the first backtick read
    # "`gh issue create` / `comment` / `list`" as one verb and missed the other two — the row said
    # what it meant and the parser did not.
    for row in re.findall(r'^\|([^|]*)\|', text, re.M):
        for rx in ELEVATED:
            m = rx.search(row)
            if m:
                out.add(" ".join(m.group(0).split()))
    return out


def problems():
    used, declared = used_verbs(), declared_verbs()
    errs = []
    for verb, files in sorted(used.items()):
        if verb not in declared:
            errs.append(f"`{verb}` is used in {', '.join(sorted(files))} and is not in "
                        f"{ADR}. Add the row saying what must be granted and where.")
    return errs, used, declared


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    errs, used, declared = problems()

    if not used:
        print("no workflow uses an elevated verb — nothing to declare", file=sys.stderr)
        return 1
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    if not a.quiet:
        print(f"workflow grants: {len(used)} elevated verb(s), all declared in ADR-0071")
        for verb, files in sorted(used.items()):
            print(f"  {verb:24} {', '.join(sorted(files))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
