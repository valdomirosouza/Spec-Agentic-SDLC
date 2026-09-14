#!/usr/bin/env python3
"""Mutation tests for scripts/bash/check-corpus.sh — prove each check can actually fail (#66).

The corpus verifies its content with 50 assertions and never verified the verifier. Nothing fed a
check the defect it exists to catch, so a check written in haste was indistinguishable from one
that works: both stayed green. That is how three vacuous checks shipped in one round and two more
in the next.

Each case below applies a real mutation, runs check-corpus.sh, and requires that it fail AND that
the failure name the problem. A mutation that leaves the check green is the bug this file reports.

Restoration is guaranteed by try/finally per case, and a final guard asserts the tree is clean.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHECK = os.path.join(HERE, "scripts", "bash", "check-corpus.sh")


def run_check(*extra, env=None):
    """check-corpus.sh with the slow sub-suites off: a mutation test runs it many times.

    A mutation run is not a commit, so the changelog gate is waived by default — every mutation
    edits a watched file and would otherwise add an unrelated failure to every single run. The one
    test that exists to prove that gate clears the waiver explicitly."""
    e = dict(os.environ, CHANGELOG_WAIVER="mutation harness run, not a commit")
    e.update(env or {})
    # `extra` REPLACES the default rather than adding to it. Appending `--no-suites` to a hardcoded
    # `--no-smoke` left smoke off, so the five smoke-only checks never ran and their proofs could
    # not fail — five green-looking failures that measured nothing (R10-T2).
    flags = list(extra) or ["--no-smoke"]
    r = subprocess.run(["bash", CHECK, *flags], capture_output=True, text=True,
                       cwd=HERE, timeout=300, env=e)
    return r.returncode, r.stdout + r.stderr


class Mutation:
    """Edit a file, restore it whatever happens."""

    def __init__(self, rel, before, after, *, regex=False):
        self.path = os.path.join(HERE, rel)
        self.rel, self.before, self.after, self.regex = rel, before, after, regex
        self.original = None

    def __enter__(self):
        self.original = open(self.path, encoding="utf-8").read()
        if self.regex:
            # MULTILINE: every mutation here anchors a whole line, and `^` without it matches
            # only the start of the file, which made the pattern silently un-findable.
            new, n = re.subn(self.before, self.after, self.original, count=1, flags=re.MULTILINE)
        else:
            n = self.original.count(self.before)
            new = self.original.replace(self.before, self.after, 1)
        if not n:
            raise AssertionError(f"mutation target not found in {self.rel}: {self.before[:60]!r}")
        open(self.path, "w", encoding="utf-8").write(new)
        return self

    def __exit__(self, *exc):
        open(self.path, "w", encoding="utf-8").write(self.original)
        return False


class MovedAway:
    """Hide paths matching a glob, restore them whatever happens.

    The harness could edit a file and create one, never take one away. A check that counts files
    cannot be perturbed by editing any of them, so the primitive was missing rather than the
    proof (R9-T1)."""

    def __init__(self, pattern):
        self.pattern = os.path.join(HERE, pattern)
        self.moved = []

    def __enter__(self):
        import glob as _g
        for p in sorted(_g.glob(self.pattern)):
            hidden = p + ".mutation-hidden"
            os.rename(p, hidden)
            self.moved.append((hidden, p))
        if not self.moved:
            raise AssertionError(f"nothing matched {self.pattern}: the mutation would be a no-op")
        return self

    def __exit__(self, *exc):
        for hidden, original in self.moved:
            os.rename(hidden, original)
        return False


class NewFile:
    """Drop a file in, remove it whatever happens."""

    def __init__(self, rel, content):
        self.path = os.path.join(HERE, rel)
        self.rel, self.content = rel, content

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        open(self.path, "w", encoding="utf-8").write(self.content)
        return self

    def __exit__(self, *exc):
        if os.path.exists(self.path):
            os.unlink(self.path)
        return False


class CheckCorpusIsNotVacuous(unittest.TestCase):
    """One case per assertion under test. Each proves the check fails on its own defect."""

    @classmethod
    def setUpClass(cls):
        rc, out = run_check()
        if rc != 0:
            raise unittest.SkipTest(f"check-corpus is not green before mutation:\n{out[-1500:]}")

    def assert_mutation_is_caught(self, mutation, check_name, env=None, args=()):
        """The contract: THAT check fails, named, with a message that identifies the problem.

        Asserting only a non-zero exit is not enough and the first version of this file proved it:
        neutralising every refusal in vcs.sh left its own check green and the run failed anyway,
        because a different suite caught the damage behaviourally. The harness reported a pass on a
        check that is vacuous — the same defect it exists to find, one level up. So the failure
        marker must sit on the line naming the check under test."""
        with mutation:
            rc, out = run_check(*args, env=env)
        failed_lines = [l for l in out.split("\n") if l.lstrip().startswith("✗")]
        named = [l for l in failed_lines if check_name in l]
        self.assertTrue(
            named,
            f"`{check_name}` stayed green under its own defect.\n"
            f"Other checks that did fail: {failed_lines or 'none — the run was green'}")

    # --- the four already proven by hand in round 5 ------------------------------------------------
    def test_removing_a_human_gate_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".claude/agents/asdd-phase-2-discovery.md", "--human-gate", ""),
            "gates: 13 blocking, 9 requiring a human")

    def test_a_bare_python_invocation_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".claude/agents/asdd-phase-0-intake.md",
                     "python3 scripts/python/asdd_state.py", "python scripts/python/asdd_state.py"),
            "python3, not bare python")

    def test_removing_the_change_discipline_skill_file_is_caught(self):
        """Scope discipline is a review item, not something a test can assert about a diff, so the
        invariant is that the rule stays reachable. This check was counted as proved by the
        activation-table mutation, because that proof's name matched two checks (R9-T1)."""
        self.assert_mutation_is_caught(
            MovedAway("skills/engineering/change-discipline.md"),
            "change-discipline skill present")

    def test_dropping_the_change_discipline_reference_is_caught(self):
        self.assert_mutation_is_caught(
            # Delete the activation-table ROW. Renaming the first occurrence of the path mutated a
            # prose mention three sections earlier and the check stayed green off a later line —
            # the mutation has to remove the thing the check claims to verify.
            Mutation("CLAUDE.md", r"\| Editing existing code[^\n]*\n", "", regex=True),
            # Long enough to name one check. Bare `change-discipline` matched two, so the proof
            # could not say which one it proved and inflated the count by one.
            "change-discipline is in the activation table")

    def test_unmarking_an_implemented_spec_s_evidence_is_caught(self):
        """R5-T4. The rule that caught SPEC-FEAT-001 was widened by directory prefix until 145 of
        146 paths were exempt and it caught nothing. Exemption is now the author's own marker."""
        self.assert_mutation_is_caught(
            Mutation("specs/api/SPEC-API-002-idempotency-keys.md",
                     "adopter:src/agents/idempotency_store.py", "src/agents/idempotency_store.py"),
            "evidence paths resolve")

    def test_removing_the_schedule_is_caught(self):
        """R5-T7. The cadence lived in a sentence for five rounds and never fired. Deleting the
        cron entry must be as loud as deleting a test."""
        self.assert_mutation_is_caught(
            Mutation(".github/workflows/corpus-measure.yml",
                     r"^    - cron:[^\n]*\n", "", regex=True),
            "measurement is scheduled")

    def test_stripping_the_job_level_token_is_caught(self):
        """R6-T2. Declared only on the step that filed the issue, the measurement ran without a
        token and the archived report silently lost its CI rows — the rows --check is told to
        ignore, so no existing gate could have noticed."""
        self.assert_mutation_is_caught(
            Mutation(".github/workflows/corpus-measure.yml",
                     r"^      GH_TOKEN:[^\n]*\n", "", regex=True),
            "measurement is scheduled")

    def test_dropping_the_pull_request_that_forms_the_series_is_caught(self):
        """Without it the report is archived and never lands, so next week there is still exactly
        one dated report and the comparison has nothing to compare against."""
        self.assert_mutation_is_caught(
            Mutation(".github/workflows/corpus-measure.yml", "gh pr create", "gh pr view"),
            "measurement is scheduled")

    def test_removing_a_proof_from_this_file_is_caught(self):
        """R6-T3. The harness proves checks can fail; nothing proved the harness keeps doing so.
        Pointing an entry at a check that does not exist must be as loud as deleting a test."""
        self.assert_mutation_is_caught(
            # Anchored on the call, not the bare name: the first `"adr-index"` in this file is the
            # literal on this very line, so a looser target mutated the mutation into a no-op and
            # the harness reported a pass. Self-reference, caught by the run failing to fail.
            Mutation(__file__.replace(HERE + os.sep, ""),
                     '\n            "adr-index")', '\n            "adr-index-gone")'),
            "mutation coverage has not fallen")

    def test_a_changelog_that_cannot_record_anything_is_caught(self):
        """R6-T5. Seven commits of round 5, one a breaking schema change, reached main with no entry
        and nothing looked. The first version of this proof created a watched file and depended on
        CHANGELOG.md happening to be clean, so it passed or failed according to the working tree.
        The section is an invariant instead, true on every run."""
        self.assert_mutation_is_caught(
            Mutation("CHANGELOG.md", "## [Unreleased]", "## [Nope]"),
            "recorded in the changelog",
            env={"CHANGELOG_WAIVER": ""})

    def test_an_open_item_past_its_date_is_caught(self):
        """R6-T6. Every open item in the corpus was deferred to a review nothing convenes or to an
        event named only in prose, so nothing could ever come due."""
        self.assert_mutation_is_caught(
            # The date here moves when the schedule is restaggered, so the mutation reads the
            # live value instead of hard-coding one that goes stale (it did, in #82).
            Mutation("specs/data/data-quality.md",
                     r"\| 20\d\d-\d\d-\d\d\s*\|", "| 2026-01-05 |", regex=True),
            "open items carry a date")

    def test_deleting_a_check_from_the_verifier_is_caught(self):
        """R7-T1. The ratchet guarded the ratio, and a ratio rises when its denominator shrinks, so
        deleting unproved checks was the cheapest way to satisfy the gate that exists to protect
        them. Renaming one keeps the count identical and the ratio unchanged, which is why the
        baseline had to record names."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/check-corpus.sh", 'result "bash -n"', 'result "bash -n gone"'),
            "mutation coverage has not fallen")

    def test_renaming_an_open_items_heading_is_caught(self):
        """R7-T2. Scope was keyed to the literal `Open items`, so `### Open finding` in the data
        catalogue fell outside it — taking DQ-REG-006, the corpus's only live open finding, with it.
        A silent scope collapse looks exactly like success: every remaining item still passes."""
        self.assert_mutation_is_caught(
            # `## 10. Open items` — the corpus numbers its headings, which is also what broke the
            # first attempt at widening the pattern.
            Mutation("specs/data/data-quality.md", "## 10. Open items", "## 10. Pending"),
            "open items carry a date")
        # The scope ratchet now names the table that vanished; before #86 the floors were constants
        # that widened into non-guards as items were added.

    def test_an_unfounded_compatibility_claim_is_caught(self):
        """R8-T5. The claim is derived from what the last release actually published, not from a
        word. A contract added after the release cannot break anyone on it — which is what made
        the BREAKING label here, and the 2.0.0 it forced, an overstatement of my own."""
        self.assert_mutation_is_caught(
            Mutation("CHANGELOG.md", "### Fixed",
                     "### Fixed\n\n- **BREAKING: an invented incompatibility.**"),
            "compatibility claims match")

    def test_neutering_a_check_into_an_unconditional_pass_is_caught(self):
        """R8-T1. Replacing a check's two-branch construct with a bare `ok` keeps its name, so the
        coverage ratchet approved it: the verifier printed `bash -n — neutered` and stayed green.
        Two thirds of the checks could be turned into no-ops that way."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/check-corpus.sh",
                     r'\n[^\n]*result "bash -n"[^\n]*\n', '\nresult "bash -n" ok "neutered"\n',
                     regex=True),
            "every named check has a failing path")

    # --- R8-T2. The checks that guard the guardrails -------------------------------------------
    # Chosen by a stated criterion, not to reach a number: these assert Constitution articles and
    # the C8 governance invariants, where a vacuous check is most dangerous. Writing mutations to
    # hit a percentage produces weak mutations, which is the round-5 pathology inverted.

    def test_a_script_that_pushes_is_caught(self):
        """Constitution V. No script here performs an outward version-control action."""
        self.assert_mutation_is_caught(
            NewFile("scripts/bash/mutation-push-probe.sh",
                    "#!/usr/bin/env bash\ngit push origin main\n"),
            "scripts never push")

    def test_a_second_script_creating_a_branch_is_caught(self):
        """ADR-0095 names exactly one exception, behind the protected-name guard."""
        self.assert_mutation_is_caught(
            NewFile("scripts/bash/mutation-branch-probe.sh",
                    "#!/usr/bin/env bash\ngit checkout -b probe\n"),
            "only vcs.sh creates a branch")

    def test_the_delivery_state_reaching_for_git_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("scripts/python/asdd_state.py",
                     'STATUSES = ("done", "blocked")',
                     'STATUSES = ("done", "blocked")\n_PROBE = ["git"]'),
            "asdd_state.py runs no git or gh")

    def test_unhooking_the_high_risk_guard_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".claude/settings.json",
                     "high-risk-action-guard.py", "disabled-guard.py"),
            "settings.json keeps the PreToolUse high-risk guard")

    def test_deleting_a_constitutional_article_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("memory/constitution.md",
                     "### V. Human Oversight of Agents", "### V. Oversight"),
            "constitution has articles")

    def test_a_second_coverage_floor_is_caught(self):
        """One number, one place. Two declared floors is the ambiguity the check exists for."""
        self.assert_mutation_is_caught(
            Mutation("docs/adr/ADR-0022-testing-strategy.md",
                     "> ## The declared coverage floor is 85%",
                     "> ## The declared coverage floor is 85%\n>\n> ## The declared coverage floor is 80%"),
            "ADR-0022 declares exactly one floor")

    def test_dropping_tests_first_from_the_task_template_is_caught(self):
        """Constitution II. The template is where tests-first reaches every generated task."""
        self.assert_mutation_is_caught(
            Mutation("templates/tasks-template.md",
                     "### Tests first (write, run, watch them FAIL)", "### Tests (optional)"),
            "tasks-template keeps tests-first")

    def test_removing_the_approved_spec_requirement_is_caught(self):
        """Article I. Without it the prerequisite script stops demanding an approved spec."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/check-prerequisites.sh",
                     "--require-approved) REQ_APPROVED=true ;;",
                     "--require-anything) REQ_APPROVED=true ;;"),
            "check-prerequisites keeps --require-approved")

    def test_reintroducing_the_red_team_finding_is_caught(self):
        """RT-04 (High): `$(which git) push` evaded the guard because command substitution hid the
        binary name. The exercise's twelve attempts are kept as tests precisely so the fix cannot
        be undone quietly."""
        self.assert_mutation_is_caught(
            Mutation(".claude/hooks/high-risk-action-guard.py",
                     "return _RESOLVER.sub(lambda m: m.group(1) or m.group(2), segment)",
                     "return segment"),
            "red-team RT-2026-09-13 findings stay closed")

    # --- R9-T1. The checks that could be switched off by widening -------------------------------
    # Proving a check also defends it against widening: with the rule widened the proof itself goes
    # red, which was measured before this plan was written. That closes both the widening case and
    # the always-true-condition residual of the vacuity invariant, for each check it covers.

    def test_an_unmarked_adopter_path_reference_is_caught(self):
        """The rule the round-5 audit found widened until it exempted 145 of 146 paths."""
        self.assert_mutation_is_caught(
            NewFile("docs/mutation-adopter-probe.md",
                    "# probe\n\nIt names `src/` and `.github/workflows/` without a marker.\n"),
            "adopter-paths")

    def test_a_script_that_does_not_parse_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("scripts/bash/mutation-syntax-probe.sh",
                    # A real parse error. `if [ 1 = 1 ; then …` parses fine — `[` is a command,
                    # not syntax, so the first probe tested nothing.
                    "#!/usr/bin/env bash\nif true; then echo x\n"),
            "bash -n")

    def test_a_control_matrix_pointing_at_nothing_is_caught(self):
        """ADR-0072: a dead implemented_by path is the defect the matrix gate exists for."""
        self.assert_mutation_is_caught(
            Mutation("specs/security/asvs-control-matrix.yaml",
                     "      - adopter:src/api/rest/routers/requests.py",
                     "      - src/does/not/exist.py"),
            "check_control_matrix")

    def test_a_rendered_command_drifting_from_its_source_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".agents/skills/sdd-analyze/SKILL.md", "\n", "\nDRIFT\n", regex=False),
            "render_commands --check")

    def test_a_registry_that_disagrees_with_disk_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("docs/governance/spec-registry.json", '"count": 58', '"count": 57'),
            "spec registry matches disk")

    def test_an_upstream_pin_missing_a_field_is_caught(self):
        """The pin records which spec-kit commit this corpus was compared against; without the
        commit it records nothing that can be checked."""
        self.assert_mutation_is_caught(
            Mutation("docs/sdlc/spec-kit-upstream.json", '"commit"', '"commit_was"'),
            "spec-kit-upstream.json")

    def test_a_corpus_with_no_measurement_is_caught(self):
        """The one check a file edit cannot perturb: it counts reports."""
        self.assert_mutation_is_caught(
            MovedAway("docs/sre/corpus-metrics-*.md"),
            "the corpus carries at least one measurement")

    def test_a_runner_line_that_grows_logic_is_caught(self):
        """R10-T1. Drift, not forgery: a line that genuinely runs a suite later gains an assertion
        inline and keeps its name, which used to exempt it from ever needing a proof."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/check-corpus.sh",
                     'if out=$(python3 tests/scripts/test_check_changelog.py 2>&1); then',
                     'if [ -f README.md ] && out=$(python3 tests/scripts/test_check_changelog.py 2>&1); then'),
            "mutation coverage has not fallen")

    # --- R10-T2. The adopter's first commands -------------------------------------------------
    # These five were exempted last round as "tooling rather than governance". SETUP.md line 16
    # tells a new adopter to run `create-new-feature.sh --json --dry-run` as their first step, and
    # the README says the same, so the exemption's stated reason was wrong: they guard the entry
    # path. They run only under smoke, where a verifier run costs ~60s against ~7, so each of these
    # is roughly eight times the cost of any other proof. `--no-suites` keeps the dry-runs on
    # without recursing into this harness.
    SMOKE_ARGS = ("--no-suites",)

    def test_a_broken_dry_run_report_is_caught(self):
        """Perturb the REPORTED result, never the behaviour. The first version of this mutation set
        `DRY_RUN=maybe`, which stopped the flag being a dry run at all: the script created a feature
        directory on disk and left the registry disagreeing with it. A mutation must make the system
        fail an assertion, never make it do more."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/create-new-feature.sh",
                     '"BRANCH_NAME":"%s","DRY_RUN":%s}', '"BRANCH_NAME":"%s","DRY_RAN":%s}'),
            "create-new-feature --dry-run", args=self.SMOKE_ARGS)

    def test_setup_plan_not_writing_quickstart_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/setup-plan.sh",
                     "copy_if_absent quickstart-template.md \"$QUICKSTART\"",
                     ": # copy_if_absent quickstart-template.md"),
            "setup-plan (scratch)", args=self.SMOKE_ARGS)

    def test_prerequisites_dropping_tasks_from_available_docs_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/check-prerequisites.sh",
                     '$INC_TASKS && [ -f "$TASKS" ] && docs="$docs tasks.md"',
                     '$INC_TASKS && [ -f "$TASKS" ] && docs="$docs"'),
            "check-prerequisites (example)", args=self.SMOKE_ARGS)

    def test_tasks_to_issues_planning_nothing_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/tasks-to-issues.sh",
                     "    planned=$((planned+1))", "    planned=$((planned+0))"),
            "tasks-to-issues --dry-run (example)", args=self.SMOKE_ARGS)

    def test_a_missing_example_bundle_is_caught(self):
        """The bundle the corpus ships as the worked example an adopter reads first."""
        self.assert_mutation_is_caught(
            # The whole bundle. Hiding only spec.md left the directory present, so this check never
            # fired and three other checks failed on the wreckage instead — a mutation has to remove
            # the thing the check actually looks for.
            MovedAway("specs/features/SPEC-LGS-001-log-based-golden-signals"),
            "example bundle present", args=self.SMOKE_ARGS)

    def test_a_throttled_response_without_retry_after_is_caught(self):
        """REL-T2. The standard requires three headers on every 429; the published contract carried
        none. A caller that cannot read its budget discovers the ceiling by hitting it, and without
        Retry-After it returns immediately — the load the limit exists to prevent."""
        self.assert_mutation_is_caught(
            Mutation("docs/api/openapi/v1/openapi.yaml",
                     '            Retry-After: { $ref: "#/components/headers/RetryAfter" }\n', ""),
            "throttled responses name the caller's budget")

    def test_an_unindexed_adr_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("docs/adr/ADR-9999-mutation-probe.md",
                    "# ADR-9999 — probe\n\n**Status:** Accepted\n"),
            "adr-index")

    # --- the assertions this round repairs ---------------------------------------------------------
    def test_a_broken_internal_link_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("docs/mutation-probe.md",
                    "<!-- adopter-paths: probe -->\n\n# probe\n\n[dead](./does-not-exist.md)\n"),
            "links")

    def test_a_spec_with_a_bad_id_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("specs/api/mutation-probe.md",
                    "---\nid: NOT-A-SPEC-ID\nkind: spec\nstatus: approved\n---\n\n# probe\n"),
            "frontmatter")

    def test_a_neutralised_refusal_is_caught(self):
        """R5-T2. The check counted the string `refuse "` and passed while every refusal was a
        no-op — the single script that touches git was guarded by a word count."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/vcs.sh",
                     'refuse() {\n    echo "REFUSED: $1" >&2',
                     'refuse() {\n    return 0\n    echo "REFUSED: $1" >&2'),
            "refuses merge, release, deploy, push")

    def test_a_productivity_ratio_is_caught_in_every_form(self):
        """R5-T3. The repaired regex caught only `N× faster` and lost the divided form the
        previous one caught."""
        forms = [
            "human-equivalent 320h ÷ agent wall-clock 2h = 160×",
            "We observed 160 times faster delivery.",
            "speedup ratio: 160",
            "The run was 160× faster.",
            "A 40x quicker pipeline than any benchmark.",
        ]
        for i, form in enumerate(forms):
            with self.subTest(form=form):
                self.assert_mutation_is_caught(
                    NewFile(f"docs/mutation-probe-ratio-{i}.md",
                            f"<!-- adopter-paths: probe -->\n\n# probe\n\n{form}\n"),
                    "speedup ratio")

    def test_a_restated_coverage_number_is_caught(self):
        """R5-T3. `Coverage MUST be 80% per ADR-0022.` passed, because citing the ADR exempted the
        line — and citing the ADR is exactly what a restated number would do."""
        self.assert_mutation_is_caught(
            Mutation("CLAUDE.md",
                     "- Unit coverage **MUST** be at or above the floor declared in ADR-0022",
                     "- Unit coverage **MUST** be 80% per ADR-0022"),
            "bare number")

    def test_a_stale_measurement_report_is_caught(self):
        """R5-T5. `--check` compared only section headings, so no number could fail it."""
        report = sorted(f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                        if f.startswith("corpus-metrics-") and f.endswith(".md"))[-1]
        self.assert_mutation_is_caught(
            Mutation(f"docs/sre/{report}", r"\| Markdown files \| \d+ \|",
                     "| Markdown files | 1 |", regex=True),
            "measurement report")

    def test_unmarked_unresolvable_evidence_is_caught(self):
        """R5-T4. The exemption list was widened until 145 of 146 evidence paths were exempt and
        the rule could no longer catch the case it was written for."""
        self.assert_mutation_is_caught(
            NewFile("specs/api/mutation-probe-evidence.md",
                    "---\nid: SPEC-API-099\nkind: spec\nstatus: implemented\n"
                    "verified_by:\n  - nowhere/does-not-exist.py\n---\n\n# probe\n"),
            "data-quality")


