#!/usr/bin/env bash
# Copy a layer of the Spec-Agentic-SDLC corpus into a product repository (issue #16, ADR-0091).
# The corpus equivalent of spec-kit's `specify init --here`, without a CLI runtime.
#
# Usage: adopt.sh (--here | <target-dir>) [--layer minimal|governed|full]
#                 [--integration claude|copilot|cursor|gemini|codex]... [--force] [--dry-run] [--json]
#
# Layers (SETUP.md §1):
#   minimal   memory/ templates/ scripts/bash/ scripts/python/ specs/spec-frontmatter.schema.json
#             specs/features/README.md .claude/skills/sdd-*/ .claude/settings.json .claude/hooks/
#             .markdownlint-cli2.jsonc version.txt
#   governed  minimal + CLAUDE.md AGENTS.md CLAUDE_SESSION_INIT.md SETUP.md skills/ .claude/ (all)
#             docs/adr/ docs/process/ docs/sdlc/ docs/governance/ docs/reference/ specs/security/
#             harness/ .github/ (templates, CODEOWNERS, workflows/corpus-check.yml)
#   full      governed + everything else under docs/ specs/ prompts/ and the root policies
# Integrations add the rendered per-agent command copies (scripts/bash/render-commands.sh):
#   claude → .claude/skills (always included) · copilot → .github/skills · cursor → .cursor/skills
#   gemini → .gemini/commands · codex → .agents/skills
# Existing files are never overwritten unless --force. Nothing is deleted. No git command runs.
set -e
TARGET=""; LAYER="minimal"; INTEGRATIONS="claude"; FORCE=false; DRY=false; JSON=false
while [ $# -gt 0 ]; do
    case "$1" in
        --here) TARGET="$PWD" ;;
        --layer) shift; LAYER="$1" ;;
        --integration) shift; INTEGRATIONS="$INTEGRATIONS $1" ;;
        --force) FORCE=true ;;
        --dry-run) DRY=true ;;
        --json) JSON=true ;;
        --help|-h) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) echo "ERROR: unknown option $1" >&2; exit 1 ;;
        *) TARGET="$1" ;;
    esac
    shift
done
[ -n "$TARGET" ] || { echo "ERROR: give --here or a target directory" >&2; exit 1; }
case "$LAYER" in minimal|governed|full) ;; *) echo "ERROR: --layer must be minimal, governed or full" >&2; exit 1 ;; esac
SRC="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$TARGET"; TARGET="$(CDPATH="" cd "$TARGET" && pwd)"
[ "$SRC" != "$TARGET" ] || { echo "ERROR: target is the corpus itself" >&2; exit 1; }

MINIMAL="memory templates scripts/bash scripts/python specs/spec-frontmatter.schema.json specs/features/README.md .claude/settings.json .claude/hooks .markdownlint-cli2.jsonc version.txt LICENSE"
GOVERNED="CLAUDE.md AGENTS.md CLAUDE_SESSION_INIT.md SETUP.md skills .claude docs/adr docs/process docs/sdlc docs/governance docs/reference specs/security specs/README.md harness .github/ISSUE_TEMPLATE .github/PULL_REQUEST_TEMPLATE .github/DISCUSSION_TEMPLATE .github/pull_request_template.md .github/CODEOWNERS .github/workflows/corpus-check.yml tests/scripts"
FULL="docs specs prompts README.md CONTRIBUTING.md CUSTOMISING.md SECURITY.md PRIVACY.md CODE_OF_CONDUCT.md CHANGELOG.md CITATION.cff"

paths="$MINIMAL"
for d in "$SRC"/.claude/skills/sdd-*; do paths="$paths ${d#$SRC/}"; done
[ "$LAYER" != minimal ] && paths="$paths $GOVERNED"
[ "$LAYER" = full ] && paths="$paths $FULL"
for i in $INTEGRATIONS; do
    case "$i" in
        claude) ;;
        copilot) paths="$paths .github/skills" ;;
        cursor) paths="$paths .cursor/skills" ;;
        gemini) paths="$paths .gemini/commands" ;;
        codex) paths="$paths .agents/skills" ;;
        *) echo "ERROR: unknown integration $i" >&2; exit 1 ;;
    esac
done

# Expand to a unique, sorted file list relative to SRC.
files=$(for p in $paths; do
    if [ -d "$SRC/$p" ]; then (cd "$SRC" && find "$p" -type f); elif [ -f "$SRC/$p" ]; then echo "$p"; fi
done | grep -v '/\.DS_Store$' | sort -u)

copied=0; skipped=0; total=0; skipped_list=""
for f in $files; do
    total=$((total+1))
    if [ -e "$TARGET/$f" ] && ! $FORCE; then skipped=$((skipped+1)); skipped_list="$skipped_list $f"; continue; fi
    if ! $DRY; then mkdir -p "$TARGET/$(dirname "$f")"; cp -p "$SRC/$f" "$TARGET/$f"; fi
    copied=$((copied+1))
done

if $JSON; then
    printf '{"TARGET":"%s","LAYER":"%s","INTEGRATIONS":"%s","DRY_RUN":%s,"FORCE":%s,"total":%d,"copied":%d,"skipped_existing":%d}\n' \
        "$TARGET" "$LAYER" "$(printf '%s' "$INTEGRATIONS" | sed 's/^ *//')" "$DRY" "$FORCE" "$total" "$copied" "$skipped"
else
    echo "adopt: layer=$LAYER integrations=[$INTEGRATIONS] target=$TARGET dry-run=$DRY"
    echo "files: $total · copied: $copied · skipped (already present): $skipped"
    [ -n "$skipped_list" ] && ! $FORCE && echo "  re-run with --force to overwrite:$(printf '%s' "$skipped_list" | tr ' ' '\n' | head -10 | sed 's/^/\n    /')" | head -12
    echo "next: read SETUP.md §2 (what your repository provides), then run /sdd-constitution and /sdd-specify."
fi
