#!/usr/bin/env python3
"""Render the /sdd-* commands for other coding agents from .claude/skills/sdd-*/SKILL.md (ADR-0091, #17).

Claude Code is canonical. Layouts follow github/spec-kit v1.0.6 integrations:
  copilot  .github/skills/<name>/SKILL.md      ($ARGUMENTS kept)
  cursor   .cursor/skills/<name>/SKILL.md      ($ARGUMENTS kept)
  codex    .agents/skills/<name>/SKILL.md      ($ARGUMENTS kept)
  gemini   .gemini/commands/<name>.toml        (description = "…", prompt = \"\"\"…\"\"\", $ARGUMENTS → {{args}})

  --render [--out DIR]   write the files (default: repository root)
  --check                render to a temp dir and fail if the committed copies differ
"""
import sys, os, glob, re, tempfile, filecmp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_GLOB = ".claude/skills/sdd-*/SKILL.md"
TARGETS = {
    "copilot": (".github/skills/{name}/SKILL.md", "md"),
    "cursor":  (".cursor/skills/{name}/SKILL.md", "md"),
    "codex":   (".agents/skills/{name}/SKILL.md", "md"),
    "gemini":  (".gemini/commands/{name}.toml", "toml"),
}
NOTE_MD = "<!-- generated from {src} by scripts/python/render_commands.py — edit the source, then re-render (ADR-0091) -->"
NOTE_TOML = "# generated from {src} by scripts/python/render_commands.py — edit the source, then re-render (ADR-0091)"

def split_frontmatter(text):
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    fm = text[4:end]
    body = text[text.find("\n", end + 1) + 1:]
    return fm, body

def description(fm):
    m = re.search(r"^description:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""

def render_md(src_rel, text):
    fm, body = split_frontmatter(text)
    note = NOTE_MD.format(src=src_rel)
    return f"---\n{fm}\n---\n\n{note}\n\n{body.lstrip()}" if fm else f"{note}\n\n{text}"

def render_toml(src_rel, text):
    fm, body = split_frontmatter(text)
    desc = description(fm).replace("\\", "\\\\").replace('"', '\\"')
    prompt = body.lstrip().replace("$ARGUMENTS", "{{args}}").replace('"""', '\\"\\"\\"')
    return f'{NOTE_TOML.format(src=src_rel)}\ndescription = "{desc}"\n\nprompt = """\n{prompt.rstrip()}\n"""\n'

def render_all(out_root):
    written = []
    for src in sorted(glob.glob(os.path.join(ROOT, SRC_GLOB))):
        src_rel = os.path.relpath(src, ROOT)
        name = os.path.basename(os.path.dirname(src))
        text = open(src, encoding="utf-8").read()
        for agent, (pattern, kind) in TARGETS.items():
            rel = pattern.format(name=name)
            out = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            content = render_md(src_rel, text) if kind == "md" else render_toml(src_rel, text)
            open(out, "w", encoding="utf-8").write(content)
            written.append(rel)
    return written

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--render"
    if mode == "--render":
        out = ROOT
        if "--out" in sys.argv:
            out = sys.argv[sys.argv.index("--out") + 1]
        w = render_all(out)
        print(f"rendered {len(w)} file(s) into {out}")
        return 0
    if mode == "--check":
        tmp = tempfile.mkdtemp()
        w = render_all(tmp)

        # Only integrations this repository actually installed. A repository that adopted the corpus
        # asking for `claude` alone has no `.github/skills` or `.cursor/skills` at all, and calling
        # forty never-installed files "stale" made a fresh adoption look broken when it was simply
        # not using those agents (#107). An installed integration missing one file is still stale.
        installed = set()
        for agent, (pattern, kind) in TARGETS.items():
            base = os.path.join(ROOT, pattern.split("{name}")[0].rstrip("/"))
            if os.path.isdir(base):
                installed.add(agent)

        def agent_of(rel):
            for agent, (pattern, kind) in TARGETS.items():
                if rel.startswith(pattern.split("{name}")[0]):
                    return agent
            return None

        w = [rel for rel in w if agent_of(rel) in installed]
        stale = [rel for rel in w if not os.path.exists(os.path.join(ROOT, rel)) or not filecmp.cmp(os.path.join(tmp, rel), os.path.join(ROOT, rel), shallow=False)]
        # committed copies that no longer have a source
        extra = []
        for agent, (pattern, kind) in TARGETS.items():
            base = pattern.split("{name}")[0]
            for p in glob.glob(os.path.join(ROOT, base, "sdd-*" + ("" if kind == "md" else ".toml"))):
                rel = os.path.relpath(p if kind == "toml" else os.path.join(p, "SKILL.md"), ROOT)
                if rel not in w:
                    extra.append(rel)
        if stale or extra:
            print(f"{len(stale)} stale, {len(extra)} orphaned rendered command file(s) — run: python3 scripts/python/render_commands.py --render")
            for r in stale: print(f"  stale: {r}")
            for r in extra: print(f"  orphan: {r}")
            return 1
        print(f"{len(w)} rendered command files up to date")
        return 0
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main())
