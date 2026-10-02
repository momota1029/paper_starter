"""Real CLI regression checks; all review reports here are SYNTHETIC TEST DATA.

These tests check record handling, never manuscript quality or actual review.
Run: python3 -m unittest discover -s tools/tests -v
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest


REPOSITORY = Path(__file__).resolve().parents[2]
CLI = REPOSITORY / "tools" / "paper.py"
ROLES = ("correctness", "argument", "sources", "bibliography", "structure", "reader", "render", "human")
SYNTHETIC = "SYNTHETIC TEST DATA: no human or AI review was executed.\n"


class PaperCLI(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="paper-cli-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY / "templates" / "project", self.root / "templates" / "project")
        shutil.copytree(REPOSITORY / ".codex", self.root / ".codex")
        for name in ("AGENTS.md", "README.md", "index.md", "rules/INDEX.md", ".agents/skills/paper-writing/SKILL.md"):
            self.write(name, "# Synthetic fixture\n")
        self.write("rules/quality-contract.md", "# Synthetic quality contract rule\n")
        self.write("rules/INDEX.md", "[Quality contract](quality-contract.md)\n")

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def json(self, name, value):
        return self.write(name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def run_cli(self, *args, ok=True, contains=None, env=None):
        result = subprocess.run([sys.executable, str(CLI), "--root", str(self.root), *map(str, args)],
                                text=True, capture_output=True, env=env, timeout=15)
        message = f"{args!r}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        if ok:
            self.assertEqual(result.returncode, 0, message)
        else:
            self.assertNotEqual(result.returncode, 0, message)
            self.assertNotIn("Traceback", result.stderr, message)
        if contains:
            self.assertIn(contains, result.stdout + result.stderr, message)
        return result

    def new(self, slug="sample", **options):
        args = ["new", slug, "--title", options.pop("title", "Synthetic project")]
        for key, value in options.items():
            args += ["--" + key, value]
        return self.run_cli(*args)

    def meta(self):
        return tomllib.loads((self.root / "writing/sample/meta.toml").read_text(encoding="utf-8"))

    def set_meta(self, **updates):
        values = self.meta()
        values.update(updates)
        self.write("writing/sample/meta.toml", "\n".join(
            f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in values.items()) + "\n")

    def finish_draft(self):
        self.write("writing/sample/quality-contract.md", SYNTHETIC + "Scope: synthetic fixture only.\n")
        self.write("writing/sample/sample.md", "# Synthetic test manuscript\n\nA fixture for record checks only.\n")
        self.json("writing/sample/claims.json", {"claims": [{
            "id": "C1", "statement": "Synthetic claim, not a research finding.",
            "kind": "routine", "status": "verified", "location": "sample.md:3",
            "evidence": "SYNTHETIC TEST DATA; no substantive verification performed."
        }]})
        self.write("output/sample/sample.html", "<p>SYNTHETIC TEST DATA</p>\n")

    def snapshot(self, rendered=False, *extras):
        args = ["snapshot", "sample", *extras]
        if rendered:
            args += ["--artifact", "output/sample/sample.html"]
        return self.run_cli(*args).stdout.strip()

    def manifest(self, run):
        return json.loads((self.root / run / "manifest.json").read_text(encoding="utf-8"))

    def record(self, run, role, reviewer_id=None, **updates):
        reviewer = reviewer_id or ("synthetic-reader" if role == "reader" else "synthetic-" + role)
        evidence = "test-input/evidence.md"
        self.write(evidence, SYNTHETIC + "Scope: entire synthetic fixture. No actual review occurred.\n")
        report = {
            "run_id": self.manifest(run)["run_id"], "role": role,
            "reviewer_id": reviewer, "kind": "human" if role == "human" else "ai",
            "verdict": "pass", "independent": role not in {"human", "render"},
            "scope": "Entire SYNTHETIC TEST DATA fixture", "unread": [],
            "findings": [], "evidence": evidence,
        }
        if role == "reader":
            report.update(reader_goals_met=True, isolation="passed", checkpoints=[
                {"at": "2026-01-01T00:00:00+00:00", "location": "sample.md:1",
                 "observation": "SYNTHETIC checkpoint before second block."},
                {"at": "2026-01-01T00:00:01+00:00", "location": "sample.md:3",
                 "observation": "SYNTHETIC checkpoint after second block."},
            ])
        coverage_key = {"argument": "external_inputs", "sources": "attribution", "structure": "constraints"}.get(role)
        if coverage_key:
            report["coverage"] = {coverage_key: {
                "scope": "Entire synthetic fixture; not a real audit",
                "items": [], "none_reason": "SYNTHETIC TEST DATA: no applicable inputs in fixture."
            }}
        report.update(updates)
        path = self.json("test-input/report.json", report)
        return self.run_cli("record", run, path.relative_to(self.root))

    def all_reports(self, run, omit=(), **reader_options):
        for role in ROLES:
            if role not in omit:
                self.record(run, role, **(reader_options if role == "reader" else {}))

    def ready_fixture(self):
        self.new()
        self.finish_draft()
        return self.snapshot(True)

    def synthetic_receipt(self, run):
        """Record validator fixture, NOT an executed reader receipt."""
        folder = run + "/reader/synthetic"
        raw = self.write(folder + "/synthetic.txt", SYNTHETIC)
        observation = {"context": "absent", "extra_context": [], "understanding": {
            key: SYNTHETIC for key in ("scope", "conditions", "claim", "support", "mechanism",
                                      "limitations", "uncertainty", "confusion", "unread")}}
        manifest = self.manifest(run)
        artifact = (self.root / run / manifest["rendered"]["file"]).read_bytes()
        end = len(artifact.decode().splitlines())
        begun = self.json(folder + "/begin.json", {
            "manifest_sha256": hashlib.sha256((self.root / run / "manifest.json").read_bytes()).hexdigest(),
            "plan": {"ends": [end]}})
        observed = [{"at": "2026-01-01T00:00:00+00:00", "location": f"lines 1-{end}",
                     "block_sha256": hashlib.sha256(artifact).hexdigest(), "observation": observation}]
        checkpoint = self.json(folder + "/block-001.checkpoint.json", observed[0])
        events = self.write(folder + "/block-001.events.jsonl", "\n".join(json.dumps(e) for e in [
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(observation)}},
            {"type": "turn.completed"}]) + "\n")
        path = self.json(folder + "/observations.json", {
            "run_id": self.manifest(run)["run_id"], "reviewer_id": "synthetic-reader",
            "status": "process-checked", "checkpoints": observed,
            "artifact_sha256": self.manifest(run)["rendered"]["sha256"],
            "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw, checkpoint, events, begun)}})
        return {
            "reader_transport": "supplementary-cli-text",
            "reader_receipt": path.relative_to(self.root).as_posix(),
            "isolation_review": SYNTHETIC, "goal_adjudication": SYNTHETIC,
            "checkpoints": [{**cp, "observation": json.dumps(cp["observation"], ensure_ascii=False, indent=2) + "\n"}
                            for cp in observed]
        }

    def test_supplementary_receipt_integrity_not_understanding(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        self.all_reports(run, **options)
        self.run_cli("readiness", run, contains="NOT a certification")
        self.write(run + "/reader/synthetic/synthetic.txt", "changed evidence")
        self.run_cli("readiness", run, ok=False, contains="raw evidence changed")

    def test_supplementary_receipt_does_not_supply_goal_adjudication(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        options["goal_adjudication"] = ""
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="not goal adjudication")

    def test_supplementary_receipt_does_not_allow_rewritten_observation(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        options["checkpoints"][0]["observation"] = "An invented favorable observation"
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="differs from raw observation")

    def test_supplementary_receipt_rejects_changed_summary_before_record(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        receipt = json.loads((self.root / options["reader_receipt"]).read_text())
        receipt["checkpoints"][0]["observation"]["understanding"]["claim"] = "Invented favorable summary"
        self.json(options["reader_receipt"], receipt)
        options["checkpoints"][0]["observation"] = json.dumps(receipt["checkpoints"][0]["observation"], ensure_ascii=False, indent=2) + "\n"
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="summary differs from saved checkpoint")

    def test_supplementary_receipt_rejects_changed_checkpoint_but_original_events(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        receipt = json.loads((self.root / options["reader_receipt"]).read_text())
        cp = receipt["checkpoints"][0]
        cp["observation"]["understanding"]["claim"] = "Invented favorable checkpoint"
        name = run + "/reader/synthetic/block-001.checkpoint.json"
        path = self.json(name, cp)
        receipt["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.json(options["reader_receipt"], receipt)
        options["checkpoints"][0]["observation"] = json.dumps(cp["observation"], ensure_ascii=False, indent=2) + "\n"
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="checkpoint differs from raw events")

    def test_supplementary_receipt_rejects_extra_summary(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        receipt = json.loads((self.root / options["reader_receipt"]).read_text())
        receipt["checkpoints"] *= 2
        self.json(options["reader_receipt"], receipt)
        options["checkpoints"] *= 2
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="does not cover boundary plan")

    def test_supplementary_receipt_rejects_wrong_artifact(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        receipt = json.loads((self.root / options["reader_receipt"]).read_text())
        receipt["artifact_sha256"] = "0" * 64
        self.json(options["reader_receipt"], receipt)
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="artifact mismatch")

    def test_supplementary_receipt_preserves_duplicate_key_rejection(self):
        run = self.ready_fixture()
        options = self.synthetic_receipt(run)
        receipt = json.loads((self.root / options["reader_receipt"]).read_text())
        name = run + "/reader/synthetic/block-001.events.jsonl"
        original = (self.root / name).read_text()
        path = self.write(name, original.replace('"type": "turn.started"',
                         '"type": "tool.call", "type": "turn.started"'))
        receipt["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.json(options["reader_receipt"], receipt)
        self.all_reports(run, **options)
        self.run_cli("readiness", run, ok=False, contains="duplicate JSON field")

    def test_new_roundtrips_toml_and_tex_special_title(self):
        title = '研究 "quoted" \\ 50% & $value_1 # {x} ~ ^ <tag> | [label]'
        self.new(title=title, format="tex", profile="theory", language="ja")
        self.assertEqual(self.meta()["title"], title)
        self.assertEqual(self.meta()["profile"], "theory")
        tex = (self.root / "writing/sample/sample.tex").read_text(encoding="utf-8")
        for escaped in (r"\textbackslash{}", r"50\%", r"\&", r"\$value\_1", r"\#", r"\{x\}",
                        r"\textasciitilde{}", r"\textasciicircum{}"):
            self.assertIn(escaped, tex)
        self.run_cli("index", "--check")

    def test_index_escapes_markdown_link_title(self):
        self.new(title=r"A [x](https://invalid.example) | <b> & \ title")
        index = (self.root / "writing/index.md").read_text(encoding="utf-8")
        self.assertIn("&#124;", index)
        self.assertIn("&lt;b&gt;", index)
        self.assertIn("&amp;", index)
        self.assertNotIn("[x](https://invalid.example)", index,
                         "A title must not create nested Markdown links in the index.")
        self.assertIn("(sample/sample.md)", index)

    def test_new_refuses_overwrite(self):
        self.new()
        marker = self.write("writing/sample/sample.md", "User-owned work\n")
        original = marker.read_bytes()
        self.run_cli("new", "sample", "--title", "Replacement", ok=False, contains="refusing overwrite")
        self.assertEqual(marker.read_bytes(), original)

    def test_new_includes_unfinished_quality_contract(self):
        self.new()
        body = (self.root / "writing/sample/quality-contract.md").read_text()
        self.assertIn("TODO", body)

    def test_final_requires_positive_coverage_even_with_no_findings(self):
        run = self.ready_fixture()
        self.all_reports(run, omit=("argument",))
        self.record(run, "argument", coverage={})
        self.run_cli("readiness", run, ok=False, contains="missing positive coverage")

    def test_final_requires_external_input_application_location(self):
        run = self.ready_fixture()
        self.all_reports(run, omit=("argument",))
        self.record(run, "argument", coverage={"external_inputs": {
            "scope": "SYNTHETIC entire fixture", "none_reason": "", "items": [{
                "input": "SYNTHETIC external lemma", "definition": "section 1",
                "statement": "section 2", "source": "synthetic source section A"
            }]}})
        self.run_cli("readiness", run, ok=False, contains="missing application")

    def test_final_rejects_empty_coverage_without_none_reason(self):
        run = self.ready_fixture()
        self.all_reports(run, omit=("sources",))
        self.record(run, "sources", coverage={"attribution": {
            "scope": "SYNTHETIC entire fixture", "items": [], "none_reason": ""}})
        self.run_cli("readiness", run, ok=False, contains="grounded none_reason")

    def test_final_rejects_unfinished_quality_contract(self):
        self.new()
        self.finish_draft()
        self.write("writing/sample/quality-contract.md", "TODO: reader scope and inherited constraints\n")
        run = self.snapshot(True)
        self.all_reports(run)
        self.run_cli("readiness", run, ok=False, contains="unfinished quality contract")

    def test_index_detects_staleness_and_inbox(self):
        self.new()
        self.write("writing/sample/inbox/note.md", "Unprocessed input\n")
        self.run_cli("index", "--check", ok=False, contains="stale")
        self.run_cli("index")
        self.run_cli("index", "--check")
        self.assertIn("pending", (self.root / "writing/index.md").read_text())

    def test_invalid_new_arguments_leave_no_project(self):
        for slug in ("../escape", "/absolute", "Upper", "two--hyphens"):
            with self.subTest(slug=slug):
                self.run_cli("new", slug, "--title", "Invalid", ok=False)
        self.run_cli("new", "sample", "--title", "Invalid", "--profile", "unknown", ok=False)
        self.run_cli("new", "sample", "--title", "two\nlines", ok=False)
        self.assertFalse((self.root / "writing/sample").exists())

    def test_metadata_validation(self):
        self.new()
        original = (self.root / "writing/sample/meta.toml").read_text()
        for changes in ({"profile": "unknown"}, {"status": "certified"}, {"reader": ""},
                        {"inputs": "not-an-array"}, {"manuscript": "../../outside.md"},
                        {"inputs": ["../outside.md"]}, {"inputs": ["/tmp/outside.md"]}):
            with self.subTest(changes=changes):
                self.write("writing/sample/meta.toml", original)
                self.set_meta(**changes)
                self.run_cli("index", ok=False)
        self.write("writing/sample/meta.toml", "not valid TOML = [\n")
        self.run_cli("index", ok=False)

    def test_draft_check_does_not_claim_final_readiness(self):
        self.new()
        self.run_cli("check", contains="Semantic review not performed")
        run = self.snapshot()
        self.run_cli("readiness", run, ok=False, contains="no main claims")

    def test_agent_config_rejects_reviewer_write_access_and_readonly_writer(self):
        self.run_cli("check")
        for role, original_permission, invalid_permission in (
                ("blind_reader", "read-only", "workspace-write"),
                ("correctness_reviewer", "read-only", "danger-full-access"),
                ("writer", "workspace-write", "read-only")):
            with self.subTest(role=role):
                path = self.root / ".codex/agents" / (role + ".toml")
                original = path.read_text(encoding="utf-8")
                needle = f'sandbox_mode = "{original_permission}"'
                self.assertIn(needle, original)
                path.write_text(original.replace(needle, f'sandbox_mode = "{invalid_permission}"'), encoding="utf-8")
                self.run_cli("check", ok=False, contains="agent permission mismatch")
                path.write_text(original, encoding="utf-8")

    def test_agent_config_rejects_misdirected_registration(self):
        path = self.root / ".codex/config.toml"
        original = path.read_text(encoding="utf-8")
        for replacement in ("agents/writer.toml", "../../outside.toml", "agents/missing.toml"):
            with self.subTest(replacement=replacement):
                path.write_text(original.replace("agents/blind_reader.toml", replacement), encoding="utf-8")
                self.run_cli("check", ok=False)

    def test_agent_config_requires_shipped_reader_role(self):
        (self.root / ".codex/agents/blind_reader.toml").unlink()
        self.run_cli("check", ok=False, contains="missing configured agent roles: blind_reader")

    def test_agent_config_preserves_primary_model_and_effort_selection(self):
        path = self.root / ".codex/config.toml"
        original = path.read_text(encoding="utf-8")
        for setting in ('model = "synthetic-forbidden-primary"', 'model_reasoning_effort = "high"'):
            with self.subTest(setting=setting):
                path.write_text(setting + "\n" + original, encoding="utf-8")
                self.run_cli("check", ok=False, contains="preserve primary model selection")
        path.write_text(original, encoding="utf-8")
        self.run_cli("check")

    def test_final_rejects_pending_claim_and_unfinished_manuscript(self):
        self.new()
        self.finish_draft()
        path = self.root / "writing/sample/claims.json"
        claims = json.loads(path.read_text())
        claims["claims"][0]["status"] = "pending"
        self.json("writing/sample/claims.json", claims)
        self.run_cli("readiness", self.snapshot(True), ok=False, contains="unresolved claim")
        self.finish_draft()
        self.write("writing/sample/sample.md", "# Test\nTODO: unfinished\n")
        self.run_cli("readiness", self.snapshot(True), ok=False, contains="unfinished manuscript")

    def test_snapshot_is_historical_but_current_changes_are_stale(self):
        self.new()
        run = self.snapshot()
        self.run_cli("verify", run)
        self.write("writing/sample/sample.md", "Changed current manuscript\n")
        self.run_cli("verify", run, ok=False, contains="current inputs differ")
        self.run_cli("verify", run, "--frozen-only", contains="Frozen integrity OK")
        self.write(run + "/frozen/writing/sample/sample.md", "Tampered frozen manuscript\n")
        self.run_cli("verify", run, "--frozen-only", ok=False, contains="snapshot changed")

    def test_snapshot_detects_added_and_deleted_inputs(self):
        self.new()
        run = self.snapshot()
        added = self.write("writing/sample/addendum.md", "Additional dependency\n")
        self.run_cli("verify", run, ok=False, contains="current inputs differ")
        added.unlink()
        self.run_cli("verify", run)
        (self.root / "writing/sample/corpus.md").unlink()
        self.run_cli("verify", run, ok=False, contains="current inputs differ")
        self.run_cli("verify", run, "--frozen-only")

    def test_snapshot_tracks_external_evidence_and_bibliography(self):
        self.new()
        self.write("refs/source.txt", "Original evidence\n")
        self.write("index.bib", "% Original bibliography\n")
        self.set_meta(inputs=["refs/source.txt"])
        run = self.snapshot()
        for name in ("refs/source.txt", "index.bib"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                self.write(name, "Changed input\n")
                self.run_cli("verify", run, ok=False, contains="current inputs differ")
                path.write_bytes(original)
                self.run_cli("verify", run)

    def test_symlinked_project_and_inputs_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "writing").mkdir()
        link = self.root / "writing/sample"
        link.symlink_to(outside, target_is_directory=True)
        self.run_cli("new", "sample", "--title", "Unsafe", ok=False, contains="symlink")
        self.run_cli("index", ok=False, contains="symlink")
        link.unlink()
        self.new()
        (self.root / "writing/sample/alias.md").symlink_to(outside / "missing.md")
        self.run_cli("snapshot", "sample", ok=False, contains="symlink")

    def test_run_and_manifest_paths_cannot_escape(self):
        self.new()
        run = self.snapshot()
        self.run_cli("verify", "../escape", ok=False, contains="unsafe relative path")
        manifest = self.manifest(run)
        manuscript = manifest["manuscript"]
        sha = manifest["files"].pop(manuscript)
        manifest["manuscript"] = "../../outside.md"
        manifest["files"]["../../outside.md"] = sha
        self.json(run + "/manifest.json", manifest)
        self.run_cli("verify", run, "--frozen-only", ok=False, contains="unsafe relative path")

    def test_reader_packet_does_not_disclose_design_or_manifest(self):
        self.new()
        self.write("writing/sample/design.md", "SECRET_EXPECTED_ANSWER\n")
        run = self.snapshot()
        output = self.run_cli("packet", run, "--role", "reader").stdout
        packet = json.loads(output)
        self.assertEqual(set(packet), {"artifact", "reader", "procedure"})
        for secret in ("SECRET_EXPECTED_ANSWER", "design.md", "manifest.json", "contributors", "writer_id"):
            self.assertNotIn(secret, output)
        self.assertTrue(Path(packet["artifact"]).is_file())
        self.assertIn("before opening the next", packet["procedure"])
        specialist = json.loads(self.run_cli("packet", run, "--role", "sources").stdout)
        self.assertIn("frozen", specialist)

    def test_tex_reader_packet_requires_rendered_artifact(self):
        self.new(format="tex")
        self.run_cli("packet", self.snapshot(), "--role", "reader", ok=False, contains="render TeX first")

    def test_record_rejects_wrong_run_and_missing_evidence(self):
        run = self.ready_fixture()
        self.record(run, "correctness")
        report = json.loads((self.root / "test-input/report.json").read_text())
        report["run_id"] = "wrong-run"
        self.json("test-input/report.json", report)
        self.run_cli("record", run, "test-input/report.json", ok=False, contains="another run")
        report["run_id"] = self.manifest(run)["run_id"]
        report["evidence"] = "test-input/missing.md"
        self.json("test-input/report.json", report)
        self.run_cli("record", run, "test-input/report.json", ok=False, contains="missing actual review evidence")
        self.write("test-input/missing.md", " \n")
        self.run_cli("record", run, "test-input/report.json", ok=False, contains="missing actual review evidence")
        self.assertEqual(len(list((self.root / run / "reports").glob("*.json"))), 1)

    def test_self_review_is_recorded_but_never_counts_as_independent(self):
        run = self.ready_fixture()
        self.all_reports(run, omit=("correctness",))
        self.record(run, "correctness", reviewer_id="author", independent=True)
        self.run_cli("readiness", run, ok=False, contains="self review")

    def test_designer_contributor_cannot_self_certify(self):
        self.new()
        self.finish_draft()
        run = self.snapshot(True, "--contributor", "synthetic-designer")
        self.all_reports(run, omit=("structure",))
        self.record(run, "structure", reviewer_id="synthetic-designer")
        self.run_cli("readiness", run, ok=False, contains="self review")

    def test_readiness_requires_reports_and_human(self):
        run = self.ready_fixture()
        self.run_cli("readiness", run, ok=False, contains="missing required final review roles")
        self.all_reports(run, omit=("human",))
        self.run_cli("readiness", run, ok=False, contains="human")
        self.record(run, "human", kind="ai")
        self.run_cli("readiness", run, ok=False, contains="human read cannot be an AI report")

    def test_readiness_success_means_record_checks_only(self):
        run = self.ready_fixture()
        self.all_reports(run)
        output = self.run_cli("readiness", run, contains="Record checks passed").stdout
        self.assertIn("NOT a certification", output)
        for evidence in (self.root / run / "reports").glob("*.md"):
            self.assertIn(SYNTHETIC.strip(), evidence.read_text())

    def test_readiness_rejects_stale_inputs_after_pass(self):
        run = self.ready_fixture()
        self.all_reports(run)
        self.run_cli("readiness", run)
        self.write("writing/sample/design.md", "Changed design after review\n")
        self.run_cli("readiness", run, ok=False, contains="current inputs differ")

    def test_readiness_rejects_reused_reader(self):
        first = self.ready_fixture()
        self.record(first, "reader", reviewer_id="same-synthetic-reader")
        second = self.snapshot(True)
        self.all_reports(second, reviewer_id="same-synthetic-reader")
        self.run_cli("readiness", second, ok=False, contains="reader was used in an earlier run")

    def test_readiness_rejects_reader_specialist_overlap(self):
        run = self.ready_fixture()
        self.all_reports(run, reviewer_id="synthetic-correctness")
        self.run_cli("readiness", run, ok=False, contains="blind reader cannot double")

    def test_readiness_rejects_isolation_failure_and_absent_observations(self):
        self.new()
        self.finish_draft()
        for options, message in (({"isolation": "failed"}, "reader goals/isolation incomplete"),
                                 ({"reader_goals_met": False}, "reader goals/isolation incomplete"),
                                 ({"checkpoints": []}, "no forward-reading checkpoints"),
                                 ({"checkpoints": [{"at": "2026-01-01T00:00:00", "location": "1", "observation": "synthetic"}]},
                                  "timezone-aware times")):
            with self.subTest(options=options):
                run = self.snapshot(True)
                self.all_reports(run, reviewer_id="reader-" + Path(run).name, **options)
                self.run_cli("readiness", run, ok=False, contains=message)

    def test_reader_checkpoint_order_uses_instants_not_timestamp_strings(self):
        self.new()
        self.finish_draft()
        pairs = (
            ("2026-01-01T09:00:00+09:00", "2026-01-01T00:00:01+00:00", True),
            ("2026-01-01T00:00:01+00:00", "2026-01-01T09:00:00+09:00", False),
            ("2026-01-01T00:00:00+00:00", "2026-01-01T09:00:00+09:00", False),
        )
        for first, second, passes in pairs:
            with self.subTest(first=first, second=second):
                run = self.snapshot(True)
                checkpoints = [{"at": stamp, "location": str(i), "observation": "SYNTHETIC checkpoint"}
                               for i, stamp in enumerate((first, second), 1)]
                self.all_reports(run, reviewer_id="reader-" + Path(run).name, checkpoints=checkpoints)
                self.run_cli("readiness", run, ok=passes,
                             contains="Record checks passed" if passes else "timezone-aware times")

    def test_malformed_checkpoint_returns_a_diagnostic_without_traceback(self):
        run = self.ready_fixture()
        self.all_reports(run, checkpoints=["not a checkpoint object"])
        self.run_cli("readiness", run, ok=False)

    def test_readiness_rejects_unclosed_findings_unread_scope_and_failed_reports(self):
        self.new()
        self.finish_draft()
        for options, message in (({"findings": [{"status": "open", "reason": "synthetic blocking defect"}]}, "unclosed finding"),
                                 ({"unread": ["conclusion"]}, "unread scope"),
                                 ({"verdict": "fail"}, "nonpassing report remains")):
            with self.subTest(options=options):
                run = self.snapshot(True)
                self.all_reports(run, omit=("correctness",), reviewer_id="reader-" + Path(run).name)
                self.record(run, "correctness", **options)
                self.run_cli("readiness", run, ok=False, contains=message)

    def test_readiness_detects_changed_report_evidence(self):
        run = self.ready_fixture()
        self.all_reports(run)
        evidence = next((self.root / run / "reports").glob("*.md"))
        evidence.write_text("Tampered SYNTHETIC report evidence\n")
        self.run_cli("readiness", run, ok=False, contains="review evidence changed")

    def test_current_and_frozen_artifacts_are_checked(self):
        run = self.ready_fixture()
        artifact = self.root / "output/sample/sample.html"
        original = artifact.read_bytes()
        artifact.write_text("Changed rendered output\n")
        self.run_cli("verify", run, ok=False, contains="current artifact changed")
        self.run_cli("verify", run, "--frozen-only")
        artifact.write_bytes(original)
        self.write(run + "/artifact.html", "Changed frozen artifact\n")
        self.run_cli("verify", run, "--frozen-only", ok=False, contains="frozen artifact changed")

    def test_build_failure_preserves_previous_artifact_and_receipt(self):
        self.new()
        output = self.write("output/sample/sample.html", "Previous successful output\n")
        receipt = self.write("output/sample/build.json", '{"previous": true}\n')
        executable = self.write("test-bin/pandoc", f"#!{sys.executable}\n"
                                "import pathlib, sys\n"
                                "pathlib.Path(sys.argv[sys.argv.index('--output') + 1]).write_text('partial output')\n"
                                "sys.exit(7)\n")
        executable.chmod(0o755)
        env = dict(os.environ, PATH=str(executable.parent) + os.pathsep + os.environ.get("PATH", ""))
        self.run_cli("build", "sample", ok=False, env=env)
        self.assertEqual(output.read_text(), "Previous successful output\n")
        self.assertEqual(receipt.read_text(), '{"previous": true}\n')
        self.assertFalse((output.parent / "archive").exists())

    def test_nested_manuscript_build_uses_project_relative_path_and_archives_previous(self):
        self.new()
        self.write("writing/sample/chapters/main.md", "SYNTHETIC nested manuscript\n")
        self.set_meta(manuscript="chapters/main.md")
        previous = self.write("output/sample/sample.html", "Previous successful output\n")
        executable = self.write("test-bin/pandoc", f"#!{sys.executable}\n"
                                "import pathlib, sys\n"
                                "body = pathlib.Path(sys.argv[1]).read_text()\n"
                                "pathlib.Path(sys.argv[sys.argv.index('--output') + 1]).write_text(body)\n")
        executable.chmod(0o755)
        env = dict(os.environ, PATH=str(executable.parent) + os.pathsep + os.environ.get("PATH", ""))
        self.run_cli("build", "sample", env=env, contains="visual inspection pending")
        self.assertEqual(previous.read_text(), "SYNTHETIC nested manuscript\n")
        archived = list((previous.parent / "archive").glob("*sample.html"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_text(), "Previous successful output\n")
        receipt = json.loads((previous.parent / "build.json").read_text())
        self.assertEqual(receipt["command"][1], "chapters/main.md")
        self.assertEqual(receipt["visual_inspection"], "pending")


if __name__ == "__main__":
    unittest.main()
