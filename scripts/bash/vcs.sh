#!/usr/bin/env bash
# Version-control actions for the delivery agents (issue #45).
#
# Phases 1, 2, 3, 4 and 7 of the 15-phase workflow call this to open issues, open pull requests,
# read CI status and create a feature branch. It did not exist, so those phases could not run.
#
# WHY THIS IS NOT A THIN `gh` WRAPPER. This is the only script in the corpus that touches git and
# gh, which makes it the one place where Constitution V could be circumvented: a wrapper that
# forwarded anything to `gh` would hand agents the merge, push-to-default and release verbs that
# the PreToolUse guard exists to deny. So the allowed verbs are an ALLOW-LIST, and the forbidden
# ones are refused here too — defence in depth, because a subagent may invoke this script directly.
#
#   issue create --title T --body-file F [--label "a,b"] [--assignee U]
#   issue edit N [--add-label L] [--remove-label L] [--add-assignee U]
#   pr create [--fill | --title T --body-file F] [--base B] [--draft]
#   pr edit N [--add-reviewer R] [--add-label L]
#   pr checks N [--watch]
#   pr view N [--json FIELDS]
#   branch create <name>            # local branch only; never pushes
#
# Global: --dry-run prints the command instead of running it. --repo OWNER/NAME overrides origin.
#
# REFUSED, always, with exit 3: pr merge, push to the default branch, release create, any deploy
# verb, force-push, and history rewriting. These are human decisions (Constitution V, ADR-0011);
# the agent stops at the gate and asks.
set -euo pipefail

DRY_RUN=false
REPO_ARG=()
REFUSAL_EXIT=3

die()    { echo "ERROR: $*" >&2; exit 1; }
refuse() {
    echo "REFUSED: $1" >&2
    echo "  This action is reserved to a human (Constitution V, ADR-0011). The agent stops at the" >&2
    echo "  gate and asks; it does not perform it. See docs/process/HITL-GOVERNANCE.md." >&2
    exit "$REFUSAL_EXIT"
}
run() {
    if $DRY_RUN; then printf 'DRY-RUN:'; printf ' %q' "$@"; printf '\n'; return 0; fi
    "$@"
}

default_branch() {
    gh repo view ${REPO_ARG[@]+"${REPO_ARG[@]}"} --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main
}

# ---- refusal checks -----------------------------------------------------------------------------
guard_pr_verb() {
    case "$1" in
        merge|close|ready) [ "$1" = merge ] && refuse "gh pr merge — merging a pull request" ;;
    esac
}
guard_branch_name() {
    local b="$1" d; d=$(default_branch)
    [ "$b" = "$d" ] && refuse "operating directly on the default branch ($d)"
    case "$b" in
        main|master|develop|release/*) refuse "operating on a protected branch ($b)" ;;
    esac
}

# ---- argument parsing ---------------------------------------------------------------------------
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --repo) shift; REPO_ARG=(--repo "$1") ;;
        --help|-h) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) ARGS+=("$1") ;;
    esac
    shift
done
set -- ${ARGS[@]+"${ARGS[@]}"}
[ $# -ge 1 ] || die "usage: vcs.sh <issue|pr|branch> <verb> [options] — see --help"

NOUN="$1"; shift
VERB="${1:-}"; [ $# -ge 1 ] && shift || true

command -v gh >/dev/null 2>&1 || { $DRY_RUN || die "gh is required (and authenticated) for vcs.sh"; }

case "$NOUN" in
    issue)
        case "$VERB" in
            create|edit|view|list) run gh issue "$VERB" ${REPO_ARG[@]+"${REPO_ARG[@]}"} "$@" ;;
            delete) refuse "gh issue delete — deleting an issue destroys the traceability chain (Constitution VII)" ;;
            *) die "unsupported: issue $VERB (allowed: create, edit, view, list)" ;;
        esac
        ;;
    pr)
        guard_pr_verb "$VERB"
        case "$VERB" in
            create)
                # A PR is opened FROM a feature branch; opening one from the default branch would
                # mean the agent committed there, which the guard forbids upstream of this script.
                cur=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
                [ -n "$cur" ] && guard_branch_name "$cur"
                run gh pr create ${REPO_ARG[@]+"${REPO_ARG[@]}"} "$@"
                ;;
            edit|view|checks|diff|status|list) run gh pr "$VERB" ${REPO_ARG[@]+"${REPO_ARG[@]}"} "$@" ;;
            merge) refuse "gh pr merge" ;;
            *) die "unsupported: pr $VERB (allowed: create, edit, view, checks, diff, status, list)" ;;
        esac
        ;;
    branch)
        case "$VERB" in
            create)
                name="${1:-}"; [ -n "$name" ] || die "usage: vcs.sh branch create <name>"
                guard_branch_name "$name"
                run git checkout -b "$name"
                ;;
            *) die "unsupported: branch $VERB (allowed: create)" ;;
        esac
        ;;
    release) refuse "creating a release" ;;
    deploy|rollout|promote) refuse "deploying" ;;
    push)   refuse "pushing from an agent" ;;
    *) die "unsupported noun: $NOUN (allowed: issue, pr, branch)" ;;
esac
