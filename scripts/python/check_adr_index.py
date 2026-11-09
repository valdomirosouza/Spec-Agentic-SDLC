#!/usr/bin/env python3
"""ADR index check for check-corpus.sh C3 (ADR-0097).

Every docs/adr/ADR-NNNN-*.md is linked from docs/adr/README.md, every link resolves, and numbering
is contiguous within each range: ADR-0001-0999 belong to this corpus, ADR-1000 and up to the
repository that adopted it. Each range is checked on its own, so a corpus ADR added by a sync
never breaks an adopter and an adopter ADR never breaks a sync.

A number may appear twice in the corpus range only when one of the two files is
`Superseded by ADR-1NNN`: the adopter restated its colliding ADR in its own range and kept the old
file, as ADR-0059 requires. The successor must exist.

Output (read by check-corpus.sh): `n/a: <reason>` alone, or three blocks of lines: the file count,
the problem count, then one problem per line. Run from the repository root.
"""
import glob
import os
import re
import sys

CORPUS_MAX = 999
LOCAL_START = 1000
# Both header styles in use: `**Status:** Superseded by ADR-1000` and `| **Status** | Superseded by ADR-1000 |`.
SUPERSEDED_BY = re.compile(r"\*\*Status:?\*\*:?\s*(?:\|\s*)?Superseded by ADR-(\d{4})")


def number(path):
    return int(os.path.basename(path)[4:8])


def superseded_by(path):
    m = SUPERSEDED_BY.search(open(path, encoding="utf-8").read())
    return int(m.group(1)) if m else None


def gaps(nums, start):
    return [n for n in range(start, max(nums) + 1) if n not in nums] if nums else []


def problems(root="."):
    """(file count, [problem]) for the ADRs under root, or None when the check does not apply."""
    files = sorted(glob.glob(os.path.join(root, "docs/adr/ADR-[0-9][0-9][0-9][0-9]-*.md")))
    index = os.path.join(root, "docs/adr/README.md")
    if not files or not os.path.isfile(index):
        return None
    bad = []
    by_num = {}
    for f in files:
        by_num.setdefault(number(f), []).append(f)
    corpus = sorted(n for n in by_num if n <= CORPUS_MAX)
    local = sorted(n for n in by_num if n >= LOCAL_START)
    if gaps(corpus, 1):
        bad.append(f"numbering not contiguous in the corpus range: {gaps(corpus, 1)} missing")
    if gaps(local, LOCAL_START):
        bad.append(f"numbering not contiguous in the adopter range (ADR-1000+): {gaps(local, LOCAL_START)} missing")
    for n, paths in sorted(by_num.items()):
        if len(paths) == 1:
            continue
        names = ", ".join(os.path.basename(p) for p in paths)
        restated = [p for p in paths if (superseded_by(p) or 0) >= LOCAL_START]
        if n >= LOCAL_START or len(paths) != 2 or len(restated) != 1:
            bad.append(f"duplicate ADR-{n:04d}: {names} (a corpus-range duplicate is allowed only "
                       f"when one of two files is Superseded by an ADR-1000+, ADR-0097)")
            continue
        successor = superseded_by(restated[0])
        if successor not in by_num:
            bad.append(f"{os.path.basename(restated[0])} is Superseded by ADR-{successor:04d}, "
                       f"which does not exist")
    text = open(index, encoding="utf-8").read()
    linked = set(re.findall(r"\]\((ADR-[0-9]{4}-[^)]+\.md)\)", text))
    for f in files:
        if os.path.basename(f) not in linked:
            bad.append(f"not in docs/adr/README.md: {os.path.basename(f)}")
    for link in sorted(linked):
        if not os.path.exists(os.path.join(root, "docs/adr", link)):
            bad.append(f"index links a missing file: {link}")
    return len(files), bad


def main():
    result = problems(".")
    if result is None:
        print("n/a: no docs/adr index in this repository")
        return 0
    count, bad = result
    print(count)
    print(len(bad))
    print("\n".join(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
