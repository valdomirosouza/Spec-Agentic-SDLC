#!/usr/bin/env python3
"""Tests for scripts/python/asdd_state.py against docs/sdlc/agent-handoff-schema.md (#44)."""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "asdd_state.py")

# The nine phases whose agents declare --human-gate, and the full 15-phase chain.
HUMAN_GATES = {2, 4, 5, 7, 10, 11, 12, 13, 14}


class AsddState(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.env = dict(os.environ, ASDD_ROOT=self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_cmd(self, *args):
        r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                           env=self.env, timeout=60)
        return r.returncode, r.stdout, r.stderr

    def init(self, feature="FEAT-42"):
        return self.run_cmd("init", "--feature", feature, "--title", "Bulk HITL approval",
                            "--risk-class", "normal feature")

    def append(self, phase, status="done", feature="FEAT-42", **kw):
        args = ["append-handoff", "--feature", feature, "--status", status, "--phase", str(phase),
                "--agent", kw.get("agent", f"asdd-phase-{phase}-x"),
                "--handoff-to", kw.get("to", "next")]
        if kw.get("artifacts"): args += ["--artifacts", *kw["artifacts"]]
        if kw.get("reason"): args += ["--reason", kw["reason"]]
        if kw.get("human_gate"): args += ["--human-gate"]
        if kw.get("force"): args += ["--force"]
        return self.run_cmd(*args)

    def state(self, feature="FEAT-42"):
        rc, out, err = self.run_cmd("show", "--feature", feature, "--json")
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    # --- lifecycle -------------------------------------------------------------------------------
    def test_init_creates_state_at_the_documented_path(self):
        rc, out, err = self.init()
        self.assertEqual(rc, 0, err)
        self.assertTrue(os.path.isfile(os.path.join(self.root, ".agent", "delivery", "FEAT-42", "state.json")))
        s = self.state()
        self.assertEqual(s["schema_version"], "asdd_state_v1")
        self.assertEqual((s["current_phase"], s["blocked"], s["handoffs"]), (0, False, []))

    def test_init_refuses_to_overwrite_without_force(self):
        self.init()
        rc, _, err = self.init()
        self.assertEqual(rc, 1); self.assertIn("already exists", err)
        self.assertEqual(self.run_cmd("init", "--feature", "FEAT-42", "--title", "x", "--force")[0], 0)

    def test_full_fifteen_phase_run(self):
        self.init()
        for p in range(15):
            rc, _, err = self.append(p, human_gate=(p in HUMAN_GATES), artifacts=[f"docs/a{p}.md"],
                                     to="next" if p < 14 else "none (terminal)")
            self.assertEqual(rc, 0, err)
        s = self.state()
        self.assertEqual(len(s["handoffs"]), 15)
        self.assertEqual(s["current_phase"], 14)
        self.assertEqual(len(s["artifacts"]), 15)
        self.assertEqual({h["phase"] for h in s["handoffs"] if h["human_gate"]}, HUMAN_GATES)

    def test_blocked_halts_and_exits_two(self):
        self.init(); self.append(0)
        rc, _, err = self.append(1, status="blocked", reason="spec not approved")
        self.assertEqual(rc, 2); self.assertIn("BLOCKED", err)
        self.assertTrue(self.state()["blocked"])
        rc, _, err = self.append(2)                      # pipeline must not advance
        self.assertEqual(rc, 1); self.assertIn("blocked", err)
        self.assertEqual(self.append(2, force=True)[0], 0)

    # --- validation rules from the schema ---------------------------------------------------------
    def test_blocked_without_reason_is_refused(self):
        self.init()
        rc, _, err = self.append(1, status="blocked")
        self.assertEqual(rc, 1); self.assertIn("reason is required", err)

    def test_phase_out_of_range_is_refused(self):
        self.init()
        for bad in ("15", "-1", "99"):
            rc, _, err = self.run_cmd("append-handoff", "--feature", "FEAT-42", "--status", "done",
                                      "--phase", bad, "--agent", "a", "--handoff-to", "b")
            self.assertEqual(rc, 1, bad); self.assertIn("phase must be an int", err)

    def test_unknown_status_is_refused_by_the_parser(self):
        self.init()
        rc, _, err = self.run_cmd("append-handoff", "--feature", "FEAT-42", "--status", "maybe",
                                  "--phase", "1", "--agent", "a", "--handoff-to", "b")
        self.assertEqual(rc, 2); self.assertIn("invalid choice", err)

    def test_unsafe_feature_id_is_refused(self):
        for bad in ("../etc", "a/b", ""):
            rc, _, err = self.run_cmd("init", "--feature", bad, "--title", "x")
            self.assertEqual(rc, 1, bad)

    def test_operations_on_unknown_feature_fail_closed(self):
        rc, _, err = self.run_cmd("show", "--feature", "NOPE")
        self.assertEqual(rc, 1); self.assertIn("no delivery state", err)

    def test_corrupt_state_is_detected_not_ignored(self):
        self.init()
        p = os.path.join(self.root, ".agent", "delivery", "FEAT-42", "state.json")
        open(p, "w").write("{not json")
        rc, _, err = self.run_cmd("validate", "--feature", "FEAT-42")
        self.assertEqual(rc, 1); self.assertIn("not valid JSON", err)
        s = json.loads('{"schema_version":"wrong","feature_id":"FEAT-42","current_phase":0,'
                       '"blocked":false,"artifacts":{},"handoffs":[]}')
        json.dump(s, open(p, "w"))
        rc, _, err = self.run_cmd("validate", "--feature", "FEAT-42")
        self.assertEqual(rc, 1); self.assertIn("schema_version", err)

    def test_validate_passes_on_a_real_run(self):
        self.init()
        for p in range(3): self.append(p)
        self.assertEqual(self.run_cmd("validate", "--feature", "FEAT-42")[0], 0)

    # --- Constitution V: this script never touches version control --------------------------------
    def test_script_runs_no_git_or_gh(self):
        src = open(SCRIPT, encoding="utf-8").read()
        code = "\n".join(l for l in src.split("\n") if not l.strip().startswith("#"))
        for forbidden in ('"git"', "'git'", '"gh"', "'gh'", "subprocess", "os.system", "popen"):
            self.assertNotIn(forbidden, code, f"asdd_state.py must not reference {forbidden}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
