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
        if kw.get("force_order"): args += ["--force-order"]
        if kw.get("force_unblock"): args += ["--force-unblock"]
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
        self.assertEqual(s["schema_version"], "asdd_state_v2")
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
        self.assertEqual(len(s["artifacts"]), 15)  # keyed by path, one per phase
        self.assertEqual({h["phase"] for h in s["handoffs"] if h["human_gate"]}, HUMAN_GATES)

    def test_blocked_halts_and_exits_two(self):
        self.init(); self.append(0)
        rc, _, err = self.append(1, status="blocked", reason="spec not approved")
        self.assertEqual(rc, 2); self.assertIn("BLOCKED", err)
        self.assertTrue(self.state()["blocked"])
        rc, _, err = self.append(2)                      # pipeline must not advance
        self.assertEqual(rc, 1); self.assertIn("blocked", err)
        self.assertEqual(self.append(2, force_unblock=True)[0], 0)

    def test_a_phase_cannot_go_backwards(self):
        """R4-T3. The state accepted any phase in any order, so it could record a sequence the
        lifecycle does not permit and the FINAL-REPORT would read it as fact."""
        self.init(); self.append(5)
        rc, _, err = self.append(3)
        self.assertEqual(rc, 1); self.assertIn("runs forward", err)
        self.assertEqual(self.append(5)[0], 1, "re-running the same phase also needs --force-order")
        self.assertEqual(self.append(3, force_order=True)[0], 0)

    def test_the_order_guard_compares_against_the_furthest_phase_not_the_last(self):
        """R5-T6. Comparing with the LAST handoff gave the guard an escape one entry deep: the
        forced entry became the yardstick, so the next unforced step back sailed through and
        `validate` pronounced the whole sequence good."""
        self.init(); self.append(5)
        self.assertEqual(self.append(3, force_order=True)[0], 0)
        rc, _, err = self.append(4)
        self.assertEqual(rc, 1, "4 does not advance past 5, which is still the furthest reached")
        self.assertIn("furthest", err)

    def test_forcing_order_does_not_also_clear_a_block(self):
        """R5-T6. One flag cleared both guards, so an operator rewinding a phase silently
        unblocked the pipeline as well — two decisions taken by one word."""
        self.init(); self.append(0)
        self.assertEqual(self.append(1, status="blocked", reason="spec not approved")[0], 2)
        rc, _, err = self.append(0, force_order=True)
        self.assertEqual(rc, 1); self.assertIn("blocked", err)

    def _make_v1(self, feature="FEAT-42"):
        """A v1 state with two phases each producing a `spec.md` — the collision v1 lost to."""
        import json as _j
        self.init(feature)
        self.append(4, artifacts=["specs/x/spec.md"], feature=feature)
        self.append(5, artifacts=["specs/y/spec.md"], feature=feature)
        path = os.path.join(self.root, ".agent", "delivery", feature, "state.json")
        st = _j.load(open(path, encoding="utf-8"))
        st["schema_version"] = "asdd_state_v1"
        st["artifacts"] = {"spec.md": "specs/y/spec.md"}   # what v1 actually stored
        open(path, "w", encoding="utf-8").write(_j.dumps(st))
        return path

    def test_migrate_keeps_every_handoff_and_reindexes_by_path(self):
        """R6-T4. The old advice was `init --force`, which writes over handoffs, artifacts and the
        current phase. That list is the traceability Constitution VII reads."""
        import json as _j
        path = self._make_v1()
        before = _j.load(open(path, encoding="utf-8"))
        rc, out, err = self.run_cmd("migrate", "--feature", "FEAT-42")
        self.assertEqual(rc, 0, out + err)
        after = _j.load(open(path, encoding="utf-8"))
        self.assertEqual(after["schema_version"], "asdd_state_v2")
        self.assertEqual(len(after["handoffs"]), len(before["handoffs"]),
                         "migration must not cost a single handoff")
        self.assertEqual(after["current_phase"], before["current_phase"])
        self.assertEqual(set(after["artifacts"]), {"specs/x/spec.md", "specs/y/spec.md"},
                         "the artefact v1 lost to the basename collision comes back")
        self.assertEqual(after["artifacts"]["specs/x/spec.md"], 4)
        self.assertEqual(self.run_cmd("validate", "--feature", "FEAT-42")[0], 0)

    def test_migrate_refuses_rather_than_guessing_a_phase(self):
        """An artefact the handoffs never name has no phase to attribute. Refusing beats inventing
        one, and beats dropping it quietly."""
        import json as _j
        path = self._make_v1()
        st = _j.load(open(path, encoding="utf-8"))
        st["artifacts"]["stray.md"] = "docs/stray.md"
        open(path, "w", encoding="utf-8").write(_j.dumps(st))
        rc, _, err = self.run_cmd("migrate", "--feature", "FEAT-42")
        self.assertEqual(rc, 1)
        self.assertIn("docs/stray.md", err)

    def test_migrate_is_idempotent(self):
        self._make_v1()
        self.assertEqual(self.run_cmd("migrate", "--feature", "FEAT-42")[0], 0)
        rc, out, _ = self.run_cmd("migrate", "--feature", "FEAT-42")
        self.assertEqual(rc, 0)
        self.assertIn("nothing to migrate", out)

    def test_a_v1_state_is_refused_not_rendered_inverted(self):
        """R5-T6. The artefact map flipped from {basename: path} to {path: phase} and the version
        stayed put, so a v1 file rendered backwards and validated clean."""
        import json as _j
        self.init(); self.append(0, artifacts=["docs/a.md"])
        path = os.path.join(self.root, ".agent", "delivery", "FEAT-42", "state.json")
        st = _j.load(open(path, encoding="utf-8"))
        st["schema_version"] = "asdd_state_v1"
        st["artifacts"] = {"a.md": "docs/a.md"}
        open(path, "w", encoding="utf-8").write(_j.dumps(st))
        rc, _, err = self.run_cmd("validate", "--feature", "FEAT-42")
        self.assertEqual(rc, 1)
        self.assertIn("asdd_state_v1", err)
        self.assertIn("migrate", err, "the error must point at the conversion, not at --force")
        self.assertNotIn("--force", err, "telling an adopter to reset destroys the handoff trail")

    def test_a_forward_jump_is_allowed_because_tiers_skip_phases(self):
        """Right-sizing (ADR-0064) legitimately skips phases, so 0 → 14 must stay possible.
        Only going backwards is the error."""
        self.init()
        self.assertEqual(self.append(0)[0], 0)
        self.assertEqual(self.append(14, to="none (terminal)")[0], 0)

    def test_artifacts_from_different_phases_do_not_collide(self):
        """R4-T3. Keyed by basename, two phases each producing a `spec.md` left only the later
        one — the state silently lost an artefact it exists to track."""
        self.init()
        self.append(4, artifacts=["specs/x/spec.md"])
        self.append(5, artifacts=["specs/y/spec.md"])
        arts = self.state()["artifacts"]
        self.assertEqual(set(arts), {"specs/x/spec.md", "specs/y/spec.md"})
        self.assertEqual(arts["specs/x/spec.md"], 4)

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

    # --- the documented interface, not just the module ---------------------------------------------
    def test_the_command_the_agents_document_actually_runs(self):
        """R4-T1. The 12 tests above call sys.executable, so they exercise the MODULE and never the
        COMMAND the 16 agent files prescribe. That blind spot let `python scripts/python/asdd_state.py`
        ship in 20 places while `python` exists on neither this machine nor a stock Debian/Ubuntu.
        This runs the documented line verbatim."""
        import re
        import shutil as sh
        docs = os.path.join(HERE, ".claude", "agents")
        invocations = set()
        for name in os.listdir(docs):
            if not name.endswith(".md"):
                continue
            for m in re.finditer(r"(python[0-9.]*) (scripts/[\w./-]*asdd_state\.py)", open(os.path.join(docs, name), encoding="utf-8").read()):
                invocations.add(m.groups())
        self.assertTrue(invocations, "no asdd_state invocation found in the agent files")
        for interpreter, script in sorted(invocations):
            self.assertIsNotNone(sh.which(interpreter),
                                 f"the agents document `{interpreter}`, which is not on PATH")
            self.assertTrue(os.path.isfile(os.path.join(HERE, script)),
                            f"the agents document `{script}`, which does not exist")
            r = subprocess.run([interpreter, os.path.join(HERE, script), "--help"],
                               capture_output=True, text=True, env=self.env, timeout=60)
            self.assertEqual(r.returncode, 0, f"`{interpreter} {script} --help` failed: {r.stderr}")

    # --- Constitution V: this script never touches version control --------------------------------
    def test_script_runs_no_git_or_gh(self):
        src = open(SCRIPT, encoding="utf-8").read()
        code = "\n".join(l for l in src.split("\n") if not l.strip().startswith("#"))
        for forbidden in ('"git"', "'git'", '"gh"', "'gh'", "subprocess", "os.system", "popen"):
            self.assertNotIn(forbidden, code, f"asdd_state.py must not reference {forbidden}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
