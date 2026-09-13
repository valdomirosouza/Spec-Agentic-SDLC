#!/usr/bin/env bash
# Tests for scripts/bash/*.sh (issue #13). Pure bash 3.2+, no bats. Each test builds a scratch
# repository (git init) with the corpus's templates, constitution and scripts, so branch-based
# feature resolution can be exercised without touching this repository.
# Usage: tests/scripts/test_scripts.sh [-v]     Exit code = number of failing tests.
set -u
VERBOSE=false; [ "${1:-}" = "-v" ] && VERBOSE=true
HERE="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
pass=0; fail=0
ok()   { pass=$((pass+1)); if $VERBOSE; then echo "  ✓ $1"; fi; return 0; }
bad()  { fail=$((fail+1)); echo "  ✗ $1${2:+ — $2}"; }
assert_eq() { [ "$2" = "$3" ] && ok "$1" || bad "$1" "expected '$3', got '$2'"; }
assert_contains() { printf '%s' "$2" | grep -q -- "$3" && ok "$1" || bad "$1" "'$3' not in: $2"; }
assert_exit() { [ "$2" = "$3" ] && ok "$1" || bad "$1" "expected exit $3, got $2"; }

scratch() { # → path of a fresh scratch repo
    local t; t=$(mktemp -d)
    mkdir -p "$t/templates" "$t/memory" "$t/scripts/bash" "$t/specs/features" "$t/specs/api"
    cp "$HERE"/templates/*.md "$t/templates/"; cp "$HERE/memory/constitution.md" "$t/memory/"
    cp "$HERE"/scripts/bash/*.sh "$t/scripts/bash/"
    (cd "$t" && git init -q && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init && git branch -M main) >/dev/null 2>&1
    printf '%s' "$t"
}
spec_with() { # dir id status
    mkdir -p "$1"; printf -- '---\nid: %s\nkind: feature-spec\nstatus: %s\n---\n# x\n' "$2" "$3" > "$1/spec.md"
}

echo "create-new-feature.sh"
T=$(scratch)
out=$(cd "$T" && scripts/bash/create-new-feature.sh --json --dry-run "Add cursor pagination to the requests list")
assert_contains "first id in domain is 001" "$out" '"SPEC_ID":"SPEC-FEAT-001"'
assert_contains "slug drops stop words, keeps ≤ 4 words" "$out" 'SPEC-FEAT-001-cursor-pagination-requests-list'
assert_contains "branch name follows CLAUDE.md §6" "$out" '"BRANCH_NAME":"feature/SPEC-FEAT-001-cursor-pagination-requests-list"'
assert_eq "dry-run writes nothing" "$(ls "$T/specs/features" | wc -l | tr -d ' ')" "0"
out=$(cd "$T" && scripts/bash/create-new-feature.sh --json --issue 42 "Add cursor pagination to the requests list")
assert_eq "real run creates spec.md" "$([ -f "$T/specs/features/SPEC-FEAT-001-cursor-pagination-requests-list/spec.md" ] && echo yes)" "yes"
assert_contains "issue number lands in frontmatter" "$(head -8 "$T/specs/features/SPEC-FEAT-001-cursor-pagination-requests-list/spec.md")" 'issue: 42'
assert_contains "id lands in frontmatter" "$(head -3 "$T/specs/features/SPEC-FEAT-001-cursor-pagination-requests-list/spec.md")" 'id: SPEC-FEAT-001'
assert_eq "checklists/ and contracts/ created" "$([ -d "$T/specs/features/SPEC-FEAT-001-cursor-pagination-requests-list/checklists" ] && [ -d "$T/specs/features/SPEC-FEAT-001-cursor-pagination-requests-list/contracts" ] && echo yes)" "yes"
assert_contains "state file records the feature dir" "$(cat "$T/.sdd/feature.json")" 'specs/features/SPEC-FEAT-001-cursor-pagination-requests-list'
out=$(cd "$T" && scripts/bash/create-new-feature.sh --json --dry-run "Second feature")
assert_contains "numbering increments per domain (dir scan)" "$out" '"SPEC_ID":"SPEC-FEAT-002"'
printf -- '---\nid: SPEC-API-007\nkind: spec\nstatus: approved\n---\n' > "$T/specs/api/pagination.md"
out=$(cd "$T" && scripts/bash/create-new-feature.sh --json --dry-run --domain api "Rate limiting")
assert_contains "numbering scans frontmatter ids of other domains" "$out" '"SPEC_ID":"SPEC-API-008"'
out=$(cd "$T" && scripts/bash/create-new-feature.sh --json --dry-run --short-name "My Custom Name!" "whatever")
assert_contains "--short-name is slugified" "$out" 'SPEC-FEAT-002-my-custom-name'
out=$(cd "$T" && scripts/bash/create-new-feature.sh 2>&1); rc=$?
assert_exit "empty description fails" "$rc" 1
assert_eq "no git branch created by the script" "$(cd "$T" && git branch --list 'feature/*' | wc -l | tr -d ' ')" "0"
rm -rf "$T"

echo "check-prerequisites.sh — feature resolution"
T=$(scratch); spec_with "$T/specs/features/SPEC-FEAT-003-env" SPEC-FEAT-003 draft
out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-003-env scripts/bash/check-prerequisites.sh --json)
assert_contains "resolves from SDD_FEATURE_DIRECTORY (relative)" "$out" '"SPEC_ID":"SPEC-FEAT-003"'
out=$(cd "$T" && SDD_FEATURE_DIRECTORY="$T/specs/features/SPEC-FEAT-003-env" scripts/bash/check-prerequisites.sh --json)
assert_contains "resolves from SDD_FEATURE_DIRECTORY (absolute)" "$out" '"SPEC_ID":"SPEC-FEAT-003"'
mkdir -p "$T/.sdd"; printf '{"feature_directory": "specs/features/SPEC-FEAT-003-env"}\n' > "$T/.sdd/feature.json"
out=$(cd "$T" && scripts/bash/check-prerequisites.sh --json)
assert_contains "resolves from .sdd/feature.json" "$out" '"SPEC_ID":"SPEC-FEAT-003"'
rm -rf "$T/.sdd"; spec_with "$T/specs/features/SPEC-FEAT-004-branch" SPEC-FEAT-004 draft
out=$(cd "$T" && git checkout -q -b feature/SPEC-FEAT-004-branch && scripts/bash/check-prerequisites.sh --json)
assert_contains "resolves from the branch name" "$out" '"SPEC_ID":"SPEC-FEAT-004"'
out=$(cd "$T" && git checkout -q main && scripts/bash/check-prerequisites.sh --json 2>&1); rc=$?
assert_exit "no feature resolvable → exit 1" "$rc" 1
assert_contains "error names the three resolution paths" "$out" 'SDD_FEATURE_DIRECTORY'
rm -rf "$T"

echo "check-prerequisites.sh — gates"
T=$(scratch); D="$T/specs/features/SPEC-FEAT-005-gates"; spec_with "$D" SPEC-FEAT-005 draft
run() { (cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-005-gates scripts/bash/check-prerequisites.sh "$@" 2>&1); }
out=$(run --json --require-approved); rc=$?
assert_exit "--require-approved refuses draft" "$rc" 1
assert_contains "refusal cites Constitution I" "$out" 'Constitution I'
out=$(run --json --require-plan); rc=$?
assert_exit "--require-plan fails without plan.md" "$rc" 1
sed -i.bak 's/^status: draft/status: approved/' "$D/spec.md"; rm -f "$D/spec.md.bak"
out=$(run --json --require-approved); rc=$?
assert_exit "--require-approved accepts approved" "$rc" 0
sed -i.bak 's/^status: approved/status: implemented/' "$D/spec.md"; rm -f "$D/spec.md.bak"
out=$(run --json --require-approved); rc=$?
assert_exit "--require-approved accepts implemented" "$rc" 0
printf '# plan\n' > "$D/plan.md"; printf '# tasks\n' > "$D/tasks.md"; printf '# r\n' > "$D/research.md"
out=$(run --json --require-plan --require-tasks --include-tasks)
assert_contains "AVAILABLE_DOCS lists research.md" "$out" 'research.md'
assert_contains "--include-tasks lists tasks.md" "$out" 'tasks.md'
printf -- '---\nid: SPEC-FEAT-005\nkind: feature-spec\nstatus: approved\n---\nFR-01 [NEEDS CLARIFICATION: x]\n' > "$D/spec.md"
out=$(run --json --require-plan)
assert_contains "warns on NEEDS CLARIFICATION before plan" "$out" 'NEEDS CLARIFICATION'
rm -rf "$T"

echo "setup-plan.sh"
T=$(scratch); D="$T/specs/features/SPEC-FEAT-006-plan"; spec_with "$D" SPEC-FEAT-006 approved
out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-006-plan scripts/bash/setup-plan.sh --json)
for f in plan.md research.md data-model.md quickstart.md contracts/README.md; do
    [ -f "$D/$f" ] && ok "creates $f" || bad "creates $f"
done
printf 'custom\n' > "$D/plan.md"
out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-006-plan scripts/bash/setup-plan.sh --json)
assert_eq "never overwrites an existing plan" "$(cat "$D/plan.md")" "custom"
rm "$D/spec.md"; out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-006-plan scripts/bash/setup-plan.sh 2>&1); rc=$?
assert_exit "fails without spec.md" "$rc" 1
rm -rf "$T"

echo "tasks-to-issues.sh"
T=$(scratch); D="$T/specs/features/SPEC-FEAT-007-issues"; spec_with "$D" SPEC-FEAT-007 draft
cat > "$D/tasks.md" <<'T'
# Tasks
## Phase 1: Setup
- [ ] T001 Create branch — Refs: FR-01
- [X] T002 [P] Done already — Refs: FR-01
- [ ] T003 [P] [US1] Has issue — Refs: AC-01 (#12)
- [ ] T004 [US1] Service in src/x.py — Refs: FR-02, AC-02
T
(cd "$T" && git remote add origin https://github.com/example/scratch.git)
out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-007-issues scripts/bash/tasks-to-issues.sh --dry-run --json)
assert_contains "dry-run plans only open tasks without an issue" "$out" '"planned":2'
assert_contains "skips [X] tasks" "$out" '"skipped_done":1'
assert_contains "skips tasks already carrying (#N)" "$out" '"skipped_existing":1'
assert_contains "title = SPEC-ID + task id + description" "$out" '"title":"SPEC-FEAT-007 T004: Service in src/x.py"'
assert_contains "repo derived from the origin remote" "$out" '"REPO":"example/scratch"'
out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-FEAT-007-issues scripts/bash/tasks-to-issues.sh 2>&1); rc=$?
assert_exit "real run refuses a draft spec" "$rc" 1
assert_contains "refusal cites Constitution I" "$out" 'Constitution I'
assert_eq "tasks.md untouched by the refused run" "$(grep -c '(#' "$D/tasks.md")" "1"
rm -rf "$T"

echo "adopt.sh"
T=$(mktemp -d)
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer minimal --json)
assert_eq "minimal layer copies every file it lists" "$(printf '%s' "$out" | sed -E 's/.*"total":([0-9]+),"copied":([0-9]+).*/\1=\2/' | awk -F= '{print ($1==$2 && $1>30) ? "yes" : "no:"$0}')" "yes"
assert_eq "constitution, templates, scripts, sdd skills, hook present" "$([ -f "$T/memory/constitution.md" ] && [ -f "$T/templates/spec-template.md" ] && [ -f "$T/scripts/bash/create-new-feature.sh" ] && [ -f "$T/.claude/skills/sdd-specify/SKILL.md" ] && [ -f "$T/.claude/settings.json" ] && echo yes)" "yes"
assert_eq "minimal layer excludes ADRs" "$([ -d "$T/docs/adr" ] && echo yes || echo no)" "no"
out=$(cd "$T" && bash scripts/bash/create-new-feature.sh --json --dry-run "Feature in adopted repo")
assert_contains "/sdd-specify script works in the adopted directory (no git)" "$out" '"SPEC_ID":"SPEC-FEAT-001"'
printf 'mine\n' > "$T/memory/constitution.md"
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer minimal --json)
assert_contains "second run skips existing files" "$out" '"copied":0'
assert_eq "existing file not overwritten without --force" "$(cat "$T/memory/constitution.md")" "mine"
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer minimal --force --json)
assert_contains "--force overwrites" "$(head -1 "$T/memory/constitution.md")" "# Spec-Agentic-SDLC Constitution"
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer governed --dry-run --json)
assert_contains "dry-run reports without copying" "$out" '"DRY_RUN":true'
assert_eq "dry-run copied nothing" "$([ -d "$T/docs/adr" ] && echo yes || echo no)" "no"
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer governed --json)
assert_eq "governed layer adds ADRs, harness and CLAUDE.md" "$([ -d "$T/docs/adr" ] && [ -d "$T/harness" ] && [ -f "$T/CLAUDE.md" ] && echo yes)" "yes"
out=$(bash "$HERE/scripts/bash/adopt.sh" "$T" --layer bogus 2>&1); rc=$?
assert_exit "unknown layer fails" "$rc" 1
out=$(bash "$HERE/scripts/bash/adopt.sh" 2>&1); rc=$?
assert_exit "missing target fails" "$rc" 1
assert_eq "adopt never creates a git repository or branch" "$([ -d "$T/.git" ] && echo yes || echo no)" "no"
rm -rf "$T"

