#!/usr/bin/env bash
# Deterministic validation of the Spec-Agentic-SDLC corpus (issue #11). Runs locally and in CI.
#
# Usage: check-corpus.sh [--quiet] [--no-smoke] [--no-hook] [--no-suites]
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
#      referenced, not restated, in the constitution and CLAUDE.md; no unqualified speedup ratio
#   C9 the Copilot/Cursor/Codex/Gemini copies of the sdd-* commands match a fresh render of
#      .claude/skills/sdd-*/SKILL.md (scripts/python/render_commands.py --check)
#  C10 docs/sdlc/spec-kit-upstream.json parses and carries commit, release, dates and tracked paths
#  C11 tests of the sdd-gate UserPromptSubmit hook (tests/hooks/test_sdd_gate.py, ADR-0092)
#  C12 control matrices (ASVS, OWASP GenAI, EU AI Act, ISO 42001): ids unique, owner and status
#      present, n/a justified, partial has a gap, every corpus path exists (adopter:/ci:/planned: aside)
#  C6 also runs the mutation harness: each entry injects a defect and requires that check to fail
#  C11 also runs the red-team exercise suite, so a demonstrated bypass cannot reopen (ADR-0050)
#  C15 the 14 data-quality rules over the corpus's own datasets (spec registry, ADR index,
#      control matrices, adopter-path inventory); critical blocks, major is reported every run
#  C14 the corpus has measured itself at least once (docs/sre/corpus-metrics-*.md) and the
#      measurement script states a method for every number and lists what it cannot measure
#  C13 docs/governance/spec-registry.{json,md} regenerate byte-identically from the specs on disk
#      (scripts/python/build_spec_registry.py --check) — the drift that left it at 50 of 58
# Exit code = number of failing checks (0 = green).
set -u
# ---------------------------------------------------------------------------------------------
# What this suite defends against, and what it does not. Written down because six rounds of audit
# kept rediscovering the same boundary as if it were new (R9-T2).
#
#   Covered: accident and drift. A check deleted, renamed, emptied into an unconditional pass, or
#   widened until it exempts everything. Every check carrying its own logic has a mutation that
#   fails when the check stops working, and the coverage tool refuses a new one without a proof.
#
#   NOT covered: an author who intends to disable the suite. Nothing static wins that race — a
#   condition can always be made true in a way no pattern anticipates. The defence there is human
#   review and the audit trail (Constitution V, Article VII), not another grep. Treating it as a
#   tooling problem would produce an arms race whose only measurable outcome is more tooling.
#
#   Cost, for the next person weighing a change: one run is ~7s with --no-smoke, ~60s with the
#   dry-runs on, and the mutation harness pays one run per proof, so its cost grows with the square
#   of the check count. `--no-suites` runs the dry-runs without recursing into the harness.
# ---------------------------------------------------------------------------------------------
QUIET=false; SMOKE=true; HOOK=true; SUITES=true
for a in "$@"; do case "$a" in --quiet) QUIET=true ;; --no-smoke) SMOKE=false ;; --no-suites) SUITES=false ;; --no-hook) HOOK=false ;; --help|-h) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac; done
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
ROOT=$(get_repo_root); cd "$ROOT"
EXAMPLE="specs/features/SPEC-LGS-001-log-based-golden-signals"
fails=0
say() { $QUIET || echo "$@"; }
result() { # name status detail — ok | note | fail
    case "$2" in
        ok)   say "  ✓ $1${3:+ — $3}" ;;
        note) echo "  ! $1${3:+ — $3}" ;;   # alert severity: visible, does not fail the build
        *)    echo "  ✗ $1${3:+ — $3}"; fails=$((fails+1)) ;;
    esac
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
if [ -z "$ckout" ] && grep -q 'guard_branch_name "$name"' scripts/bash/vcs.sh; then result "only vcs.sh creates a branch, and only behind the protected-name guard" ok; else result "only vcs.sh creates a branch, and only behind the protected-name guard" fail "${ckout:-guard missing in vcs.sh}"; fi
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
# Behaviour, not presence. Grepping the file for the flag matched the usage comment on line 6, so
# deleting the case arm that implements it left the check green — the same string-counting mistake
# the refusal check made in R5-T2, found here by writing the mutation for it (R8-T2).
prereq_bad=""
if bash scripts/bash/check-prerequisites.sh --require-approved --paths-only 2>&1 \
        | grep -q 'unknown option'; then
    prereq_bad="[--require-approved is not accepted]"
