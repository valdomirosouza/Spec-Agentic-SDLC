#!/usr/bin/env python3
"""Behavioural tests for .claude/hooks/sdd-gate.py (ADR-0092, #22). stdlib only: python3 tests/hooks/test_sdd_gate.py"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(HERE, ".claude", "hooks", "sdd-gate.py")


def scratch(status="draft", checklist=None, with_feature=True):
    t = tempfile.mkdtemp()
    os.makedirs(os.path.join(t, "memory"))
    shutil.copy(os.path.join(HERE, "memory", "constitution.md"), os.path.join(t, "memory"))
    shutil.copytree(os.path.join(HERE, "scripts", "bash"), os.path.join(t, "scripts", "bash"))
    if with_feature:
        d = os.path.join(t, "specs", "features", "SPEC-ZZ-001-gate")
        os.makedirs(os.path.join(d, "checklists"))
        open(os.path.join(d, "spec.md"), "w").write(f"---\nid: SPEC-ZZ-001\nkind: feature-spec\nstatus: {status}\n---\n# x\n")
        if checklist is not None:
            open(os.path.join(d, "checklists", "requirements.md"), "w").write(checklist)
        os.makedirs(os.path.join(t, ".sdd"))
        open(os.path.join(t, ".sdd", "feature.json"), "w").write('{"feature_directory": "specs/features/SPEC-ZZ-001-gate"}\n')
    return t


def run(root, prompt, raw=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=root)
    env.pop("SDD_FEATURE_DIRECTORY", None)
    data = raw if raw is not None else json.dumps({"hook_event_name": "UserPromptSubmit", "user_prompt": prompt, "cwd": root})
    r = subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True, env=env, cwd=root, timeout=20)
    return r.returncode, r.stdout, r.stderr


class SddGate(unittest.TestCase):
    def test_non_sdd_prompt_is_silent(self):
        t = scratch("draft"); rc, out, err = run(t, "explain the architecture"); shutil.rmtree(t)
        self.assertEqual((rc, out, err), (0, "", ""))

    def test_mid_sentence_mention_is_not_a_command(self):
        t = scratch("draft"); rc, out, err = run(t, "should I run /sdd-implement now?"); shutil.rmtree(t)
        self.assertEqual((rc, out, err), (0, "", ""))

    def test_non_code_producing_command_is_silent(self):
        t = scratch("draft"); rc, out, err = run(t, "/sdd-clarify security"); shutil.rmtree(t)
        self.assertEqual((rc, out), (0, ""))

    def test_draft_spec_blocks_implement(self):
        t = scratch("draft"); rc, out, err = run(t, "/sdd-implement only US1"); shutil.rmtree(t)
        self.assertEqual(rc, 2); self.assertIn("Constitution I", err); self.assertIn("SPEC-ZZ-001", err)

    def test_draft_spec_blocks_plan_tasks_taskstoissues(self):
        for cmd in ("/sdd-plan python", "/sdd-tasks", "/sdd-taskstoissues --dry-run"):
            t = scratch("draft"); rc, out, err = run(t, cmd); shutil.rmtree(t)
            self.assertEqual(rc, 2, cmd)

    def test_approved_with_unchecked_items_prints_table(self):
        t = scratch("approved", "- [x] CHK001 a\n- [ ] CHK002 b\n- [ ] CHK003 c\n")
        rc, out, err = run(t, "  /sdd-implement"); shutil.rmtree(t)
        self.assertEqual(rc, 0); self.assertIn("| requirements.md | 3 | 1 | 2 |", out); self.assertIn("proceed anyway?", out)

    def test_implemented_all_checked(self):
        t = scratch("implemented", "- [x] CHK001 a\n"); rc, out, err = run(t, "/sdd-tasks"); shutil.rmtree(t)
        self.assertEqual(rc, 0); self.assertIn("All checklist items are checked", out)

    def test_no_feature_dir_fails_open_with_context(self):
        t = scratch(with_feature=False); rc, out, err = run(t, "/sdd-implement"); shutil.rmtree(t)
        self.assertEqual(rc, 0); self.assertIn("no active feature", out)

    def test_malformed_input_fails_open(self):
        t = scratch("draft"); rc, out, err = run(t, "", raw="not json"); shutil.rmtree(t)
        self.assertEqual((rc, out), (0, ""))

    def test_hook_never_writes(self):
        t = scratch("approved", "- [ ] CHK001 a\n")
        before = {os.path.join(d, f): os.path.getmtime(os.path.join(d, f)) for d, _, fs in os.walk(t) for f in fs}
        run(t, "/sdd-implement")
        after = {os.path.join(d, f): os.path.getmtime(os.path.join(d, f)) for d, _, fs in os.walk(t) for f in fs}
        shutil.rmtree(t); self.assertEqual(before, after)

    def test_settings_registers_the_gate_without_touching_the_guard(self):
        cfg = json.load(open(os.path.join(HERE, ".claude", "settings.json")))
        ups = cfg["hooks"]["UserPromptSubmit"]
        self.assertTrue(any("sdd-gate.py" in h["command"] for m in ups for h in m["hooks"]))
        pre = cfg["hooks"]["PreToolUse"]
        self.assertTrue(any("high-risk-action-guard.py" in h["command"] for m in pre for h in m["hooks"]))



def bug(root, decision_rows, spec_line="**Spec:** specs/api/SPEC-ZZ-002-x.md", spec_status="approved"):
    """docs/bugs/BUG-7/assessment.md in `root`, citing a spec of `spec_status` (ADR-0096)."""
    os.makedirs(os.path.join(root, "specs", "api"), exist_ok=True)
    open(os.path.join(root, "specs", "api", "SPEC-ZZ-002-x.md"), "w").write(
        f"---\nid: SPEC-ZZ-002\nstatus: {spec_status} # draft | approved\n---\n# x\n")
    d = os.path.join(root, "docs", "bugs", "BUG-7")
    os.makedirs(d, exist_ok=True)
    rows = "".join(f"| {r} |\n" for r in decision_rows)
    open(os.path.join(d, "assessment.md"), "w").write(
        f"# BUG-7 assessment\n\n{spec_line}\n\n## Root cause\n\nx\n\n## Decision\n\n"
        f"| Decided by | Date | accepted / rejected | Note |\n| --- | --- | --- | --- |\n{rows}")


ACCEPTED = "Tech Lead | 2026-11-07 | accepted | ok"


class BugfixFixGate(unittest.TestCase):
    """ADR-0096: `/sdd-bugfix fix` starts only from an accepted diagnosis citing an approved spec."""

    def gate(self, prompt="/sdd-bugfix fix BUG-7", **kw):
        t = scratch(with_feature=False)
        self.addCleanup(shutil.rmtree, t)
        if kw.pop("assessment", True):
            bug(t, **kw)
        return run(t, prompt)

    def test_accepted_diagnosis_and_approved_spec_pass(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED])
        self.assertEqual(rc, 0, err); self.assertIn("SPEC-ZZ-002-x.md is approved", out)

    def test_missing_assessment_blocks(self):
        rc, out, err = self.gate(assessment=False)
        self.assertEqual(rc, 2); self.assertIn("assessment.md does not exist", err)

    def test_unfilled_decision_blocks(self):
        rc, out, err = self.gate(decision_rows=["{…} | {…} | accepted / rejected | {…}"])
        self.assertEqual(rc, 2); self.assertIn("no decision recorded", err)

    def test_rejected_diagnosis_blocks(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED, "Tech Lead | 2026-11-08 | rejected | wrong cause"])
        self.assertEqual(rc, 2); self.assertIn("'rejected'", err)

    def test_the_last_decision_wins(self):
        rc, out, err = self.gate(decision_rows=["Tech Lead | 2026-11-06 | rejected | x", ACCEPTED])
        self.assertEqual(rc, 0, err)

    def test_unapproved_spec_blocks(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED], spec_status="draft")
        self.assertEqual(rc, 2); self.assertIn("status 'draft'", err); self.assertIn("Constitution I", err)

    def test_missing_spec_line_blocks(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED], spec_line="")
        self.assertEqual(rc, 2); self.assertIn("no `**Spec:**` line", err)

    def test_a_spec_outside_specs_is_not_accepted(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED], spec_line="**Spec:** ../../etc/passwd")
        self.assertEqual(rc, 2)

    def test_a_rem_id_stands_in_for_the_spec(self):
        rc, out, err = self.gate(decision_rows=[ACCEPTED], spec_line="**Spec:** REM-012")
        self.assertEqual(rc, 0, err); self.assertIn("REM-012", out)

    def test_assess_and_test_stages_are_not_gated(self):
        for p in ("/sdd-bugfix assess #7", "/sdd-bugfix test BUG-7"):
            rc, out, err = self.gate(prompt=p, assessment=False)
            self.assertEqual((rc, out, err), (0, "", ""), p)

    def test_fix_without_a_bug_id_fails_open_with_context(self):
        rc, out, err = self.gate(prompt="/sdd-bugfix fix", assessment=False)
        self.assertEqual(rc, 0); self.assertIn("no BUG-<issue> given", out)


class GatedSkillsAreUserInvoked(unittest.TestCase):
    """The hook sees only what a person types; a skill the model invokes itself skips it (#138)."""

    def gated(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("sdd_gate", HOOK)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return list(mod.COMMANDS) + ["sdd-bugfix"]

    def test_every_gated_command_disables_model_invocation(self):
        for name in self.gated():
            text = open(os.path.join(HERE, ".claude", "skills", name, "SKILL.md"), encoding="utf-8").read()
            fm = text.split("\n---", 1)[0]
            self.assertIn("\ndisable-model-invocation: true", fm, name)

if __name__ == "__main__":
    unittest.main(verbosity=1)
