"""Deterministic local tests using synthetic facts; no model or network calls."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("interview_session", Path(__file__).resolve().parents[1] / "application-interview" / "session.py")
assert SPEC and SPEC.loader
session = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(session)
REPO = Path(__file__).resolve().parents[2]


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def init(self, kind="cv"):
        return session.initialize(self.root, "sample", kind)[0]

    def save(self, state):
        path = session.safe_path(self.root, "sample", "session.json")
        path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def resolved(self, kind="cv"):
        state = session.new_state("sample", kind)
        state["requirements"].update(status="verified", source="fixture:form:section-1", checked_at="2026-09-26")
        field = state["fields"][0]
        field.update(required=True, status="confirmed", value="Synthetic example", sources=["fixture:answer-1"])
        return state

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(session, "ROOT", self.root), redirect_stdout(out), redirect_stderr(err):
            result = session.main(list(args))
        return result, out.getvalue(), err.getvalue()

    def test_all_kinds_start_provisional(self):
        for kind in session.KINDS:
            with self.subTest(kind=kind):
                state = session.new_state("sample", kind)
                self.assertEqual(session.validate(state), [])
                self.assertEqual(state["requirements"]["status"], "unverified")
                self.assertTrue(all(not f["required"] and not f["value"] for f in state["fields"]))
                self.assertTrue(session.validate(state, complete=True))

    def test_initialization_creates_utf8_state_draft_and_guard(self):
        directory = self.init()
        self.assertEqual(session.load(self.root, "sample")["kind"], "cv")
        self.assertIn("未完成", (directory / "draft.md").read_text(encoding="utf-8"))
        self.assertEqual((directory.parent / ".gitignore").read_text(), "*\n")

    def test_resume_preserves_both_files_byte_for_byte(self):
        directory = self.init()
        state = session.load(self.root, "sample")
        state["phase"] = "paused"
        state["round"] = 3
        state["fields"][0].update(status="confirmed", value="架空の氏名", sources=["fixture:answer"])
        self.save(state)
        (directory / "draft.md").write_text("保存された本文\n", encoding="utf-8")
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        self.assertFalse(session.initialize(self.root, "sample", "cv")[1])
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_kind_collision_does_not_reset(self):
        directory = self.init()
        before = (directory / "session.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "different kind"):
            session.initialize(self.root, "sample", "grant")
        self.assertEqual((directory / "session.json").read_bytes(), before)

    def test_missing_draft_preserves_checkpoint(self):
        directory = self.init()
        before = (directory / "session.json").read_bytes()
        (directory / "draft.md").unlink()
        with self.assertRaisesRegex(ValueError, "draft.md is missing"):
            session.initialize(self.root, "sample", "cv")
        self.assertEqual((directory / "session.json").read_bytes(), before)
        self.assertFalse((directory / "draft.md").exists())
        self.assertEqual(self.cli("check", "sample")[0], 1)

    def test_changed_or_missing_guard_blocks_reads_without_exposing_values(self):
        directory = self.init()
        state = self.resolved()
        state["fields"][0]["value"] = "SYNTHETIC_SECRET"
        self.save(state)
        guard = directory.parent / ".gitignore"
        for content in ("!*.json\n", None):
            if content is None:
                guard.unlink()
            else:
                guard.write_text(content)
            code, out, err = self.cli("status", "sample")
            self.assertEqual(code, 1)
            self.assertIn("ignore guard", err)
            self.assertNotIn("SYNTHETIC_SECRET", out + err)

    def test_explicit_root_cli_from_unrelated_working_directory(self):
        script = REPO / "tools/application-interview/session.py"
        result = subprocess.run(
            [sys.executable, "-B", str(script), "--root", str(self.root),
             "init", "portable", "--kind", "other"],
            cwd=self.root, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(session.load(self.root, "portable")["kind"], "other")

    def test_invalid_slugs(self):
        for slug in ("../escape", "/absolute", "a/b", "a\\b", "", "日本語", "a--b", "CON", "con", "aux", "com1", "lpt9", "a" * 65, None):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                session.validate_slug(slug)
        session.validate_slug("cv-2026")
        session.validate_slug("a")

    def test_invalid_kind_and_filename(self):
        with self.assertRaises(ValueError):
            session.new_state("sample", "paper")
        with self.assertRaises(ValueError):
            session.safe_path(self.root, "sample", "../outside")

    def test_unexpected_ignore_guard_blocks_creation(self):
        local = self.root / session.LOCAL
        local.mkdir()
        (local / ".gitignore").write_text("!*.json\n")
        with self.assertRaisesRegex(ValueError, "ignore guard"):
            self.init()
        self.assertFalse((local / "sample").exists())

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")

    def test_symlink_local_directory_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.symlink(self.root / session.LOCAL, outside, True)
        with self.assertRaises(ValueError):
            self.init()
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_session_directory_rejected(self):
        local = self.root / session.LOCAL
        local.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        self.symlink(local / "sample", outside, True)
        with self.assertRaises(ValueError):
            self.init()
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_state_and_draft_rejected(self):
        directory = self.init()
        outside = self.root / "outside.txt"
        outside.write_text("untouched")
        for name in ("session.json", "draft.md"):
            path = directory / name
            before = path.read_bytes()
            path.unlink()
            self.symlink(path, outside)
            with self.assertRaises(ValueError):
                session.safe_path(self.root, "sample", name)
            path.unlink()
            path.write_bytes(before)
        self.assertEqual(outside.read_text(), "untouched")

    def test_symlink_ignore_guard_rejected(self):
        local = self.root / session.LOCAL
        local.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("*\n")
        self.symlink(local / ".gitignore", outside)
        with self.assertRaisesRegex(ValueError, "ignore guard"):
            self.init()
        self.assertFalse((local / "sample").exists())

    def test_malformed_json_not_echoed_or_reset(self):
        directory = self.init()
        broken = '{"private": "SYNTHETIC_SECRET",'
        (directory / "session.json").write_text(broken)
        code, out, err = self.cli("init", "sample", "--kind", "cv")
        self.assertEqual(code, 1)
        self.assertNotIn("SYNTHETIC_SECRET", out + err)
        self.assertEqual((directory / "session.json").read_text(), broken)

    def test_duplicate_json_keys_rejected(self):
        directory = self.init()
        (directory / "session.json").write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            session.load(self.root, "sample")

    def test_bom_supported(self):
        directory = self.init()
        path = directory / "session.json"
        path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8-sig")
        self.assertEqual(session.load(self.root, "sample")["slug"], "sample")

    def test_directory_slug_mismatch_rejected(self):
        self.init()
        state = session.new_state("another", "cv")
        self.save(state)
        with self.assertRaisesRegex(ValueError, "does not match"):
            session.load(self.root, "sample")

    def test_malformed_structure_reports_errors_without_crashing(self):
        for value in (None, [], "wrong", 1):
            self.assertTrue(session.validate(value))
        for key, value in (("schema_version", True), ("round", True), ("round", -1), ("phase", []), ("kind", []), ("target", None), ("requirements", []), ("fields", []), ("fields", [None])):
            state = session.new_state("sample", "cv")
            state[key] = value
            with self.subTest(key=key, value=value):
                self.assertTrue(session.validate(state, True))

    def test_field_types_and_duplicate_ids(self):
        for key, value in (("id", []), ("status", []), ("value", None), ("required", 1), ("sources", "bad"), ("sources", [""])):
            state = self.resolved()
            state["fields"][0][key] = value
            with self.subTest(key=key):
                self.assertTrue(session.validate(state, True))
        state = self.resolved()
        state["fields"][1]["id"] = state["fields"][0]["id"]
        self.assertTrue(any("duplicate id" in e for e in session.validate(state)))

    def test_confirmed_requires_value_and_source(self):
        state = self.resolved()
        state["fields"][0]["sources"] = []
        self.assertTrue(any("supporting source" in e for e in session.validate(state)))
        state["fields"][0]["value"] = " "
        self.assertTrue(any("needs a value" in e for e in session.validate(state)))

    def test_missing_cannot_hide_candidate_value(self):
        state = session.new_state("sample", "cv")
        state["fields"][0]["value"] = "unverified idea"
        self.assertTrue(any("candidate" in e for e in session.validate(state)))

    def test_not_applicable_requires_reason_and_decision(self):
        state = self.resolved()
        state["fields"][0].update(status="not_applicable", value="", note="User says not applicable")
        self.assertEqual(session.validate(state, True), [])
        state["fields"][0]["note"] = ""
        self.assertTrue(session.validate(state))
        state["fields"][0].update(note="Reason", sources=[])
        self.assertTrue(session.validate(state))

    def test_unresolved_required_fields_block_completion(self):
        for status in ("missing", "candidate", "conflict", "deferred"):
            state = self.resolved()
            state["fields"][0].update(status=status, value="", sources=[])
            self.assertTrue(any("required field unresolved" in e for e in session.validate(state, True)))

    def test_optional_unconfirmed_content_blocks_completion(self):
        for status in ("candidate", "deferred", "conflict"):
            state = self.resolved()
            state["fields"][1].update(status=status, value="Unverified text")
            self.assertEqual(session.validate(state), [])
            self.assertTrue(session.validate(state, True))

    def test_explicitly_empty_optional_deferral_is_allowed(self):
        state = self.resolved()
        state["fields"][1].update(status="deferred", value="", note="Omitted from this draft")
        self.assertEqual(session.validate(state, True), [])

    def test_grant_completion_needs_actual_requirements_record(self):
        state = self.resolved("grant")
        self.assertEqual(session.validate(state, True), [])
        for status in ("unverified", "not_applicable"):
            state["requirements"].update(status=status, note="Not a verified official form")
            self.assertTrue(session.validate(state, True))

    def test_verified_requirements_need_source_and_date(self):
        for key in ("source", "checked_at"):
            state = self.resolved()
            state["requirements"][key] = ""
            self.assertTrue(session.validate(state))
        state = self.resolved()
        state["requirements"]["status"] = []
        self.assertTrue(session.validate(state, True))

    def test_verified_requirements_reject_invalid_calendar_date(self):
        for value in ("2026-02-30", "20260926", "yesterday", "2026-09-26T00:00:00"):
            state = self.resolved()
            state["requirements"]["checked_at"] = value
            with self.subTest(value=value):
                self.assertTrue(session.validate(state))

    def test_free_form_cv_requirements_can_be_not_applicable(self):
        state = self.resolved()
        state["requirements"].update(status="not_applicable", note="Author chose a free-form CV")
        self.assertEqual(session.validate(state, True), [])

    def test_question_limit_ids_and_pending_completion(self):
        state = self.resolved()
        question = {"field_ids": ["name"], "question": "Example question?"}
        state["pending_questions"] = [question]
        self.assertEqual(session.validate(state), [])
        self.assertTrue(session.validate(state, True))
        state["pending_questions"] = [question] * 4
        self.assertTrue(session.validate(state))
        for keys in (["unknown"], [None], "name"):
            state["pending_questions"] = [{"field_ids": keys, "question": "Example?"}]
            self.assertTrue(session.validate(state))
        state["pending_questions"] = [{"field_ids": [], "question": "General purpose?"}]
        self.assertEqual(session.validate(state), [])

    def test_status_does_not_print_values_notes_or_questions(self):
        self.init()
        state = self.resolved()
        state["fields"][0]["value"] = "SYNTHETIC_SECRET"
        state["notes"] = "SYNTHETIC_SECRET"
        state["pending_questions"] = [{"field_ids": ["name"], "question": "SYNTHETIC_SECRET?"}]
        self.save(state)
        code, out, err = self.cli("status", "sample")
        self.assertEqual(code, 0)
        self.assertIn("Pending questions: 1", out)
        self.assertNotIn("SYNTHETIC_SECRET", out + err)

    def test_cli_exit_codes_and_limited_claims(self):
        self.assertEqual(self.cli("init", "sample", "--kind", "cv")[0], 0)
        self.assertEqual(self.cli("check", "sample")[0], 0)
        self.assertEqual(self.cli("check", "sample", "--complete")[0], 1)
        self.save(self.resolved())
        code, out, err = self.cli("check", "sample", "--complete")
        self.assertEqual(code, 0)
        self.assertIn("Not checked: truth", out)
        self.assertEqual(self.cli("status", "missing")[0], 1)

    def test_existing_file_never_clobbered(self):
        path = self.root / "example"
        path.write_text("original")
        with self.assertRaises(FileExistsError):
            session.write_new(path, "replacement")
        self.assertEqual(path.read_text(), "original")

    @unittest.skipUnless(shutil.which("git"), "Git not available")
    def test_personal_outputs_ignored_by_git(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        shutil.copyfile(REPO / ".gitignore", self.root / ".gitignore")
        directory = self.init()
        (directory / "export.docx").write_bytes(b"synthetic placeholder")
        for filename in ("session.json", "draft.md", "export.docx"):
            result = subprocess.run(["git", "check-ignore", "--quiet", str(directory / filename)], cwd=self.root)
            self.assertEqual(result.returncode, 0)


class RegistrationTests(unittest.TestCase):
    def test_roles_have_explicit_read_only_luna_settings(self):
        for name in ("application_interviewer", "application_reviewer"):
            role = tomllib.loads((REPO / ".codex/agents" / (name + ".toml")).read_text(encoding="utf-8"))
            self.assertEqual(role["name"], name)
            self.assertEqual(role["sandbox_mode"], "read-only")
            self.assertEqual(role["model"], "gpt-6-luna")
            self.assertEqual(role["model_reasoning_effort"], "high")
            self.assertTrue(role["developer_instructions"].strip())


if __name__ == "__main__":
    unittest.main()
