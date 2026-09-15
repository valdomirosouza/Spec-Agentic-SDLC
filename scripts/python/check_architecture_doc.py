"""ARCHITECTURE.md describes this repository, and keeps describing it (#111).

A structure document is the easiest kind of file to be quietly wrong. `docs/repo-structure.md`
opened with "Auto-generated reference" for months while nothing generated it, and the sentence
after it admitted the maintenance was manual — a declaration with nothing behind it, which is the
defect class this series has spent fourteen rounds closing.

So this one is checked rather than trusted, in three ways:

  paths         every repository path the document names exists
  integrations  the rendered-copy table matches render_commands.TARGETS, name for name
  measured      the generated block holds today's numbers

The third is regenerated rather than hand-corrected, the same arrangement the measurement report
uses: `--update` writes the block, `--check` fails when it is stale.

    check_architecture_doc.py [--check] [--update] [--quiet]
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC = os.path.join(ROOT, "ARCHITECTURE.md")
sys.path.insert(0, os.path.join(ROOT, "scripts", "python"))

BEGIN = "<!-- generated: check_architecture_doc.py --update — do not edit by hand -->"
END = "<!-- /generated -->"

# A backticked path: it has a slash or a known root-file extension, and no spaces or placeholders.
PATH = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./*-]*)`')
PLACEHOLDER = ("<", "{", "*")


def named_paths(text):
    out = []
    for m in PATH.finditer(text):
        p = m.group(1)
        if any(c in p for c in PLACEHOLDER):
            continue
        if "/" not in p and not p.startswith("."):
            continue                                   # a bare word, not a path
        out.append(p.rstrip("/"))
    return sorted(set(out))


def missing_paths():
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()
    return [p for p in named_paths(text) if not os.path.exists(os.path.join(ROOT, p))]


def integration_drift():
    """The rendered-copy table must name exactly the integrations render_commands renders."""
    import render_commands
    declared = set(render_commands.TARGETS)
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()
    # Each target's path template, with {name} loosened, must appear in the document.
    missing = [k for k, (tmpl, _) in render_commands.TARGETS.items()
               if tmpl.split("{name}")[0] not in text]
    # Only the Copies table. `.claude/skills` appears above it as the render SOURCE, and the
    # first version of this scan read the source as a stale copy — the section boundary is the
    # declaration of which column a path is in, so the scan respects it rather than special-casing
    # the one name that tripped it.
    start = text.index("### Copies")
    copies = text[start:text.index("\n## ", start)]
    # The FIRST cell of each row — the copy. Scoping to the section was not enough: the render
    # source is named in the second cell of every row of the copies table, so a scan of the whole
    # section read `.claude/skills` as a stale copy of itself. The column is the declaration.
    stale = [d for d in re.findall(r'^\|\s*`(\.[a-z]+/(?:skills|commands))/', copies, re.M)
             if not any(t.startswith(d) for t, _ in render_commands.TARGETS.values())]
    return sorted(missing), sorted(set(stale)), len(declared)


def measurements():
    import mutation_coverage
    named, proved, logic = mutation_coverage.counts() if hasattr(mutation_coverage, "counts") else (None, None, None)
    rows = []
    if named is None:
        out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "python", "mutation_coverage.py"),
                              "--check"], capture_output=True, text=True, cwd=ROOT, timeout=600).stdout
        m = re.search(r'(\d+)/(\d+) named checks proved.*?(\d+) logic check', out, re.S)
        proved, named, logic = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
    rows.append(("Named checks in the verifier", named))
    rows.append(("Of those, proved able to fail", proved))
    rows.append(("Checks containing logic, all proved", logic))
    rows.append(("`sdd-*` commands rendered to four tools",
                 len([d for d in os.listdir(os.path.join(ROOT, ".claude", "skills"))
                      if d.startswith("sdd-")])))
    for layer in ("minimal", "governed", "full"):
        r = subprocess.run(["bash", os.path.join(ROOT, "scripts", "bash", "adopt.sh"),
                            "--list", "--layer", layer, "/tmp/__arch_probe"],
                           capture_output=True, text=True, cwd=ROOT, timeout=300)
        rows.append((f"Files in the `{layer}` layer",
                     len([l for l in r.stdout.split("\n") if l.strip()])))
    return rows


def render_block(rows):
    body = ["| Measured | Value |", "| --- | --- |"]
    body += [f"| {k} | {v} |" for k, v in rows]
    return BEGIN + "\n" + "\n".join(body) + "\n" + END


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(DOC):
        print("ARCHITECTURE.md is missing: this repository describes everyone's structure but its "
              "own", file=sys.stderr)
        return 1
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()

    problems = []
    gone = missing_paths()
    if gone:
        problems.append(f"{len(gone)} path(s) named by ARCHITECTURE.md do not exist: "
                        f"{', '.join(gone[:4])}")
    missing_t, stale_t, n_int = integration_drift()
    if missing_t:
        problems.append(f"render_commands renders to {', '.join(missing_t)}, which "
                        f"ARCHITECTURE.md does not list")
    if stale_t:
        problems.append(f"ARCHITECTURE.md lists {', '.join(stale_t)}, which render_commands does "
                        f"not render to")

    if a.update:
        rows = measurements()
        i, j = text.index(BEGIN), text.index(END) + len(END)
        with open(DOC, "w", encoding="utf-8") as fh:
            fh.write(text[:i] + render_block(rows) + text[j:])
        if not a.quiet:
            print(f"ARCHITECTURE.md measured block updated ({len(rows)} rows)")
        return 1 if problems else 0

    if BEGIN in text:
        current = text[text.index(BEGIN):text.index(END) + len(END)]
        if current != render_block(measurements()):
            problems.append("the measured block is stale — run: check_architecture_doc.py --update")
    else:
        problems.append("the measured block is gone from ARCHITECTURE.md")

    if not a.quiet:
        print(f"ARCHITECTURE.md: {len(named_paths(text))} paths named, {n_int} integrations, "
              f"measured block current" if not problems else "\n".join(problems))
    if a.check and problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
