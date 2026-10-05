#!/usr/bin/env python3
"""Prepare an installed-wheel, detached-field qualification run.

The harness deliberately records rather than interprets theorem freshness or
truth. It only exercises transport, bounded offline projections, relocation,
and an isolated installed CLI against explicitly selected exposition inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
FIELD = Path(__file__).resolve().parent
ASSEMBLED = Path(
    "/home/codex/projects/lean/matrix-factorization/latex/lean/"
    "poisson_fixed_epoch_exposition_evidence_r02/target-capture-r44/assembled"
)
MANIFEST = ASSEMBLED / "note.canonical.result.json"
ARTIFACTS = ASSEMBLED / "artifacts"
GUIDE = ROOT / "openspec/changes/ladon-proof-reading-guides/evidence/guide-r47/field/guide.json"
LINEAGE_INPUTS = ROOT / ".codex/state/dossier-r46/real-lineage-inputs.json"
SOURCE_DB = Path(
    "/home/codex/projects/lean/matrix-factorization/.ladon/index/"
    "fixed-epoch-field-u4t2qh3h.sqlite"
)
FIELD_DB = FIELD / "selected-lineage.sqlite"
TEX = ASSEMBLED.parent / "exposition.tex"
TARGET_ID = "uniform-total"
LINEAGE_ENTRY_ID = "prior-lineage-r06"
DATABASE_ID = "selected-lineage-store"
ARTIFACT_BYTES = 22_514_919
EXPECTED_ARTIFACTS = 89
GUIDE_SECTIONS = (
    "steps", "citations", "reviews", "correspondence", "targets",
    "checking", "assumptions", "lineage", "evidence",
)
DOSSIER_SECTIONS = (
    "components", "claims", "targets", "reviews", "assessments",
    "checking", "assumptions", "lineage", "evidence",
)
SOURCE_DATABASE_TEXT = str(SOURCE_DB)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_path(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"selected input is not a regular nonsymlink file: {path}")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            size += len(block)
            digest.update(block)
    return {"bytes": size, "sha256": "sha256:" + digest.hexdigest()}


def hash_inputs(artifact_paths: list[Path], lineage_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    paths = [LINEAGE_INPUTS, MANIFEST, GUIDE, TEX, FIELD_DB, *artifact_paths]
    return {str(path): digest_path(path) for path in paths}


def regular_artifacts() -> list[Path]:
    paths = sorted(ARTIFACTS.glob("*.json"), key=lambda path: path.name)
    if len(paths) != EXPECTED_ARTIFACTS:
        raise RuntimeError(f"expected exactly {EXPECTED_ARTIFACTS} canonical artifacts, found {len(paths)}")
    actual_bytes = sum(digest_path(path)["bytes"] for path in paths)
    if actual_bytes != ARTIFACT_BYTES:
        raise RuntimeError(f"canonical artifact bytes changed: expected {ARTIFACT_BYTES}, got {actual_bytes}")
    return paths


def _entry(identifier: str, role: str, path: Path | str) -> dict[str, str]:
    return {
        "id": identifier,
        "role": role,
        "disclosure": "supplied",
        "permission": "include",
        "path": str(path),
    }


def prepare_selection(output: Path, artifact_paths: list[Path], lineage_data: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    selected_entry = next(row for row in lineage_data["entries"] if row.get("targetId") == TARGET_ID)
    if selected_entry.get("closureId") != "cca9fd8a42d4e39267003768ff4650f1abc86fa20addebfdc92e1bf910cc2f12":
        raise RuntimeError("explicit lineage input no longer selects the reviewed uniform-total closure")
    if selected_entry.get("database") != SOURCE_DATABASE_TEXT:
        raise RuntimeError("explicit lineage input source database changed")
    if not FIELD_DB.is_file() or FIELD_DB.is_symlink():
        raise RuntimeError(f"selected-lineage fixture is unavailable: {FIELD_DB}")

    derived_lineage = json.loads(json.dumps(lineage_data))
    selected_entry = next(row for row in derived_lineage["entries"] if row["id"] == LINEAGE_ENTRY_ID)
    selected_entry["database"] = str(FIELD_DB)
    lineage_path = output / "lineage-inputs.json"
    lineage_path.write_bytes(canonical(derived_lineage) + b"\n")

    entries = [_entry("artifact-" + path.stem, "artifact", path) for path in artifact_paths]
    entries.extend([
        _entry("field-guide", "guide", GUIDE),
        _entry("field-lineage-inputs", "lineage", lineage_path),
        _entry(DATABASE_ID, "lineage-database", FIELD_DB),
        _entry("exposition-tex", "attachment", TEX),
    ])
    selection = {
        "schema": "ladon-result-bundle-selection-v1",
        "supplier": {"identity": "Ladon r48 installed-candidate field harness", "kind": "tool"},
        "entries": entries,
        "lineageBindings": [{"entryId": LINEAGE_ENTRY_ID, "databaseId": DATABASE_ID}],
        "identifiers": [],
        "externalDependencies": [{"id": "lean-replay-environment", "kind": "lean-toolchain-and-imports", "reason": "The Lean 4.33.0 compiler and imported compiled dependencies are not bundled; replay is not run."}],
    }
    selection_path = output / "bundle-selection.json"
    selection_path.write_bytes(canonical(selection) + b"\n")
    return selection_path, lineage_path, derived_lineage


def parse_text_projection(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in text.splitlines():
        key, marker, value = line.partition(": ")
        if not marker or key in result:
            raise RuntimeError("installed CLI text projection is malformed")
        result[key] = json.loads(value)
    return result


def parse_time(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    elapsed, peak = raw.splitlines()[-1].split("\t", 1)
    return {"elapsedSeconds": float(elapsed), "peakRssKiB": int(peak)}


class Runner:
    def __init__(self, output: Path, candidate_run: Path, timeout: int):
        self.output = output
        self.candidate_run = candidate_run
        self.console = candidate_run / "py311/bin/ladon"
        self.python = candidate_run / "py311/bin/python"
        self.runtime = candidate_run / "py311"
        self.timeout = timeout
        self.logs = output / "logs"
        self.results = output / "results"
        self.logs.mkdir()
        self.results.mkdir()
        self.records: list[dict[str, Any]] = []
        self.environment = os.environ.copy()
        for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "VIRTUAL_ENV", "PYTHONSTARTUP"):
            self.environment.pop(name, None)
        self.environment.update({
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LC_ALL": "C.UTF-8",
        })

    def timed(self, name: str, argv: list[str], *, cwd: Path, sandbox: bool = False) -> tuple[str, str, dict[str, Any]]:
        stdout_path = self.results / f"{name}.stdout"
        stderr_path = self.results / f"{name}.stderr"
        timing_path = self.logs / f"{name}.time"
        if stdout_path.exists() or stderr_path.exists() or timing_path.exists():
            raise RuntimeError(f"refusing to overwrite prior step outputs: {name}")
        command = ["/usr/bin/time", "-f", "%e\t%M", "-o", str(timing_path), *argv]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=self.environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            stdout_path.write_text(stdout, encoding="utf-8")
            stderr_path.write_text(stderr, encoding="utf-8")
            record = {
                "name": name, "command": argv, "cwd": str(cwd), "sandboxed": sandbox,
                "exitCode": "timeout", "timeoutSeconds": self.timeout,
                "wallSeconds": round(time.monotonic() - started, 6),
                "stdoutFile": str(stdout_path), "stderrFile": str(stderr_path),
                "stdoutBytes": len(stdout.encode("utf-8")), "stderrBytes": len(stderr.encode("utf-8")),
            }
            self.records.append(record)
            raise RuntimeError(f"step {name} exceeded {self.timeout} seconds; partial output preserved") from exc
        wall = round(time.monotonic() - started, 6)
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        metrics = parse_time(timing_path) if timing_path.is_file() else {}
        record = {
            "name": name,
            "command": argv,
            "cwd": str(cwd),
            "sandboxed": sandbox,
            "exitCode": completed.returncode,
            "wallSeconds": wall,
            **metrics,
            "stdoutFile": str(stdout_path),
            "stderrFile": str(stderr_path),
            "stdoutBytes": len(completed.stdout.encode("utf-8")),
            "stderrBytes": len(completed.stderr.encode("utf-8")),
        }
        self.records.append(record)
        (self.output / "commands.json").write_text(json.dumps(self.records, indent=2) + "\n")
        if record["stdoutBytes"] > 32768:
            raise RuntimeError(f"step {name} exceeded compact output limit")
        if completed.returncode != 0:
            raise RuntimeError(f"step {name} exited {completed.returncode}: {completed.stderr[-1200:]}")
        return completed.stdout, completed.stderr, record

    def sandbox_prefix(self, output: Path) -> list[str]:
        executable = shutil.which("bwrap")
        if not executable:
            raise RuntimeError("bwrap is required for detached offline view checks")
        config = (self.runtime / "pyvenv.cfg").read_text(encoding="utf-8")
        home = next((line.partition("=")[2].strip() for line in config.splitlines() if line.startswith("home =")), None)
        if not home:
            raise RuntimeError("candidate pyvenv.cfg has no runtime home")
        base = Path(home).resolve().parent
        if not base.is_dir():
            raise RuntimeError(f"candidate runtime base is missing: {base}")
        args = [executable, "--unshare-net"]
        system_paths = [path for path in (Path("/usr"), Path("/etc"), Path("/lib"), Path("/lib64")) if path.exists()]
        dirs = {Path("/home"), Path("/out"), *system_paths, self.runtime, base}
        for target in (self.runtime, base):
            dirs.update(target.parents)
            dirs.add(target)
        # Create only the mount-parent skeleton; sibling candidate/source trees remain absent.
        for directory in sorted(dirs, key=lambda item: (len(item.parts), str(item))):
            if directory == Path("/"):
                continue
            args.extend(["--dir", str(directory)])
        for system_path in system_paths:
            args.extend(["--ro-bind", str(system_path), str(system_path)])
        args.extend(["--ro-bind", str(base), str(base)])
        args.extend(["--ro-bind", str(self.runtime), str(self.runtime)])
        args.extend(["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"])
        args.extend(["--bind", str(output), "/out", "--chdir", "/out"])
        return args

    def isolated(self, name: str, command: list[str], *, output: Path) -> tuple[str, str, dict[str, Any]]:
        argv = self.sandbox_prefix(output) + ["--", *command]
        return self.timed(name, argv, cwd=output, sandbox=True)

    def view_pair(self, bundle_path: str, operation: str, section: str, output: Path, *, limit: int = 5,
                  target: str | None = None, cursor: str | None = None) -> dict[str, Any]:
        args = [str(self.console), "result", operation, bundle_path, "--section", section, "--limit", str(limit)]
        if target is not None:
            args.extend(["--target", target])
        if cursor is not None:
            args.extend(["--cursor", cursor])
        json_stdout, _, _ = self.isolated(f"{operation}-{section}-json-{len(self.records):03d}", args + ["--format", "json"], output=output)
        text_stdout, _, _ = self.isolated(f"{operation}-{section}-text-{len(self.records):03d}", args + ["--format", "text"], output=output)
        json_value = json.loads(json_stdout)
        text_value = parse_text_projection(text_stdout)
        if text_value != json_value:
            raise RuntimeError(f"text/JSON semantic parity failed for {operation}:{section}")
        page = json_value.get("pagination", {})
        return {
            "operation": operation,
            "section": section,
            "target": target,
            "limit": limit,
            "status": json_value.get("status"),
            "guideStatus": json_value.get("guideStatus"),
            "inputBinding": json_value.get("inputBinding"),
            "pagination": {
                "total": page.get("total"),
                "returned": page.get("returned"),
                "omitted": page.get("omitted"),
                "nextCursorPresent": bool(page.get("nextCursor")),
            },
            "jsonTextParity": True,
            "jsonDigest": "sha256:" + hashlib.sha256(canonical(json_value)).hexdigest(),
            "textDigest": "sha256:" + hashlib.sha256(canonical(text_value)).hexdigest(),
            "firstRow": (json_value.get("rows") or [None])[0],
        }


def bwrap_probe(runner: Runner, output: Path) -> dict[str, Any]:
    visible_paths = [
        str(ROOT),
        "/home/codex/projects/lean/matrix-factorization",
        str(runner.candidate_run / "candidate"),
    ]
    code = (
        "import importlib,json,os,pathlib; import ladon; from ladon.acceptance_network import observe_network_isolation; "
        f"network=observe_network_isolation({os.readlink('/proc/self/ns/net')!r}); "
        f"hidden={json.dumps(visible_paths)}; "
        "visible=[p for p in hidden if pathlib.Path(p).exists()]; "
        "print(json.dumps({'module':str(pathlib.Path(ladon.__file__).resolve()),'visibleForbiddenPaths':visible,'network':network})); "
        "sys_exit=bool(visible); raise SystemExit(1 if sys_exit else 0)"
    )
    stdout, _, record = runner.isolated("sandbox-isolation-probe", [str(runner.python), "-c", code], output=output)
    result = json.loads(stdout)
    package = Path(result["module"])
    if result["visibleForbiddenPaths"]:
        raise RuntimeError(f"forbidden source paths are visible in bwrap: {result['visibleForbiddenPaths']}")
    if runner.runtime not in package.parents:
        raise RuntimeError(f"runtime imported Ladon outside installed candidate package: {package}")
    return {**result, "networkNamespace": "--unshare-net", "probeCommand": record["command"]}


def summarize_archive(path: Path) -> dict[str, Any]:
    archive_hash = digest_path(path)
    with zipfile.ZipFile(path, "r") as stream:
        names = stream.namelist()
        raw_index = stream.read("bundle.json")
        index = json.loads(raw_index)
        info_bytes = sum(info.file_size for info in stream.infolist())
        payload_bytes = sum(row["bytes"] for row in index["inventory"])
        role_counts = Counter(row["role"] for row in index["inventory"])
        database_entry = next(row for row in index["inventory"] if row["role"] == "lineage-database")
        lineage_entry = next(row for row in index["inventory"] if row["role"] == "lineage")
        lineage_inputs = json.loads(stream.read(lineage_entry["path"]))
        selected = next(row for row in lineage_inputs["entries"] if row["id"] == LINEAGE_ENTRY_ID)
        if selected["database"] != str(FIELD_DB):
            raise RuntimeError("bundled lineage companion does not point to the selected fixture name")
        if SOURCE_DATABASE_TEXT.encode("utf-8") in stream.read("bundle.json"):
            raise RuntimeError("bundle index contains the original source database path")
        if SOURCE_DATABASE_TEXT.encode("utf-8") in b"".join(stream.read(name) for name in names if name != "bundle.json"):
            raise RuntimeError("bundle payload contains the original source database path")
        tex_entry = next(row for row in index["inventory"] if row["id"] == "exposition-tex")
        if stream.read(tex_entry["path"]) != TEX.read_bytes():
            raise RuntimeError("TeX attachment differs from the selected source bytes")
        if len([row for row in index["inventory"] if row["role"] == "artifact"]) != EXPECTED_ARTIFACTS:
            raise RuntimeError("bundle artifact inventory is not exactly the selected 89 artifacts")
        if role_counts != Counter({"manifest": 1, "artifact": 89, "guide": 1, "lineage": 1,
                                   "lineage-database": 1, "attachment": 1}):
            raise RuntimeError(f"unexpected bundle member roles: {role_counts}")
        if len(names) != len(index["inventory"]) + 1 or set(names) != {"bundle.json", *[row["path"] for row in index["inventory"]]}:
            raise RuntimeError("archive member list does not equal bundle index plus exact inventory")
        if database_entry["bytes"] != FIELD_DB.stat().st_size:
            raise RuntimeError("selected lineage database payload size disagrees with fixture")
    return {
        "archivePath": str(path),
        "archiveBytes": archive_hash["bytes"],
        "archiveSha256": archive_hash["sha256"],
        "archiveMembers": len(names),
        "inventoryEntries": len(index["inventory"]),
        "payloadExpandedBytes": payload_bytes,
        "archiveExpandedBytes": info_bytes,
        "bundleIndexBytes": len(raw_index),
        "roleCounts": dict(role_counts),
        "memberNames": names,
        "lineageDatabaseBytes": database_entry["bytes"],
        "selectedLineageEntryDatabase": selected["database"],
        "resultId": index.get("resultId"),
        "manifestRevision": index.get("revision"),
        "bundleIndexSha256": "sha256:" + hashlib.sha256(raw_index).hexdigest(),
    }


def write_report(output: Path, report: dict[str, Any]) -> Path:
    path = output / "field-run-report.json"
    path.write_bytes(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_run_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    candidate_run = args.candidate_run_directory.resolve(strict=True)
    output = args.output_directory.absolute()
    if output.exists():
        raise SystemExit(f"output directory already exists; preserve prior evidence: {output}")
    output.mkdir(parents=True)
    runner = Runner(output, candidate_run, args.timeout)
    report: dict[str, Any] = {
        "schema": "ladon-result-bundle-installed-field-run-v1",
        "status": "running",
        "candidateRunDirectory": str(candidate_run),
        "candidateCheckout": str(candidate_run / "candidate"),
        "installedConsole": str(runner.console),
        "sourceCheckoutHiddenDuringViews": str(ROOT),
        "leanProjectHiddenDuringViews": "/home/codex/projects/lean/matrix-factorization",
        "fieldFixture": str(FIELD_DB),
        "measured": False,
        "authorityLimitations": [
            "Producer-selected source freshness is not assessed.",
            "Bundle integrity and offline views do not authenticate the producer or run Lean checks.",
            "Only the first bounded page of each guide/dossier section is inspected.",
        ],
        "steps": runner.records,
    }
    try:
        if not runner.console.is_file() or not os.access(runner.console, os.X_OK):
            raise RuntimeError(f"installed candidate console is unavailable: {runner.console}")
        if not (candidate_run / "candidate").is_dir():
            raise RuntimeError(f"candidate checkout directory is missing: {candidate_run / 'candidate'}")
        lineage_data = json.loads(LINEAGE_INPUTS.read_text(encoding="utf-8"))
        artifact_paths = regular_artifacts()
        input_hashes_before = hash_inputs(artifact_paths, lineage_data)
        selection_path, lineage_path, derived_lineage = prepare_selection(output, artifact_paths, lineage_data)
        report["inputHashesBefore"] = input_hashes_before
        write_report(output, report)
        bundle = output / "result.zip"
        repeat = output / "result-repeat.zip"
        export_args = [str(runner.console), "result", "export", str(MANIFEST),
                       "--selection", str(selection_path), "--output", str(bundle), "--format", "json"]
        export_stdout, _, _ = runner.timed("export-first", export_args, cwd=output)
        export_result = json.loads(export_stdout)
        repeat_args = [str(runner.console), "result", "export", str(MANIFEST),
                       "--selection", str(selection_path), "--output", str(repeat), "--format", "json"]
        repeat_stdout, _, _ = runner.timed("export-repeat", repeat_args, cwd=output)
        repeat_result = json.loads(repeat_stdout)
        first_archive = summarize_archive(bundle)
        repeat_archive = summarize_archive(repeat)
        deterministic = (first_archive["archiveSha256"] == repeat_archive["archiveSha256"]
                         and bundle.read_bytes() == repeat.read_bytes())
        if not deterministic or export_result != repeat_result:
            raise RuntimeError("repeat export did not produce stable archive bytes and report")

        sandbox = bwrap_probe(runner, output)
        guide_views = []
        for section in GUIDE_SECTIONS:
            guide_views.append(runner.view_pair("/out/result.zip", "guide", section, output))
        dossier_views = []
        for section in DOSSIER_SECTIONS:
            dossier_views.append(runner.view_pair("/out/result.zip", "inspect", section, output))

        targeted_lineage = runner.view_pair("/out/result.zip", "guide", "lineage", output,
                                            limit=5, target=TARGET_ID)
        if targeted_lineage["pagination"]["total"] != 1:
            raise RuntimeError("selected target lineage view did not resolve to one target row")
        first_cursor = runner.view_pair("/out/result.zip", "inspect", "assumptions", output, limit=1)
        first_json_path = Path(next(record["stdoutFile"] for record in reversed(runner.records)
                                    if record["name"].startswith("inspect-assumptions-json-")))
        first_page = json.loads(first_json_path.read_text(encoding="utf-8"))
        cursor = first_page["pagination"]["nextCursor"]
        if not cursor:
            raise RuntimeError("selected assumptions population did not produce a continuation cursor")

        relocated_dir = output / "relocated"
        relocated_dir.mkdir()
        relocated_bundle = relocated_dir / "result.zip"
        before_relocation_hash = digest_path(bundle)
        bundle.rename(relocated_bundle)
        if digest_path(relocated_bundle) != before_relocation_hash:
            raise RuntimeError("archive bytes changed during relocation")
        continuation_json, _, _ = runner.isolated(
            "cursor-after-relocation-json",
            [str(runner.console), "result", "inspect", "/out/relocated/result.zip",
             "--section", "assumptions", "--limit", "1", "--cursor", cursor, "--format", "json"],
            output=output,
        )
        continuation_text, _, _ = runner.isolated(
            "cursor-after-relocation-text",
            [str(runner.console), "result", "inspect", "/out/relocated/result.zip",
             "--section", "assumptions", "--limit", "1", "--cursor", cursor, "--format", "text"],
            output=output,
        )
        continued = json.loads(continuation_json)
        if parse_text_projection(continuation_text) != continued:
            raise RuntimeError("cursor continuation text/JSON parity failed")
        if continued["inputBinding"] != first_page["inputBinding"] or continued["pagination"]["offset"] != 1:
            raise RuntimeError("continuation cursor did not survive archive relocation")

        extracted = output / "extracted"
        verify_stdout, _, _ = runner.isolated(
            "verify-and-extract",
            [str(runner.console), "result", "verify", "/out/relocated/result.zip",
             "--extract-to", "/out/extracted", "--format", "json"],
            output=output,
        )
        verify_result = json.loads(verify_stdout)
        if verify_result.get("integrity") != "passed" or verify_result.get("replay") != "not-run":
            raise RuntimeError("detached verification did not report integrity-only success")
        extracted_archive = summarize_directory(extracted)

        archive_directory_lineage = runner.view_pair("/out/relocated/result.zip", "guide", "lineage", output,
                                                      limit=5, target=TARGET_ID)
        extracted_directory_lineage = runner.view_pair("/out/extracted", "guide", "lineage", output,
                                                        limit=5, target=TARGET_ID)
        archive_directory_assumptions = runner.view_pair("/out/relocated/result.zip", "inspect", "assumptions", output,
                                                         limit=5, target=TARGET_ID)
        extracted_directory_assumptions = runner.view_pair("/out/extracted", "inspect", "assumptions", output,
                                                           limit=5, target=TARGET_ID)
        if (archive_directory_lineage["jsonDigest"] != extracted_directory_lineage["jsonDigest"]
                or archive_directory_assumptions["jsonDigest"] != extracted_directory_assumptions["jsonDigest"]):
            raise RuntimeError("extracted directory view differs from relocated archive view")

        input_hashes_after = hash_inputs(artifact_paths, lineage_data)
        if input_hashes_before != input_hashes_after:
            raise RuntimeError("one or more original selected inputs changed during the field run")
        generated_file_bytes = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
        report.update({
            "status": "completed",
            "measured": True,
            "selection": {
                "manifest": str(MANIFEST),
                "manifestRevision": json.loads(MANIFEST.read_text(encoding="utf-8"))["revision"],
                "canonicalArtifacts": len(artifact_paths),
                "canonicalArtifactBytes": sum(input_hashes_before[str(path)]["bytes"] for path in artifact_paths),
                "guide": str(GUIDE),
                "lineageCompanion": str(lineage_path),
                "lineageDatabase": str(FIELD_DB),
                "lineageEntryId": LINEAGE_ENTRY_ID,
                "lineageDatabaseId": DATABASE_ID,
                "texAttachment": str(TEX),
                "roleCounts": dict(Counter(entry["role"] for entry in json.loads(selection_path.read_text(encoding="utf-8"))["entries"])),
                "lineageCompanionDatabasePath": next(row for row in derived_lineage["entries"]
                                                     if row["id"] == LINEAGE_ENTRY_ID)["database"],
            },
            "inputHashesBefore": input_hashes_before,
            "inputHashesAfter": input_hashes_after,
            "inputHashesUnchanged": True,
            "bundle": {
                "initialArchive": first_archive,
                "repeatArchive": repeat_archive,
                "deterministicRepeat": deterministic,
                "exportReport": export_result,
                "repeatExportReport": repeat_result,
                "verificationReport": verify_result,
                "extractedDirectory": extracted_archive,
            },
            "sandbox": sandbox,
            "guideSections": guide_views,
            "dossierSections": dossier_views,
            "cursorRelocation": {
                "firstPage": first_page,
                "cursor": cursor,
                "continuedPage": continued,
                "archiveSha256Unchanged": before_relocation_hash["sha256"] == digest_path(relocated_bundle)["sha256"],
                "textJsonParity": True,
            },
            "directoryViewParity": {
                "guideLineageJsonDigest": extracted_directory_lineage["jsonDigest"],
                "dossierAssumptionsJsonDigest": extracted_directory_assumptions["jsonDigest"],
                "archiveDirectoryParity": True,
            },
            "generatedOutputBytesBeforeReport": generated_file_bytes,
            "steps": runner.records,
        })
        write_report(output, report)
        print(json.dumps({
            "status": report["status"],
            "outputDirectory": str(output),
            "report": str(output / "field-run-report.json"),
            "archiveBytes": first_archive["archiveBytes"],
            "expandedBytes": first_archive["archiveExpandedBytes"],
            "deterministicRepeat": deterministic,
            "guideSections": len(guide_views),
            "dossierSections": len(dossier_views),
            "timedCommands": len(runner.records),
        }, sort_keys=True))
        return 0
    except BaseException as exc:
        report.update({
            "status": "failed",
            "failure": f"{type(exc).__name__}: {exc}",
            "steps": runner.records,
            "preservedFailureOutputs": True,
        })
        try:
            lineage_data = json.loads(LINEAGE_INPUTS.read_text(encoding="utf-8"))
            artifact_paths = regular_artifacts()
            report["inputHashesAfterFailure"] = hash_inputs(artifact_paths, lineage_data)
        except BaseException as hash_exc:
            report["inputHashFailure"] = f"{type(hash_exc).__name__}: {hash_exc}"
        write_report(output, report)
        print(json.dumps({"status": "failed", "report": str(output / "field-run-report.json"),
                          "failure": report["failure"]}, sort_keys=True), file=sys.stderr)
        return 1


def summarize_directory(root: Path) -> dict[str, Any]:
    index_path = root / "bundle.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    files = sorted(path for path in root.rglob("*") if path.is_file())
    declared = {"bundle.json", *(row["path"] for row in index["inventory"])}
    actual = {path.relative_to(root).as_posix() for path in files}
    if actual != declared:
        raise RuntimeError("extracted directory does not contain exactly its bundle inventory")
    return {
        "files": len(files),
        "expandedBytes": sum(path.stat().st_size for path in files),
        "bundleIndexDigest": "sha256:" + hashlib.sha256(index_path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
