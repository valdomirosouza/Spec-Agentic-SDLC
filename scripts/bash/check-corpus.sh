#!/usr/bin/env bash
# Deterministic validation of the Spec-Agentic-SDLC corpus (issue #11). Runs locally and in CI.
#
# Usage: check-corpus.sh [--quiet] [--no-smoke] [--no-hook]
#
# Checks
#   C1 internal Markdown links resolve (adopter-provided paths, placeholders and archived
#      reference copies are skipped — see ADOPTER_PREFIXES below)
#   C2 spec frontmatter: every specs/**/spec-like file has id/kind/status; id matches
#      ^SPEC-[A-Z][A-Z0-9]{1,5}-[0-9]{3}$ (ADR-0085 domain codes include K8S); kind and status in the schema enums; superseded needs superseded_by
#   C3 ADR index: every docs/adr/ADR-NNNN-*.md is linked from docs/adr/README.md, every link
#      resolves, numbering is contiguous from 0001
#   C4 bash -n on scripts/bash/*.sh; smoke: create-new-feature --dry-run, check-prerequisites and
#      tasks-to-issues --dry-run on the worked example bundle
#   C5 high-risk-action guard self-test (.claude/hooks/verify-high-risk-guard.py)
#   C6 tests/scripts/test_scripts.sh (behavioural tests of the scripts in a scratch repository)
#   C7 every file naming an adopter-provided path (src/, make targets, services.yaml, …) carries
#      the corpus banner or the adopter-paths marker (scripts/python/adopter_paths.py --check)
#   C8 governance invariants that must never regress: tests-first and mandatory tests in the
#      tasks template; scripts never create/switch branches, push, merge or commit; constitution
#      articles I–IX and version line present; PreToolUse high-risk guard wired; --require-approved kept;
#      vcs.sh keeps its refusal list; asdd_state.py touches no version control; the gate counts
#      (13 blocking, 9 human) still match the agents and phase-gates.yaml; the coverage floor is
#      referenced, not restated, in the constitution and CLAUDE.md
#   C9 the Copilot/Cursor/Codex/Gemini copies of the sdd-* commands match a fresh render of
#      .claude/skills/sdd-*/SKILL.md (scripts/python/render_commands.py --check)
#  C10 docs/sdlc/spec-kit-upstream.json parses and carries commit, release, dates and tracked paths
#  C11 tests of the sdd-gate UserPromptSubmit hook (tests/hooks/test_sdd_gate.py, ADR-0092)
#  C12 control matrices (ASVS, OWASP GenAI, EU AI Act, ISO 42001): ids unique, owner and status
#      present, n/a justified, partial has a gap, every corpus path exists (adopter:/ci:/planned: aside)
#  C11 also runs the red-team exercise suite, so a demonstrated bypass cannot reopen (ADR-0050)
#  C14 the corpus has measured itself at least once (docs/sre/corpus-metrics-*.md) and the
#      measurement script states a method for every number and lists what it cannot measure
#  C13 docs/governance/spec-registry.{json,md} regenerate byte-identically from the specs on disk
#      (scripts/python/build_spec_registry.py --check) — the drift that left it at 50 of 58
# Exit code = number of failing checks (0 = green).
set -u
QUIET=false; SMOKE=true; HOOK=true
for a in "$@"; do case "$a" in --quiet) QUIET=true ;; --no-smoke) SMOKE=false ;; --no-hook) HOOK=false ;; --help|-h) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac; done
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root); cd "$ROOT"
EXAMPLE="specs/features/SPEC-LGS-001-log-based-golden-signals"
fails=0
say() { $QUIET || echo "$@"; }
result() { # name status detail
    if [ "$2" = ok ]; then say "  ✓ $1${3:+ — $3}"; else echo "  ✗ $1${3:+ — $3}"; fails=$((fails+1)); fi
}

