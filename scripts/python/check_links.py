#!/usr/bin/env python3
"""Internal Markdown links resolve — check-corpus.sh C1, as a script (#108).

The rule lived inline in the verifier, which was fine while the verifier was its only caller. It
now has a second one: the adoption check runs it over a freshly adopted tree, where the question is
the same and the answer is not — a layer can copy a file and omit what it points at.

Two rules stay behind, both of them corpus facts rather than link facts: paths the ADOPTING
repository provides (`src/`, `make`, `services.yaml`, CI workflows) are not this corpus's to
resolve, and the archived copies of another project's README describe that project's tree.

    check_links.py [--root DIR]      # prints: <files> <broken>, then one line per broken link
    check_links.py --check           # exit 1 when a link is broken

Exit 0 by default, and that is load-bearing rather than incidental: check-corpus.sh sources a
common.sh that sets `errexit`, so a helper that exits 1 inside a bare assignment ends the whole
verifier — at check 1 of 58, before a single failure line is printed. A reader sees a short, quiet
run. `--check` is the mode that fails, the same convention every other script here follows.
"""
import argparse
import os
import re
import sys

ADOPTER = ('src/', 'tests/', 'services/', 'frontend/', 'infrastructure/', 'scaffold/', 'deprecated/',
           'services.yaml', '.env.example', 'Makefile', 'pyproject.toml', 'version.txt.bak',
           '.github/workflows/', 'scripts/governance/', 'docs/api/grpc/', 'reports/')
SKIP_FILES = ('docs/reference/repository-template-v2-README.md',
              'docs/reference/repository-template-v2-SETUP.md')
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
PRUNE = ('.git', '.serena', '.sdd', 'node_modules')


def broken_links(root="."):
    """(markdown files considered, ['<file> → <target>', …])."""
    cwd = os.getcwd()
    os.chdir(root)
    try:
        md = []
        for d, dn, fn in os.walk('.'):
            dn[:] = [x for x in dn if x not in PRUNE]
            md += [os.path.normpath(os.path.join(d, f)) for f in fn if f.endswith('.md')]
        md = [p for p in md if p not in SKIP_FILES]
        bad = []
        for p in md:
            with open(p, encoding='utf-8', errors='replace') as fh:
                s = fh.read()
            for m in LINK.finditer(s):
                t = m.group(1)
                if t.startswith(('http://', 'https://', '#', 'mailto:', '<')):
                    continue
                t = t.split('#')[0]
                if not t or '...' in t or 'XXX' in t or '{' in t or '<' in t:
                    continue
                tgt = os.path.normpath(os.path.join(os.path.dirname(p), t))
                if tgt.startswith(ADOPTER) or ('/' + tgt).endswith(
                        tuple('/' + a for a in ADOPTER if not a.endswith('/'))):
                    continue
                if not os.path.exists(tgt):
                    bad.append(f"{p} → {t}")
        return len(md), bad
    finally:
        os.chdir(cwd)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files, bad = broken_links(a.root)
    print(files)
    print(len(bad))
    print("\n".join(bad))
    return 1 if (bad and a.check) else 0


if __name__ == "__main__":
    sys.exit(main())
