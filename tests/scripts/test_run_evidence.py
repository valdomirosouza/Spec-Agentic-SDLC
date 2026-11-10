#!/usr/bin/env python3
"""Tests for scripts/python/run_evidence.py, IPE manifests and the evidence ledger (ADR-0102). stdlib only."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "run_evidence.py")
SCHEMAS = os.path.join(HERE, "docs", "audit", "schema")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import run_evidence as ev  # noqa: E402

RUN = "o2c-20261031T230005Z"


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Evidence(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.ledger = os.path.join(self.d, "evidence", "ledger.jsonl")
        for name, text in (("a.csv", "invoice,amount\n1,10\n"), ("b.csv", "invoice,amount\n2,20\n"),
                           ("c.csv", "invoice,amount\n3,30\n")):
            write(os.path.join(self.d, name), text)
            ev.append(self.ledger, RUN, "extract", os.path.join(self.d, name))

    def tearDown(self):
        shutil.rmtree(self.d)

    def lines(self):
        with open(self.ledger) as f:
            return f.read().splitlines()

    def _w(self, lines):
        write(self.ledger, "\n".join(lines) + "\n")
        return self.ledger

    # The entries carry absolute paths, so root="/" checks each file where it was written.
    def test_an_intact_ledger_verifies(self):
        self.assertEqual(ev.ledger_problems(self.ledger, root="/"), [])
        first = json.loads(self.lines()[0])
        self.assertEqual((first["seq"], first["prev"]), (1, ev.ZERO))

    def test_each_line_chains_to_the_one_before(self):
        a, b = self.lines()[:2]
        self.assertEqual(json.loads(b)["prev"], hashlib.sha256(a.encode()).hexdigest())

    def test_a_deleted_line_breaks_the_chain(self):
        lines = self.lines()
        del lines[1]
        self.assertTrue(any("chain broken" in p for p in ev.ledger_problems(self._w(lines))))

    def test_an_edited_line_breaks_the_chain(self):
        lines = self.lines()
        e = json.loads(lines[0])
        e["sha256"] = "f" * 64
        lines[0] = json.dumps(e, sort_keys=True)
        self.assertTrue(any("chain broken" in p for p in ev.ledger_problems(self._w(lines))))

    def test_reordered_lines_break_the_chain(self):
        lines = self.lines()
        lines[1], lines[2] = lines[2], lines[1]
        self.assertTrue(any("chain broken" in p for p in ev.ledger_problems(self._w(lines))))

    def test_an_edited_last_line_is_caught_only_by_the_sealed_head(self):
        """No later link covers the last line. The head kept with the write-once copy does."""
        sealed = ev.head(self.ledger)
        lines = self.lines()
        e = json.loads(lines[-1])
        e["sha256"] = "f" * 64
        lines[-1] = json.dumps(e, sort_keys=True)
        self._w(lines)
        self.assertEqual(ev.ledger_problems(self.ledger), [])
        self.assertTrue(any("head" in p for p in ev.ledger_problems(self.ledger, expect_head=sealed)))

    def test_a_changed_copy_is_caught_against_its_hash(self):
        write(os.path.join(self.d, "b.csv"), "invoice,amount\n2,21\n")
        self.assertTrue(any("does not match" in p for p in ev.ledger_problems(self.ledger, root="/")))

    def test_a_missing_copy_is_caught(self):
        os.remove(os.path.join(self.d, "c.csv"))
        self.assertTrue(any("missing" in p for p in ev.ledger_problems(self.ledger, root="/")))

    def test_a_ledger_mixing_runs_is_caught(self):
        ev.append(self.ledger, "o2c-20261130T230005Z", "extract", os.path.join(self.d, "a.csv"))
        self.assertTrue(any("mixes runs" in p for p in ev.ledger_problems(self.ledger)))

    def test_verify_exits_nonzero_on_a_broken_chain_and_prints_the_head_when_intact(self):
        r = subprocess.run([sys.executable, SCRIPT, "verify", self.ledger], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn(f"head {ev.head(self.ledger)}", r.stdout)
        lines = self.lines()
        del lines[0]
        self._w(lines)
        r = subprocess.run([sys.executable, SCRIPT, "verify", self.ledger], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)


class Manifest(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        git = ["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        os.makedirs(os.path.join(self.repo, "sql"))
        write(os.path.join(self.repo, "sql", "q.sql"), "select invoice, amount from ar;\n")
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "q"], check=True)
        self.commit = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        self.out = os.path.join(self.repo, "out.csv")
        write(self.out, "invoice,amount\n1,10\n")

    def tearDown(self):
        shutil.rmtree(self.repo)

    def build(self, **out_kw):
        return ev.manifest(RUN, self.commit, "extract",
                           inputs=[ev.source("erp", repo=self.repo, commit=self.commit, query_path="sql/q.sql",
                                             parameters={"period": "2026-10"})],
                           outputs=[ev.output(self.out, rows=1, columns=["invoice", "amount"], **out_kw)])

    def test_the_query_hash_is_taken_at_the_commit_not_the_working_tree(self):
        committed = self.build()["inputs"][0]["query_sha256"]
        write(os.path.join(self.repo, "sql", "q.sql"), "select * from ar;\n")
        self.assertEqual(self.build()["inputs"][0]["query_sha256"], committed)

    def test_a_query_absent_from_the_commit_is_refused(self):
        with self.assertRaises(ValueError):
            ev.source("erp", repo=self.repo, commit=self.commit, query_path="sql/missing.sql")

    def test_a_good_manifest_round_trips_through_check(self):
        p = os.path.join(self.repo, "out.manifest.json")
        ev.write_manifest(p, self.build())
        r = subprocess.run([sys.executable, SCRIPT, "check-manifest", p], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_unknown_copy_kind_is_refused(self):
        """ADR-0102 §5: the copy is the file, a pseudonymised extract, or only the hash."""
        with self.assertRaises(ValueError):
            self.build(copy="raw")

    def test_a_data_value_in_the_manifest_is_caught(self):
        m = self.build()
        m["outputs"][0]["sample"] = ["1,10"]
        self.assertTrue(any("must have exactly" in p for p in ev.manifest_problems(m)))

    def test_nested_parameters_are_caught(self):
        m = self.build()
        m["inputs"][0]["parameters"] = {"customers": ["a", "b"]}
        self.assertTrue(any("flat object" in p for p in ev.manifest_problems(m)))

    def test_a_query_path_without_its_hash_is_caught(self):
        m = self.build()
        m["inputs"][0]["query_sha256"] = None
        self.assertTrue(any("query path" in p for p in ev.manifest_problems(m)))

    def test_the_column_hash_changes_with_the_column_order(self):
        self.assertNotEqual(ev.columns_sha256(["a", "b"]), ev.columns_sha256(["b", "a"]))


class AuditPackage(unittest.TestCase):
    """The builder in the template is code: run it, rather than trust it (ADR-0102 §4)."""
    TEMPLATE = os.path.join(HERE, "templates", "audit-package-template.md")

    def builder(self):
        with open(self.TEMPLATE, encoding="utf-8") as f:
            text = f.read()
        start = text.index("```sh\n#!/bin/sh\n# build-audit-package.sh") + len("```sh\n")
        return text[start:text.index("```", start)]

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.repo = os.path.join(self.d, "repo")
        git = ["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        os.makedirs(os.path.join(self.repo, "scripts", "python"))
        for script in (SCRIPT, os.path.join(HERE, "scripts", "python", "reconcile.py")):
            shutil.copy(script, os.path.join(self.repo, "scripts", "python"))
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "tooling"], check=True)
        commit = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        self.sealed = os.path.join(self.d, "store", RUN)
        os.makedirs(os.path.join(self.sealed, "copies"))
        os.makedirs(os.path.join(self.sealed, "manifests"))
        write(os.path.join(self.sealed, "copies", "ar.csv"), "invoice,amount\n1,10\n")
        cwd = os.getcwd()
        os.chdir(self.sealed)
        try:
            m = ev.manifest(RUN, commit, "extract", inputs=[ev.source("erp")],
                            outputs=[ev.output("copies/ar.csv", rows=1)])
            ev.write_manifest("manifests/extract.manifest.json", m)
            ev.append("ledger.jsonl", RUN, "extract", "copies/ar.csv")
            write("ledger.head", ev.head("ledger.jsonl") + "\n")
        finally:
            os.chdir(cwd)
        self.history = os.path.join(self.d, "history.jsonl")
        write(self.history, json.dumps({"run_id": RUN, "commit": commit, "status": "succeeded"},
                                       sort_keys=True) + "\n")
        self.script = os.path.join(self.d, "build.sh")
        write(self.script, self.builder())

    def tearDown(self):
        shutil.rmtree(self.d)

    def build(self, out):
        return subprocess.run(["sh", self.script, RUN, self.history, self.sealed, os.path.join(self.d, out)],
                              cwd=self.repo, capture_output=True, text=True)

    def sums(self, out):
        with open(os.path.join(self.d, out, RUN, "SHA256SUMS")) as f:
            return f.read()

    def test_the_package_is_built_from_the_commit_and_is_reproducible(self):
        r1, r2 = self.build("p1"), self.build("p2")
        self.assertEqual((r1.returncode, r2.returncode), (0, 0), r1.stderr + r2.stderr)
        self.assertEqual(self.sums("p1"), self.sums("p2"))
        self.assertIn("./code/scripts/python/run_evidence.py", self.sums("p1"))

    def test_a_tampered_copy_fails_the_build(self):
        write(os.path.join(self.sealed, "copies", "ar.csv"), "invoice,amount\n1,11\n")
        r = self.build("p1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not match", r.stdout)


class Schemas(unittest.TestCase):
    """Two descriptions of one record drift unless something compares them."""

    def load(self, name):
        with open(os.path.join(SCHEMAS, name)) as f:
            return json.load(f)

    def test_the_manifest_schema_and_the_script_name_the_same_fields(self):
        s = self.load("step-manifest.schema.json")
        self.assertEqual(s["required"], list(ev.MANIFEST_FIELDS))
        self.assertEqual(s["properties"]["inputs"]["items"]["required"], list(ev.INPUT_FIELDS))
        out = s["properties"]["outputs"]["items"]
        self.assertEqual(out["required"], list(ev.OUTPUT_FIELDS))
        self.assertEqual(out["properties"]["copy"]["enum"], list(ev.COPIES))

    def test_the_ledger_schema_and_the_script_name_the_same_fields(self):
        self.assertEqual(self.load("evidence-ledger.schema.json")["required"], list(ev.LEDGER_FIELDS))


if __name__ == "__main__":
    unittest.main(verbosity=1)
