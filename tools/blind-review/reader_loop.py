#!/usr/bin/env python3
"""Record reader-state feedback around native reviews; never run a model or edit prose."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

import review as blind

SCALES = ("sentence", "paragraph", "section", "architecture")
EVENTS = {"STUMBLE", "BACKTRACK", "LOST_THREAD", "WRONG_MODEL", "MISSING_PAYOFF"}
BRIDGE_KINDS = {"WORKING_MODEL", "TOY_EXAMPLE", "OPERATIONAL_DEFINITION",
                "BLACK_BOX_INTERFACE", "PURPOSE_BEFORE_NOTATION", "DEPENDENCY_BRIDGE"}
RECOVERY = {"recovered", "partial", "missing", "misread"}
EXECUTIONS = {"native", "local", "synthetic"}
REJECTIONS = {"textual_counterevidence", "allowed_background", "contract_allows_deferral"}
LIMIT = 1024 * 1024


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text(value: Any, label: str) -> str:
    need(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def fields(value: Any, keys: str) -> None:
    need(isinstance(value, dict) and set(value) == set(keys.split()), f"expected fields: {keys}")


def strings(value: Any, label: str, *, empty: bool = False) -> list[str]:
    need(isinstance(value, list) and (empty or bool(value)), f"{label} must be a list")
    for item in value:
        text(item, label)
    need(len(value) == len(set(value)), f"duplicate {label}")
    return value


def identifier(value: Any) -> str:
    need(isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value) is not None,
         "invalid stable ID")
    return value


def json_read(root: Path, path: str | Path) -> Any:
    source = blind.confined(root, path)
    need(source.stat().st_size <= LIMIT, "JSON input exceeds 1 MiB")
    return json.loads(blind.read_bytes(source).decode("utf-8"), object_pairs_hook=blind.unique_keys)


def slot(run: str, name: str) -> Path:
    return blind.STORE / run / name


def save(root: Path, run: str, name: str, payload: Any) -> None:
    # Seals detect accidental changes, not a malicious actor who can rewrite both fields.
    data = {"payload": payload, "sha256": blind.digest(blind.json_bytes(payload))}
    path = blind.confined(root, slot(run, name))
    encoded = blind.json_bytes(data)
    need(len(encoded) <= LIMIT, "record exceeds 1 MiB")
    blind.new_file(path, encoded)


def saved(root: Path, run: str, name: str) -> Any:
    value = json_read(root, slot(run, name))
    fields(value, "payload sha256")
    need(blind.digest(blind.json_bytes(value["payload"])) == value["sha256"], "record seal mismatch")
    return value["payload"]


def contract_check(value: Any) -> dict[str, Any]:
    need(isinstance(value, dict), "contract must be an object")
    value = dict(value)
    value.setdefault("max_rounds", None)
    fields(value, "schema_version scope entry goals preserve sources edit_targets mode max_rounds max_repair_scale")
    need(type(value["schema_version"]) is int and value["schema_version"] == 1, "unsupported contract version")
    for key in ("scope", "entry"):
        text(value[key], key)
    strings(value["preserve"], "preserve constraints")
    strings(value["sources"], "source paths")
    strings(value["edit_targets"], "edit targets", empty=True)
    need(set(value["edit_targets"]) <= set(value["sources"]), "edit targets must be included in bound sources")
    need(value["mode"] in ("edit", "read-only"), "invalid authorization mode")
    need(bool(value["edit_targets"]) == (value["mode"] == "edit"), "read-only has no edit targets; editing needs explicit targets")
    need(value["max_rounds"] is None or (type(value["max_rounds"]) is int and value["max_rounds"] >= 1),
         "round cap must be null or a positive integer")
    need(value["max_repair_scale"] in SCALES, "invalid authorized repair scale")
    need(isinstance(value["goals"], list) and 1 <= len(value["goals"]) <= 20, "use 1..20 scoped goals")
    ids = []
    for goal in value["goals"]:
        fields(goal, "id by outcome required")
        ids.append(identifier(goal["id"]))
        text(goal["by"], "checkpoint boundary")
        text(goal["outcome"], "reader outcome")
        need(type(goal["required"]) is bool, "required must be boolean")
    need(len(ids) == len(set(ids)), "duplicate goal ID")
    need(any(g["required"] for g in value["goals"]), "at least one goal must be required")
    return value


def source_hashes(root: Path, paths: list[str]) -> dict[str, str]:
    result = {}
    for path in paths:
        source = blind.confined(root, path)
        canonical = source.relative_to(root.resolve()).as_posix()
        need(path == canonical, "source paths must be canonical repository-relative paths")
        need(not source.is_relative_to(root.resolve() / ".git"), "Git internals are not manuscript sources")
        need(not source.is_relative_to(root.resolve() / blind.STORE), "snapshots are not manuscript sources")
        result[path] = blind.digest(blind.read_bytes(source))
    return result


def chain(root: Path, run: str, *, current: bool = True) -> list[tuple[dict, dict]]:
    result = []
    seen = set()
    while run is not None:
        need(isinstance(run, str) and run not in seen, "invalid loop ancestry")
        seen.add(run)
        manifest = blind.verify(root, run, check_source=current and not result)
        state = saved(root, run, "loop.json")
        fields(state, "schema_version run round parent baseline contract manifest_sha256 sources revision")
        need(type(state["schema_version"]) is int and state["schema_version"] == 1, "unsupported loop version")
        need(state["run"] == run, "loop/run mismatch")
        contract_check(state["contract"])
        cap = state["contract"].get("max_rounds")
        need(type(state["round"]) is int and state["round"] >= 1 and
             (cap is None or state["round"] <= cap), "invalid round")
        need(state["manifest_sha256"] == blind.digest(blind.json_bytes(manifest)), "manifest changed after binding")
        text(state["revision"], "revision")
        need(isinstance(state["sources"], dict) and set(state["sources"]) == set(state["contract"]["sources"]), "source set changed")
        for path, sha in state["sources"].items():
            blind.confined(root, path)
            need(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha) is not None, "invalid source digest")
        if current and not result:
            need(source_hashes(root, state["contract"]["sources"]) == state["sources"], "source changed since this review was prepared")
        result.append((state, manifest))
        run = state["parent"]
    base = result[-1][0]["run"]
    need(result[-1][0]["round"] == 1, "missing initial round")
    for index, (state, manifest) in enumerate(result):
        need(state["baseline"] == base, "original baseline changed")
        need(state["round"] == len(result) - index, "round sequence mismatch")
        need(state["contract"] == result[-1][0]["contract"], "contract changed between rounds")
        need(manifest["source"] == result[-1][1]["source"] and manifest["lanes"] == result[-1][1]["lanes"], "target or reader backgrounds changed")
        need(manifest["reader_role"] == result[-1][1]["reader_role"], "reader role changed")
    need(len({manifest["sha256"] for _, manifest in result}) == len(result),
         "artifact repeated in loop ancestry; return to design")
    return result


def prepare(root: Path, target: str, contract: dict, readers: list[str], revision: str,
            parent: str | None = None, role: str = "blind_reader") -> str:
    contract = contract_check(contract)
    blind.reader_role(role)
    text(revision, "revision")
    sources = source_hashes(root, contract["sources"])
    previous = None
    if parent is not None:
        history = chain(root, parent, current=False)
        previous = history[0]
        decision = status(root, parent, current=False)
        need(decision["next_action"] == "REPAIR", "previous round does not authorize another repair/review")
        need(contract == previous[0]["contract"], "cannot weaken the frozen contract")
        need(target == previous[1]["source"], "cannot change the target mid-loop")
        need(readers == [x["reader_background"] for x in previous[1]["lanes"]], "cannot change the reader profile mid-loop")
        need(role == previous[1]["reader_role"], "cannot change the reader role mid-loop")
        changed = {path for path in sources if sources[path] != previous[0]["sources"][path]}
        need(bool(changed), "no source change; do not spend another reader round")
        need(changed <= set(contract["edit_targets"]), "a read-only dependency changed; return to design rather than expanding write scope")
        need(blind.digest(blind.read_bytes(blind.confined(root, target))) != previous[1]["sha256"], "artifact unchanged; rebuild or verify the repaired artifact first")
        need(blind.digest(blind.read_bytes(blind.confined(root, target))) not in
             {manifest["sha256"] for _, manifest in history}, "artifact repeats a prior round; return to design")
    run = blind.prepare(root, target, readers, role)
    manifest = blind.verify(root, run)
    need(source_hashes(root, contract["sources"]) == sources, f"source changed during prepare; incomplete loop: {run}")
    state = {"schema_version": 1, "run": run,
             "round": previous[0]["round"] + 1 if previous else 1,
             "parent": parent, "baseline": previous[0]["baseline"] if previous else run,
             "contract": contract, "manifest_sha256": blind.digest(blind.json_bytes(manifest)),
             "sources": sources, "revision": revision}
    save(root, run, "loop.json", state)
    return run


def report_check(report: Any) -> None:
    fields(report, "schema_version prefix_isolation checkpoints events unread")
    need(type(report["schema_version"]) is int and report["schema_version"] == 1, "unsupported report version")
    need(type(report["prefix_isolation"]) is bool, "prefix_isolation must be boolean")
    strings(report["unread"], "unread scope", empty=True)
    need(isinstance(report["checkpoints"], list) and bool(report["checkpoints"]), "missing reader reconstruction")
    ids = []
    for point in report["checkpoints"]:
        fields(point, "id location summary evidence")
        ids.append(identifier(point["id"]))
        text(point["location"], "checkpoint location")
        text(point["summary"], "reader reconstruction")
        strings(point["evidence"], "quoted/location evidence")
    need(len(ids) == len(set(ids)), "duplicate checkpoint ID")
    need(isinstance(report["events"], list), "events must be a list")
    ids = []
    for event in report["events"]:
        need(isinstance(event, dict), "event must be an object")
        optional = {"concept", "bridge_kind", "minimal_bridge"}
        fields({key: value for key, value in event.items() if key not in optional},
               "id kind location reading evidence recovery")
        for key in optional & event.keys():
            text(event[key], key)
        if "bridge_kind" in event:
            need(event["bridge_kind"] in BRIDGE_KINDS, "unknown prerequisite bridge kind")
        ids.append(identifier(event["id"]))
        need(event["kind"] in EVENTS, "unknown reading event")
        for key in ("location", "reading", "evidence"):
            text(event[key], key)
        if event["recovery"] is not None:
            text(event["recovery"], "later recovery")
    need(len(ids) == len(set(ids)), "duplicate event ID")


def receipts(root: Path, history: list[tuple[dict, dict]], *, complete: bool) -> dict[int, dict]:
    current_reports = {}
    threads = set()
    for index, (state, manifest) in enumerate(history):
        for lane in manifest["lanes"]:
            name = f"observation-{lane['id']}.json"
            path = blind.confined(root, slot(state["run"], name))
            if not path.exists():
                need(index == 0 and not complete, "missing reader report")
                continue
            receipt = saved(root, state["run"], name)
            fields(receipt, "run lane artifact_sha256 execution agent_id report")
            need(receipt["run"] == state["run"] and type(receipt["lane"]) is int and receipt["lane"] == lane["id"], "report run/lane mismatch")
            need(receipt["artifact_sha256"] == manifest["sha256"], "report belongs to another artifact")
            need(receipt["execution"] in EXECUTIONS, "invalid execution provenance")
            text(receipt["agent_id"], "observed agent ID")
            need(receipt["agent_id"] not in threads, "fresh reader required; thread was reused")
            threads.add(receipt["agent_id"])
            report_check(receipt["report"])
            if index == 0:
                current_reports[lane["id"]] = receipt
    return current_reports


def record(root: Path, run: str, lane: int, report: dict, agent_id: str, execution: str) -> None:
    history = chain(root, run)
    manifest = history[0][1]
    need(type(lane) is int and 1 <= lane <= len(manifest["lanes"]), "reader lane does not exist")
    need(execution in EXECUTIONS, "invalid execution provenance")
    text(agent_id, "observed agent ID")
    report_check(report)
    receipts(root, history, complete=False)
    destination = blind.confined(root, slot(run, f"observation-{lane}.json"))
    if destination.exists():
        raise FileExistsError("reader report already exists; reports are write-once")
    for state, item in history:
        for old_lane in item["lanes"]:
            path = blind.confined(root, slot(state["run"], f"observation-{old_lane['id']}.json"))
            if path.exists():
                previous = saved(root, state["run"], path.name)
                need(previous["agent_id"] != agent_id, "fresh reader required; thread was reused")
    save(root, run, f"observation-{lane}.json", {"run": run, "lane": lane,
         "artifact_sha256": manifest["sha256"], "execution": execution, "agent_id": agent_id, "report": report})


def assess(contract: dict, reports: dict[int, dict], value: Any) -> bool:
    """Validate complete evidence coverage; semantic adjudication belongs to editor/primary."""
    fields(value, "goals events repair")
    need(isinstance(value["goals"], list) and isinstance(value["events"], list), "assessment lists required")
    goals = {g["id"]: g for g in contract["goals"]}
    expected = {(lane, goal) for lane in reports for goal in goals}
    seen = set()
    unmet = False
    for item in value["goals"]:
        fields(item, "lane goal status checkpoints reason")
        need(type(item["lane"]) is int and isinstance(item["goal"], str), "invalid goal key")
        key = (item["lane"], item["goal"])
        need(key in expected and key not in seen, "unknown or duplicate lane/goal")
        seen.add(key)
        need(item["status"] in RECOVERY, "unknown recovery status; goals cannot be dropped after reading")
        refs = strings(item["checkpoints"], "checkpoint references")
        valid = {p["id"] for p in reports[item["lane"]]["report"]["checkpoints"]}
        need(set(refs) <= valid, "assessment cites nonexistent checkpoints")
        text(item["reason"], "recovery evidence")
        unmet |= goals[item["goal"]]["required"] and item["status"] != "recovered"
    need(seen == expected, "every goal needs evidence from every assigned reader")
    expected_events = {(lane, e["id"]): e for lane, r in reports.items() for e in r["report"]["events"]}
    seen = set()
    for item in value["events"]:
        fields(item, "lane event disposition reason evidence")
        need(type(item["lane"]) is int and isinstance(item["event"], str), "invalid event key")
        key = (item["lane"], item["event"])
        need(key in expected_events and key not in seen, "unknown or duplicate reading event")
        seen.add(key)
        disposition = item["disposition"]
        need(disposition in REJECTIONS | {"repair", "defer", "tolerate_stumble"}, "invalid event disposition; minor/out-of-scope is not closure")
        text(item["reason"], "event disposition reason")
        text(item["evidence"], "event counterevidence or closure evidence")
        if disposition == "tolerate_stumble":
            need(expected_events[key]["kind"] == "STUMBLE", "only a local STUMBLE can be tolerated")
        unmet |= disposition in {"repair", "defer"}
    need(seen == set(expected_events), "every reading event needs an explicit disposition")
    if unmet:
        repair = value["repair"]
        fields(repair, "scale instructions closure")
        need(repair["scale"] in SCALES, "invalid repair scale")
        text(repair["instructions"], "batched repair specification")
        strings(repair["closure"], "observable closure conditions")
    else:
        need(value["repair"] is None, "no repair is needed; preserve the baseline rather than churn")
    return unmet


def reconcile(root: Path, run: str, assessment: dict) -> dict:
    history = chain(root, run)
    reports = receipts(root, history, complete=True)
    assess(history[0][0]["contract"], reports, assessment)
    save(root, run, "reconciliation.json", assessment)
    return status(root, run)


def status(root: Path, run: str, *, current: bool = True) -> dict:
    history = chain(root, run, current=current)
    state, manifest = history[0]
    reports = receipts(root, history, complete=True)
    assessment = saved(root, run, "reconciliation.json")
    unmet = assess(state["contract"], reports, assessment)
    limited = any(r["execution"] != "native" or not r["report"]["prefix_isolation"] for r in reports.values())
    if not unmet:
        action = "LIMITED_REVIEW" if limited else "HUMAN_READ"
    elif state["contract"]["mode"] == "read-only":
        action = "REPORT_ONLY"
    elif SCALES.index(assessment["repair"]["scale"]) > SCALES.index(state["contract"]["max_repair_scale"]):
        action = "RETURN_TO_DESIGN"
    elif state["contract"].get("max_rounds") is not None and state["round"] >= state["contract"]["max_rounds"]:
        action = "STOP_BUDGET"
    else:
        action = "REPAIR"
    return {"run": run, "round": state["round"], "baseline": state["baseline"],
            "scope": state["contract"]["scope"], "entry": state["contract"]["entry"],
            "unread_by_lane": {str(n): r["report"]["unread"] for n, r in reports.items()},
            "artifact_sha256": manifest["sha256"], "reader_state": "UNMET" if unmet else "RECOVERED_IN_REPORTS",
            "evidence": "LIMITED" if limited else "NATIVE_REPORTED_NOT_AUTHENTICATED",
            "next_action": action, "human_readability_certified": False,
            "limits": "Evidence coverage and input integrity only; no model execution, prefix enforcement, semantic grading, build equivalence, or disciplinary certification."}


def role_packet(root: Path, run: str, role: str) -> dict:
    history = chain(root, run)
    state, manifest = history[0]
    if role in blind.READER_ROLES:
        raise ValueError("use review.py packet; never send loop state to a blind reader")
    receipts(root, history, complete=True)
    base = chain(root, state["baseline"], current=False)[0][1]
    message = {"target_artifact": str(blind.confined(root, slot(run, f"reader-1/artifact{manifest['format']}"))),
               "fixed_baseline": str(blind.confined(root, slot(state["baseline"], f"reader-1/artifact{base['format']}"))),
               "contract": str(blind.confined(root, slot(run, "loop.json"))),
               "sources": state["contract"]["sources"],
               "edit_targets": state["contract"]["edit_targets"],
               "protocol": "tools/blind-review/READER_LOOP.md"}
    if role == "structure_reviewer":
        message["reports"] = [str(blind.confined(root, slot(run, f"observation-{lane['id']}.json"))) for lane in manifest["lanes"]]
        message["assignment"] = "Reconcile expected and observed reader states using the schema. Propose one smallest sufficient repair and its scale; do not draft prose or certify your own design. Primary adjudicates."
    elif role == "writer":
        need(status(root, run)["next_action"] == "REPAIR", "repair is not authorized by the current scope, evidence, or budget")
        message["accepted_bundle"] = str(blind.confined(root, slot(run, "reconciliation.json")))
        message["assignment"] = "Implement only the primary-adopted batched reader repair within edit_targets and frozen constraints; other sources are read-only dependencies. Smallest sufficient repair, not smallest diff. No model or Git operations; primary owns the one build and fresh review."
    else:
        raise ValueError("unsupported role")
    return {"agent_type": role, "fork_turns": "none", "message": json.dumps(message, ensure_ascii=False)}


def advance(root: Path, run: str, revision: str) -> str:
    state, manifest = chain(root, run, current=False)[0]
    return prepare(root, manifest["source"], state["contract"],
                   [x["reader_background"] for x in manifest["lanes"]], revision, parent=run,
                   role=manifest["reader_role"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("prepare")
    init.add_argument("target")
    init.add_argument("--contract", required=True)
    init.add_argument("--reader", action="append", required=True)
    init.add_argument("--role", choices=sorted(blind.READER_ROLES), default="blind_reader")
    init.add_argument("--revision", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("run")
    rec.add_argument("--lane", type=int, default=1)
    rec.add_argument("--report", required=True)
    rec.add_argument("--agent-id", required=True)
    rec.add_argument("--execution", required=True, choices=sorted(EXECUTIONS))
    match = sub.add_parser("reconcile")
    match.add_argument("run")
    match.add_argument("--assessment", required=True)
    for name in ("status", "editor-packet", "repair-packet"):
        sub.add_parser(name).add_argument("run")
    nxt = sub.add_parser("advance")
    nxt.add_argument("run")
    nxt.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    root = blind.ROOT
    try:
        if args.command == "prepare":
            result = prepare(root, args.target, json_read(root, args.contract), args.reader, args.revision, role=args.role)
        elif args.command == "record":
            record(root, args.run, args.lane, json_read(root, args.report), args.agent_id, args.execution)
            result = {"recorded": True, "model_execution_verified": False}
        elif args.command == "reconcile":
            result = reconcile(root, args.run, json_read(root, args.assessment))
        elif args.command == "status":
            result = status(root, args.run)
        elif args.command == "advance":
            result = advance(root, args.run, args.revision)
        else:
            result = role_packet(root, args.run, "structure_reviewer" if args.command == "editor-packet" else "writer")
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