echo "render-commands"
T=$(mktemp -d)
out=$(python3 "$HERE/scripts/python/render_commands.py" --render --out "$T")
assert_contains "renders 4 files per sdd-* skill" "$out" "rendered $(( $(ls -d "$HERE"/.claude/skills/sdd-* | wc -l) * 4 )) file(s)"
assert_eq "gemini toml has description and prompt" "$(grep -c '^description = \|^prompt = """' "$T/.gemini/commands/sdd-specify.toml")" "2"
assert_eq "gemini toml uses {{args}}, not \$ARGUMENTS" "$(grep -c '{{args}}' "$T/.gemini/commands/sdd-specify.toml"):$(grep -c 'ARGUMENTS' "$T/.gemini/commands/sdd-specify.toml")" "1:0"
assert_eq "copilot/cursor/codex copies keep frontmatter and \$ARGUMENTS" "$(head -1 "$T/.github/skills/sdd-specify/SKILL.md"):$(grep -c 'ARGUMENTS' "$T/.cursor/skills/sdd-specify/SKILL.md"):$(grep -c '^name: sdd-specify' "$T/.agents/skills/sdd-specify/SKILL.md")" "---:1:1"
assert_exit "--check passes on the committed copies" "$(cd "$HERE" && python3 scripts/python/render_commands.py --check >/dev/null 2>&1; echo $?)" 0
rm -rf "$T"

echo "---"; echo "scripts tests: $pass passed, $fail failed"
exit "$fail"
