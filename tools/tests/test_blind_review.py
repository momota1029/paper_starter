"""Synthetic command tests, not live model execution or semantic blindness tests."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("blind_review", Path(__file__).resolve().parents[1] / "blind-review/review.py")
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)
REPO = Path(__file__).resolve().parents[2]


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "author-secret-revision.md"
        self.target.write_text("# Synthetic paper\n\nFirst paragraph.\n", encoding="utf-8")

    def prepare(self, readers=None):
        return review.prepare(self.root, self.target.name, readers or ["A mathematician familiar with metric spaces."])

    def manifest_path(self, run):
        return review.run_directory(self.root, run) / "manifest.json"

    def mutate(self, run, key, value):
        p = self.manifest_path(run)
        data = json.loads(p.read_text(encoding="utf-8"))
        data[key] = value
        p.write_text(json.dumps(data), encoding="utf-8")

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(review, "ROOT", self.root), redirect_stdout(out), redirect_stderr(err):
            code = review.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")

    def test_prepare_copies_exact_bytes_and_keeps_original(self):
        before = self.target.read_bytes()
        run = self.prepare()
        manifest = review.verify(self.root, run)
        snapshot = review.run_directory(self.root, run) / "reader-1/artifact.md"
        self.assertEqual(snapshot.read_bytes(), before)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(manifest["state"], "prepared")
        self.assertEqual(manifest["sha256"], review.digest(before))

    def test_two_readers_get_distinct_paths_and_briefs(self):
        run = self.prepare(["A metric geometer.", "An analyst."])
        first, second = (review.packet(self.root, run, n) for n in (1, 2))
        a, b = json.loads(first["message"]), json.loads(second["message"])
        self.assertNotEqual(a["target_artifact"], b["target_artifact"])
        self.assertEqual(Path(a["target_artifact"]).read_bytes(), Path(b["target_artifact"]).read_bytes())
        self.assertEqual(a["reader_background"], "A metric geometer.")
        self.assertEqual(b["reader_background"], "An analyst.")
        self.assertNotIn("An analyst.", first["message"])

    def test_packet_has_only_role_and_two_content_inputs(self):
        run = self.prepare()
        packet = review.packet(self.root, run, 1)
        self.assertEqual(set(packet), {"agent_type", "fork_turns", "message"})
        self.assertEqual(packet["agent_type"], "blind_reader")
        self.assertEqual(packet["fork_turns"], "none")
        self.assertEqual(set(json.loads(packet["message"])), {"target_artifact", "reader_background"})
        for forbidden in (self.target.name, "manifest.json", "SKILL.md", "git diff", "Spec", "model"):
            self.assertNotIn(forbidden, packet["message"])

    def test_selected_reader_roles_keep_neutral_packet(self):
        for role in ("blind_reader", "blind_reader_sol", "undergraduate_reader"):
            with self.subTest(role=role):
                run = review.prepare(self.root, self.target.name, ["A new reader."], role)
                packet = review.packet(self.root, run, 1, role)
                self.assertEqual(packet["agent_type"], role)
                self.assertEqual(set(json.loads(packet["message"])),
                                 {"target_artifact", "reader_background"})
                code, out, err = self.cli("packet", run, "--role", role)
                self.assertEqual(code, 0, err)
                self.assertEqual(json.loads(out)["agent_type"], role)
                self.assertEqual(review.packet(self.root, run, 1)["agent_type"], role)
        for role in ("writer", "structure_reviewer", "invented", []):
            with self.subTest(role=role), self.assertRaises(ValueError):
                review.packet(self.root, run, 1, role)
        with self.assertRaisesRegex(ValueError, "frozen run"):
            review.packet(self.root, run, 1, "blind_reader")

    def test_prepare_role_validation_and_cli_freezing(self):
        for role in ("writer", "invented", [], None):
            with self.subTest(role=role), self.assertRaises(ValueError):
                review.prepare(self.root, self.target.name, ["A reader."], role)
        code, run, err = self.cli("prepare", self.target.name, "--reader", "A reader.",
                                  "--role", "undergraduate_reader")
        self.assertEqual(code, 0, err)
        code, out, err = self.cli("packet", run.strip())
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["agent_type"], "undergraduate_reader")

    def test_json_roundtrips_quoted_unicode_and_spaces(self):
        target = self.root / "paper with space.md"
        target.write_text("架空の本文", encoding="utf-8")
        brief = '距離空間の「基礎」と "measure" を知る数学者。'
        run = review.prepare(self.root, target.name, [brief])
        packet = review.packet(self.root, run, 1)
        self.assertEqual(json.loads(packet["message"])["reader_background"], brief)

    def test_each_prepare_has_a_new_run(self):
        a, b = self.prepare(), self.prepare()
        self.assertNotEqual(a, b)
        self.assertEqual(review.verify(self.root, a)["sha256"], review.verify(self.root, b)["sha256"])

    def test_source_edit_invalidates_verify_and_packet(self):
        run = self.prepare()
        self.target.write_text("new version")
        for operation in (lambda: review.verify(self.root, run), lambda: review.packet(self.root, run, 1)):
            with self.assertRaisesRegex(ValueError, "source changed"):
                operation()
        self.assertTrue(self.manifest_path(run).exists())

    def test_snapshot_edit_invalidates_run(self):
        run = self.prepare()
        snapshot = review.run_directory(self.root, run) / "reader-1/artifact.md"
        snapshot.write_text("changed")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            review.verify(self.root, run)

    def test_extra_reader_context_rejected(self):
        run = self.prepare()
        (review.run_directory(self.root, run) / "reader-1/report.md").write_text("prior report")
        with self.assertRaisesRegex(ValueError, "only its artifact"):
            review.verify(self.root, run)

    def test_report_outside_reader_input_not_transferred(self):
        run = self.prepare()
        (review.run_directory(self.root, run) / "report-1.md").write_text("SYNTHETIC_SECRET")
        self.assertNotIn("SYNTHETIC_SECRET", review.packet(self.root, run, 1)["message"])

    def test_reader_count_and_brief_validation(self):
        for readers in ([], ["x"] * 3, [""], ["x\ny"], ["x\ty"], ["x\u2028y"], ["a" * 601], [None]):
            with self.subTest(readers=readers), self.assertRaises(ValueError):
                review.prepare(self.root, self.target.name, readers)

    def test_path_traversal_and_absolute_paths_rejected(self):
        for target in ("../outside.md", str(self.target), "a/../../outside.md", ""):
            with self.subTest(target=target), self.assertRaises(ValueError):
                review.prepare(self.root, target, ["Reader."])

    def test_unsupported_tex_and_empty_text_rejected(self):
        for name, data in (("paper.tex", b"\\input{other}"), ("empty.md", b""), ("invalid.txt", b"\xff")):
            (self.root / name).write_bytes(data)
            with self.subTest(name=name), self.assertRaises(ValueError):
                review.prepare(self.root, name, ["Reader."])

    def test_pdf_header_check_and_copy(self):
        path = self.root / "test.PDF"
        path.write_bytes(b"%PDF-1.7\nsynthetic fixture, not a rendering test\n")
        run = review.prepare(self.root, path.name, ["Reader."])
        self.assertEqual(review.verify(self.root, run)["format"], ".pdf")
        path.write_bytes(b"not a PDF")
        with self.assertRaisesRegex(ValueError, "signature"):
            review.prepare(self.root, path.name, ["Reader."])

    def test_maximum_size_and_nonregular_file(self):
        with patch.object(review, "MAX_BYTES", 4), self.assertRaises(ValueError):
            self.prepare()
        folder = self.root / "directory.md"
        folder.mkdir()
        with self.assertRaises(ValueError):
            review.prepare(self.root, folder.name, ["Reader."])

    def test_symlink_source_rejected(self):
        link = self.root / "alias.md"
        self.symlink(link, self.target)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            review.prepare(self.root, link.name, ["Reader."])

    def test_symlink_store_ancestor_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.symlink(self.root / ".paper-local", outside, True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.prepare()
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_snapshot_rejected(self):
        run = self.prepare()
        snapshot = review.run_directory(self.root, run) / "reader-1/artifact.md"
        snapshot.unlink()
        self.symlink(snapshot, self.target)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            review.packet(self.root, run, 1)

    def test_invalid_run_and_lane_rejected(self):
        for run in ("../bad", "", "a" * 31, "A" * 32, None):
            with self.assertRaises(ValueError):
                review.run_directory(self.root, run)
        run = self.prepare()
        for lane in (0, 2, -1, True, "1"):
            with self.assertRaises(ValueError):
                review.packet(self.root, run, lane)

    def test_previous_snapshot_not_accepted_as_fresh_source(self):
        run = self.prepare()
        target = (review.STORE / run / "reader-1/artifact.md").as_posix()
        with self.assertRaisesRegex(ValueError, "previous"):
            review.prepare(self.root, target, ["Reader."])

    def test_malformed_manifest_never_reset_or_echoed(self):
        run = self.prepare()
        before = '{"SYNTHETIC_SECRET":'
        self.manifest_path(run).write_text(before)
        code, out, err = self.cli("verify", run)
        self.assertEqual(code, 1)
        self.assertNotIn("SYNTHETIC_SECRET", out + err)
        self.assertEqual(self.manifest_path(run).read_text(), before)

    def test_duplicate_json_keys_rejected(self):
        run = self.prepare()
        self.manifest_path(run).write_text('{"state": "prepared", "state": "prepared"}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            review.verify(self.root, run)

    def test_manifest_bad_types_rejected_without_crashing(self):
        for key, value in (("schema_version", True), ("format", []), ("sha256", []), ("size", True),
                           ("source", []), ("source", "../outside.md"), ("lanes", {}),
                           ("lanes", [None]), ("lanes", [{"id": True, "reader_background": "x"}]),
                           ("lanes", [{"id": 1, "reader_background": []}]), ("run", "wrong"),
                           ("state", "completed")):
            run = self.prepare()
            self.mutate(run, key, value)
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                review.verify(self.root, run)
        run = self.prepare()
        self.manifest_path(run).write_text("[]")
        with self.assertRaises(ValueError):
            review.verify(self.root, run)

    def test_missing_snapshot_and_incomplete_run_fail(self):
        run = self.prepare()
        (review.run_directory(self.root, run) / "reader-1/artifact.md").unlink()
        self.assertEqual(self.cli("verify", run)[0], 1)
        self.manifest_path(run).unlink()
        self.assertEqual(self.cli("verify", run)[0], 1)

    def test_source_change_during_preparation_retains_incomplete_run(self):
        original = review.read_bytes
        count = 0
        def changing(path):
            nonlocal count
            count += 1
            return original(path) if count == 1 else b"changed"
        with patch.object(review, "read_bytes", side_effect=changing), self.assertRaisesRegex(ValueError, "incomplete run"):
            self.prepare()
        runs = list((self.root / review.STORE).iterdir())
        self.assertEqual(len(runs), 1)
        self.assertFalse((runs[0] / "manifest.json").exists())

    def test_exclusive_creation_prevents_overwrite(self):
        with self.assertRaises(FileExistsError):
            review.new_file(self.target, b"replacement")
        self.assertIn("Synthetic paper", self.target.read_text())

    def test_windows_reparse_attribute_rejected(self):
        real_lstat = Path.lstat
        def lstat(path):
            if path.name == self.target.name:
                return SimpleNamespace(st_file_attributes=0x400, st_mode=real_lstat(path).st_mode)
            return real_lstat(path)
        with patch.object(Path, "lstat", lstat), self.assertRaisesRegex(ValueError, "junctions"):
            review.confined(self.root, self.target.name)

    def test_manifest_symlink_rejected(self):
        run = self.prepare()
        manifest = self.manifest_path(run)
        backup = self.root / "manifest-copy.json"
        backup.write_bytes(manifest.read_bytes())
        manifest.unlink()
        self.symlink(manifest, backup)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            review.verify(self.root, run)

    @unittest.skipUnless(shutil.which("git"), "Git not available")
    def test_runs_are_ignored_by_existing_git_policy(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        shutil.copyfile(REPO / ".gitignore", self.root / ".gitignore")
        run = self.prepare()
        directory = review.run_directory(self.root, run)
        for path in (directory / "manifest.json", directory / "reader-1/artifact.md"):
            result = subprocess.run(["git", "check-ignore", "--quiet", str(path)], cwd=self.root)
            self.assertEqual(result.returncode, 0)

    def test_cli_outputs_packet_and_truthful_limits(self):
        code, out, err = self.cli("prepare", self.target.name, "--reader", "Reader.")
        self.assertEqual(code, 0, err)
        run = out.strip()
        code, out, err = self.cli("packet", run)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["fork_turns"], "none")
        code, out, err = self.cli("verify", run)
        self.assertEqual(code, 0, err)
        self.assertIn("Not checked: model execution", out)



if __name__ == "__main__":
    unittest.main()
