#!/usr/bin/env python3
"""Generate and verify the spec registry from the specs on disk (issue #47).

The registry at docs/governance/spec-registry.{json,md} is a generated artefact whose generator
lived in the product repository. Nothing here regenerated it and no check compared it against
disk, so it drifted silently: the seven specs added by the governance packages never appeared,
leaving 50 of 58 entries. The corpus warns against exactly this rot elsewhere and did not protect
itself from it.

  --build            regenerate both files from the frontmatter of specs/**/*.md
  --check            exit 1 when either file disagrees with disk (CI mode)
  --json             print the computed registry to stdout without writing

A spec is any specs/**/*.md with ADR-0085 frontmatter carrying an `id`. READMEs and templates are
not specs and are skipped by the same rule check_control_matrix and check-corpus use.
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JSON_PATH = "docs/governance/spec-registry.json"
MD_PATH = "docs/governance/spec-registry.md"
ID_RE = re.compile(r"^SPEC-[A-Z][A-Z0-9]{1,5}-[0-9]{3}$")
LIST_FIELDS = ("governing_adrs", "new_adrs_required", "implemented_by", "verified_by",
               "related_specs", "requirement_tests")
SCALAR_FIELDS = ("id", "kind", "status", "owner", "issue", "superseded_by", "last_updated")


def is_spec_file(path):
    base = os.path.basename(path)
    if base == "README.md" or "template" in base.lower() or "TEMPLATE" in base:
        return False
    rel = path.replace(os.sep, "/")
    if "/checklists/" in rel or "/contracts/" in rel:
        return False
    if rel.split("/")[-1] in ("plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md"):
        return False
    return True


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    block = text[4:end]
    out, key = {}, None
    for line in block.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            val = re.sub(r"\s+#.*$", "", val).strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                out[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            elif val == "":
                out[key] = []
            else:
                out[key] = val.strip('"').strip("'")
        elif line.lstrip().startswith("- ") and key:
            if not isinstance(out.get(key), list):
                out[key] = []
            out[key].append(line.lstrip()[2:].strip().strip('"').strip("'"))
    return out


KINDS = ("spec", "policy", "feature-spec", "threat-model")
STATUSES = ("draft", "in-review", "approved", "implemented", "superseded")


def validate(entry):
    """Refuse a malformed spec rather than registering it. ID_RE was defined and never used, so the
    registry accepted any id, any kind and any status, and a duplicate (id, kind) went unreported
    (R4-T5)."""
    errs = []
    if not ID_RE.match(entry.get("id", "")):
        errs.append(f"{entry['path']}: id {entry.get('id')!r} does not match {ID_RE.pattern}")
    if entry.get("kind") not in KINDS:
        errs.append(f"{entry['path']}: kind {entry.get('kind')!r} not in {KINDS}")
    if entry.get("status") not in STATUSES:
        errs.append(f"{entry['path']}: status {entry.get('status')!r} not in {STATUSES}")
    return errs


# Exemption is by DECLARATION, never by shape. `adopter:`, `ci:` and `planned:` are things the
# spec author wrote down and can be held to; a directory prefix is the tool guessing on their
# behalf. The guess was widened twice to quieten the output and ended up exempting 145 of 146
# evidence paths, including `tests/` and `.github/workflows/`, which exist HERE — so the rule
# stopped being able to catch the SPEC-FEAT-001 case that created it (R5-T4).
EXPLICIT_MARKERS = ("adopter:", "ci:", "planned:")

# Used only to SORT the unresolved paths, never to excuse them: a path shaped like something the
# adopting repository provides is a missing `adopter:` marker (minor, has a known fix), while any
# other dead path is the real finding. Both are reported; neither is silently dropped.
ADOPTER_SHAPED = ("src/", "tests/", "services/", "frontend/", "infrastructure/",
                  "scripts/governance/", "alembic/", "reports/",
                  ".github/workflows/", "services.yaml", "Makefile", "pyproject.toml")


def unresolved_evidence(entry):
    """Evidence paths that neither resolve on disk nor carry an explicit marker.

    Returns (unresolved, unmarked): `unmarked` is adopter-shaped and wants a marker; `unresolved`
    resolves nowhere and belongs nowhere, which is what SPEC-FEAT-001 had before it was marked."""
    unresolved, unmarked = [], []
    for field in ("implemented_by", "verified_by"):
        for p in entry.get(field, []):
            path = p.split("#")[0].strip()
            if path.startswith(EXPLICIT_MARKERS):
                continue
            if os.path.exists(os.path.join(ROOT, path)):
                continue
            (unmarked if path.startswith(ADOPTER_SHAPED) else unresolved).append(p)
    return unresolved, unmarked


def collect():
    specs = []
    for path in sorted(glob.glob(os.path.join(ROOT, "specs", "**", "*.md"), recursive=True)):
        if not is_spec_file(path):
            continue
        fm = parse_frontmatter(open(path, encoding="utf-8").read())
        if not fm or not fm.get("id"):
            continue
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        entry = {"path": rel}
        for f in SCALAR_FIELDS:
            v = fm.get(f)
            if f == "issue":
                entry[f] = int(v) if isinstance(v, str) and v.isdigit() else None
            elif v not in (None, ""):
                entry[f] = v
        for f in LIST_FIELDS:
            v = fm.get(f)
            entry[f] = v if isinstance(v, list) else ([] if v in (None, "") else [v])
        specs.append(entry)
    specs.sort(key=lambda e: (e.get("id", ""), e["path"]))
    for e in specs:
        e["unresolved_evidence"], e["unmarked_evidence"] = unresolved_evidence(e)
    return specs


def problems(specs):
    """Validation errors plus duplicate (id, kind) among live specs."""
    errs = []
    for e in specs:
        errs += validate(e)
    live = [e for e in specs if e.get("status") != "superseded"]
    seen = {}
    for e in live:
        key = (e.get("id"), e.get("kind"))
        if key in seen:
            errs.append(f"duplicate (id, kind) {key[0]}/{key[1]}: {seen[key]} and {e['path']}")
        seen[key] = e["path"]
    return errs


def render_json(specs):
    return json.dumps({
        "$comment": ("Generated by scripts/python/build_spec_registry.py from the ADR-0085 frontmatter "
                     "of specs/**/*.md. Do not edit by hand; run --build. check-corpus C13 fails when "
                     "this file disagrees with disk."),
        "generated_from": "specs/**/*.md",
        "count": len(specs),
        "specs": specs,
    }, indent=2, ensure_ascii=False) + "\n"


def _evidence(entry, field):
    """`n` when every path is accounted for — never a bare count over paths nobody checked."""
    paths = entry.get(field, [])
    bad = [p for p in entry.get("unresolved_evidence", []) if p in paths]
    todo = [p for p in entry.get("unmarked_evidence", []) if p in paths]
    notes = ([f"{len(bad)} unresolved"] if bad else []) + ([f"{len(todo)} unmarked"] if todo else [])
    return f"{len(paths)}" + (f" ({', '.join(notes)})" if notes else "")


def render_md(specs):
    from collections import Counter
    by_status = Counter(s.get("status", "?") for s in specs)
    by_kind = Counter(s.get("kind", "?") for s in specs)
    lines = [
        "<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->",
        "",
        "# Spec registry",
        "",
        "> **Generated** by `scripts/python/build_spec_registry.py --build` from the ADR-0085",
        "> frontmatter of every spec on disk. Do not edit by hand. `check-corpus.sh` C13 fails when",
        "> this file or its JSON companion disagrees with disk, which is what let the registry drift",
        "> to 50 of 58 entries before issue #47.",
        "",
        f"**{len(specs)} specs** · " + " · ".join(f"{k}: {v}" for k, v in sorted(by_status.items())),
        "",
        "| Spec | Kind | Status | Owner | Issue | Path | Governing ADRs | Impl | Verif |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in specs:
        adrs = ", ".join(s.get("governing_adrs", [])) or "—"
        lines.append(
            f"| {s.get('id','?')} | {s.get('kind','?')} | {s.get('status','?')} | "
            f"{s.get('owner','—')} | {s.get('issue') or ''} | `{s['path']}` | {adrs} | "
            f"{_evidence(s, 'implemented_by')} | {_evidence(s, 'verified_by')} |"
        )
    lines += ["", "## By kind", "", "| Kind | Count |", "| --- | --- |"]
    lines += [f"| {k} | {v} |" for k, v in sorted(by_kind.items())]

    unresolved = [(s, p) for s in specs for p in s.get("unresolved_evidence", [])]
    backlog = [(s, p) for s in specs for p in s.get("unmarked_evidence", [])]
    lines += [
        "",
        "## Evidence accounting",
        "",
        "An evidence path is accounted for when it resolves on disk or carries an explicit",
        "`adopter:` / `ci:` / `planned:` marker. Directory shape is not an exemption: exempting",
        "anything under `src/`, `tests/` or `.github/workflows/` left 145 of 146 paths unchecked",
        "and the rule could no longer catch the case it was written for (R5-T4).",
        "",
        f"- **Unresolved — resolves nowhere, marked nowhere:** {len(unresolved)}. This is the finding.",
        f"- **Unmarked — shaped like an adopter path, missing its marker:** {len(backlog)} "
        f"across {len({s['id'] for s, _ in backlog})} specs. Minor: the fix is one prefix per line.",
    ]
    if unresolved:
        lines += ["", "| Spec | Path |", "| --- | --- |"]
        lines += [f"| {s.get('id','?')} | `{p}` |" for s, p in unresolved]
    if backlog:
        from collections import Counter as _C
        per = _C(s.get("id", "?") for s, _ in backlog)
        lines += ["", "### Marking backlog", "", "| Spec | Paths to mark |", "| --- | --- |"]
        lines += [f"| {k} | {v} |" for k, v in sorted(per.items())]
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    specs = collect()
    errs = problems(specs)
    # Validate BEFORE choosing an output format. `and not a.json` let --json skip validation
    # entirely — and --json is exactly what check_data_quality.py consumes, so the one caller
    # that feeds a governance gate was the one caller the gate could not protect (R5-T6).
    if errs:
        print(f"spec registry: {len(errs)} malformed or duplicate spec(s) — refusing to register",
              file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    js, md = render_json(specs), render_md(specs)

    if a.json:
        print(js, end="")
        return 0

    if a.build:
        for rel, content in ((JSON_PATH, js), (MD_PATH, md)):
            with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
                fh.write(content)
        print(f"spec registry rebuilt: {len(specs)} specs → {JSON_PATH}, {MD_PATH}")
        return 0

    # --check (default)
    errs = []
    for rel, content in ((JSON_PATH, js), (MD_PATH, md)):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            errs.append(f"{rel}: missing")
            continue
        on_disk = open(p, encoding="utf-8").read()
        if on_disk != content:
            if rel == JSON_PATH:
                try:
                    have = {e["path"] for e in json.loads(on_disk).get("specs", [])}
                except Exception:
                    have = set()
                want = {e["path"] for e in specs}
                for p_ in sorted(want - have):
                    errs.append(f"{rel}: spec on disk missing from the registry: {p_}")
                for p_ in sorted(have - want):
                    errs.append(f"{rel}: registry names a spec that is not on disk: {p_}")
                if have == want:
                    errs.append(f"{rel}: same specs, but a field differs — run --build")
            else:
                errs.append(f"{rel}: out of date — run --build")

    if errs:
        print(f"spec registry: {len(errs)} problem(s) — run: python3 scripts/python/build_spec_registry.py --build")
        for e in errs:
            print(f"  {e}")
        return 1
    if not a.quiet:
        print(f"spec registry: up to date ({len(specs)} specs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
