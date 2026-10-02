#!/usr/bin/env python3
"""Local interview checkpoints; no network, model calls, Git writes, or submission.

The agent edits session.json and draft.md. This helper initializes without
clobbering, resumes, and checks bookkeeping, not factual truth or form compliance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ".application-local"
KINDS = ("cv", "grant", "other")
STATUSES = {"missing", "candidate", "confirmed", "conflict", "deferred", "not_applicable"}
PHASES = {"interviewing", "drafting", "review", "paused", "ready_for_user"}
# Conversation starters, NOT official forms or universal eligibility requirements.
STARTERS = {
    "cv": [("name", "氏名"), ("education", "学歴・学位"),
           ("employment", "職歴・所属"), ("research", "研究概要"),
           ("publications", "研究業績"), ("teaching", "教育歴")],
    "grant": [("title", "研究課題名"), ("question", "研究の問い"),
              ("background", "背景・既存研究との関係"), ("approach", "方法・実行計画"),
              ("outcomes", "到達目標"), ("feasibility", "遂行能力・研究環境"),
              ("budget", "経費と必要性"), ("ethics", "倫理・法令等の確認")],
    "other": [("purpose", "書類の目的"), ("content", "記載内容")],
}


def new_state(slug: str, kind: str) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError("unsupported kind")
    validate_slug(slug)
    return {
        "schema_version": 1, "slug": slug, "kind": kind,
        "phase": "interviewing", "round": 0,
        "target": {key: "" for key in (
            "audience", "purpose", "fiscal_year", "scheme", "format",
            "source_path", "output_path", "deadline", "institutional_deadline")},
        "requirements": {"status": "unverified", "source": "", "checked_at": "", "note": ""},
        "fields": [{"id": key, "label": label, "required": False,
                    "status": "missing", "value": "", "sources": [], "note": ""}
                   for key, label in STARTERS[kind]],
        "pending_questions": [], "notes": "",
    }


def validate_slug(slug: str) -> None:
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug) or len(slug) > 64:
        raise ValueError("slug must be 1-64 lowercase kebab-case characters, starting with a letter")
    # Windows device names are reserved even when used as directory names.
    if slug in {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}:
        raise ValueError("slug is a reserved Windows device name")


def safe_path(root: Path, slug: str, filename: str | None = None) -> Path:
    validate_slug(slug)
    root = root.resolve(strict=True)
    path = root
    parts = [LOCAL, slug]
    if filename is not None:
        if filename not in {"session.json", "draft.md"}:
            raise ValueError("unsupported checkpoint filename")
        parts.append(filename)
    for part in parts:
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("checkpoint paths must not be symlinks or junctions")
        if not path.resolve().is_relative_to(root):
            raise ValueError("checkpoint path escapes repository")
    return path


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def validate(state: Any, complete: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["session must be an object"]
    if type(state.get("schema_version")) is not int or state["schema_version"] != 1:
        errors.append("unsupported schema_version")
    try:
        validate_slug(state.get("slug"))
    except ValueError as error:
        errors.append(str(error))
    if state.get("kind") not in KINDS:
        errors.append("unsupported kind")
    if not isinstance(state.get("phase"), str) or state["phase"] not in PHASES:
        errors.append("invalid phase")
    if type(state.get("round")) is not int or state["round"] < 0:
        errors.append("round must be a nonnegative integer")
    if not isinstance(state.get("notes"), str):
        errors.append("notes must be a string")
    target = state.get("target")
    if not isinstance(target, dict) or any(not isinstance(target.get(key), str) for key in (
        "audience", "purpose", "fiscal_year", "scheme", "format", "source_path",
        "output_path", "deadline", "institutional_deadline")):
        errors.append("target must contain the documented string fields")
    req = state.get("requirements")
    if not isinstance(req, dict):
        errors.append("requirements must be an object")
    else:
        status = req.get("status")
        if status not in ("unverified", "verified", "not_applicable"):
            errors.append("invalid requirements status")
        if any(not isinstance(req.get(key), str) for key in ("source", "checked_at", "note")):
            errors.append("requirements source, checked_at and note must be strings")
        elif status == "verified" and (not req["source"].strip() or not req["checked_at"].strip()):
            errors.append("verified requirements need a source and check date")
        elif status == "verified":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", req["checked_at"]):
                    raise ValueError
                date.fromisoformat(req["checked_at"])
            except ValueError:
                errors.append("requirements checked_at must be an ISO calendar date")
        elif status == "not_applicable" and not req["note"].strip():
            errors.append("not_applicable requirements need a reason")
        if complete and state.get("kind") == "grant" and status != "verified":
            errors.append("grant requirements unresolved; verify the actual call/form requirements")
        elif complete and status == "unverified":
            errors.append("document requirements unresolved; verify them or record why none apply")
    fields = state.get("fields")
    if not isinstance(fields, list) or not fields:
        return errors + ["fields must be a nonempty list"]
    ids: set[str] = set()
    for index, field in enumerate(fields):
        location = f"fields[{index}]"
        if not isinstance(field, dict):
            errors.append(f"{location}: must be an object")
            continue
        key = field.get("id")
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_.-]*", key):
            errors.append(f"{location}: invalid id")
        elif key in ids:
            errors.append(f"{location}: duplicate id")
        else:
            ids.add(key)
        for name in ("label", "value", "note"):
            if not isinstance(field.get(name), str):
                errors.append(f"{location}: {name} must be a string")
        if type(field.get("required")) is not bool:
            errors.append(f"{location}: required must be boolean")
        status = field.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{location}: invalid status")
        value = field.get("value")
        sources = field.get("sources")
        valid_sources = isinstance(sources, list) and all(isinstance(s, str) and s.strip() for s in sources)
        if not valid_sources:
            errors.append(f"{location}: sources must be nonempty locator strings (or an empty list)")
        if status == "confirmed" and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{location}: confirmed field needs a value")
        if status in ("confirmed", "not_applicable") and (not valid_sources or not sources):
            errors.append(f"{location}: resolved field needs supporting source/author decision")
        if status == "missing" and isinstance(value, str) and value.strip():
            errors.append(f"{location}: a proposed value must be candidate, not missing")
        if status == "not_applicable" and (not isinstance(field.get("note"), str) or not field["note"].strip()):
            errors.append(f"{location}: not_applicable needs a reason")
        if complete and field.get("required") is True and status not in ("confirmed", "not_applicable"):
            errors.append(f"{location}: required field unresolved")
        if complete and (status == "conflict" or (status in ("candidate", "deferred") and bool(value))):
            errors.append(f"{location}: resolve or explicitly omit unconfirmed content")
    questions = state.get("pending_questions")
    if not isinstance(questions, list) or len(questions) > 3:
        errors.append("pending_questions must be a list of at most three questions")
    else:
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                errors.append(f"pending_questions[{index}]: must be an object")
                continue
            keys = question.get("field_ids")
            if not isinstance(keys, list) or any(not isinstance(k, str) or k not in ids for k in keys):
                errors.append(f"pending_questions[{index}]: unknown field id")
            if not isinstance(question.get("question"), str) or not question["question"].strip():
                errors.append(f"pending_questions[{index}]: missing question")
        if complete and questions:
            errors.append("pending questions remain")
    return errors


def load(root: Path, slug: str) -> dict[str, Any]:
    path = safe_path(root, slug, "session.json")
    check_guard(path.parent.parent)
    if not safe_path(root, slug, "draft.md").is_file():
        raise ValueError("draft.md is missing; preserve session.json and recover the draft explicitly")
    try:
        state = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicate_keys)
    except json.JSONDecodeError as error:
        # Do not echo personal data from malformed input.
        raise ValueError(f"invalid JSON at line {error.lineno}, column {error.colno}") from error
    errors = validate(state)
    if errors:
        raise ValueError("; ".join(errors))
    if state["slug"] != slug:
        raise ValueError("session slug does not match its directory")
    return state


def write_new(path: Path, content: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def check_guard(local: Path) -> None:
    ignore = local / ".gitignore"
    if (ignore.is_symlink() or getattr(ignore, "is_junction", lambda: False)()
            or not ignore.is_file() or ignore.read_text(encoding="utf-8").strip() != "*"):
        raise ValueError("local ignore guard is unexpected; inspect before storing personal data")


def initialize(root: Path, slug: str, kind: str) -> tuple[Path, bool]:
    state = new_state(slug, kind)
    directory = safe_path(root, slug)
    local = directory.parent
    local.mkdir(mode=0o700, exist_ok=True)
    ignore = local / ".gitignore"
    if ignore.exists() or ignore.is_symlink():
        check_guard(local)
    try:
        write_new(ignore, "*\n")
    except FileExistsError:
        pass
    check_guard(local)
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        existing = load(root, slug)
        if existing["kind"] != kind:
            raise ValueError("existing session has a different kind; choose a different slug")
        return directory, False
    write_new(directory / "session.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    write_new(directory / "draft.md", "# 下書き\n\n[未完成：対話で確認した内容をここに反映する]\n")
    return directory, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="existing directory for local checkpoints (default: script repository)")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create or resume without overwriting existing files")
    init.add_argument("slug")
    init.add_argument("--kind", choices=KINDS, required=True)
    status = sub.add_parser("status", help="show progress without printing personal field values")
    status.add_argument("slug")
    check = sub.add_parser("check", help="validate checkpoint structure, not factual truth")
    check.add_argument("slug")
    check.add_argument("--complete", action="store_true", help="also detect unresolved required fields")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            path, created = initialize(args.root, args.slug, args.kind)
            print(f"{'Created' if created else 'Resumed'} {path}")
        else:
            state = load(args.root, args.slug)
            if args.command == "status":
                print(f"{state['slug']}: {state['kind']}, {state['phase']}, round {state['round']}")
                print(json.dumps(dict(Counter(f["status"] for f in state["fields"])), sort_keys=True))
                remaining = [f["id"] for f in state["fields"] if f["required"] and f["status"] not in ("confirmed", "not_applicable")]
                print("Unresolved required IDs: " + (", ".join(remaining) or "none"))
                print(f"Pending questions: {len(state['pending_questions'])}; requirements: {state['requirements']['status']}")
            else:
                errors = validate(state, complete=args.complete)
                if errors:
                    raise ValueError("; ".join(errors))
                print("Checkpoint checks passed. Not checked: truth, complete requirement coverage, draft/form consistency, layout, or submission readiness.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