say "C1 internal links"
C1=$(python3 - <<'PY'
import re,os,glob,sys
ADOPTER=('src/','tests/','services/','frontend/','infrastructure/','scaffold/','deprecated/','services.yaml','.env.example',
         'Makefile','pyproject.toml','version.txt.bak','.github/workflows/','scripts/governance/','docs/api/grpc/','reports/')
SKIP_FILES=('docs/reference/repository-template-v2-README.md','docs/reference/repository-template-v2-SETUP.md')
link=re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
md=[]
for d,dn,fn in os.walk('.'):
    dn[:]=[x for x in dn if x not in ('.git','.serena','.sdd','node_modules')]
    md+=[os.path.normpath(os.path.join(d,f)) for f in fn if f.endswith('.md')]
md=[p for p in md if p not in SKIP_FILES]
bad=[]
for p in md:
    s=open(p,encoding='utf-8',errors='replace').read()
    for m in link.finditer(s):
        t=m.group(1)
        if t.startswith(('http://','https://','#','mailto:','<')): continue
        t=t.split('#')[0]
        if not t or '...' in t or 'XXX' in t or '{' in t or '<' in t: continue
        tgt=os.path.normpath(os.path.join(os.path.dirname(p),t))
        if tgt.startswith(ADOPTER) or ('/'+tgt).endswith(tuple('/'+a for a in ADOPTER if not a.endswith('/'))): continue
        if not os.path.exists(tgt): bad.append(f"{p} → {t}")
print(len(md)); print(len(bad)); print("\n".join(bad))
PY
)
c1_files=$(printf '%s\n' "$C1" | sed -n 1p); c1_bad=$(printf '%s\n' "$C1" | sed -n 2p)
if [ "$c1_bad" = 0 ]; then result "links" ok "$c1_files Markdown files, 0 broken"; else result "links" fail "$c1_bad broken"; printf '%s\n' "$C1" | sed -n '3,$p' | sed 's/^/      /'; fi

say "C2 spec frontmatter"
C2=$(python3 - <<'PY'
import re,glob,os
KINDS={'spec','policy','feature-spec','threat-model'}; STATUS={'draft','in-review','approved','implemented','superseded'}
BUNDLE_NON_SPEC={'plan.md','tasks.md','research.md','data-model.md','quickstart.md'}
bad=[]; n=0
for p in sorted(glob.glob('specs/**/*.md',recursive=True)):
    b=os.path.basename(p)
    if b=='README.md' or 'template' in b.lower() or 'TEMPLATE' in b: continue
    if p.startswith('specs/features/') and (b in BUNDLE_NON_SPEC or '/checklists/' in p or '/contracts/' in p): continue
    n+=1
    s=open(p,encoding='utf-8',errors='replace').read()
    if not s.startswith('---\n'): bad.append(f"{p}: no frontmatter"); continue
    fm=s.split('\n---',1)[0]
    def f(k):
        m=re.search(r'^'+k+r':[ \t]*([^\n#]*)',fm,re.M); return m.group(1).strip().strip(chr(34)).strip(chr(39)) if m else None
    i,k,st=f('id'),f('kind'),f('status')
    if not i or not re.fullmatch(r'SPEC-[A-Z][A-Z0-9]{1,5}-[0-9]{3}',i): bad.append(f"{p}: bad id {i!r}")
    if k not in KINDS: bad.append(f"{p}: bad kind {k!r}")
    if st not in STATUS: bad.append(f"{p}: bad status {st!r}")
    if st=='superseded' and not f('superseded_by'): bad.append(f"{p}: superseded without superseded_by")
    lu=f('last_updated')
    if lu and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',lu): bad.append(f"{p}: bad last_updated {lu!r}")
print(n); print(len(bad)); print("\n".join(bad))
PY
)
c2_n=$(printf '%s\n' "$C2" | sed -n 1p); c2_bad=$(printf '%s\n' "$C2" | sed -n 2p)
if [ "$c2_bad" = 0 ]; then result "frontmatter" ok "$c2_n specs valid"; else result "frontmatter" fail "$c2_bad invalid"; printf '%s\n' "$C2" | sed -n '3,$p' | sed 's/^/      /'; fi

say "C3 ADR index"
C3=$(python3 - <<'PY'
import re,glob,os
files=sorted(glob.glob('docs/adr/ADR-[0-9][0-9][0-9][0-9]-*.md'))
nums=sorted(int(os.path.basename(f)[4:8]) for f in files)
bad=[]
if nums!=list(range(1,len(nums)+1)): bad.append(f"numbering not contiguous: {[n for n in range(1,max(nums)+1) if n not in nums]} missing, duplicates {[n for n in set(nums) if nums.count(n)>1]}")
idx=open('docs/adr/README.md',encoding='utf-8').read()
linked=set(re.findall(r'\]\((ADR-[0-9]{4}-[^)]+\.md)\)',idx))
for f in files:
    b=os.path.basename(f)
    if b not in linked: bad.append(f"not in docs/adr/README.md: {b}")
for l in sorted(linked):
    if not os.path.exists('docs/adr/'+l): bad.append(f"index links a missing file: {l}")
print(len(files)); print(len(bad)); print("\n".join(bad))
PY
)
c3_n=$(printf '%s\n' "$C3" | sed -n 1p); c3_bad=$(printf '%s\n' "$C3" | sed -n 2p)
if [ "$c3_bad" = 0 ]; then result "adr-index" ok "$c3_n ADRs, contiguous, all indexed"; else result "adr-index" fail "$c3_bad problems"; printf '%s\n' "$C3" | sed -n '3,$p' | sed 's/^/      /'; fi

