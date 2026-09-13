#!/usr/bin/env bash
# Copy the plan template — and the research / data-model / quickstart / contracts templates —
# into the active feature directory. Never overwrites an existing file.
# Usage: setup-plan.sh [--json]
set -e
JSON=false; [ "${1:-}" = "--json" ] && JSON=true
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root)
FEATURE_DIR=$(get_feature_dir "$ROOT")
IMPL_PLAN="$FEATURE_DIR/plan.md"
RESEARCH="$FEATURE_DIR/research.md"
DATA_MODEL="$FEATURE_DIR/data-model.md"
QUICKSTART="$FEATURE_DIR/quickstart.md"
CONTRACTS="$FEATURE_DIR/contracts"
[ -f "$FEATURE_DIR/spec.md" ] || { echo "ERROR: spec.md missing — run /sdd-specify" >&2; exit 1; }

copy_if_absent() { # template target
    if [ ! -f "$2" ]; then cp "$ROOT/templates/$1" "$2"; fi
}
copy_if_absent plan-template.md "$IMPL_PLAN"
copy_if_absent research-template.md "$RESEARCH"
copy_if_absent data-model-template.md "$DATA_MODEL"
copy_if_absent quickstart-template.md "$QUICKSTART"
mkdir -p "$CONTRACTS"
copy_if_absent contracts-README-template.md "$CONTRACTS/README.md"

if $JSON; then
    printf '{"FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","RESEARCH":"%s","DATA_MODEL":"%s","QUICKSTART":"%s","CONTRACTS":"%s","CONSTITUTION":"%s"}\n' \
        "$FEATURE_DIR" "$FEATURE_DIR/spec.md" "$IMPL_PLAN" "$RESEARCH" "$DATA_MODEL" "$QUICKSTART" "$CONTRACTS" "$ROOT/memory/constitution.md"
else
    echo "IMPL_PLAN:  $IMPL_PLAN"
    echo "RESEARCH:   $RESEARCH"
    echo "DATA_MODEL: $DATA_MODEL"
    echo "QUICKSTART: $QUICKSTART"
    echo "CONTRACTS:  $CONTRACTS/"
fi
