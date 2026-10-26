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
ROW = re.compile(r'^\|\s*`([A-Za-z0-9._-]+-template\.md)`\s*\|([^|]*)\|', re.M)

# The "Filled by" cell names its consumers in backticks: a script, or a slash command.
CONSUMER = re.compile(r'`([^`]+)`')

# A skill may name several templates at once by brace expansion, so the literal filename is
# absent from a consumer that is perfectly correct:
#   templates/{plan,research,data-model,quickstart,contracts-README}-template.md
# A naive literal search fails the right answer, which is the failure mode this series has
# rejected most often — so the brace form is expanded before the search (R15-T3).
BRACE = re.compile(r'\{([^}]+)\}')


def rows():
    with open(INDEX, encoding="utf-8") as fh:
        return ROW.findall(fh.read())


def discrepancies():
    """(missing from the index, indexed but absent), both sorted."""
    on_disk = {f for f in os.listdir(TEMPLATES) if f.endswith(".md") and f != "README.md"}
    indexed = {t for t, _ in rows()}
    return sorted(on_disk - indexed), sorted(indexed - on_disk)


def _mentions(text, template):
    """Does this file name the template, literally or through a brace expansion?

    `templates/{plan,research,data-model}-template.md` names three templates and contains the
    literal filename of none of them."""
    if template in text:
        return True
    stem = template[: -len("-template.md")]
    for m in re.finditer(r'\{([^}]+)\}(-template\.md)', text):
        if stem in [alt.strip() for alt in m.group(1).split(",")]:
            return True
    return False


def unverified_consumers():
    """[(template, consumer, why)] for a "Filled by" claim that does not hold."""
    out = []
    for template, filled_by in rows():
        for name in CONSUMER.findall(filled_by):
            name = name.lstrip("/")
            candidates = [os.path.join(ROOT, "scripts", "bash", name),
                          os.path.join(ROOT, ".claude", "skills", name, "SKILL.md")]
            found = [c for c in candidates if os.path.exists(c)]
            if not found:
                out.append((template, name, "names a consumer that does not exist"))
                continue
            with open(found[0], encoding="utf-8", errors="replace") as fh:
                if not _mentions(fh.read(), template):
                    out.append((template, name, "names a consumer that never mentions it"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(INDEX):
        print("templates/README.md is missing: the templates have no index", file=sys.stderr)
        return 1
    unindexed, phantom = discrepancies()
    unverified = unverified_consumers()
    if not a.quiet:
        if unindexed:
            print(f"{len(unindexed)} template(s) with no entry in templates/README.md: "
                  f"{', '.join(unindexed)}")
        if phantom:
            print(f"{len(phantom)} entr(y/ies) naming a template that does not exist: "
                  f"{', '.join(phantom)}")
        for t, name, why in unverified:
            print(f"{t}: {why} ({name})")
        if not unindexed and not phantom and not unverified:
            n = len(os.listdir(TEMPLATES)) - 1
            print(f"templates/README.md indexes all {n} templates and nothing else, and every "
                  f"consumer it names references the template it claims to fill")
    if a.check and (unindexed or phantom or unverified):
        for t in unindexed:
            print(f"{t}: shipped with no entry in templates/README.md", file=sys.stderr)
        for t in phantom:
            print(f"{t}: indexed in templates/README.md but not present", file=sys.stderr)
        for t, name, why in unverified:
            print(f"{t}: {why} — `{name}`", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