def _tracked_status():
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                       cwd=HERE, timeout=60)
    # Untracked files are the author's business; a leak shows up as a MODIFIED tracked file.
    return sorted(l for l in r.stdout.split("\n") if l and not l.startswith("??"))


# Taken at import, before any mutation runs. Demanding a clean tree instead compared the harness
# against the wrong baseline: the tree is never clean at the moment this runs, because it runs
# from check-corpus.sh immediately before a commit. It reported a leak on the author's own edits.
_STATUS_AT_START = _tracked_status()


class NoSuitesFlag(unittest.TestCase):
    """R10-T3. `--no-suites` was added one round ago to make a deferred decision possible and
    nothing ran it — a flag in the verifier that nobody exercises can break in silence, which is the
    category this corpus spent three rounds closing everywhere else.

    It has five real users now: the proofs for the adopter-entry checks need the dry-runs on and the
    sub-suites off, because leaving the suites on would recurse into this harness. Those five
    exercise the flag behaviourally. What they cannot assert is the flag's own contract, which is
    what these two do, statically and at no runtime cost."""

    def setUp(self):
        with open(CHECK, encoding="utf-8") as fh:
            self.t = fh.read()

    def test_the_flag_exists_and_gates_the_suite_block(self):
        self.assertIn("--no-suites) SUITES=false ;;", self.t)
        self.assertIn("if $SMOKE && $SUITES; then", self.t,
                      "the sub-suite block, which contains this harness, must be what SUITES gates")

    def test_the_smoke_proofs_are_what_exercise_it(self):
        """If this stops being true the flag has no user again, and should go rather than sit
        unexercised."""
        with open(__file__, encoding="utf-8") as fh:
            mine = fh.read()
        self.assertIn('SMOKE_ARGS = ("--no-suites",)', mine)
        self.assertGreaterEqual(mine.count("args=self.SMOKE_ARGS"), 5)


class TreeIsClean(unittest.TestCase):
    def test_no_mutation_leaked(self):
        leaked = [l for l in _tracked_status() if l not in _STATUS_AT_START]
        self.assertEqual(leaked, [], f"a mutation leaked into the tree:\n{chr(10).join(leaked)}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
