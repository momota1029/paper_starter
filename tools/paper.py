#!/usr/bin/env python3
"""Portable research workspace helpers. Record checks are not semantic review."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime, timezone
from urllib.parse import unquote
from uuid import uuid4

PROFILES = {"theory", "empirical", "qualitative", "review", "mixed", "custom"}
STATUSES = {"draft", "reviewing", "revision", "ready", "submitted", "published", "archived"}
ROLES = {"correctness", "argument", "sources", "bibliography", "structure", "reader", "render", "human"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
OMIT = {"inbox", "reviews", "__pycache__", ".git"}
AUX = {".aux", ".log", ".fls", ".fdb_latexmk", ".synctex", ".pyc"}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def safe(root, relative):
    """Confine paths and reject aliases, including dangling symlinks."""
    require(isinstance(relative, str) and bool(relative), "empty or non-string path")
    p = Path(relative)
    require(not p.is_absolute() and ".." not in p.parts, f"unsafe relative path: {relative}")
    current = root
    for part in p.parts:
        current = current / part
        require(not current.is_symlink(), f"symlink not allowed: {relative}")
    require(current.resolve().is_relative_to(root.resolve()), f"outside workspace: {relative}")
    return current


def save_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        f.write(content)


def replace_text(path, content):
    require(not path.is_symlink(), f"symlink not allowed: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".paper-", delete=False) as f:
        temporary = Path(f.name)
        f.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def project(root, slug):
    require(bool(SLUG.fullmatch(slug)), "slug must use lowercase letters, digits, and hyphens")
    folder = safe(root, f"writing/{slug}")
    meta = tomllib.loads(safe(root, f"writing/{slug}/meta.toml").read_text(encoding="utf-8"))
    for key in ("title", "profile", "language", "status", "manuscript", "writer_id", "reader"):
        require(isinstance(meta.get(key), str) and meta[key].strip(), f"{slug}: missing {key}")
    require(meta["profile"] in PROFILES, f"{slug}: invalid profile")
    require(meta["status"] in STATUSES, f"{slug}: invalid status")
    manuscript = safe(root, f"writing/{slug}/{meta['manuscript']}")
    require(manuscript.is_file(), f"{slug}: manuscript missing")
    require(manuscript.suffix in {".md", ".tex"}, "manuscript must be .md or .tex")
    inputs = meta.get("inputs", [])
    require(isinstance(inputs, list) and all(isinstance(x, str) for x in inputs), "inputs must be paths")
    for name in inputs:
        require(safe(root, name).is_file(), f"missing input: {name}")
    return folder, meta


def projects(root):
    writing = safe(root, "writing")
    if not writing.exists():
        return []
    result = []
    for folder in sorted(writing.iterdir()):
        require(not folder.is_symlink(), f"symlink in writing: {folder.name}")
        if folder.is_dir():
            result.append((folder.name, project(root, folder.name)[1]))
    return result


def cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\", "&#92;").replace("[", "&#91;").replace("]", "&#93;").replace("|", "&#124;").replace("\n", " ").replace("\r", " ")


def index_text(root):
    rows = ["# Writing index", "", "Generated from local meta.toml files. Do not publish by accident.", "",
            "| Project | Profile | Language | Status | Inbox |", "| --- | --- | --- | --- | --- |"]
    for slug, meta in projects(root):
        inbox = safe(root, f"writing/{slug}/inbox")
        pending = inbox.exists() and any(p.name != "processed" for p in inbox.iterdir())
        rows.append(f"| [{cell(meta['title'])}]({slug}/{meta['manuscript']}) | {meta['profile']} | "
                    f"{cell(meta['language'])} | {meta['status']} | {'pending' if pending else ''} |")
    return "\n".join(rows) + "\n"


def update_index(root, check=False):
    path = safe(root, "writing/index.md")
    expected = index_text(root)
    if check:
        require(path.is_file() and path.read_text(encoding="utf-8") == expected,
                "writing/index.md is stale; run index")
    else:
        replace_text(path, expected)


def tex_escape(text):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
               "^": r"\textasciicircum{}"}
    return "".join(mapping.get(c, c) for c in text)


def new_project(root, args):
    require(bool(SLUG.fullmatch(args.slug)), "invalid slug")
    folder = safe(root, f"writing/{args.slug}")
    require(not folder.exists(), "project exists; refusing overwrite")
    require(args.title.strip() and "\n" not in args.title and "\r" not in args.title, "title must be one nonempty line")
    require(args.language.strip(), "language is required")
    replacements = {"TITLE": args.title, "PROFILE": args.profile, "LANGUAGE": args.language,
                    "MANUSCRIPT": f"{args.slug}.{args.format}"}
    template = safe(root, "templates/project")
    content = {}
    for name in ("meta.toml", "evidence.md", "design.md", "corpus.md", "quality-contract.md", "claims.json", f"manuscript.{args.format}"):
        body = (template / name).read_text(encoding="utf-8")
        for key, value in replacements.items():
            if name == "meta.toml":
                value = json.dumps(value, ensure_ascii=False)[1:-1]
            elif name.endswith(".tex"):
                value = tex_escape(value)
            body = body.replace("{{" + key + "}}", value)
        destination = replacements["MANUSCRIPT"] if name.startswith("manuscript.") else name
        content[destination] = body
    # Validate all inputs before creating the project; never overwrite a prior project.
    tomllib.loads(content["meta.toml"])
    folder.mkdir(parents=True, exist_ok=False)
    for name, body in content.items():
        save_new(folder / name, body)
    (folder / "inbox").mkdir()
    update_index(root)
    print(f"Created writing/{args.slug}; draft only")


def claims_check(folder, final=False):
    data = read_json(folder / "claims.json")
    require(isinstance(data, dict) and isinstance(data.get("claims"), list), "claims.json needs a claims array")
    claims = data["claims"]
    if final:
        require(bool(claims), "no main claims recorded")
    seen = set()
    for claim in claims:
        require(isinstance(claim, dict), "claim must be an object")
        for key in ("id", "statement", "kind", "status", "location", "evidence"):
            require(isinstance(claim.get(key), str) and claim[key].strip(), f"claim missing {key}")
        require(claim["id"] not in seen, "duplicate claim ID")
        seen.add(claim["id"])
        require(claim["kind"] in {"original", "cited", "routine", "unresolved"}, "invalid claim kind")
        require(claim["status"] in {"pending", "verified", "contradicted"}, "invalid claim status")
        if final:
            require(claim["kind"] != "unresolved" and claim["status"] == "verified",
                    f"unresolved claim: {claim['id']}")


def source_bytes(root, slug):
    folder, meta = project(root, slug)
    paths = set()
    for path in folder.rglob("*"):
        relative = path.relative_to(folder)
        if any(p in OMIT for p in relative.parts) or path.suffix in AUX:
            continue
        require(not path.is_symlink(), f"symlink in project: {relative}")
        if path.is_file():
            paths.add(path.relative_to(root).as_posix())
    paths.update(meta.get("inputs", []))
    if safe(root, "index.bib").exists():
        paths.add("index.bib")
    return {p: safe(root, p).read_bytes() for p in sorted(paths)}


def snapshot(root, args):
    folder, meta = project(root, args.slug)
    claims_check(folder)
    before = source_bytes(root, args.slug)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    run = safe(root, f".paper-local/reviews/{args.slug}/{run_id}")
    run.mkdir(parents=True, exist_ok=False)
    files = {p: digest(b) for p, b in before.items()}
    for name, data in before.items():
        dest = safe(run, "frozen/" + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    rendered = None
    if args.artifact:
        source = safe(root, args.artifact)
        require(source.suffix in {".pdf", ".html", ".md", ".txt"} and source.is_file(), "unsupported artifact")
        data = source.read_bytes()
        artifact_name = "artifact" + source.suffix
        (run / artifact_name).write_bytes(data)
        rendered = {"source": args.artifact, "file": artifact_name, "sha256": digest(data)}
    # If a source changed during capture, retain the incomplete directory as evidence,
    # but do not produce a usable manifest.
    require(before == source_bytes(root, args.slug), "sources changed during snapshot; retry in a fresh run")
    manifest = {"schema": 1, "run_id": run_id, "slug": args.slug, "created": now(),
                "manuscript": f"writing/{args.slug}/{meta['manuscript']}", "reader": meta["reader"],
                "writer_id": meta["writer_id"], "contributors": sorted(set([meta["writer_id"]] + args.contributor)),
                "files": files, "rendered": rendered}
    save_new(run / "manifest.json", json_text(manifest))
    (run / "reports").mkdir()
    print(run.relative_to(root).as_posix())


def load_run(root, name):
    run = safe(root, name)
    require(run.parent.parent == root / ".paper-local/reviews", "run must be under .paper-local/reviews/<slug>/<run>")
    m = read_json(safe(root, name + "/manifest.json"))
    require(m.get("schema") == 1 and m.get("run_id") == run.name and m.get("slug") == run.parent.name,
            "invalid run identity")
    require(isinstance(m.get("files"), dict) and m["files"], "empty snapshot")
    require(m.get("manuscript") in m["files"], "missing manuscript in snapshot")
    require(isinstance(m.get("contributors"), list) and m.get("writer_id") in m["contributors"], "missing contributors")
    return run, m


def verify(root, name, current=True):
    run, m = load_run(root, name)
    for path, sha in m["files"].items():
        require(isinstance(sha, str) and bool(HASH.fullmatch(sha)), "invalid hash")
        require(digest(safe(run, "frozen/" + path).read_bytes()) == sha, f"snapshot changed: {path}")
    if current:
        actual = {p: digest(b) for p, b in source_bytes(root, m["slug"]).items()}
        require(actual == m["files"], "current inputs differ from reviewed snapshot")
    artifact = m.get("rendered")
    if artifact:
        require(digest(safe(run, artifact["file"]).read_bytes()) == artifact["sha256"], "frozen artifact changed")
        if current:
            require(digest(safe(root, artifact["source"]).read_bytes()) == artifact["sha256"], "current artifact changed")
    return run, m


def packet(root, args):
    run, m = verify(root, args.run)
    if args.role == "reader":
        # Do not reveal the manifest, contract, sources, or expected answers.
        artifact = run / (m["rendered"]["file"] if m.get("rendered") else "frozen/" + m["manuscript"])
        require(artifact.suffix != ".tex", "render TeX first and snapshot with --artifact for a reader")
        print(json_text({"artifact": str(artifact), "reader": m["reader"],
                         "procedure": "Read only the next natural block; save a timestamped observation before opening the next. Record what the text supports, first confusion, later recovery, and unread scope. Do not inspect neighboring files or propose repairs. If the tool loads the full text, report failed prefix isolation."}))
    else:
        print(json_text({"role": args.role, "run_id": m["run_id"], "frozen": str(run / "frozen"),
                         "procedure": "Read only assigned scope and evidence. Report exact locations, support, severity, unread scope, and closure conditions. Do not edit or read other reports."}))


def record(root, args):
    run, m = verify(root, args.run)
    source = safe(root, args.report)
    report = read_json(source)
    require(report.get("run_id") == m["run_id"], "report belongs to another run")
    require(report.get("role") in ROLES, "unknown report role")
    require(isinstance(report.get("reviewer_id"), str) and report["reviewer_id"].strip(), "missing reviewer ID")
    require(report.get("kind") in {"ai", "human"}, "unknown reviewer kind")
    require(report.get("verdict") in {"pending", "pass", "fail", "blocked"}, "unknown verdict")
    require(isinstance(report.get("independent"), bool), "independent must be boolean")
    require(isinstance(report.get("findings"), list), "findings must be a list")
    if report.get("reader_transport") == "supplementary-cli-text":
        receipt = safe(root, report.get("reader_receipt", ""))
        require(receipt.is_relative_to(run / "reader"), "reader receipt must belong to this run")
        report["reader_receipt_sha256"] = digest(receipt.read_bytes())
    # Append, never overwrite a past report. Evidence is copied to this run as well.
    evidence = safe(root, report.get("evidence", ""))
    require(evidence.is_file() and bool(evidence.read_text(encoding="utf-8").strip()), "missing actual review evidence")
    rid = uuid4().hex
    evidence_name = f"reports/{rid}.md"
    save_new(run / evidence_name, evidence.read_text(encoding="utf-8"))
    report["evidence"] = evidence_name
    report["recorded_at"] = now()
    report["evidence_sha256"] = digest((run / evidence_name).read_bytes())
    save_new(run / f"reports/{rid}.json", json_text(report))
    print(f"Recorded {rid}; report contents and independence still require adjudication")


COVERAGE = {
    "argument": ("external_inputs", ("input", "definition", "statement", "application", "source")),
    "sources": ("attribution", ("concept", "first_use", "attribution", "policy", "support")),
    "structure": ("constraints", ("id", "strength", "basis", "checked_location", "decision")),
}


def coverage_check(report):
    """Require positive review evidence, not just an empty findings array.

    This checks record structure only. Completeness, valid exceptions and actual
    manuscript locations must still be adjudicated against the frozen contract.
    """
    if report.get("role") not in COVERAGE:
        return
    key, fields = COVERAGE[report["role"]]
    coverage = report.get("coverage")
    require(isinstance(coverage, dict), f"missing positive coverage: {key}")
    entry = coverage.get(key)
    require(isinstance(entry, dict), f"missing positive coverage: {key}")
    require(isinstance(entry.get("scope"), str) and entry["scope"].strip(), f"coverage scope missing: {key}")
    items = entry.get("items")
    require(isinstance(items, list), f"coverage items missing: {key}")
    none = entry.get("none_reason", "")
    require(isinstance(none, str), f"invalid none_reason: {key}")
    require(bool(items) != bool(none.strip()), f"coverage needs items OR a grounded none_reason: {key}")
    for item in items:
        require(isinstance(item, dict), f"invalid coverage item: {key}")
        for field in fields:
            require(isinstance(item.get(field), str) and item[field].strip(),
                    f"coverage {key} missing {field}")
        if key == "constraints":
            require(item["strength"] in {"hard", "strong", "weak"}, "invalid constraint strength")


def reader_receipt_check(root, run, manifest, report):
    if report.get("reader_transport") != "supplementary-cli-text":
        return
    path = safe(root, report.get("reader_receipt", ""))
    require(path.is_relative_to(run / "reader"), "reader receipt outside this run")
    require(digest(path.read_bytes()) == report.get("reader_receipt_sha256"), "reader receipt changed")
    receipt = read_json(path)
    require(receipt.get("run_id") == manifest["run_id"] and receipt.get("reviewer_id") == report.get("reviewer_id"),
            "reader receipt identity mismatch")
    require(receipt.get("status") == "process-checked" and not (path.parent / "failure.json").exists(),
            "reader execution incomplete or failed")
    expected_artifact = manifest["rendered"]["sha256"] if manifest.get("rendered") else manifest["files"][manifest["manuscript"]]
    require(receipt.get("artifact_sha256") == expected_artifact, "reader receipt artifact mismatch")
    require(isinstance(receipt.get("files"), dict) and receipt["files"], "reader receipt lacks raw evidence")
    for name, sha in receipt["files"].items():
        require(digest(safe(path.parent, name).read_bytes()) == sha, "reader raw evidence changed")
    require(isinstance(report.get("isolation_review"), str) and report["isolation_review"].strip(),
            "supplementary transport needs explicit isolation review and limits")
    require(isinstance(report.get("goal_adjudication"), str) and report["goal_adjudication"].strip(),
            "reader receipt is not goal adjudication")
    observed = receipt.get("checkpoints")
    declared = report.get("checkpoints")
    require(isinstance(observed, list) and observed and isinstance(declared, list) and len(observed) == len(declared),
            "reader checkpoints differ from execution")
    require("begin.json" in receipt["files"], "reader receipt lacks original boundary plan")
    begun = read_json(safe(path.parent, "begin.json"))
    require(begun.get("manifest_sha256") == digest((run / "manifest.json").read_bytes()), "reader manifest mismatch")
    artifact_path = manifest["rendered"]["file"] if manifest.get("rendered") else "frozen/" + manifest["manuscript"]
    from reader import split_plan, response, context_check
    blocks = split_plan(safe(run, artifact_path).read_bytes(), begun["plan"])
    require(len(observed) == len(blocks), "reader summary does not cover boundary plan")
    start = 1
    for number, (actual, claimed) in enumerate(zip(observed, declared), 1):
        label = f"block-{number:03d}"
        for suffix in (".checkpoint.json", ".events.jsonl"):
            require(label + suffix in receipt["files"], "reader receipt lacks checkpoint/raw events")
        checkpoint = read_json(safe(path.parent, label + ".checkpoint.json"))
        require(checkpoint == actual, "reader summary differs from saved checkpoint")
        events = safe(path.parent, label + ".events.jsonl").read_text(encoding="utf-8")
        # Reuse the transport parser: unknown events, tool use, wrong sessions,
        # failed/incomplete turns, and duplicate JSON fields remain invalid here.
        _, raw_observation = response(events, report["reviewer_id"])
        context_check(raw_observation, checkpoint=True)
        require(raw_observation == actual.get("observation"), "reader checkpoint differs from raw events")
        end = begun["plan"]["ends"][number - 1]
        require(actual.get("block_sha256") == digest(blocks[number - 1].encode("utf-8")) and
                actual.get("location") == f"lines {start}-{end}", "reader checkpoint prefix mismatch")
        start = end + 1
        require(isinstance(actual, dict) and isinstance(claimed, dict) and
                actual.get("at") == claimed.get("at") and actual.get("location") == claimed.get("location") and
                json_text(actual.get("observation")) == claimed.get("observation"),
                "reader checkpoint differs from raw observation")


def readiness(root, args):
    run, m = verify(root, args.run)
    folder, meta = project(root, m["slug"])
    claims_check(folder, final=True)
    body = safe(root, m["manuscript"]).read_text(encoding="utf-8")
    require(not re.search(r"\b(?:TODO|TBD|FIXME)\b|\{\{[A-Z_]+\}\}", body), "unfinished manuscript markers")
    contract = folder / "quality-contract.md"
    require(contract.is_file() and contract.read_text(encoding="utf-8").strip(), "missing quality contract")
    require(not re.search(r"\b(?:TODO|TBD|FIXME)\b|\{\{[A-Z_]+\}\}", contract.read_text(encoding="utf-8")),
            "unfinished quality contract")
    require(m.get("rendered"), "no frozen rendered artifact")
    reports = []
    readers_seen = set()
    # A reader from an earlier run of the same project is no longer fresh.
    for previous in run.parent.iterdir():
        if previous == run or previous.is_symlink() or not previous.is_dir():
            continue
        old_manifest = previous / "manifest.json"
        if old_manifest.is_file() and read_json(old_manifest).get("created", "") < m["created"]:
            for p in (previous / "reports").glob("*.json"):
                old = read_json(p)
                if old.get("role") == "reader":
                    readers_seen.add(old.get("reviewer_id"))
    for path in sorted((run / "reports").glob("*.json")):
        safe(root, path.relative_to(root).as_posix())
        r = read_json(path)
        require(r.get("run_id") == m["run_id"], "stale report")
        require(r.get("verdict") == "pass", "nonpassing report remains; adjudicate and use a fresh closure run")
        coverage_check(r)
        require(r.get("scope", "").strip() and isinstance(r.get("unread"), list), "report lacks scope")
        require(not r["unread"], "final review has unread scope")
        evidence = safe(run, r.get("evidence", ""))
        require(digest(evidence.read_bytes()) == r.get("evidence_sha256"), "review evidence changed")
        require(isinstance(r.get("findings"), list), "missing findings")
        for finding in r["findings"]:
            require(isinstance(finding, dict), "finding must be an object")
            require(finding.get("status") in {"closed", "rejected", "not-applicable"}, "unclosed finding")
            require(bool(finding.get("reason")), "finding closure lacks evidence/reason")
        if r.get("role") not in {"render", "human"}:
            require(r.get("independent") is True and r.get("reviewer_id") not in m["contributors"],
                    "self review does not count as independent")
        if r.get("role") == "reader":
            reader_receipt_check(root, run, m, r)
            require(r.get("reviewer_id") not in readers_seen, "reader was used in an earlier run")
            require(r.get("reader_goals_met") is True and r.get("isolation") == "passed", "reader goals/isolation incomplete")
            cps = r.get("checkpoints")
            require(isinstance(cps, list) and bool(cps), "no forward-reading checkpoints")
            last = None
            for cp in cps:
                require(isinstance(cp, dict), "reader checkpoint must be an object")
                require(all(isinstance(cp.get(k), str) and cp[k].strip() for k in ("at", "location", "observation")),
                        "incomplete reader checkpoint")
                stamp = datetime.fromisoformat(cp["at"])
                require(stamp.tzinfo is not None and (last is None or stamp > last), "checkpoints need increasing timezone-aware times")
                last = stamp
        if r.get("role") == "human":
            require(r.get("kind") == "human", "human read cannot be an AI report")
        reports.append(r)
    require(ROLES <= {r.get("role") for r in reports}, "missing required final review roles: " + ", ".join(sorted(ROLES - {r.get("role") for r in reports})))
    independent = {r["reviewer_id"] for r in reports if r.get("role") not in {"human", "render"}}
    require(len(independent) >= 2, "need independent reader and specialist identities")
    reader_ids = {r["reviewer_id"] for r in reports if r.get("role") == "reader"}
    other_ids = {r["reviewer_id"] for r in reports if r.get("role") not in {"reader", "human", "render"}}
    require(not reader_ids & other_ids, "blind reader cannot double as informed specialist")
    print("Record checks passed for this snapshot. NOT a certification of correctness, readability, or submission eligibility.")


def build(root, args):
    folder, meta = project(root, args.slug)
    source = safe(root, f"writing/{args.slug}/{meta['manuscript']}")
    before = source_bytes(root, args.slug)
    output = safe(root, f"output/{args.slug}")
    output.mkdir(parents=True, exist_ok=True)
    dest = safe(root, f"output/{args.slug}/{args.slug}.{'html' if source.suffix == '.md' else 'pdf'}")
    # Isolate each build; keep the previous successful artifact on failure.
    with tempfile.TemporaryDirectory(prefix="paper-build-") as td:
        temp = Path(td)
        if source.suffix == ".md":
            executable = shutil.which("pandoc")
            require(executable, "pandoc is required for Markdown rendering; source editing and review remain available")
            result = temp / "artifact.html"
            command = [executable, meta["manuscript"], "--standalone", "--mathjax", "--output", str(result)]
        else:
            executable = shutil.which("latexmk")
            require(executable, "latexmk and a TeX distribution are required")
            result = temp / (source.stem + ".pdf")
            command = [executable, "-lualatex", "-interaction=nonstopmode", "-halt-on-error",
                       "-no-shell-escape", "-outdir=" + str(temp), meta["manuscript"]]
        subprocess.run(command, cwd=folder, check=True)
        require(result.is_file(), "builder did not produce artifact")
        require(before == source_bytes(root, args.slug), "sources changed while building")
        if dest.exists():
            archive = safe(root, f"output/{args.slug}/archive/{uuid4().hex}-{dest.name}")
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, archive)
        shutil.copy2(result, dest)
    receipt = {"created": now(), "artifact": dest.relative_to(root).as_posix(),
               "sha256": digest(dest.read_bytes()), "inputs": {p: digest(b) for p, b in before.items()},
               "command": command, "visual_inspection": "pending"}
    replace_text(safe(root, f"output/{args.slug}/build.json"), json_text(receipt))
    print(f"Built {dest.relative_to(root)}; visual inspection pending")


def agent_config_check(root):
    config = tomllib.loads(safe(root, ".codex/config.toml").read_text(encoding="utf-8"))
    require("model" not in config and "model_reasoning_effort" not in config, "project must preserve primary model selection")
    agents = config.get("agents", {})
    require(agents.get("enabled") is True, "subagents are not enabled")
    maximum = agents.get("max_concurrent_threads_per_session")
    require(type(maximum) is int and maximum > 0, "invalid agent concurrency")
    found = set()
    for path in sorted(safe(root, ".codex/agents").glob("*.toml")):
        safe(root, path.relative_to(root).as_posix())
        role = tomllib.loads(path.read_text(encoding="utf-8"))
        for key in ("name", "description", "developer_instructions", "model", "model_reasoning_effort"):
            require(isinstance(role.get(key), str) and role[key].strip(), f"agent {path.name}: missing {key}")
        require(role["name"] == path.stem and role["name"] not in found, f"agent identity mismatch: {path.name}")
        expected = "workspace-write" if role["name"] == "writer" else "read-only"
        require(role.get("sandbox_mode") == expected, f"agent permission mismatch: {path.name}")
        require(role["model_reasoning_effort"] in {"low", "medium", "high", "xhigh", "max", "ultra"}, "unknown reasoning effort")
        registration = agents.get(role["name"], {})
        require(isinstance(registration, dict) and bool(registration.get("description")), f"missing role registration: {path.name}")
        registered = safe(root, ".codex/" + registration.get("config_file", ""))
        require(registered == path, f"role config_file mismatch: {path.name}")
        found.add(role["name"])
    needed = {"inventory", "designer", "writer", "correctness_reviewer", "argument_reviewer",
              "source_reviewer", "bibliography_reviewer", "structure_reviewer", "blind_reader",
              "blind_reader_sol", "render_reviewer", "undergraduate_reader",
              "application_interviewer", "application_reviewer"}
    require(needed <= found, "missing configured agent roles: " + ", ".join(sorted(needed - found)))
    registered_roles = {name for name, value in agents.items() if isinstance(value, dict)}
    require(registered_roles == found, "role registry and files disagree")
    require("human" not in found, "human read cannot be configured as an AI role")


def skill_config_check(root):
    """Check the shipped single-line metadata and invocation policy, not all YAML."""
    policies = {"paper-writing": "true", "application-interview": "true",
                "blind-referee": "false", "undergraduate-lecture": "true"}
    for name, expected in policies.items():
        base = f".agents/skills/{name}"
        entry = safe(root, base + "/SKILL.md")
        require(entry.is_file(), f"missing {base}/SKILL.md")
        content = entry.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", content, re.DOTALL)
        require(front is not None, f"skill {name}: missing frontmatter")
        for key in ("name", "description"):
            values = re.findall(rf"^{key}: ([^\n]+)$", front[1], re.MULTILINE)
            require(len(values) == 1 and values[0].strip() not in {"", "''", '\"\"'},
                    f"skill {name}: missing or duplicate {key}")
            if key == "name":
                require(values[0] == name, f"skill {name}: identity mismatch")
        metadata = safe(root, base + "/agents/openai.yaml")
        # The lecture overlay inherits the host's automatic-invocation default.
        if name == "undergraduate-lecture" and not metadata.exists():
            continue
        require(metadata.is_file(), f"skill {name}: missing agents/openai.yaml")
        text = metadata.read_text(encoding="utf-8")
        sections = re.findall(r"^policy:\n((?:[ \t]+[^\n]*\n?)*)", text, re.MULTILINE)
        require(len(sections) == 1, f"skill {name}: missing or duplicate policy")
        values = re.findall(r"^  allow_implicit_invocation: (true|false)$",
                            sections[0], re.MULTILINE)
        keys = re.findall(r"^[ \t]+allow_implicit_invocation:", sections[0], re.MULTILINE)
        require(len(keys) == 1 and values == [expected],
                f"skill {name}: invocation policy mismatch")


def check_workspace(root):
    for name in ("AGENTS.md", "README.md", "index.md", "rules/INDEX.md",
                 ".agents/skills/paper-writing/SKILL.md",
                 ".agents/skills/blind-referee/SKILL.md",
                 ".agents/skills/undergraduate-lecture/SKILL.md",
                 ".agents/skills/application-interview/SKILL.md"):
        require(safe(root, name).is_file(), f"missing {name}")
    required_rules = {p.name for p in (root / "rules").glob("*.md") if p.name != "INDEX.md"}
    rule_index = (root / "rules/INDEX.md").read_text(encoding="utf-8")
    require(all(f"({name})" in rule_index for name in required_rules), "rule missing from INDEX")
    agent_config_check(root)
    skill_config_check(root)
    checked = 0
    for path in root.rglob("*.md"):
        rel = path.relative_to(root)
        if rel.parts[0] in {"writing", "inbox", "output", "refs", ".paper-local", ".application-local", ".git", ".venv"}:
            continue
        require(not path.is_symlink(), f"symlink: {rel}")
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", text):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = (path.parent / target).resolve()
            require(resolved.is_relative_to(root) and resolved.exists(), f"broken local link: {rel}: {target}")
        checked += 1
    items = projects(root)
    for slug, _ in items:
        folder, _ = project(root, slug)
        claims_check(folder)
        source_bytes(root, slug)
    if items or (root / "writing/index.md").exists():
        update_index(root, check=True)
    print(f"Workspace records and local link targets OK ({checked} Markdown files, {len(items)} projects). Semantic review not performed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new")
    new.add_argument("slug")
    new.add_argument("--title", required=True)
    new.add_argument("--profile", choices=sorted(PROFILES), default="custom")
    new.add_argument("--language", default="ja")
    new.add_argument("--format", choices=["md", "tex"], default="md")
    index = commands.add_parser("index")
    index.add_argument("--check", action="store_true")
    commands.add_parser("check")
    snap = commands.add_parser("snapshot")
    snap.add_argument("slug")
    snap.add_argument("--artifact", help="repository-relative rendered artifact; correspondence needs inspection")
    snap.add_argument("--contributor", action="append", default=[], help="ID of every designer/editor; repeatable")
    ver = commands.add_parser("verify")
    ver.add_argument("run")
    ver.add_argument("--frozen-only", action="store_true", help="historical integrity only; does not check current sources")
    pack = commands.add_parser("packet")
    pack.add_argument("run")
    pack.add_argument("--role", choices=sorted(ROLES), required=True)
    rec = commands.add_parser("record")
    rec.add_argument("run")
    rec.add_argument("report", help="repository-relative JSON report with evidence path")
    ready = commands.add_parser("readiness")
    ready.add_argument("run")
    render = commands.add_parser("build")
    render.add_argument("slug")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "new":
            new_project(root, args)
        elif args.command == "index":
            update_index(root, args.check)
            print("Index checked" if args.check else "Index updated")
        elif args.command == "check":
            check_workspace(root)
        elif args.command == "snapshot":
            snapshot(root, args)
        elif args.command == "verify":
            verify(root, args.run, not args.frozen_only)
            print("Frozen integrity OK" if args.frozen_only else "Frozen and current inputs match")
        elif args.command == "packet":
            packet(root, args)
        elif args.command == "record":
            record(root, args)
        elif args.command == "readiness":
            readiness(root, args)
        elif args.command == "build":
            build(root, args)
    except (Invalid, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