fi
grep -q 'approved|implemented' scripts/bash/check-prerequisites.sh \
    || prereq_bad="$prereq_bad [approved|implemented vocabulary missing]"
[ -z "$prereq_bad" ] \
    && result "check-prerequisites keeps --require-approved (approved|implemented only)" ok \
    || result "check-prerequisites keeps --require-approved (approved|implemented only)" fail "$prereq_bad"
# The coverage floor is one number in one place. A bare number in a normative text is how it
# came to be stated three ways (80 in the constitution, 85 in ADR-0022, 75 as the escalation
# trigger, with nothing reconciling them).
# A bare percentage anywhere near the word coverage, in either order. The exclusion may not be
# line-wide: exempting any line that mentions ADR-0022 exempted `Coverage MUST be 80% per
# ADR-0022.`, and citing the ADR is exactly what a restated number would do (R5-T3).
cov_bad=$(grep -nEi '(coverage[^.]{0,30}(7[0-9]|8[0-9]|9[0-9])%|(7[0-9]|8[0-9]|9[0-9])% *coverage)' memory/constitution.md CLAUDE.md 2>/dev/null \
    | grep -viE 'ratcheted from|floor declared in ADR-0022 before merge \(' || true)
[ -z "$cov_bad" ] && result "constitution and CLAUDE.md reference the floor, not a bare number" ok || result "constitution and CLAUDE.md reference the floor, not a bare number" fail "$cov_bad"
cov_n=$(grep -oE 'declared coverage floor is [0-9]{2}%' docs/adr/ADR-0022-testing-strategy.md | grep -oE '[0-9]{2}%' | sort -u)
[ "$(printf '%s' "$cov_n" | wc -w | tr -d ' ')" = 1 ] && result "ADR-0022 declares exactly one floor" ok "$cov_n" || result "ADR-0022 declares exactly one floor" fail "found: ${cov_n:-none}"
# No unqualified performance ratio. The corpus published "≈160×" by dividing a measured
# wall-clock by a sum of t-shirt estimates (issue #55). The claim was withdrawn AND the
# instruction that produced it was removed, because fixing only the output regenerates it.
# Narrow on purpose: this targets a DELIVERY-THROUGHPUT ratio (agent vs human), not a technical
# benchmark. "uv is 10-100x faster than pip" is a tool comparison and stays.
# Every form the claim can take. The round-4 repair caught only `N× faster` and silently dropped
# the divided form the version before it caught, so a regression shipped inside a fix (R5-T3).
# Forms proven by tests/scripts/test_check_corpus.py:
#   160× faster · 160 times faster · speedup ratio: 160 · human-equiv 320h ÷ agent 2h = 160×
# Exclusion is deliberately narrow: only a line that says the claim is withdrawn or hypothetical.
# The previous filter dropped any line containing "benchmark", so one word bought an exemption.
ratio_bad=$(grep -rniE '([0-9]+(\.[0-9]+)?\s*(×|x)\s*(faster|quicker|speedup))|([0-9]+(\.[0-9]+)?\s*times\s+(faster|quicker))|(speedup ratio[^|]{0,40}[0-9])|(human.equiv[^|]{0,60}÷)|(÷\s*agent wall.clock)' --include='*.md' . 2>/dev/null \
    | grep -v '^\./\.git/' \
    | grep -viE 'withdrawn|no speedup ratio|not a ratio|would require|forbids|hypothetical|than pip' || true)
