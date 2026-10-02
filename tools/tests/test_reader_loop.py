"""Synthetic protocol tests. No native agents, human readers, or manuscript builds run."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import importlib.util

TOOL_DIR = Path(__file__).resolve().parents[1] / "blind-review"
SPEC = importlib.util.spec_from_file_location("review", TOOL_DIR / "review.py")
blind = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blind)
sys.modules["review"] = blind
SPEC = importlib.util.spec_from_file_location("reader_loop", TOOL_DIR / "reader_loop.py")
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


def contract():
    return {"schema_version": 1, "scope": "Introduction", "entry": "Beginning of the artifact",
            "goals": [{"id": "G1", "by": "End of Introduction", "outcome": "Explain the problem and why the construction is needed", "required": True}],
            "preserve": ["Preserve claims, uncertainty and citations"], "sources": ["paper.md"], "edit_targets": ["paper.md"],
            "mode": "edit", "max_rounds": 2, "max_repair_scale": "section"}


def report(*, failed=False, prefix=True):
    return {"schema_version": 1, "prefix_isolation": prefix,
            "checkpoints": [{"id": "C1", "location": "Introduction, paragraph 1", "summary": "The role is unclear" if failed else "The construction separates unequal thresholds",
                             "evidence": ["Paragraph 1: 'independent thresholds'"]}],
            "events": [{"id": "E1", "kind": "MISSING_PAYOFF", "location": "Paragraph 1", "reading": "Purpose missing", "evidence": "Paragraph 1 begins with machinery", "recovery": None}] if failed else [],
            "unread": []}


def assessment(*, failed=False, lanes=(1,), scale="paragraph"):
    return {"goals": [{"lane": n, "goal": "G1", "status": "missing" if failed else "recovered", "checkpoints": ["C1"], "reason": "Compare the checkpoint evidence with the frozen boundary"} for n in lanes],
            "events": [{"lane": n, "event": "E1", "disposition": "repair", "reason": "Purpose must precede machinery", "evidence": "Paragraph 1 / G1"} for n in lanes] if failed else [],
            "repair": {"scale": scale, "instructions": "Move the supported purpose before the machinery", "closure": ["Recover the purpose by C1"]} if failed else None}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "paper.md").write_text("Draft one.\n", encoding="utf-8")

    def start(self, c=None, readers=1):
        return loop.prepare(self.root, "paper.md", c or contract(), [f"Reader background {i}." for i in range(readers)], "fixture-revision")

    def fill(self, run, *, failed=False, prefix=True, execution="native", lanes=(1,), agent_prefix="fixture-thread"):
        for lane in lanes:
            loop.record(self.root, run, lane, report(failed=failed, prefix=prefix), f"{agent_prefix}-{lane}", execution)

    def finish(self, run, *, failed=False, lanes=(1,), scale="paragraph", **kw):
        self.fill(run, failed=failed, lanes=lanes, **kw)
        return loop.reconcile(self.root, run, assessment(failed=failed, lanes=lanes, scale=scale))

    def change(self):
        (self.root / "paper.md").write_text("Draft two: independent thresholds have a purpose.\n", encoding="utf-8")

    def test_complete_loop_fixed_baseline_fresh_reader(self):
        first = self.start()
        self.assertEqual(self.finish(first, failed=True)["next_action"], "REPAIR")
        self.change()
        second = loop.advance(self.root, first, "fixture-revision-2")
        result = self.finish(second, agent_prefix="another-fixture-thread")
        self.assertEqual(result["baseline"], first)
        self.assertEqual(result["round"], 2)
        self.assertEqual(result["next_action"], "HUMAN_READ")
        self.assertFalse(result["human_readability_certified"])
        with self.assertRaises(ValueError):
            loop.status(self.root, first)

    def test_packet_hides_contract_and_reports(self):
        run = self.start()
        packet = blind.packet(self.root, run, 1)
        message = json.loads(packet["message"])
        self.assertEqual(set(message), {"target_artifact", "reader_background"})
        self.assertNotIn("G1", packet["message"])
        self.assertEqual(packet["fork_turns"], "none")
        self.assertEqual(len(list(Path(message["target_artifact"]).parent.iterdir())), 1)

    def test_read_only_dependencies_are_not_write_targets(self):
        (self.root / "references.bib").write_text("Stable reference.")
        c = contract(); c["sources"].append("references.bib")
        run = self.start(c); self.finish(run, failed=True)
        message = json.loads(loop.role_packet(self.root, run, "writer")["message"])
        self.assertEqual(message["edit_targets"], ["paper.md"])
        self.assertIn("references.bib", message["sources"])
        self.change()
        (self.root / "references.bib").write_text("Concurrent reference change.")
        with self.assertRaisesRegex(ValueError, "read-only dependency"):
            loop.advance(self.root, run, "later")

    def test_write_target_authority_is_explicit(self):
        for mode, targets in [("read-only", ["paper.md"]), ("edit", []), ("edit", ["unbound.md"])]:
            c = contract(); c.update(mode=mode, edit_targets=targets)
            with self.assertRaises(ValueError):
                self.start(c)

    def test_original_helper_still_checks_live_source_by_default(self):
        run = self.start()
        self.change()
        with self.assertRaises(ValueError):
            blind.verify(self.root, run)
        blind.verify(self.root, run, check_source=False)

    def test_source_change_before_record(self):
        run = self.start()
        self.change()
        with self.assertRaises(ValueError):
            self.fill(run)

    def test_separate_source_change_even_when_pdf_unchanged(self):
        (self.root / "paper.pdf").write_bytes(b"%PDF-fixture")
        run = loop.prepare(self.root, "paper.pdf", contract(), ["Reader."], "fixture")
        self.change()
        with self.assertRaises(ValueError):
            self.fill(run)

    def test_missing_reader_is_not_clean_or_editor_packet(self):
        run = self.start(readers=2)
        self.fill(run)
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, assessment())
        with self.assertRaises(ValueError):
            loop.role_packet(self.root, run, "structure_reviewer")

    def test_all_reader_goal_pairs_required(self):
        run = self.start(readers=2)
        self.fill(run, lanes=(1, 2))
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, assessment())

    def test_majority_does_not_erase_dissent(self):
        run = self.start(readers=2)
        self.fill(run)
        loop.record(self.root, run, 2, report(failed=True), "different-fixture-thread", "native")
        a = assessment()
        a["goals"] += assessment(failed=True, lanes=(2,))["goals"]
        a["events"] = assessment(failed=True, lanes=(2,))["events"]
        a["repair"] = assessment(failed=True)["repair"]
        self.assertEqual(loop.reconcile(self.root, run, a)["reader_state"], "UNMET")

    def test_synthetic_local_and_nonprefix_never_certify(self):
        for execution, prefix in [("synthetic", True), ("local", True), ("native", False)]:
            with self.subTest(execution=execution, prefix=prefix):
                run = self.start()
                r = self.finish(run, execution=execution, prefix=prefix)
                self.assertEqual(r["next_action"], "LIMITED_REVIEW")
                self.assertEqual(r["evidence"], "LIMITED")

    def test_scope_failure_returns_to_design(self):
        run = self.start()
        r = self.finish(run, failed=True, scale="architecture")
        self.assertEqual(r["next_action"], "RETURN_TO_DESIGN")
        with self.assertRaises(ValueError):
            loop.role_packet(self.root, run, "writer")

    def test_read_only_never_produces_writer_packet(self):
        c = contract(); c["mode"] = "read-only"; c["edit_targets"] = []
        run = self.start(c)
        self.assertEqual(self.finish(run, failed=True)["next_action"], "REPORT_ONLY")
        with self.assertRaises(ValueError):
            loop.role_packet(self.root, run, "writer")

    def test_budget_exhaustion_is_not_success(self):
        c = contract(); c["max_rounds"] = 1
        run = self.start(c)
        self.assertEqual(self.finish(run, failed=True)["next_action"], "STOP_BUDGET")
        self.change()
        with self.assertRaises(ValueError):
            loop.advance(self.root, run, "later")

    def test_omitted_and_null_caps_continue_beyond_three_rounds(self):
        for omitted in (True, False):
            with self.subTest(omitted=omitted):
                c = contract()
                if omitted:
                    del c["max_rounds"]
                else:
                    c["max_rounds"] = None
                original = deepcopy(c)
                run = first = self.start(c)
                self.assertEqual(c, original, "normalization must not modify caller's contract")
                for number in range(1, 6):
                    result = self.finish(run, failed=number < 5,
                                         agent_prefix=f"fixture-{omitted}-round-{number}")
                    self.assertEqual(result["round"], number)
                    self.assertEqual(result["baseline"], first)
                    self.assertEqual(result["next_action"], "REPAIR" if number < 5 else "HUMAN_READ")
                    self.assertIsNone(loop.saved(self.root, run, "loop.json")["contract"]["max_rounds"])
                    if number < 5:
                        (self.root / "paper.md").write_text(f"Fixture {omitted}, revision {number + 1}.", encoding="utf-8")
                        run = loop.advance(self.root, run, f"revision-{number + 1}")
                self.assertEqual(len(loop.chain(self.root, run)), 5)
                self.assertFalse(result["human_readability_certified"])

    def test_explicit_cap_above_three_is_supported_and_stops_unfinished(self):
        c = contract(); c["max_rounds"] = 4
        run = self.start(c)
        for number in range(1, 5):
            result = self.finish(run, failed=True, agent_prefix=f"capped-fixture-{number}")
            self.assertEqual(result["next_action"], "REPAIR" if number < 4 else "STOP_BUDGET")
            self.assertEqual(result["reader_state"], "UNMET")
            if number < 4:
                (self.root / "paper.md").write_text(f"Capped fixture {number + 1}.", encoding="utf-8")
                run = loop.advance(self.root, run, f"revision-{number + 1}")
        with self.assertRaises(ValueError):
            loop.role_packet(self.root, run, "writer")

    def test_unlimited_ancestry_still_rejects_cycles(self):
        c = contract(); c["max_rounds"] = None
        run = self.start(c)
        value = loop.saved(self.root, run, "loop.json")
        value["parent"] = run
        path = self.root / loop.slot(run, "loop.json")
        path.write_bytes(blind.json_bytes({"payload": value, "sha256": blind.digest(blind.json_bytes(value))}))
        with self.assertRaisesRegex(ValueError, "ancestry"):
            loop.chain(self.root, run)

    def test_all_blind_roles_rejected_from_editor_handoff(self):
        run = self.start()
        for role in blind.READER_ROLES:
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "never send loop state"):
                loop.role_packet(self.root, run, role)

    def test_role_is_frozen_and_preserved_when_advancing(self):
        c = contract(); c["max_rounds"] = None
        first = loop.prepare(self.root, "paper.md", c, ["Reader."], "first",
                             role="undergraduate_reader")
        self.finish(first, failed=True)
        self.change()
        with self.assertRaisesRegex(ValueError, "reader role"):
            loop.prepare(self.root, "paper.md", c, ["Reader."], "next", parent=first,
                         role="blind_reader_sol")
        second = loop.advance(self.root, first, "second")
        self.assertEqual(blind.packet(self.root, second, 1)["agent_type"], "undergraduate_reader")

    def test_cyclic_artifact_revision_does_not_start_another_round(self):
        c = contract(); c["max_rounds"] = None
        baseline = (self.root / "paper.md").read_bytes()
        first = self.start(c)
        self.finish(first, failed=True)
        self.change()
        second = loop.advance(self.root, first, "second")
        self.finish(second, failed=True, agent_prefix="second-reader")
        (self.root / "paper.md").write_bytes(baseline)
        with self.assertRaisesRegex(ValueError, "repeats a prior round"):
            loop.advance(self.root, second, "reverted")
        self.assertEqual(len(list((self.root / blind.STORE).iterdir())), 2)

    def test_no_change_no_retry(self):
        run = self.start()
        self.finish(run, failed=True)
        with self.assertRaises(ValueError):
            loop.advance(self.root, run, "later")

    def test_unchanged_render_rejected_after_source_edit(self):
        (self.root / "paper.pdf").write_bytes(b"%PDF-fixture")
        run = loop.prepare(self.root, "paper.pdf", contract(), ["Reader."], "fixture")
        self.finish(run, failed=True)
        self.change()
        with self.assertRaises(ValueError):
            loop.advance(self.root, run, "later")

    def test_reused_thread_rejected_across_rounds(self):
        run = self.start(); self.finish(run, failed=True); self.change()
        second = loop.advance(self.root, run, "later")
        with self.assertRaises(ValueError):
            self.fill(second)

    def test_reused_thread_rejected_across_lanes(self):
        run = self.start(readers=2); self.fill(run)
        with self.assertRaises(ValueError):
            loop.record(self.root, run, 2, report(), "fixture-thread-1", "native")

    def test_execution_labels_cannot_reset_reader_freshness(self):
        for previous_execution in loop.EXECUTIONS:
            for execution in loop.EXECUTIONS:
                with self.subTest(previous=previous_execution, execution=execution):
                    first = self.start()
                    self.finish(first, failed=True, execution=previous_execution)
                    self.change()
                    second = loop.advance(self.root, first, "next revision")
                    with self.assertRaisesRegex(ValueError, "fresh reader"):
                        self.fill(second, execution=execution)
                    self.assertFalse((self.root / loop.slot(second, "observation-1.json")).exists())
                    (self.root / "paper.md").write_text("Draft one.\n", encoding="utf-8")

    def test_non_native_reader_ids_are_fresh_across_lanes(self):
        for execution in ("local", "synthetic"):
            with self.subTest(execution=execution):
                run = self.start(readers=2)
                self.fill(run, execution=execution)
                with self.assertRaisesRegex(ValueError, "fresh reader"):
                    loop.record(self.root, run, 2, report(), "fixture-thread-1", execution)

    def test_report_is_write_once(self):
        run = self.start(); self.fill(run, execution="synthetic")
        with self.assertRaises(FileExistsError):
            self.fill(run, execution="synthetic")

    def test_reconciliation_is_write_once(self):
        run = self.start(); self.finish(run)
        with self.assertRaises(FileExistsError):
            loop.reconcile(self.root, run, assessment())

    def test_tampered_report_and_snapshot(self):
        run = self.start(); self.fill(run)
        path = self.root / loop.slot(run, "observation-1.json")
        data = json.loads(path.read_text()); data["payload"]["report"]["prefix_isolation"] = False
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, assessment())
        other = self.start()
        (self.root / loop.slot(other, "reader-1/artifact.md")).write_text("Corrupted")
        with self.assertRaises(ValueError):
            self.fill(other)

    def test_mutated_manifest_detected_even_consistent_snapshot(self):
        run = self.start()
        p = self.root / loop.slot(run, "manifest.json")
        data = json.loads(p.read_text()); data["lanes"][0]["reader_background"] = "Changed profile."
        p.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.fill(run)

    def test_freeze_contract_between_rounds(self):
        run = self.start(); self.finish(run, failed=True); self.change()
        c = contract(); c["max_repair_scale"] = "architecture"
        with self.assertRaises(ValueError):
            loop.prepare(self.root, "paper.md", c, ["Reader background 0."], "later", parent=run)

    def test_disallow_new_target_mid_loop(self):
        run = self.start(); self.finish(run, failed=True); self.change()
        (self.root / "other.md").write_text("Other")
        with self.assertRaises(ValueError):
            loop.prepare(self.root, "other.md", contract(), ["Reader background 0."], "later", parent=run)

    def test_invalid_goal_and_evidence_variants(self):
        for change in (lambda a: a["goals"].clear(),
                       lambda a: a["goals"].append(deepcopy(a["goals"][0])),
                       lambda a: a["goals"][0].update(status="not_applicable"),
                       lambda a: a["goals"][0].update(checkpoints=["never-read"]),
                       lambda a: a["goals"][0].update(reason="")):
            run = self.start(); self.fill(run); a = assessment(); change(a)
            with self.assertRaises(ValueError):
                loop.reconcile(self.root, run, a)

    def test_minor_and_outside_scope_cannot_close_failure(self):
        for reason in ("minor", "out_of_scope", "tolerate_stumble"):
            run = self.start(); self.fill(run, failed=True); a = assessment(failed=True)
            a["events"][0]["disposition"] = reason
            with self.assertRaises(ValueError):
                loop.reconcile(self.root, run, a)

    def test_all_events_need_dispositions(self):
        run = self.start(); self.fill(run, failed=True); a = assessment(failed=True); a["events"] = []
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, a)

    def test_unsupported_repair_not_churn(self):
        run = self.start(); self.fill(run); a = assessment(); a["repair"] = assessment(failed=True)["repair"]
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, a)

    def test_missing_repair_for_unmet_goals(self):
        run = self.start(); self.fill(run, failed=True); a = assessment(failed=True); a["repair"] = None
        with self.assertRaises(ValueError):
            loop.reconcile(self.root, run, a)

    def test_no_report_or_empty_reconstruction(self):
        run = self.start()
        with self.assertRaises(ValueError):
            loop.status(self.root, run)
        r = report(); r["checkpoints"] = []
        with self.assertRaises(ValueError):
            loop.record(self.root, run, 1, r, "fixture", "synthetic")

    def test_checkpoint_evidence_objects_are_not_silently_converted(self):
        run = self.start()
        r = report()
        r["checkpoints"][0]["evidence"] = [{"text": "independent thresholds", "locator": "Paragraph 1"}]
        original = deepcopy(r)
        with self.assertRaises(ValueError):
            loop.record(self.root, run, 1, r, "fixture-reader", "synthetic")
        self.assertEqual(r, original)
        self.assertFalse((self.root / blind.STORE / run / "observation-1.json").exists())
        valid = report()
        loop.record(self.root, run, 1, valid, "fixture-reader", "synthetic")
        self.assertEqual(loop.saved(self.root, run, "observation-1.json")["report"], valid)

    def test_bad_contract(self):
        for key, value in (("max_rounds", True), ("max_rounds", 0), ("max_rounds", -1),
                           ("max_rounds", 2.5), ("max_rounds", "unlimited"),
                           ("goals", []), ("mode", "anything"), ("preserve", [])):
            c = contract(); c[key] = value
            with self.assertRaises(ValueError):
                self.start(c)

    def test_optional_goal_is_frozen_not_dropped(self):
        c = contract(); c["goals"].append({"id": "G2", "by": "End", "outcome": "Optional insight", "required": False})
        run = self.start(c); self.fill(run); a = assessment()
        a["goals"].append({"lane": 1, "goal": "G2", "status": "missing", "checkpoints": ["C1"], "reason": "Optional by initial design"})
        self.assertEqual(loop.reconcile(self.root, run, a)["next_action"], "HUMAN_READ")

    def test_paths_traversal_absolute_alias(self):
        for path in ("../paper.md", str(self.root / "paper.md")):
            c = contract(); c["sources"] = [path]
            with self.assertRaises(ValueError):
                self.start(c)
        try:
            (self.root / "alias.md").symlink_to(self.root / "paper.md")
        except OSError:
            self.skipTest("symlink unavailable")
        c = contract(); c["sources"] = ["alias.md"]
        with self.assertRaises(ValueError):
            self.start(c)

    def test_duplicate_json_keys(self):
        (self.root / "bad.json").write_text('{"x":1,"x":2}')
        with self.assertRaises(ValueError):
            loop.json_read(self.root, "bad.json")

    def test_prerequisite_observations_preserved_without_conversion(self):
        run = self.start()
        r = report(failed=True)
        r["events"][0].update(concept="the unfamiliar method",
                              bridge_kind="BLACK_BOX_INTERFACE",
                              minimal_bridge="State its inputs and output.")
        original = deepcopy(r)
        loop.record(self.root, run, 1, r, "fixture-undergraduate", "synthetic")
        self.assertEqual(loop.saved(self.root, run, "observation-1.json")["report"], original)
        self.assertEqual(r, original)
        self.assertEqual(loop.reconcile(self.root, run, assessment(failed=True))["reader_state"], "UNMET")
        for change in ({"bridge_kind": "INVENTED"}, {"concept": ""},
                       {"minimal_bridge": []}, {"unexpected_answer": "pass"}):
            invalid = deepcopy(r)
            invalid["events"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                loop.report_check(invalid)

    def test_report_input_paths_reject_symlinks_and_traversal(self):
        (self.root / "report.json").write_text(json.dumps(report()), encoding="utf-8")
        for path in ("../report.json", str(self.root / "report.json")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                loop.json_read(self.root, path)
        try:
            (self.root / "alias.json").symlink_to(self.root / "report.json")
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            loop.json_read(self.root, "alias.json")

    def test_editor_and_writer_packets_are_distinct(self):
        run = self.start(); self.fill(run, failed=True)
        editor = loop.role_packet(self.root, run, "structure_reviewer")
        self.assertEqual(editor["agent_type"], "structure_reviewer")
        self.assertIn("reports", json.loads(editor["message"]))
        loop.reconcile(self.root, run, assessment(failed=True))
        writer = loop.role_packet(self.root, run, "writer")
        self.assertIn("accepted_bundle", json.loads(writer["message"]))
        with self.assertRaises(ValueError):
            loop.role_packet(self.root, run, "blind_reader")

    def test_cli_failure_and_help(self):
        tool = Path(loop.__file__)
        p = subprocess.run([sys.executable, "-B", str(tool), "status", "not-a-run"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("ERROR:", p.stderr)
        p = subprocess.run([sys.executable, "-B", str(tool), "--help"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