say "C4 scripts"
syn_bad=0
for f in scripts/bash/*.sh; do bash -n "$f" 2>/dev/null || { echo "      syntax error: $f"; syn_bad=$((syn_bad+1)); }; done
[ "$syn_bad" = 0 ] && result "bash -n" ok "$(ls scripts/bash/*.sh | wc -l | tr -d ' ') scripts" || result "bash -n" fail "$syn_bad scripts"
if $SMOKE; then
    out=$(scripts/bash/create-new-feature.sh --json --dry-run "Corpus check smoke feature" 2>&1) && printf '%s' "$out" | grep -q '"DRY_RUN":true' \
        && result "create-new-feature --dry-run" ok || result "create-new-feature --dry-run" fail "$out"
    if [ -d "$EXAMPLE" ]; then
        out=$(SDD_FEATURE_DIRECTORY="$EXAMPLE" scripts/bash/check-prerequisites.sh --json --require-spec --require-plan --require-tasks --include-tasks 2>&1) \
            && printf '%s' "$out" | grep -q '"tasks.md"' && result "check-prerequisites (example)" ok || result "check-prerequisites (example)" fail "$out"
        out=$(SDD_FEATURE_DIRECTORY="$EXAMPLE" scripts/bash/tasks-to-issues.sh --dry-run --json 2>&1) \
            && printf '%s' "$out" | grep -q '"planned":[1-9]' && result "tasks-to-issues --dry-run (example)" ok || result "tasks-to-issues --dry-run (example)" fail "$out"
        T=$(mktemp -d); mkdir -p "$T/specs/features/SPEC-ZZ-001-smoke" "$T/memory" "$T/templates"; cp templates/*.md "$T/templates/"; cp memory/constitution.md "$T/memory/"
        printf -- '---\nid: SPEC-ZZ-001\nkind: feature-spec\nstatus: draft\n---\n' > "$T/specs/features/SPEC-ZZ-001-smoke/spec.md"; cp scripts/bash/*.sh "$T/"
        out=$(cd "$T" && SDD_FEATURE_DIRECTORY=specs/features/SPEC-ZZ-001-smoke bash ./setup-plan.sh --json 2>&1) \
            && [ -f "$T/specs/features/SPEC-ZZ-001-smoke/quickstart.md" ] && result "setup-plan (scratch)" ok || result "setup-plan (scratch)" fail "$out"
        rm -rf "$T"
    else
        result "example bundle present" fail "$EXAMPLE missing"
    fi
fi

if $SMOKE; then
    say "C6 script tests"
    if out=$(bash tests/scripts/test_scripts.sh 2>&1); then result "tests/scripts/test_scripts.sh" ok "$(printf '%s' "$out" | tail -1 | sed 's/scripts tests: //')"; else result "tests/scripts/test_scripts.sh" fail; printf '%s\n' "$out" | grep '✗' | sed 's/^/      /'; fi
fi

say "C7 adopter-path markers"
if out=$(python3 scripts/python/adopter_paths.py --check 2>&1); then result "adopter-paths" ok "$(printf '%s' "$out" | head -1)"; else result "adopter-paths" fail "$(printf '%s' "$out" | head -1)"; printf '%s\n' "$out" | sed -n '2,15p' | sed 's/^/      /'; fi

say "C8 governance invariants (finding 8 of the spec-kit comparison)"
inv_bad=0
grep -q '^### Tests first' templates/tasks-template.md && grep -q 'tests are NOT optional (Constitution II)' templates/tasks-template.md \
    && result "tasks-template keeps tests-first and mandatory tests" ok || { result "tasks-template keeps tests-first and mandatory tests" fail; inv_bad=1; }
# No script performs an outward or irreversible version-control action. This is absolute.
gitcmd=$(grep -nE 'git (push|merge|commit|rebase|reset|switch)' scripts/bash/*.sh | grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' | grep -vE 'echo|printf|refuse|"[^"]*git (push|merge)' || true)
[ -z "$gitcmd" ] && result "scripts never push/merge/commit/rebase/reset/switch" ok || { result "scripts never push/merge/commit/rebase/reset/switch" fail "$gitcmd"; }
# Exactly one named exception: vcs.sh may create a LOCAL feature branch, which has no outward
# effect, and only behind the protected-name guard. Any other script doing it is a regression.
ckout=$(grep -nE '(^|;|&&|\||\bthen |\bdo |run )[[:space:]]*git checkout' scripts/bash/*.sh | grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' | grep -vE 'echo|printf' | grep -vE 'scripts/bash/(vcs|check-corpus)\.sh' | cut -d: -f1 | sort -u || true)
if [ -z "$ckout" ] && grep -q 'guard_branch_name "$name"' scripts/bash/vcs.sh; then result "only vcs.sh creates a branch, and only behind the protected-name guard" ok; else result "only vcs.sh creates a branch, behind the guard" fail "${ckout:-guard missing in vcs.sh}"; fi
art_missing=""
for a in "I. Specification First" "II. Test-Backed Change" "III. Privacy by Design" "IV. Security Gates Are Not Optional" "V. Human Oversight of Agents" "VI. Observability Is Part of Done" "VII. Traceability and Auditability" "VIII. Simplicity and No Gold-Plating" "IX. Grounding and Non-Fabrication"; do
    grep -q "^### $a" memory/constitution.md || art_missing="$art_missing [$a]"
done
grep -qE '^\*\*Version\*\*: [0-9]+\.[0-9]+\.[0-9]+ \| \*\*Ratified\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2} \| \*\*Last Amended\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}' memory/constitution.md || art_missing="$art_missing [version line]"
[ -z "$art_missing" ] && result "constitution has articles I–IX and a version line" ok || result "constitution has articles I–IX and a version line" fail "missing:$art_missing"
python3 - <<'PY2' && result "settings.json keeps the PreToolUse high-risk guard" ok || result "settings.json keeps the PreToolUse high-risk guard" fail
import json,sys
s=json.load(open('.claude/settings.json'))
hooks=s.get('hooks',{}).get('PreToolUse',[])
ok=any('high-risk-action-guard.py' in h.get('command','') and h.get('type')=='command'
       for m in hooks for h in m.get('hooks',[]) if any(t in m.get('matcher','') for t in ('Bash','Edit','Write')))
sys.exit(0 if ok else 1)
PY2
grep -q -- '--require-approved' scripts/bash/check-prerequisites.sh && grep -q 'approved|implemented' scripts/bash/check-prerequisites.sh \
    && result "check-prerequisites keeps --require-approved (approved|implemented only)" ok || result "check-prerequisites keeps --require-approved" fail
# The coverage floor is one number in one place. A bare number in a normative text is how it
# came to be stated three ways (80 in the constitution, 85 in ADR-0022, 75 as the escalation
# trigger, with nothing reconciling them).
cov_bad=$(grep -nE 'coverage (MUST be|≥|>=) *(7[0-9]|8[0-9]|9[0-9])%' memory/constitution.md CLAUDE.md 2>/dev/null || true)
[ -z "$cov_bad" ] && result "constitution and CLAUDE.md reference the floor, not a bare number" ok || result "constitution and CLAUDE.md reference the floor, not a bare number" fail "$cov_bad"
cov_n=$(grep -oE 'declared coverage floor is [0-9]{2}%' docs/adr/ADR-0022-testing-strategy.md | grep -oE '[0-9]{2}%' | sort -u)
[ "$(printf '%s' "$cov_n" | wc -w | tr -d ' ')" = 1 ] && result "ADR-0022 declares exactly one floor" ok "$cov_n" || result "ADR-0022 declares exactly one floor" fail "found: ${cov_n:-none}"
n_human=$(grep -l -- "--human-gate" .claude/agents/asdd-phase-*.md | wc -l | tr -d " ")
n_block=$(grep -c "blocking: true" docs/process/gates/phase-gates.yaml | tr -d " ")
if [ "$n_human" = 9 ] && [ "$n_block" = 13 ]; then
    result "gates: 13 blocking, 9 requiring a human" ok
else
    result "gates: 13 blocking, 9 requiring a human" fail "found $n_block blocking and $n_human human — update the docs that state these numbers, then this assertion"
fi
nref=$(grep -c 'refuse "' scripts/bash/vcs.sh 2>/dev/null || echo 0)
[ "${nref:-0}" -ge 5 ] && grep -q 'gh pr merge' scripts/bash/vcs.sh \
    && result "vcs.sh keeps its refusal list (merge, release, deploy, push, protected branch)" ok "$nref refusals" \
    || result "vcs.sh keeps its refusal list" fail "only ${nref:-0} refusals"
grep -qE '"(git|gh)"' scripts/python/asdd_state.py \
    && result "asdd_state.py runs no git or gh" fail \
    || result "asdd_state.py runs no git or gh" ok

say "C9 rendered per-agent commands"
if out=$(python3 scripts/python/render_commands.py --check 2>&1); then result "render_commands --check" ok "$(printf '%s' "$out" | head -1)"; else result "render_commands --check" fail "$(printf '%s' "$out" | head -1)"; printf '%s\n' "$out" | sed -n '2,12p' | sed 's/^/      /'; fi

say "C10 upstream pin"
if out=$(python3 - <<'PY3'
import json,re,sys
d=json.load(open('docs/sdlc/spec-kit-upstream.json'))
assert re.fullmatch(r'[0-9a-f]{7,40}',d['commit']), 'commit'
assert re.fullmatch(r'v\d+\.\d+\.\d+',d['release']), 'release'
for k in ('release_date','compared_on','next_review_due'): assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',d[k]), k
assert d['tracked_paths'], 'tracked_paths'
print(f"{d['repository']} {d['commit']} ({d['release']}), review due {d['next_review_due']}")
PY3
); then result "spec-kit-upstream.json" ok "$out"; else result "spec-kit-upstream.json" fail "$out"; fi

say "C14 corpus measurement"
if $SMOKE; then
    if out=$(python3 tests/scripts/test_corpus_metrics.py 2>&1); then result "tests/scripts/test_corpus_metrics.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_corpus_metrics.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi
nrep=$(ls docs/sre/corpus-metrics-*.md 2>/dev/null | wc -l | tr -d ' ')
[ "${nrep:-0}" -ge 1 ] && result "the corpus carries at least one measurement of itself" ok "$nrep report(s)" || result "the corpus carries at least one measurement of itself" fail

say "C13 spec registry"
if out=$(python3 scripts/python/build_spec_registry.py --check --quiet 2>&1); then
    result "spec registry matches disk" ok
else
    result "spec registry matches disk" fail; printf '%s\n' "$out" | head -10 | sed 's/^/      /'
fi
if $SMOKE; then
    if out=$(python3 tests/scripts/test_build_spec_registry.py 2>&1); then result "tests/scripts/test_build_spec_registry.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_build_spec_registry.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi

say "C12 control matrices"
if out=$(python3 scripts/python/check_control_matrix.py --quiet 2>&1); then
    result "check_control_matrix" ok "ASVS · OWASP GenAI · EU AI Act · ISO 42001"
    printf '%s\n' "$out" | grep -E '^  note:' | sed 's/^/    /'
else
    result "check_control_matrix" fail
    printf '%s\n' "$out" | grep -E 'ERROR' | head -10 | sed 's/^/      /'
fi
if $SMOKE; then
    if out=$(python3 tests/scripts/test_check_control_matrix.py 2>&1); then result "tests/scripts/test_check_control_matrix.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_check_control_matrix.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi

if $HOOK; then
    say "C11 sdd-gate UserPromptSubmit hook"
    if out=$(python3 tests/hooks/test_sdd_gate.py 2>&1); then result "tests/hooks/test_sdd_gate.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/hooks/test_sdd_gate.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
    if out=$(python3 tests/hooks/test_red_team_2026_09_13.py 2>&1); then result "red-team RT-2026-09-13 findings stay closed" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "red-team RT-2026-09-13 findings stay closed" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi

if $HOOK; then
    say "C5 high-risk-action guard"
    if out=$(python3 .claude/hooks/verify-high-risk-guard.py 2>&1); then result "verify-high-risk-guard" ok; else result "verify-high-risk-guard" fail; printf '%s\n' "$out" | tail -5 | sed 's/^/      /'; fi
fi

if [ "$fails" = 0 ]; then say "check-corpus: all checks green"; else echo "check-corpus: $fails check(s) failed"; fi
exit "$fails"
