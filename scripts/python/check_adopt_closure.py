#!/usr/bin/env python3
"""An adoption layer copies every file the files it copies point at (#107).

Adopting the `governed` layer into a clean directory arrived with eleven broken internal links:
`AGENTS.md` pointing at a `CONTRIBUTING.md` the layer does not copy, `CLAUDE.md` at `CHANGELOG.md`
and `docs/troubleshooting.md`, and so on. The layer was a hand-written list of paths, and a
hand-written list is complete only where someone looked.

This is the same defect this corpus found in its own spec-kit tracking on the same day, from the
other side of the relationship: the tracked set is not closed under reference either, and two
scripts named by tracked commands sit outside it. A set chosen by enumeration is incomplete exactly
where nobody looked, and the fix is to close it under the property rather than to add the names
that happen to be missing today.

The check reads the layer definitions out of `adopt.sh` rather than restating them, so the two
cannot drift.

    check_adopt_closure.py            # report, per layer
    check_adopt_closure.py --check    # fail when a copied file points at one that is not copied
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADOPT = os.path.join(ROOT, "scripts", "bash", "adopt.sh")
LAYERS = ("minimal", "governed", "full")

# Markdown links to a repository path. Anchors, URLs, mailto and pure fragments are not files.
LINK = re.compile(r'\[[^\]]*\]\(([^)#?\s]+)[^)]*\)')
SKIP_PREFIX = ("http://", "https://", "mailto:", "#", "<", "{")

# Archived copies of another project's documentation. Their links describe that project's tree, not
# this one — the corpus's own link check and its markdownlint glob already exempt them, and this
# mirrors that exemption rather than inventing a second rule.
ARCHIVED = ("docs/reference/repository-template-v2-",)


def layer_files(layer):
    """The files adopt.sh would copy, asked of adopt.sh itself via --dry-run."""
    r = subprocess.run(["bash", ADOPT, "--list", "--layer", layer, "/tmp/__adopt_closure_probe"],
                       capture_output=True, text=True, cwd=ROOT, timeout=300)
    if r.returncode != 0:
        return None, f"adopt.sh --list --layer {layer} exited {r.returncode}: {r.stderr.strip()[:120]}"
    files = {l.strip() for l in r.stdout.split("\n") if l.strip()}
    return files, None


# Evidence paths inside a control matrix are references too, in a different language. The matrix
# gate requires each to resolve, so a layer that copies the matrix and not its evidence arrives
# failing — closure is the same property whether the reference is a Markdown link or a YAML path.
EVIDENCE = re.compile(r'^\s+- ((?:docs|specs|skills|memory|templates|harness)/[\w./-]+)\s*$', re.M)


def link_targets(rel):
    """Repository-relative targets of the references inside one file."""
    path = os.path.join(ROOT, rel)
    if rel.endswith((".yaml", ".yml")):
        try:
            with open(path, encoding="utf-8") as fh:
                return EVIDENCE.findall(fh.read())
        except (OSError, UnicodeDecodeError):
            return []
    if not rel.endswith(".md"):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return []
    out = []
    base = os.path.dirname(rel)
    for target in LINK.findall(text):
        if target.startswith(SKIP_PREFIX):
            continue
        resolved = os.path.normpath(os.path.join(base, target))
        if resolved.startswith(".."):
            continue
        out.append(resolved)
    return out


def dangling(layer):
    files, err = layer_files(layer)
    if err:
        return None, err
    missing = {}
    for rel in sorted(files):
        if rel.startswith(ARCHIVED):
            continue
        for target in link_targets(rel):
            if target in files:
                continue
            if not os.path.exists(os.path.join(ROOT, target)):
                continue          # broken in the corpus too: that is C1's finding, not this one
            missing.setdefault(target, []).append(rel)
    return missing, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--layer", choices=LAYERS, action="append")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    layers = a.layer or list(LAYERS)

    total, errs = 0, []
    for layer in layers:
        missing, err = dangling(layer)
        if err:
            errs.append(err)
            continue
        total += len(missing)
        if missing and not a.quiet:
            print(f"{layer}: {len(missing)} target(s) a copied file points at and the layer omits")
            for target, sources in sorted(missing.items()):
                print(f"  {target}  ← {', '.join(sorted(sources)[:2])}")
        elif not missing and not a.quiet:
            print(f"{layer}: closed under reference")

    if a.check:
        if errs:
            for e in errs:
                print(e, file=sys.stderr)
            return 1
        if total:
            print(f"{total} dangling target(s) across {len(layers)} layer(s) — add them to the "
                  f"layer, or stop the copied file from pointing at them", file=sys.stderr)
            return 1
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