[ -z "$ratio_bad" ] && result "no unqualified speedup ratio is published" ok || { result "no unqualified speedup ratio is published" fail "$(printf '%s' "$ratio_bad" | head -3)"; }
# `python` is not on PATH on macOS or a stock Debian/Ubuntu. The agents shipped 20 invocations of
# it, so the delivery layer could not start (R4-T1). Only `python3` is portable here.
# The change-discipline skill is the corpus's only rule about the SCOPE of a change. It is a
# review item, not a gate — scope is not a property a test can assert — so the invariant checks
# that the rule is still reachable, not that a diff obeyed it.
for f in skills/engineering/change-discipline.md .claude/skills/change-discipline/SKILL.md; do
    [ -f "$f" ] || { result "change-discipline skill present" fail "$f missing"; break; }
done
# The message promised two placements and a single grep verified neither: it matched the PR
# checklist line alone and stayed green when the activation row was dropped (R5-T3 audit).
cd_bad=""
grep -qE '^\|.*skills/engineering/change-discipline\.md' CLAUDE.md || cd_bad="$cd_bad [activation table row missing]"
grep -q 'Every changed line traces to the issue' CLAUDE.md || cd_bad="$cd_bad [PR checklist item missing]"
[ -z "$cd_bad" ] \
    && result "change-discipline is in the activation table and the PR checklist" ok \
    || result "change-discipline is in the activation table and the PR checklist" fail "$cd_bad"
