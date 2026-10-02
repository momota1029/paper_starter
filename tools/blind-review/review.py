#!/usr/bin/env python3
"""Prepare and verify blind-reader inputs; never run a model or edit a manuscript."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any
import uuid

ROOT = Path(__file__).resolve().parents[2]
STORE = Path(".paper-local/blind-review")
READER_ROLES = {"blind_reader", "blind_reader_sol", "undergraduate_reader"}
FORMATS = {".pdf", ".md", ".txt"}
MAX_BYTES = 64 * 1024 * 1024


def confined(root: Path, relative: str | Path) -> Path:
    """Reject traversal and aliases before reading or creating a scoped path."""
    root = root.resolve(strict=True)
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("use a repository-relative path without '..'")
    path = root
    for part in relative.parts:
        path = path / part
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
        except FileNotFoundError:
            attributes = 0
        reparse = attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if reparse or path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("symlinks and junctions are not supported")
        if not path.resolve().is_relative_to(root):
            raise ValueError("path leaves the repository")
    return path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> bytes:
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
        raise ValueError("input must be a regular file of at most 64 MiB")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    after = path.stat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or len(data) != before.st_size:
        raise ValueError("input changed while being read")
    return data


def new_file(path: Path, data: bytes) -> None:
    # Exclusive creation: no existing draft, manifest or input is overwritten.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def reader_brief(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 600:
        raise ValueError("reader background must be a nonempty string of at most 600 characters")
    if len(value.splitlines()) != 1 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("reader background must be one line without control characters")
    # Sentence count and neutrality are semantic checks owned by the primary.
    return value.strip()


def run_directory(root: Path, run: str) -> Path:
    if not isinstance(run, str) or not re.fullmatch(r"[0-9a-f]{32}", run):
        raise ValueError("run must be the 32-character ID printed by prepare")
    return confined(root, STORE / run)


def reader_role(role: Any) -> str:
    if not isinstance(role, str) or role not in READER_ROLES:
        raise ValueError("unsupported blind-reader role")
    return role


def prepare(root: Path, target: str, readers: list[str], role: str = "blind_reader") -> str:
    reader_role(role)
    if not 1 <= len(readers) <= 2:
        raise ValueError("specify one or two reader backgrounds within the review budget")
    readers = [reader_brief(r) for r in readers]
    source = confined(root, target)
    relative = source.relative_to(root.resolve()).as_posix()
    if source.is_relative_to(root.resolve() / STORE):
        raise ValueError("use the actual target, not a previous blind-review snapshot")
    suffix = source.suffix.lower()
    if suffix not in FORMATS:
        raise ValueError("use a rendered PDF or self-contained UTF-8 .md/.txt artifact; build TeX first")
    data = read_bytes(source)
    if not data:
        raise ValueError("target artifact is empty")
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("PDF signature missing; this is not a PDF validation or rendering check")
    else:
        try:
            data.decode("utf-8-sig")
        except UnicodeError as error:
            raise ValueError("text artifact must be UTF-8") from error
    sha = digest(data)
    store = confined(root, STORE)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    run = uuid.uuid4().hex
    directory = run_directory(root, run)
    directory.mkdir(mode=0o700)
    lanes = []
    for index, brief in enumerate(readers, start=1):
        lane = directory / f"reader-{index}"
        lane.mkdir(mode=0o700)
        new_file(lane / ("artifact" + suffix), data)
        lanes.append({"id": index, "reader_background": brief})
    # Detect changes during copying. Preserve any incomplete run for inspection.
    if digest(read_bytes(confined(root, relative))) != sha:
        raise ValueError(f"source changed during preparation; incomplete run retained: {run}")
    manifest = {
        "schema_version": 1, "run": run, "state": "prepared",
        "source": relative, "format": suffix, "sha256": sha, "size": len(data),
        "lanes": lanes, "reader_role": role,
    }
    # Written last; absence means preparation did not complete.
    new_file(directory / "manifest.json", json_bytes(manifest))
    return run


def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result


def load(root: Path, run: str) -> tuple[Path, dict[str, Any]]:
    directory = run_directory(root, run)
    path = confined(root, STORE / run / "manifest.json")
    try:
        manifest = json.loads(read_bytes(path).decode("utf-8"), object_pairs_hook=unique_keys)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid manifest JSON; preserve this run and prepare a fresh one") from error
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported manifest version")
    if manifest.get("run") != run or manifest.get("state") != "prepared":
        raise ValueError("manifest run/state mismatch")
    reader_role(manifest.get("reader_role"))
    suffix = manifest.get("format")
    if not isinstance(suffix, str) or suffix not in FORMATS:
        raise ValueError("invalid manifest format")
    sha = manifest.get("sha256")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("invalid manifest digest")
    if type(manifest.get("size")) is not int or not 1 <= manifest["size"] <= MAX_BYTES:
        raise ValueError("invalid manifest size")
    source = manifest.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("invalid source path")
    source_path = confined(root, source)
    if source_path.suffix.lower() != suffix or source_path.is_relative_to(root.resolve() / STORE):
        raise ValueError("invalid source artifact")
    lanes = manifest.get("lanes")
    if not isinstance(lanes, list) or not 1 <= len(lanes) <= 2:
        raise ValueError("invalid reader count")
    for index, lane in enumerate(lanes, start=1):
        if not isinstance(lane, dict) or type(lane.get("id")) is not int or lane["id"] != index:
            raise ValueError("invalid reader ID")
        reader_brief(lane.get("reader_background"))
    return directory, manifest


def verify(root: Path, run: str, *, check_source: bool = True) -> dict[str, Any]:
    """Check snapshots and, by default, their live source; historical loops opt out explicitly."""
    directory, manifest = load(root, run)
    for lane in manifest["lanes"]:
        relative = STORE / run / f"reader-{lane['id']}"
        lane_dir = confined(root, relative)
        expected = "artifact" + manifest["format"]
        if {p.name for p in lane_dir.iterdir()} != {expected}:
            raise ValueError("reader directory must contain only its artifact; keep reports outside it")
        content = read_bytes(confined(root, relative / expected))
        if len(content) != manifest["size"] or digest(content) != manifest["sha256"]:
            raise ValueError("snapshot changed; this run is invalid")
    if check_source:
        content = read_bytes(confined(root, manifest["source"]))
        if len(content) != manifest["size"] or digest(content) != manifest["sha256"]:
            raise ValueError("source changed; results refer only to the old snapshot, not the current artifact")
    return manifest


def packet(root: Path, run: str, lane: int, role: str | None = None) -> dict[str, Any]:
    manifest = verify(root, run)
    selected = manifest["reader_role"]
    if role is not None and reader_role(role) != selected:
        raise ValueError("reader role differs from the frozen run")
    if type(lane) is not int or not 1 <= lane <= len(manifest["lanes"]):
        raise ValueError("reader lane does not exist")
    artifact = confined(root, STORE / run / f"reader-{lane}" / ("artifact" + manifest["format"]))
    # No source filename, hash, manifest, previous report, author intent, or history.
    # The existing blind_reader role provides its standing protocol, not this tool.
    message = json.dumps({"target_artifact": str(artifact),
                          "reader_background": manifest["lanes"][lane - 1]["reader_background"]},
                         ensure_ascii=False)
    return {"agent_type": selected, "fork_turns": "none", "message": message}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("prepare", help="freeze the artifact; print a new run ID")
    init.add_argument("target", help="repository-relative .pdf/.md/.txt")
    init.add_argument("--reader", action="append", required=True, help="one neutral background sentence; repeat once for two readers")
    init.add_argument("--role", choices=sorted(READER_ROLES), default="blind_reader")
    dispatch = sub.add_parser("packet", help="print a native subagent request, not execute it")
    dispatch.add_argument("run")
    dispatch.add_argument("--lane", type=int, default=1)
    dispatch.add_argument("--role", choices=sorted(READER_ROLES), help="optional assertion of the already frozen role")
    check = sub.add_parser("verify", help="detect changed inputs; not proof of a model run or blindness")
    check.add_argument("run")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            print(prepare(ROOT, args.target, args.reader, args.role))
        elif args.command == "packet":
            print(json.dumps(packet(ROOT, args.run, args.lane, args.role), ensure_ascii=False, indent=2))
        else:
            manifest = verify(ROOT, args.run)
            print(f"Verified frozen inputs: {args.run}; readers={len(manifest['lanes'])}; sha256={manifest['sha256']}")
            print("Not checked: model execution, filesystem access isolation, prefix-reading behavior, PDF rendering, or disciplinary correctness.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
