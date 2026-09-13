#!/usr/bin/env bash
# Compare the tracked github/spec-kit files between the pinned commit (docs/sdlc/spec-kit-upstream.json)
# and a newer ref (default: main). Prints which tracked files changed so the quarterly review
# (docs/sdlc/spec-kit-sync.md) knows what to look at. Read-only; needs `gh` (authenticated) and python3.
# Usage: spec-kit-diff.sh [--ref <ref>] [--show <path>]
set -e
REF="main"; SHOW=""
while [ $# -gt 0 ]; do case "$1" in --ref) shift; REF="$1" ;; --show) shift; SHOW="$1" ;; --help|-h) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; *) echo "ERROR: unknown option $1" >&2; exit 1 ;; esac; shift; done
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root); PIN="$ROOT/docs/sdlc/spec-kit-upstream.json"
REPO=$(python3 -c "import json;print(json.load(open('$PIN'))['repository'])")
COMMIT=$(python3 -c "import json;print(json.load(open('$PIN'))['commit'])")
PATHS=$(python3 -c "import json;print('\n'.join(json.load(open('$PIN'))['tracked_paths']))")
fetch() { gh api "repos/$REPO/contents/$2?ref=$1" -q '.content' 2>/dev/null | tr -d '\n' | base64 -d 2>/dev/null || true; }
if [ -n "$SHOW" ]; then
    T=$(mktemp -d); fetch "$COMMIT" "$SHOW" > "$T/pinned"; fetch "$REF" "$SHOW" > "$T/ref"
    diff -u --label "$SHOW@$COMMIT" --label "$SHOW@$REF" "$T/pinned" "$T/ref" || true; rm -rf "$T"; exit 0
fi
HEAD_SHA=$(gh api "repos/$REPO/commits/$REF" -q '.sha' | cut -c1-7)
LATEST=$(gh api "repos/$REPO/releases/latest" -q '.tag_name' 2>/dev/null || echo "?")
echo "upstream $REPO: pinned $COMMIT → $REF ($HEAD_SHA); latest release $LATEST"
changed=0; missing=0
for p in $PATHS; do
    a=$(fetch "$COMMIT" "$p" | shasum | cut -c1-12); b=$(fetch "$REF" "$p" | shasum | cut -c1-12)
    if [ -z "$(fetch "$REF" "$p")" ]; then echo "  missing upstream: $p"; missing=$((missing+1))
    elif [ "$a" != "$b" ]; then echo "  changed: $p"; changed=$((changed+1)); fi
done
echo "tracked: $(printf '%s\n' "$PATHS" | wc -l | tr -d ' ') · changed: $changed · missing: $missing"
[ "$changed" = 0 ] && [ "$missing" = 0 ] && echo "nothing to review" || echo "review each changed file: spec-kit-diff.sh --show <path>; record decisions per docs/sdlc/spec-kit-sync.md"