bare_py=$(grep -rn '\bpython [a-z_/]*\.py' .claude/agents/*.md docs/sdlc/*.md 2>/dev/null | grep -v 'python3' || true)
[ -z "$bare_py" ] && result "documented agent commands use python3, not bare python" ok || { result "documented agent commands use python3, not bare python" fail "$(printf '%s' "$bare_py" | head -3)"; }
n_human=$(grep -l -- "--human-gate" .claude/agents/asdd-phase-*.md | wc -l | tr -d " ")
n_block=$(grep -c "blocking: true" docs/process/gates/phase-gates.yaml | tr -d " ")
if [ "$n_human" = 9 ] && [ "$n_block" = 13 ]; then
    result "gates: 13 blocking, 9 requiring a human" ok
else
    result "gates: 13 blocking, 9 requiring a human" fail "found $n_block blocking and $n_human human — update the docs that state these numbers, then this assertion"
fi
# Behaviour, not word count. Counting occurrences of `refuse "` passed with every refusal
# neutralised to a no-op, leaving the one script that touches git guarded by a grep (R5-T2).
vcs_bad=""
for verb in "pr merge 1" "release create v1" "deploy staging x" "push origin main" "branch create main"; do
    # shellcheck disable=SC2086
    if bash scripts/bash/vcs.sh --dry-run $verb >/dev/null 2>&1; then
        vcs_bad="$vcs_bad [$verb exited 0]"
    else
        rc=$?; [ "$rc" = 3 ] || vcs_bad="$vcs_bad [$verb exited $rc, expected 3]"
    fi
done
[ -z "$vcs_bad" ] \
    && result "vcs.sh refuses merge, release, deploy, push and protected branches" ok "5 verbs, exit 3 each" \
    || result "vcs.sh refuses merge, release, deploy, push and protected branches" fail "$vcs_bad"
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

say "C15 data quality (corpus datasets)"
if out=$(python3 scripts/python/check_data_quality.py --run --quiet 2>&1); then
    result "data-quality rules over the corpus's own datasets" ok "14 rules, no blocking violation"
else
    crit=$(printf '%s\n' "$out" | grep -c 'CRITICAL' || true)
    if [ "${crit:-0}" -gt 0 ]; then
        result "data-quality rules over the corpus's own datasets" fail
        printf '%s\n' "$out" | grep 'CRITICAL' | head -5 | sed 's/^/      /'
    else
        # A `major` alerts and does not block (specs/data/data-quality.md §4): report it every run.
        # Printing a tick while the rule exits non-zero is how a declared rule becomes decorative.
        result "data-quality rules over the corpus's own datasets" note "open finding(s) — see below"
        printf '%s\n' "$out" | grep -E 'MAJOR|MINOR' | head -5 | sed 's/^/      note: /'
    fi
fi
if $SMOKE; then
    if out=$(python3 tests/scripts/test_check_data_quality.py 2>&1); then result "tests/scripts/test_check_data_quality.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_check_data_quality.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi

say "C14 corpus measurement"
if $SMOKE; then
    if out=$(python3 tests/scripts/test_corpus_metrics.py 2>&1); then result "tests/scripts/test_corpus_metrics.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_corpus_metrics.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
fi
if out=$(python3 scripts/python/corpus_metrics.py --check --quiet 2>&1); then
    result "the measurement report is structurally current" ok
else
    result "the measurement report is structurally current" fail "$(printf '%s' "$out" | head -3)"
fi
# The measurement has to REPEAT, and a cadence written in prose is not a cadence. Five rounds
# produced one data point per control while a note said "monthly" and nothing anywhere fired
# (R5-T7). This asserts the trigger exists, not that someone wrote about it.
sched=".github/workflows/corpus-measure.yml"
sched_bad=""
[ -f "$sched" ] || sched_bad="[workflow missing]"
if [ -z "$sched_bad" ]; then
    grep -q '^  schedule:' "$sched" || sched_bad="$sched_bad [no schedule trigger]"
    grep -qE '^    - cron:' "$sched" || sched_bad="$sched_bad [no cron entry]"
    grep -q 'corpus_metrics.py --drift' "$sched" || sched_bad="$sched_bad [does not measure]"
    grep -q 'gh issue create' "$sched" || sched_bad="$sched_bad [movement is not reported anywhere]"
    grep -q 'gh pr create' "$sched" || sched_bad="$sched_bad [report never returns to the repo, so no series forms]"
    awk '/^    steps:/{exit} /GH_TOKEN/{found=1} END{exit !found}' "$sched" || sched_bad="$sched_bad [token not declared at job level: the measurement step loses its CI rows]"
fi
[ -z "$sched_bad" ] \
    && result "the measurement is scheduled, not merely described" ok "weekly cron, token at job level, proposes the report and files what moved" \
    || result "the measurement is scheduled, not merely described" fail "$sched_bad"

nrep=$(ls docs/sre/corpus-metrics-*.md 2>/dev/null | wc -l | tr -d ' ')
[ "${nrep:-0}" -ge 1 ] && result "the corpus carries at least one measurement of itself" ok "$nrep report(s)" || result "the corpus carries at least one measurement of itself" fail

# Forty-two open-item rows and not one carried a date, so no item could ever be overdue: there was
# nothing to be late against, and the quarterly review that would resolve them is convened by
# nothing. A date fails when it passes; `on-event:` never expires but is declared, not implied
# (R6-T6).
if out=$(python3 scripts/python/check_open_items.py --check --quiet 2>&1); then
    [ -n "$out" ] && result "open items carry a date or a named trigger" note "$(printf '%s' "$out" | head -1)" \
                  || result "open items carry a date or a named trigger" ok
else
    result "open items carry a date or a named trigger" fail
    printf '%s\n' "$out" | head -8 | sed 's/^/      /'
fi

# ADR-0057 makes version.txt the version of record and says it follows SemVer, and nothing
# exercised that. The changelog records a BREAKING schema change while version.txt sits at 1.0.0;
# in three months nobody would remember a break was pending (R7-T5).
if out=$(python3 scripts/python/check_changelog.py --version --quiet 2>&1); then
    result "compatibility claims match what the last release published" ok
else
    result "compatibility claims match what the last release published" fail
    printf '%s\n' "$out" | head -5 | sed 's/^/      /'
fi

# A live feature spec says something about its abuse surface. The template's posture row and the
# Reliability line in the NFR taxonomy were section-filling: nothing failed a spec that omitted them
# (REL-T3). Either the posture row or a threat-surface entry satisfies this — demanding one shape
# would have rejected the spec that handles the concern best.
if out=$(python3 scripts/python/check_abuse_surface.py --check --quiet 2>&1); then
    result "live feature specs address their abuse surface" ok
else
    result "live feature specs address their abuse surface" fail
    printf '%s\n' "$out" | head -6 | sed 's/^/      /'
fi

# Every throttled response names the caller's budget. The corpus published a standard requiring
# X-RateLimit-Limit/Remaining and Retry-After on every 429, and its own OpenAPI declared a 429 with
# none of the three — a caller could not learn its budget or when to return, so it would retry at
# once, which is the load the limit exists to prevent (REL-T2).
if out=$(python3 scripts/python/check_rate_limit_contract.py --check --quiet 2>&1); then
    result "throttled responses name the caller's budget" ok
else
    result "throttled responses name the caller's budget" fail
    printf '%s\n' "$out" | head -6 | sed 's/^/      /'
fi

# A change to something that executes or binds owes a changelog entry. CLAUDE.md §7 has said so
# all along and §7.1 describes the gate that enforces it — in the ADOPTING repository. Nothing
# enforced it here, and seven commits of round 5, including a breaking schema change, landed with
# no entry at all (R6-T5).
if out=$(python3 scripts/python/check_changelog.py --quiet 2>&1); then
    [ -n "$out" ] && result "changed scripts and contracts are recorded in the changelog" note "$out" \
                  || result "changed scripts and contracts are recorded in the changelog" ok
else
    result "changed scripts and contracts are recorded in the changelog" fail
    printf '%s\n' "$out" | head -8 | sed 's/^/      /'
fi

# Structural vacuity. Neutering a check — replacing its two-branch construct with an unconditional
# pass — keeps the name, so the coverage ratchet, which guards names, approves it. Proved by doing
# exactly that: the verifier printed `✓ bash -n — neutered` and stayed green (R8-T1). A name that
# can only print ok cannot fail the build, whatever it claims to inspect. Costs no runtime.
if out=$(python3 scripts/python/mutation_coverage.py --vacuity --quiet 2>&1); then
    result "every named check has a failing path" ok
else
    result "every named check has a failing path" fail
    printf '%s\n' "$out" | head -8 | sed 's/^/      /'
fi

# Coverage of the mutation harness itself. It proved 14 of 47 named checks and nothing asked about
# the other 33, so check 48 could arrive with no proof at all and the build would stay green — the
# round-5 finding one level up (R6-T3). Outside the $SMOKE block on purpose: it is pure parsing,
# and the harness runs the verifier with --no-smoke, so a slow-path check would be invisible to it.
if out=$(python3 scripts/python/mutation_coverage.py --check --quiet 2>&1); then
    result "mutation coverage has not fallen" ok "$(python3 scripts/python/mutation_coverage.py --check 2>&1 | head -1)"
else
    result "mutation coverage has not fallen" fail; printf '%s\n' "$out" | head -6 | sed 's/^/      /'
fi

say "C13 spec registry"
if out=$(python3 scripts/python/build_spec_registry.py --check --quiet 2>&1); then
    result "spec registry matches disk" ok
else
    result "spec registry matches disk" fail; printf '%s\n' "$out" | head -10 | sed 's/^/      /'
fi
# Evidence accounting (R5-T4). A path that resolves nowhere and carries no `adopter:` / `ci:` /
# `planned:` marker is the SPEC-FEAT-001 defect and fails. A path merely missing its marker is a
# marking backlog and alerts. The previous rule exempted both by directory prefix and caught
# neither.
ev=$(python3 - <<'PY_EV' 2>/dev/null
import json, subprocess, sys
out = subprocess.run([sys.executable, "scripts/python/build_spec_registry.py", "--json"],
                     capture_output=True, text=True).stdout
d = json.loads(out)
# A spec whose status CLAIMS the work is done must be able to show it: an `implemented` or
# `verified` spec citing evidence that neither resolves nor carries a marker is the exact
# SPEC-FEAT-001 defect (R4-T8). At any other status an unmarked path is a marking backlog.
CLAIMS = ("implemented", "verified")
bad, backlog = [], []
for s in d["specs"]:
    strong = s.get("status") in CLAIMS
    for p in s.get("unresolved_evidence", []):
        bad.append((s["id"], p, "resolves nowhere, marked nowhere"))
    for p in s.get("unmarked_evidence", []):
        (bad if strong else backlog).append(
            (s["id"], p, f"status {s.get('status')} claims done, path is unmarked") if strong
            else (s["id"], p))
print(f"{len(bad)} {len(backlog)} {len({i for i, *_ in backlog})}")
for row in bad[:5]:
    print(f"{row[0]} {row[1]} — {row[2]}")
PY_EV
)
ev_head=$(printf '%s' "$ev" | head -1)
ev_unresolved=$(printf '%s' "$ev_head" | cut -d' ' -f1)
ev_unmarked=$(printf '%s' "$ev_head" | cut -d' ' -f2)
ev_specs=$(printf '%s' "$ev_head" | cut -d' ' -f3)
if [ -z "$ev_head" ]; then
    result "spec evidence paths resolve or carry an explicit marker" fail "could not read the registry"
elif [ "$ev_unresolved" != "0" ]; then
    result "spec evidence paths resolve or carry an explicit marker" fail "$ev_unresolved unaccounted path(s) under a status that claims the work is done"
    printf '%s\n' "$ev" | tail -n +2 | sed 's/^/      /'
elif [ "${ev_unmarked:-0}" != "0" ]; then
    result "spec evidence paths resolve or carry an explicit marker" note "0 unresolved; $ev_unmarked adopter-shaped path(s) in $ev_specs spec(s) still want a marker — see docs/governance/spec-registry.md"
else
    result "spec evidence paths resolve or carry an explicit marker" ok "every path resolves or is marked"
fi

if $SMOKE && $SUITES; then
    # The verifier's own test: every entry injects a defect and requires THAT check to fail.
    # Slow (it re-runs check-corpus once per mutation), so it is behind --no-smoke like the rest.
    # Wall clock, printed on every run. Each proof pays one full verifier run, and the number of
    # proofs grows with the number of checks, so the cost grows with the square. It fits today with
    # room to spare; the point of printing it is that the ceiling shows up before it bites, rather
    # than as a later round's finding (R8-T2).
    mut_t0=$(date +%s)
    if out=$(python3 tests/scripts/test_check_corpus.py 2>&1); then result "tests/scripts/test_check_corpus.py (mutation)" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1) · $(( $(date +%s) - mut_t0 ))s wall clock"; else result "tests/scripts/test_check_corpus.py (mutation)" fail "a check stayed green under its own defect"; printf '%s\n' "$out" | grep -E '^FAIL:' | head -8 | sed 's/^/      /'; fi
    if out=$(python3 tests/scripts/test_asdd_state.py 2>&1); then result "tests/scripts/test_asdd_state.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_asdd_state.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
    if out=$(python3 tests/scripts/test_check_open_items.py 2>&1); then result "tests/scripts/test_check_open_items.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_check_open_items.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
    if out=$(python3 tests/scripts/test_check_changelog.py 2>&1); then result "tests/scripts/test_check_changelog.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_check_changelog.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
    if out=$(python3 tests/scripts/test_mutation_coverage.py 2>&1); then result "tests/scripts/test_mutation_coverage.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_mutation_coverage.py" fail; printf '%s\n' "$out" | grep -E 'FAIL|Error' | head -5 | sed 's/^/      /'; fi
    if out=$(python3 tests/scripts/test_corpus_measure_workflow.py 2>&1); then result "tests/scripts/test_corpus_measure_workflow.py" ok "$(printf '%s' "$out" | grep -E '^Ran' | head -1)"; else result "tests/scripts/test_corpus_measure_workflow.py" fail "the scheduled job is mis-wired"; printf '%s\n' "$out" | grep -E '^FAIL:' | head -5 | sed 's/^/      /'; fi
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
