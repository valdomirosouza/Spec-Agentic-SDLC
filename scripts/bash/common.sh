#!/usr/bin/env bash
# Shared helpers for the SDD scripts (adapted from github/spec-kit scripts/bash/common.sh).
# Portable to macOS bash 3.2: no associative arrays, no mapfile, no ${var^^}.

set -e

get_repo_root() {
    # Prefer the git root; fall back to the directory that holds memory/constitution.md.
    local root
    if root=$(git rev-parse --show-toplevel 2>/dev/null); then
        printf '%s\n' "$root"
        return 0
    fi
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/memory/constitution.md" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "ERROR: not inside a Spec-Agentic-SDLC repository (no git root, no memory/constitution.md)" >&2
    return 1
}

state_file() {
    printf '%s/.sdd/feature.json\n' "$1"
}

# Resolve the active feature directory:
#   1. $SDD_FEATURE_DIRECTORY (absolute or repo-relative)
#   2. .sdd/feature.json  {"feature_directory": "specs/features/SPEC-FEAT-003-slug"}
#   3. the current branch name feature/<SPEC-ID>-<slug> → specs/features/<SPEC-ID>-<slug>
get_feature_dir() {
    local root="$1" candidate=""
    if [ -n "${SDD_FEATURE_DIRECTORY:-}" ]; then
        case "$SDD_FEATURE_DIRECTORY" in
            /*) candidate="$SDD_FEATURE_DIRECTORY" ;;
            *)  candidate="$root/$SDD_FEATURE_DIRECTORY" ;;
        esac
    elif [ -f "$(state_file "$root")" ]; then
        candidate=$(sed -n 's/.*"feature_directory"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$(state_file "$root")" | head -1)
        case "$candidate" in
            /*) ;;
            "") ;;
            *)  candidate="$root/$candidate" ;;
        esac
    fi
    if [ -z "$candidate" ]; then
        local branch
        branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
        case "$branch" in
            feature/*|fix/*|hotfix/*|chore/*) candidate="$root/specs/features/${branch#*/}" ;;
        esac
    fi
    if [ -z "$candidate" ] || [ ! -d "$candidate" ]; then
        echo "ERROR: feature directory not found. Run /sdd-specify first, set SDD_FEATURE_DIRECTORY, or check out feature/<SPEC-ID>-<slug>." >&2
        return 1
    fi
    printf '%s\n' "$candidate"
}

persist_feature_dir() {
    local root="$1" dir="$2" rel
    rel=${dir#"$root"/}
    mkdir -p "$root/.sdd"
    printf '{\n  "feature_directory": "%s"\n}\n' "$rel" > "$(state_file "$root")"
}

json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk 'BEGIN{ORS="\\n"} {print}' | sed 's/\\n$//'
}

# Frontmatter field reader: fm_field <file> <key>
fm_field() {
    awk -v key="$2" '
        NR==1 && $0!="---" {exit}
        /^---$/ {c++; if (c==2) exit; next}
        $0 ~ "^"key":" {sub("^"key":[ ]*",""); sub("[ ]*#.*",""); print; exit}
    ' "$1"
}

check_file() { [ -f "$1" ] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir()  { [ -d "$1" ] && [ -n "$(ls -A "$1" 2>/dev/null)" ] && echo "  ✓ $2" || echo "  ✗ $2"; }
