#!/usr/bin/env bash
# Copy the plan template into the active feature directory (never overwrites an existing plan).
# Usage: setup-plan.sh [--json]
set -e
JSON=false; [ "${1:-}" = "--json" ] && JSON=true
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root)
FEATURE_DIR=$(get_feature_dir "$ROOT")
IMPL_PLAN="$FEATURE_DIR/plan.md"
[ -f "$FEATURE_DIR/spec.md" ] || { echo "ERROR: spec.md missing — run /sdd-specify" >&2; exit 1; }
if [ ! -f "$IMPL_PLAN" ]; then
    cp "$ROOT/templates/plan-template.md" "$IMPL_PLAN"
fi
if $JSON; then
    printf '{"FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","CONSTITUTION":"%s"}\n' \
        "$FEATURE_DIR" "$FEATURE_DIR/spec.md" "$IMPL_PLAN" "$ROOT/memory/constitution.md"
else
    echo "IMPL_PLAN: $IMPL_PLAN"
fi
