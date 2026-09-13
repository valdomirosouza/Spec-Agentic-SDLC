#!/usr/bin/env python3
"""Tests for scripts/python/build_spec_registry.py (#47). stdlib only."""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "build_spec_registry.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import build_spec_registry as reg  # noqa: E402

FM = """---
id: {id}
kind: {kind}
status: {status}
owner: Tech Lead
issue: {issue}
governing_adrs:
  - ADR-0001
  - ADR-0002
implemented_by: []
verified_by: []
last_updated: 2026-09-13
---

# {id}
"""


class EvidenceAccounting(unittest.TestCase):
    """R5-T4. The rule was widened until it exempted 145 of 146 paths and could no longer catch
    the SPEC-FEAT-001 case that created it. Exemption is now by marker, not by directory shape."""

    def test_an_explicit_marker_exempts_and_removing_it_does_not(self):
        marked = {"implemented_by": ["adopter:src/api/rest/main.py"], "verified_by": []}
        self.assertEqual(reg.unresolved_evidence(marked), ([], []))
        unmarked = {"implemented_by": ["src/api/rest/main.py"], "verified_by": []}
        unresolved, backlog = reg.unresolved_evidence(unmarked)
        self.assertEqual(unresolved, [])
        self.assertEqual(backlog, ["src/api/rest/main.py"],
                         "stripping the marker must put the path back in front of a human")

    def test_a_path_that_belongs_nowhere_is_the_finding_not_the_backlog(self):
        entry = {"implemented_by": ["nowhere/at/all.py"], "verified_by": []}
        self.assertEqual(reg.unresolved_evidence(entry), (["nowhere/at/all.py"], []))

    def test_a_path_that_exists_here_needs_no_marker(self):
        entry = {"implemented_by": [], "verified_by": ["scripts/python/build_spec_registry.py"]}
        self.assertEqual(reg.unresolved_evidence(entry), ([], []))

    def test_directory_shape_alone_never_exempts(self):
        """The regression this issue exists for: `tests/` and `.github/workflows/` exist HERE, so
        treating them as adopter-side silently excused paths this corpus can actually resolve."""
        for shaped in ("tests/unit/test_nothing.py", ".github/workflows/nope.yml", "src/x.py"):
            unresolved, backlog = reg.unresolved_evidence({"implemented_by": [shaped], "verified_by": []})
            self.assertEqual((unresolved, backlog), ([], [shaped]), shaped)


class Frontmatter(unittest.TestCase):
    def test_parses_scalars_lists_and_inline_lists(self):
        fm = reg.parse_frontmatter(FM.format(id="SPEC-AA-001", kind="spec", status="approved", issue=7))
        self.assertEqual(fm["id"], "SPEC-AA-001")
        self.assertEqual(fm["governing_adrs"], ["ADR-0001", "ADR-0002"])
        fm2 = reg.parse_frontmatter("---\nid: SPEC-BB-002\ngoverning_adrs: [ADR-0003, ADR-0004]\n---\n")
        self.assertEqual(fm2["governing_adrs"], ["ADR-0003", "ADR-0004"])

    def test_strips_trailing_comments(self):
        fm = reg.parse_frontmatter("---\nid: SPEC-CC-003\nstatus: draft # draft | approved\n---\n")
        self.assertEqual(fm["status"], "draft")

    def test_returns_none_without_frontmatter(self):
        self.assertIsNone(reg.parse_frontmatter("# no frontmatter\n"))

    def test_bundle_companions_are_not_specs(self):
        for name in ("plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md",
                     "README.md", "spec-template.md"):
            self.assertFalse(reg.is_spec_file(f"specs/features/X/{name}"), name)
        for sub in ("checklists", "contracts"):
            self.assertFalse(reg.is_spec_file(f"specs/features/X/{sub}/a.md"), sub)
        self.assertTrue(reg.is_spec_file("specs/features/X/spec.md"))


class Drift(unittest.TestCase):
    """The drift this script exists to catch, exercised against a scratch corpus."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "specs", "api"))
        os.makedirs(os.path.join(self.root, "docs", "governance"))
        self._write("specs/api/one.md", FM.format(id="SPEC-API-001", kind="spec", status="approved", issue=1))
        self.orig_root = reg.ROOT

    def tearDown(self):
        reg.ROOT = self.orig_root
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)

    def run_script(self, *args):
        r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                           cwd=self.root, timeout=60,
                           env=dict(os.environ, PYTHONPATH=os.path.join(HERE, "scripts", "python")))
        return r.returncode, r.stdout + r.stderr

    def _in_scratch(self, fn):
        reg.ROOT = self.root
        try:
            return fn()
        finally:
            reg.ROOT = self.orig_root

    def test_build_then_check_is_clean(self):
        def go():
            specs = reg.collect()
            open(os.path.join(self.root, reg.JSON_PATH), "w").write(reg.render_json(specs))
            open(os.path.join(self.root, reg.MD_PATH), "w").write(reg.render_md(specs))
            return specs
        specs = self._in_scratch(go)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0]["id"], "SPEC-API-001")

    def test_a_new_spec_makes_the_registry_stale(self):
        def go():
            before = reg.collect()
            open(os.path.join(self.root, reg.JSON_PATH), "w").write(reg.render_json(before))
            self._write("specs/api/two.md", FM.format(id="SPEC-API-002", kind="spec", status="draft", issue=2))
            after = reg.collect()
            return before, after
        before, after = self._in_scratch(go)
        self.assertEqual(len(before), 1)
        self.assertEqual(len(after), 2)
        self.assertNotEqual(reg.render_json(before), reg.render_json(after))

    def test_output_is_deterministic(self):
        def go():
            return reg.render_json(reg.collect()), reg.render_json(reg.collect())
        a, b = self._in_scratch(go)
        self.assertEqual(a, b)


class RealCorpus(unittest.TestCase):
    def test_registry_matches_disk(self):
        r = subprocess.run([sys.executable, SCRIPT, "--check", "--quiet"], capture_output=True,
                           text=True, cwd=HERE, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_every_spec_on_disk_is_registered(self):
        specs = reg.collect()
        data = json.load(open(os.path.join(HERE, reg.JSON_PATH)))
        self.assertEqual({s["path"] for s in specs}, {e["path"] for e in data["specs"]})
        self.assertEqual(data["count"], len(specs))

    def test_ids_are_well_formed(self):
        for s in reg.collect():
            self.assertRegex(s.get("id", ""), reg.ID_RE, s["path"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
