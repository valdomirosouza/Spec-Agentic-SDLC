#!/usr/bin/env bash
# Resolve the active feature's paths and check which SDD artefacts exist
# (adapted from spec-kit's check-prerequisites.sh).
#
# Usage: check-prerequisites.sh [--json] [--paths-only] [--require-spec] [--require-plan]
#                               [--require-tasks] [--require-approved] [--include-tasks]
#
# JSON: {"FEATURE_DIR":..,"SPEC_ID":..,"SPEC_STATUS":..,"FEATURE_SPEC":..,"IMPL_PLAN":..,"TASKS":..,"AVAILABLE_DOCS":[..]}

set -e
JSON=false; PATHS_ONLY=false; REQ_SPEC=false; REQ_PLAN=false; REQ_TASKS=false; REQ_APPROVED=false; INC_TASKS=false
while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON=true ;;
        --paths-only) PATHS_ONLY=true ;;
        --require-spec) REQ_SPEC=true ;;
        --require-plan) REQ_PLAN=true ;;
        --require-tasks) REQ_TASKS=true ;;
        --require-approved) REQ_APPROVED=true ;;
        --include-tasks) INC_TASKS=true ;;
        --help|-h) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "ERROR: unknown option $1" >&2; exit 1 ;;
    esac
    shift
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root)
FEATURE_DIR=$(get_feature_dir "$ROOT")
FEATURE_SPEC="$FEATURE_DIR/spec.md"; IMPL_PLAN="$FEATURE_DIR/plan.md"; TASKS="$FEATURE_DIR/tasks.md"
RESEARCH="$FEATURE_DIR/research.md"; DATA_MODEL="$FEATURE_DIR/data-model.md"
CONTRACTS="$FEATURE_DIR/contracts"; QUICKSTART="$FEATURE_DIR/quickstart.md"; CHECKLISTS="$FEATURE_DIR/checklists"
SPEC_ID=""; SPEC_STATUS=""
if [ -f "$FEATURE_SPEC" ]; then SPEC_ID=$(fm_field "$FEATURE_SPEC" id); SPEC_STATUS=$(fm_field "$FEATURE_SPEC" status); fi

if ! $PATHS_ONLY; then
    $REQ_SPEC  && [ ! -f "$FEATURE_SPEC" ] && { echo "ERROR: spec.md missing in $FEATURE_DIR — run /sdd-specify" >&2; exit 1; }
    $REQ_PLAN  && [ ! -f "$IMPL_PLAN" ]    && { echo "ERROR: plan.md missing — run /sdd-plan" >&2; exit 1; }
    $REQ_TASKS && [ ! -f "$TASKS" ]        && { echo "ERROR: tasks.md missing — run /sdd-tasks" >&2; exit 1; }
    if $REQ_APPROVED; then
        case "$SPEC_STATUS" in
            approved|implemented) ;;
            *) echo "ERROR: spec status is '$SPEC_STATUS' — code may only be written against an approved spec (Constitution I, ADR-0085)" >&2; exit 1 ;;
        esac
    fi
    if [ -f "$FEATURE_SPEC" ] && grep -q "NEEDS CLARIFICATION" "$FEATURE_SPEC" && { $REQ_PLAN || $REQ_TASKS; }; then
        echo "WARNING: spec still contains [NEEDS CLARIFICATION] markers — run /sdd-clarify" >&2
    fi
fi

docs=""
[ -f "$RESEARCH" ] && docs="$docs research.md"
[ -f "$DATA_MODEL" ] && docs="$docs data-model.md"
[ -d "$CONTRACTS" ] && [ -n "$(ls -A "$CONTRACTS" 2>/dev/null)" ] && docs="$docs contracts/"
[ -f "$QUICKSTART" ] && docs="$docs quickstart.md"
[ -d "$CHECKLISTS" ] && [ -n "$(ls -A "$CHECKLISTS" 2>/dev/null)" ] && docs="$docs checklists/"
$INC_TASKS && [ -f "$TASKS" ] && docs="$docs tasks.md"

if $JSON; then
    json_docs=""
    for d in $docs; do json_docs="$json_docs\"$d\","; done
    json_docs="[${json_docs%,}]"
    printf '{"FEATURE_DIR":"%s","SPEC_ID":"%s","SPEC_STATUS":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s","AVAILABLE_DOCS":%s}\n' \
        "$FEATURE_DIR" "$SPEC_ID" "$SPEC_STATUS" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS" "$json_docs"
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "SPEC_ID:     $SPEC_ID   status: $SPEC_STATUS"
    echo "AVAILABLE_DOCS:"
    check_file "$FEATURE_SPEC" spec.md; check_file "$IMPL_PLAN" plan.md; check_file "$RESEARCH" research.md
    check_file "$DATA_MODEL" data-model.md; check_dir "$CONTRACTS" contracts/; check_file "$QUICKSTART" quickstart.md
    check_dir "$CHECKLISTS" checklists/; check_file "$TASKS" tasks.md
fi
