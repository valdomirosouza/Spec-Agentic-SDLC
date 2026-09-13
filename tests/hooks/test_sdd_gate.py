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


if __name__ == "__main__":
    unittest.main(verbosity=1)
