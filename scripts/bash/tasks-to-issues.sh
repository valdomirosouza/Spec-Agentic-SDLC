#!/usr/bin/env bash
# Create one GitHub issue per open task in the active feature's tasks.md (backs /sdd-taskstoissues).
# Adapted from spec-kit's taskstoissues command; uses the gh CLI instead of the GitHub MCP server.
#
# Usage: tasks-to-issues.sh [--dry-run] [--json] [--label <name>]... [--assignee <login>] [--limit N]
#
# - Skips tasks already marked [X] and tasks whose line already carries "(#N)".
# - Skips tasks that already have an issue whose title contains the task id (open or closed).
# - Title: "<SPEC-ID> T010: <description>"; body carries phase, story, Refs, bundle links.
# - Writes the created issue number back into tasks.md as " (#N)" at the end of the task line.
# - Never creates issues for a spec that is not approved/implemented (Constitution I).
set -e
DRY_RUN=false; JSON=false; LABELS=""; ASSIGNEE=""; LIMIT=0
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --json) JSON=true ;;
        --label) shift; LABELS="$LABELS --label $1" ;;
        --assignee) shift; ASSIGNEE="$1" ;;
        --limit) shift; LIMIT="$1" ;;
        --help|-h) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "ERROR: unknown option $1" >&2; exit 1 ;;
    esac
    shift
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root)
FEATURE_DIR=$(get_feature_dir "$ROOT")
TASKS="$FEATURE_DIR/tasks.md"; SPEC="$FEATURE_DIR/spec.md"
[ -f "$TASKS" ] || { echo "ERROR: tasks.md missing in $FEATURE_DIR — run /sdd-tasks" >&2; exit 1; }
SPEC_ID=$(fm_field "$SPEC" id); SPEC_STATUS=$(fm_field "$SPEC" status)
case "$SPEC_STATUS" in
    approved|implemented) ;;
    *) if ! $DRY_RUN; then
           echo "ERROR: spec status is '$SPEC_STATUS' — issues are only created for an approved spec (Constitution I). Use --dry-run to preview." >&2; exit 1
       fi ;;
esac

REMOTE=$(git -C "$ROOT" config --get remote.origin.url 2>/dev/null || true)
REPO=$(printf '%s' "$REMOTE" | sed -E 's#^(git@github\.com:|https://github\.com/)##; s#\.git$##')
case "$REMOTE" in
    *github.com*) ;;
    *) if ! $DRY_RUN; then echo "ERROR: origin is not a GitHub remote ($REMOTE)" >&2; exit 1; fi; REPO="<owner>/<repo>" ;;
esac
REL_DIR=${FEATURE_DIR#"$ROOT"/}

existing_issue_for() { # task id → issue number or empty
    $DRY_RUN && [ "$REPO" = "<owner>/<repo>" ] && return 0
    gh issue list -R "$REPO" --state all --search "\"$1\" in:title" --json number,title \
        --jq ".[] | select(.title | test(\"\\\\b$1\\\\b\")) | .number" 2>/dev/null | head -1
}

created=0; skipped_done=0; skipped_existing=0; planned=0; phase=""; json_items=""
while IFS= read -r line; do
    case "$line" in
        "## "*) phase=$(printf '%s' "$line" | sed 's/^## //') ; continue ;;
    esac
    printf '%s' "$line" | grep -qE '^- \[( |X|x)\] T[0-9]{3,} ' || continue
    mark=$(printf '%s' "$line" | sed -E 's/^- \[(.)\].*/\1/')
    tid=$(printf '%s' "$line" | sed -E 's/^- \[.\] (T[0-9]{3,}) .*/\1/')
    rest=$(printf '%s' "$line" | sed -E 's/^- \[.\] T[0-9]{3,} //')
    if [ "$mark" != " " ]; then skipped_done=$((skipped_done+1)); continue; fi
    if printf '%s' "$rest" | grep -qE '\(#[0-9]+\)[[:space:]]*$'; then skipped_existing=$((skipped_existing+1)); continue; fi
    par=false; story=""
    printf '%s' "$rest" | grep -q '^\[P\] ' && { par=true; rest=${rest#\[P\] }; }
    if printf '%s' "$rest" | grep -qE '^\[US[0-9]+\] '; then story=$(printf '%s' "$rest" | sed -E 's/^\[(US[0-9]+)\] .*/\1/'); rest=$(printf '%s' "$rest" | sed -E 's/^\[US[0-9]+\] //'); fi
    desc=$(printf '%s' "$rest" | sed -E 's/ — Refs: .*$//')
    refs=$(printf '%s' "$rest" | sed -nE 's/.* — Refs: (.*)$/\1/p')
    num=$(existing_issue_for "$tid" || true)
    if [ -n "$num" ]; then
        skipped_existing=$((skipped_existing+1))
        $JSON || echo "skip   $tid — issue #$num already exists"
        if ! $DRY_RUN; then
            sed -i.bak -E "s|^(- \[ \] $tid .*)$|\1 (#$num)|" "$TASKS" && rm -f "$TASKS.bak"
        fi
        continue
    fi
    title="$SPEC_ID $tid: $desc"
    body="**Spec:** \`$REL_DIR/spec.md\` (\`$SPEC_ID\`, status \`$SPEC_STATUS\`) · **Tasks:** \`$REL_DIR/tasks.md\`
**Phase:** $phase${story:+ · **Story:** $story}${refs:+ · **Refs:** $refs}
**Parallelizable:** $par

## Task

$desc

## Done when

- [ ] Implemented per \`plan.md\` and the requirement(s) above, tests first (Constitution II)
- [ ] Task marked \`[X]\` in \`tasks.md\`; commit trailer \`Refs: #<this issue>, $SPEC_ID, ADR-NNNN\`

_Created by \`/sdd-taskstoissues\` from tasks.md (ADR-0090)._"
    planned=$((planned+1))
    if $DRY_RUN; then
        $JSON && json_items="$json_items{\"task\":\"$tid\",\"title\":$(printf '%s' "$title" | sed 's/"/\\"/g; s/^/"/; s/$/"/'),\"phase\":\"$phase\"}," \
              || printf 'create %s — %s\n' "$tid" "$title"
        continue
    fi
    url=$(gh issue create -R "$REPO" --title "$title" --body "$body" $LABELS ${ASSIGNEE:+--assignee "$ASSIGNEE"})
    num=${url##*/}
    sed -i.bak -E "s|^(- \[ \] $tid .*)$|\1 (#$num)|" "$TASKS" && rm -f "$TASKS.bak"
    created=$((created+1)); $JSON || echo "create $tid → #$num"
    [ "$LIMIT" -gt 0 ] && [ "$created" -ge "$LIMIT" ] && break
done < "$TASKS"

if $JSON; then
    printf '{"SPEC_ID":"%s","REPO":"%s","DRY_RUN":%s,"created":%d,"planned":%d,"skipped_done":%d,"skipped_existing":%d,"items":[%s]}\n' \
        "$SPEC_ID" "$REPO" "$DRY_RUN" "$created" "$planned" "$skipped_done" "$skipped_existing" "${json_items%,}"
else
    echo "---"
    echo "spec: $SPEC_ID ($SPEC_STATUS) · repo: $REPO · dry-run: $DRY_RUN"
    echo "planned: $planned · created: $created · skipped done: $skipped_done · skipped existing: $skipped_existing"
fi
