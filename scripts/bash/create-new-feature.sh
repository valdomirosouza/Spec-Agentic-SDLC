#!/usr/bin/env bash
# Create the feature directory + spec.md for a new feature (adapted from spec-kit's
# create-new-feature.sh, using this repository's SPEC-<DOMAIN>-NNN id grammar, ADR-0085).
#
# Usage: create-new-feature.sh [--json] [--dry-run] [--domain FEAT] [--short-name <slug>] [--issue N] <description>
#
# Output (JSON mode): {"SPEC_ID":"SPEC-FEAT-004","FEATURE_DIR":"…","SPEC_FILE":"…","BRANCH_NAME":"feature/SPEC-FEAT-004-slug"}
# The script never creates or switches git branches — that is a human decision (Constitution V).

set -e

JSON_MODE=false; DRY_RUN=false; DOMAIN="FEAT"; SHORT_NAME=""; ISSUE="null"; ARGS=""
while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_MODE=true ;;
        --dry-run) DRY_RUN=true ;;
        --domain) shift; DOMAIN=$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]') ;;
        --short-name) shift; SHORT_NAME="$1" ;;
        --issue) shift; ISSUE="$1" ;;
        --help|-h)
            sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) ARGS="$ARGS $1" ;;
    esac
    shift
done
DESCRIPTION=$(printf '%s' "$ARGS" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
[ -n "$DESCRIPTION" ] || { echo "ERROR: feature description required" >&2; exit 1; }

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root)
FEATURES_DIR="$ROOT/specs/features"

# Next number for the domain: scan directory names and spec ids already in use.
highest=0
for d in "$FEATURES_DIR"/SPEC-"$DOMAIN"-[0-9]*; do
    [ -e "$d" ] || continue
    n=$(basename "$d" | sed -E "s/^SPEC-$DOMAIN-([0-9]+).*/\1/")
    n=$((10#$n)); [ "$n" -gt "$highest" ] && highest=$n
done
for f in "$ROOT"/specs/*/*.md "$ROOT"/specs/*/*/*.md; do
    [ -f "$f" ] || continue
    id=$(fm_field "$f" id)
    case "$id" in
        SPEC-$DOMAIN-[0-9]*)
            n=$(printf '%s' "$id" | sed -E "s/^SPEC-$DOMAIN-([0-9]+).*/\1/"); n=$((10#$n))
            [ "$n" -gt "$highest" ] && highest=$n ;;
    esac
done
NUM=$(printf '%03d' $((highest + 1)))
SPEC_ID="SPEC-$DOMAIN-$NUM"

# Slug: lowercase, ASCII, stop words removed, ≤ 4 words.
if [ -z "$SHORT_NAME" ]; then
    STOP='^(a|an|the|to|for|of|in|on|at|by|with|from|is|are|be|and|or|i|we|want|need|add|new|feature|implement|create)$'
    words=""; count=0
    for w in $(printf '%s' "$DESCRIPTION" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed 's/[^a-z0-9]/ /g'); do
        printf '%s' "$w" | grep -qE "$STOP" && continue
        [ ${#w} -ge 3 ] || continue
        words="$words-$w"; count=$((count + 1)); [ $count -ge 4 ] && break
    done
    SHORT_NAME=${words#-}
    [ -n "$SHORT_NAME" ] || SHORT_NAME="feature"
fi
SLUG=$(printf '%s' "$SHORT_NAME" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -e 's/[^a-z0-9]/-/g' -e 's/--*/-/g' -e 's/^-//' -e 's/-$//')

FEATURE_DIR="$FEATURES_DIR/$SPEC_ID-$SLUG"
SPEC_FILE="$FEATURE_DIR/spec.md"
BRANCH_NAME="feature/$SPEC_ID-$SLUG"

if [ "$DRY_RUN" != true ]; then
    mkdir -p "$FEATURE_DIR/checklists" "$FEATURE_DIR/contracts"
    TODAY=$(date +%Y-%m-%d)
    sed -e "s/^id: SPEC-FEAT-NNN.*/id: $SPEC_ID/" \
        -e "s/^issue: null.*/issue: $ISSUE/" \
        -e "s/^last_updated: YYYY-MM-DD/last_updated: $TODAY/" \
        -e "s|\*\*Input\*\*: <the user's feature description.*|**Input**: $DESCRIPTION|" \
        "$ROOT/templates/spec-template.md" > "$SPEC_FILE"
    persist_feature_dir "$ROOT" "$FEATURE_DIR"
fi

if $JSON_MODE; then
    printf '{"SPEC_ID":"%s","FEATURE_DIR":"%s","SPEC_FILE":"%s","BRANCH_NAME":"%s","DRY_RUN":%s}\n' \
        "$SPEC_ID" "$FEATURE_DIR" "$SPEC_FILE" "$BRANCH_NAME" "$DRY_RUN"
else
    echo "SPEC_ID:     $SPEC_ID"
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "SPEC_FILE:   $SPEC_FILE"
    echo "BRANCH_NAME: $BRANCH_NAME   (create it yourself: git checkout -b $BRANCH_NAME)"
fi
