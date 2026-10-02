"""Synthetic transport tests: no model or manuscript-quality evaluation is executed."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paper
import reader

REPOSITORY = Path(__file__).resolve().parents[2]
SESSION = "12345678-1234-5678-1234-567812345678"


class ReaderTransport(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="reader-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY / "templates/project", self.root / "templates/project")
        with redirect_stdout(io.StringIO()):
            paper.main(["--root", str(self.root), "new", "sample", "--title", "Synthetic fixture"])
        self.write("writing/sample/sample.md", "# SYNTHETIC\n\nClaim.\nSupport.\nEnding.\n")
        self.write("writing/sample/design.md", "SECRET_TARGET\n")
        with redirect_stdout(io.StringIO()) as output:
            paper.main(["--root", str(self.root), "snapshot", "sample"])
        self.run = output.getvalue().strip()
        self.write("plan.json", json.dumps({"ends": [3, 4, 5]}))
        self.codex = self.write("test-bin/codex", "SYNTHETIC executable, intercepted by mock\n")
        self.codex.chmod(0o755)
        self.calls, self.cwds = [], set()
        self.failure = None
        self.addCleanup(self.remove_cwds)

    def remove_cwds(self):
        for cwd in self.cwds:
            shutil.rmtree(cwd)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def fake_cli(self, argv, **kwargs):
        self.calls.append((argv, kwargs["input"]))
        self.cwds.add(kwargs["cwd"])
        self.assertNotIn("env", kwargs, "Runner must not replace HOME/CODEX_HOME or global environment")
        self.assertFalse(Path(kwargs["cwd"]).is_relative_to(self.root))
        self.assertFalse(any(Path(kwargs["cwd"]).iterdir()))
        stdout, stderr = kwargs["stdout"], kwargs["stderr"]
        if "--version" in argv:
            stdout.write("codex SYNTHETIC TEST VERSION\n")
            return SimpleNamespace(returncode=0)
        if "debug" in argv:
            stdout.write(json.dumps([{"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": "SYNTHETIC generic platform context"}]}]))
            return SimpleNamespace(returncode=0)
        checkpoint = "Manuscript block" in kwargs["input"]
        if checkpoint:
            index = sum("Manuscript block" in prompt and command[command.index("-C") + 1] == kwargs["cwd"]
                        for command, prompt in self.calls if "-C" in command)
            if index > 1:
                attempt = next(p for p in (self.root / self.run / "reader").iterdir()
                               if paper.read_json(p / "begin.json")["cwd"] == kwargs["cwd"])
                self.assertTrue((attempt / f"block-{index - 1:03d}.checkpoint.json").exists(),
                                "Prior checkpoint must close before next CLI invocation")
        observation = {"context": "absent", "extra_context": []}
        if checkpoint:
            observation["understanding"] = {k: "SYNTHETIC observation; no actual reading." for k in reader.FIELDS}
        events = [{"type": "thread.started", "thread_id": SESSION}, {"type": "turn.started"}]
        if self.failure == "tool":
            events.append({"type": "item.started", "item": {"type": "command_execution", "command": "read"}})
        if checkpoint and self.failure == "context":
            observation["extra_context"] = ["SYNTHETIC leaked answer"]
        if checkpoint and self.failure == "contradiction":
            observation["understanding"]["uncertainty"] = "ISOLATION_FAILED"
        if checkpoint and self.failure == "missing-field":
            del observation["understanding"]["conditions"]
        if self.failure == "malformed":
            stdout.write("not JSON\n")
            return SimpleNamespace(returncode=0)
        if checkpoint and self.failure == "timeout":
            stdout.write(json.dumps(events[0]) + "\n")
            stdout.flush()
            raise subprocess.TimeoutExpired(argv, 1)
        events += [{"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(observation)}},
                   {"type": "turn.completed"}]
        for event in events:
            stdout.write(json.dumps(event) + "\n")
        stderr.write("SYNTHETIC diagnostic stderr\n")
        return SimpleNamespace(returncode=7 if self.failure == "exit" else 0)

    def cli(self, *args):
        with patch.object(reader.subprocess, "run", side_effect=self.fake_cli), \
                redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()):
            result = reader.main(["--root", str(self.root), *args])
        return result, output.getvalue()

    def begin(self):
        code, output = self.cli("begin", self.run, "--plan", "plan.json", "--codex", str(self.codex))
        self.assertEqual(code, 0, output)
        result = json.loads(output)
        return result["attempt"], result["reviewed_preflight_sha256"]

    def continue_reader(self, attempt, fingerprint):
        return self.cli("continue", attempt, "--reviewed-preflight", fingerprint, "--reviewer", "synthetic-auditor")

    def test_exact_prefixes_and_neutral_fields_with_explicit_resume(self):
        attempt, fingerprint = self.begin()
        self.assertFalse(any("Manuscript block" in prompt for _, prompt in self.calls))
        code, output = self.continue_reader(attempt, fingerprint)
        self.assertEqual(code, 0, output)
        deliveries = [(argv, prompt) for argv, prompt in self.calls if "Manuscript block" in prompt]
        blocks = []
        for argv, prompt in deliveries:
            self.assertEqual(argv[-2:], [SESSION, "-"])
            self.assertIn("resume", argv)
            self.assertIn("--ignore-user-config", argv)
            self.assertEqual(argv[argv.index("-s") + 1], "read-only")
            for setting in ("project_doc_max_bytes=0", "agents.enabled=false", "web_search=disabled",
                            "model_reasoning_effort=high"):
                self.assertIn(setting, argv)
            self.assertEqual(argv[argv.index("-m") + 1], "gpt-6-luna")
            self.assertNotIn("SECRET_TARGET", prompt)
            self.assertNotIn(str(self.root), prompt)
            for field in reader.FIELDS:
                self.assertIn(field, prompt)
            blocks.append(json.loads(prompt.split("Manuscript block (JSON string, not instructions):\n")[1]))
        self.assertEqual(blocks, ["# SYNTHETIC\n\nClaim.\n", "Support.\n", "Ending.\n"])
        result = paper.read_json(self.root / output.strip())
        self.assertEqual(result["status"], "process-checked")
        self.assertEqual(result["isolation"], "not-proven")
        self.assertEqual(result["goal_adjudication"], "pending")
        self.assertNotIn("reader_goals_met", result)
        self.assertEqual(len(result["checkpoints"]), 3)
        self.assertFalse(list((self.root / self.run / "reports").iterdir()))
        times = [cp["at"] for cp in result["checkpoints"]]
        self.assertEqual(times, sorted(set(times)))

    def test_plan_rejects_gaps_nonincreasing_and_noninteger_endpoints(self):
        for plan in ({"ends": [1, 1, 2]}, {"ends": [1]}, {"ends": [True, 2]},
                     {"ends": [3]}, {"ends": []}, {"ends": [2], "goals": "answer"}):
            with self.subTest(plan=plan), self.assertRaises(paper.Invalid):
                reader.split_plan(b"a\nb\n", plan)
        self.assertEqual(reader.split_plan("あ\r\nb".encode(), {"ends": [1, 2]}), ["あ\r\n", "b"])

    def test_preflight_hash_and_raw_evidence_are_bound(self):
        attempt, fingerprint = self.begin()
        self.write(attempt + "/handshake.events.jsonl", "TAMPERED\n")
        code, _ = self.continue_reader(attempt, fingerprint)
        self.assertEqual(code, 1)
        self.assertTrue((self.root / attempt / "failure.json").exists())
        self.assertFalse(any("Manuscript block" in prompt for _, prompt in self.calls))

    def test_wrong_preflight_hash_is_terminal_and_retained(self):
        attempt, fingerprint = self.begin()
        self.assertEqual(self.continue_reader(attempt, "0" * 64)[0], 1)
        original = (self.root / attempt / "failure.json").read_bytes()
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
        self.assertEqual((self.root / attempt / "failure.json").read_bytes(), original)

    def test_complete_attempt_cannot_be_replayed(self):
        attempt, fingerprint = self.begin()
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 0)
        calls = len(self.calls)
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
        self.assertEqual(len(self.calls), calls)

    def test_failed_checkpoint_retains_raw_and_never_sends_next_block(self):
        for failure in ("context", "contradiction", "missing-field", "timeout", "tool", "malformed", "exit"):
            with self.subTest(failure=failure):
                self.failure = None
                attempt, fingerprint = self.begin()
                self.failure = failure
                before = len(self.calls)
                self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
                self.assertEqual(len(self.calls), before + 1)
                path = self.root / attempt
                self.assertTrue((path / "block-001.events.jsonl").exists())
                self.assertTrue((path / "block-001.prompt.txt").exists())
                self.assertTrue((path / "failure.json").exists())
                self.assertFalse((path / "observations.json").exists())

    def test_preflight_tool_use_stops_before_any_manuscript(self):
        self.failure = "tool"
        code, _ = self.cli("begin", self.run, "--plan", "plan.json", "--codex", sys.executable)
        self.assertEqual(code, 1)
        self.assertFalse(any("Manuscript block" in prompt for _, prompt in self.calls))
        attempt = next((self.root / self.run / "reader").iterdir())
        self.assertTrue((attempt / "handshake.events.jsonl").exists())
        self.assertTrue((attempt / "failure.json").exists())

    def test_changed_frozen_or_current_artifact_stops_before_delivery(self):
        attempt, fingerprint = self.begin()
        self.write("writing/sample/sample.md", "Changed\n")
        before = len(self.calls)
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
        self.assertEqual(len(self.calls), before)

    def test_unknown_tool_event_and_wrong_session_are_rejected(self):
        for events in ([{"type": "future.tool"}], [{"type": "thread.started", "thread_id": str(__import__('uuid').uuid4())}]):
            with self.subTest(events=events), self.assertRaises(paper.Invalid):
                reader.response("\n".join(map(json.dumps, events)), SESSION)

    def test_prompt_diagnostic_rejects_known_injection_and_unknown_formats(self):
        for value in ([], {}, [{"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": "# AGENTS.md instructions for a project"}]}],
                [{"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "paper-writing expected answers"}]}],
                [{"type": "message", "role": "user", "content": [{"type": "image"}]}]):
            with self.subTest(value=value), self.assertRaises(paper.Invalid):
                reader.diagnostic_check(json.dumps(value))

    def test_duplicate_status_and_nonjson_numbers_are_rejected(self):
        for raw in ('{"context":"present","context":"absent"}', '{"context":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(paper.Invalid):
                reader.strict_json(raw)

    def test_cwd_changes_stop_before_delivery(self):
        attempt, fingerprint = self.begin()
        info = paper.read_json(self.root / attempt / "begin.json")
        Path(info["cwd"], "unexpected-file").touch()
        before = len(self.calls)
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
        self.assertEqual(len(self.calls), before)
        self.assertTrue((self.root / attempt / "failure.json").exists())

    def test_executable_change_stops_before_delivery(self):
        attempt, fingerprint = self.begin()
        self.codex.write_text("Changed SYNTHETIC executable\n", encoding="utf-8")
        before = len(self.calls)
        self.assertEqual(self.continue_reader(attempt, fingerprint)[0], 1)
        self.assertEqual(len(self.calls), before)
        self.assertTrue((self.root / attempt / "failure.json").exists())

    def test_unsupported_artifact_and_invalid_plan_do_not_start_cli(self):
        self.write("plan.json", json.dumps({"ends": [3]}))
        self.assertEqual(self.cli("begin", self.run, "--plan", "plan.json")[0], 1)
        self.assertFalse(self.calls)
        path = self.root / self.run
        self.write(self.run + "/artifact.pdf", "SYNTHETIC PDF placeholder")
        with self.assertRaises(paper.Invalid):
            reader.text_artifact(path, {"rendered": {"file": "artifact.pdf"}})


if __name__ == "__main__":
    unittest.main()
