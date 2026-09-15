#!/usr/bin/env python3
"""templates/README.md indexes every template, and indexes nothing else (#112).

Thirteen templates shipped with no index, and two of them are called a spec template — one for a
feature bundle, one for a standing system spec. Nothing said which was which, so the cost fell on
whoever arrived next.

An index kept by hand is complete only where someone looked. This repository has now been bitten
by that twice in one week — its adoption layers were not closed under reference (#107), and the
set it tracks upstream was not either. So the index is closed in both directions rather than
checked in the direction that happens to be wrong today: a template with no entry fails, and an
entry with no template fails.

    check_templates_index.py [--check] [--quiet]
"""
import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATES = os.path.join(ROOT, "templates")
INDEX = os.path.join(TEMPLATES, "README.md")
# A row names its template in the first cell, as `name.md`. Case-insensitive on the stem because
# one of the thirteen is `contracts-README-template.md`, and a lowercase-only pattern reported it
# as unindexed on this check's first run — the narrower rule was wrong about a file, not about the
# index.
ROW = re.compile(r'^\|\s*`([A-Za-z0-9._-]+-template\.md)`\s*\|', re.M)


def discrepancies():
    """(missing from the index, indexed but absent), both sorted."""
    on_disk = {f for f in os.listdir(TEMPLATES) if f.endswith(".md") and f != "README.md"}
    with open(INDEX, encoding="utf-8") as fh:
        indexed = set(ROW.findall(fh.read()))
    return sorted(on_disk - indexed), sorted(indexed - on_disk)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(INDEX):
        print("templates/README.md is missing: the templates have no index", file=sys.stderr)
        return 1
    unindexed, phantom = discrepancies()
    if not a.quiet:
        if unindexed:
            print(f"{len(unindexed)} template(s) with no entry in templates/README.md: "
                  f"{', '.join(unindexed)}")
        if phantom:
            print(f"{len(phantom)} entr(y/ies) naming a template that does not exist: "
                  f"{', '.join(phantom)}")
        if not unindexed and not phantom:
            n = len(os.listdir(TEMPLATES)) - 1
            print(f"templates/README.md indexes all {n} templates and nothing else")
    if a.check and (unindexed or phantom):
        for t in unindexed:
            print(f"{t}: shipped with no entry in templates/README.md", file=sys.stderr)
        for t in phantom:
            print(f"{t}: indexed in templates/README.md but not present", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
