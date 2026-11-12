"""Prepare and run the registered four-case premise-provenance baseline."""
from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/codex/projects/ladon")
BASE = REPO / "openspec/changes/ladon-pitfall-baselines"
EVIDENCE = BASE / "evidence"
RUN = BASE / "evidence/qualification-runs/premise-provenance-v3-family-20261112b"
RUNTIME = Path("/tmp/ladon-pitfall-baseline-v3-20261112")
CASE_IDS = [
    "premise-provenance-01",
    "premise-provenance-02",
    "premise-provenance-03",
    "premise-provenance-04",
]
SLOTS = {
    "premise-provenance-01": "slot-4c19e2",
    "premise-provenance-02": "slot-7aa30d",
    "premise-provenance-03": "slot-e82b51",
    "premise-provenance-04": "slot-39d7a4",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    unexpected = [p.name for p in RUN.iterdir() if p.name != "run_family.py"]
    if unexpected:
        raise RuntimeError(f"new run directory is not empty: {unexpected}")
    cases = json.loads((EVIDENCE / "corpus/cases.json").read_text())["cases"]
    by_id = {case["caseId"]: case for case in cases}
    prep = json.loads((EVIDENCE / "corpus/reviews/r3-preparation.json").read_text())
    artifacts = {row["source"]: row for row in prep["artifacts"]}
    reg_path = EVIDENCE / "common-registration-v3.json"
    reg = json.loads(reg_path.read_text())
    registration_hash = digest(reg_path)
    profile = reg["profiles"]["premise-provenance"]
    launcher = BASE / "scripts/runtime_custody.py"
    result_rows = []
    (RUN / "run-summary.json").write_text(json.dumps({
        "schema": "ladon-premise-provenance-v3-family-run-v1",
        "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
        "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"],
        "adjudicationStatus": "not-started", "familyAcceptanceStatus": "running", "cases": []
    }, indent=2) + "\n")

    for case_id in CASE_IDS:
        case = by_id[case_id]
        slot = SLOTS[case_id]
        slot_root = RUN / slot
        slot_root.mkdir()
        workspace = slot_root / "case-workspace"
        started = time.monotonic()
        source_path = case["leanSource"].split("#", 1)[0]
        project_source = Path(*Path(source_path).parts[1:])
        selected_artifact = artifacts[source_path]
        copied = []
        for source in ("lean/Pitfalls.lean", source_path):
            row = artifacts[source]
            local_source = Path(*Path(source).parts[1:])
            source_file = EVIDENCE / "corpus" / source
            target = workspace / local_source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, target)
            artifact_rel = Path(*Path(row["artifact"]).parts[1:])
            artifact_source = EVIDENCE / "corpus" / row["artifact"]
            artifact_target = workspace / artifact_rel
            artifact_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(artifact_source, artifact_target)
            if digest(target) != row["sourceSha256"] or digest(artifact_target) != row["artifactSha256"]:
                raise RuntimeError(f"source/artifact digest mismatch: {source}")
            copied.extend([
                {"path": target.relative_to(workspace).as_posix(), "sha256": digest(target), "bytes": target.stat().st_size},
                {"path": artifact_target.relative_to(workspace).as_posix(), "sha256": digest(artifact_target), "bytes": artifact_target.stat().st_size},
            ])
        toolchain_file = EVIDENCE / "corpus/lean/lean-toolchain"
        shutil.copyfile(toolchain_file, workspace / "lean-toolchain")
        copied.append({"path": "lean-toolchain", "sha256": digest(workspace / "lean-toolchain"), "bytes": (workspace / "lean-toolchain").stat().st_size})
        copied.sort(key=lambda row: row["path"])
        prep_seconds = time.monotonic() - started
        (slot_root / "workspace-receipt.json").write_text(json.dumps({
            "schema": "ladon-pitfall-case-workspace-v1",
            "caseId": case_id,
            "slot": slot,
            "registrationId": reg["registrationId"],
            "registrationSha256": registration_hash,
            "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"],
            "excludedCountFromAcceptedCorpus": 23,
            "allowedFiles": [row["path"] for row in copied],
            "inputs": copied,
            "preparationSeconds": prep_seconds,
        }, indent=2) + "\n")
        result_rows.append({"caseId": case_id, "slot": slot, "sourcePath": source_path,
                            "module": ".".join(project_source.with_suffix("").parts),
                            "declaration": case["comparisonGoal"]["formalDeclaration"].split("#", 1)[1],
                            "selector": profile["caseCapabilityProbes"][case_id]["argvOverride"]["with"]
                            if case_id == "premise-provenance-03"
                            else profile["applicationBindings"][case_id],
                            "preparationSeconds": prep_seconds, "workspace": str(workspace)})

    isolation_script = EVIDENCE / "qualification-runs/premise-provenance-v3-batch-20261112/isolation_check.py"
    isolation_code = (
        'import sys,pathlib,runpy; a=sys.argv[1:]; r=pathlib.Path(a[0]).resolve(); '
        's=(r/"src").resolve(); sys.path.insert(0,str(s)); import ladon; '
        'assert pathlib.Path(ladon.__file__).resolve().is_relative_to(s); '
        'sys.argv=[a[1],a[0],a[2],a[3]]; runpy.run_path(a[1],run_name="__main__")'
    )
    isolation_command = [str(launcher), "exec", "--bundle", ".codex/state/pitfall-runtime/bundles/baseline-v3",
                         "--identity", reg["runtime"]["manifestIdentity"], "--root", str(RUNTIME),
                         "--profile", "python", "--", "-I", "-B", "-c", isolation_code,
                         str(RUNTIME), str(isolation_script), str(RUN), str(EVIDENCE / "corpus")]
    isolation_started = time.monotonic()
    isolation_result = subprocess.run(isolation_command, cwd=REPO, capture_output=True, text=True, timeout=600)
    isolation_wall = time.monotonic() - isolation_started
    isolation_receipt = {"schema": "ladon-pitfall-isolation-host-receipt-v1",
                         "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
                         "argv": isolation_command, "exitCode": isolation_result.returncode,
                         "elapsedSeconds": isolation_wall, "stdout": isolation_result.stdout,
                         "stderr": isolation_result.stderr, "timedOut": False,
                         "isolationScriptSha256": digest(isolation_script),
                         "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"]}
    (RUN / "isolation-host-receipt.json").write_text(json.dumps(isolation_receipt, indent=2) + "\n")
    if isolation_result.returncode != 0:
        raise RuntimeError("registered isolation qualification failed")
    isolation_report = json.loads((RUN / "isolation-check-v5.json").read_text())
    isolation_by_case = {row["caseId"]: row for row in isolation_report["results"]}

    for row in result_rows:
        case_id, slot = row["caseId"], row["slot"]
        out = RUN / slot / "proof-slice.json"
        template = profile["argvTemplates"][0]
        repl = {
            "<manifestIdentity>": reg["runtime"]["manifestIdentity"],
            "<reconstructed-baseline-v3-root>": str(RUNTIME),
            "<case-repo>": row["workspace"],
            "<leanSource-path>": str(Path(*Path(row["sourcePath"]).parts[1:])),
            "<module>": row["module"],
            "<qualified-subject>": row["declaration"],
            "<registered-case-selector>": row["selector"],
            "<external-run-directory>": str(RUN),
            "<case-slot>": slot,
        }
        argv = []
        for token in template:
            for old, new in repl.items():
                token = token.replace(old, new)
            if "<" in token or ">" in token:
                raise RuntimeError(f"unexpanded registered command token: {token}")
            argv.append(token)
        command = {"schema": "ladon-pitfall-exact-registered-command-v1",
                   "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
                   "caseId": case_id, "caseSlot": slot, "argv": argv, "cwd": str(REPO),
                   "custodyLauncher": {"path": str(launcher), "sha256": digest(launcher),
                                       "mode": format(stat.S_IMODE(launcher.stat().st_mode), "04o")},
                   "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"]}
        (RUN / slot / "command.json").write_text(json.dumps(command, indent=2) + "\n")
        command_started = time.monotonic()
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=600)
        command_seconds = time.monotonic() - command_started
        if not out.is_file():
            raise RuntimeError(f"missing registered output for {case_id}: {proc.stdout} {proc.stderr}")
        result = json.loads(out.read_text())
        host = {"schema": "ladon-pitfall-registered-probe-host-receipt-v1",
                "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
                "caseId": case_id, "caseSlot": slot, "argv": argv, "exitCode": proc.returncode,
                "elapsedSeconds": command_seconds, "stdout": proc.stdout, "stderr": proc.stderr,
                "timedOut": False, "outputPath": str(out), "outputExists": True,
                "custodyLauncher": command["custodyLauncher"],
                "runtimeManifestIdentity": command["runtimeManifestIdentity"]}
        (RUN / slot / "host-receipt.json").write_text(json.dumps(host, indent=2) + "\n")
        iso = isolation_by_case[case_id]
        isolated_seconds = sum(probe.get("elapsedSeconds", 0) for probe in iso["probes"])
        max_rss = max([probe.get("peakRssBytes") or 0 for probe in iso["probes"]] +
                      [rec.get("peak_rss_bytes") or 0 for rec in result.get("processReceipts", [])])
        row.update({"commandSeconds": command_seconds, "isolationProcessSeconds": isolated_seconds,
                    "measuredSecondsIncludingPreparation": row["preparationSeconds"] + command_seconds + isolated_seconds,
                    "isolationPassed": all(iso[key] for key in ("allExcludedModulesProvedUnavailable",
                                                                 "injectionImported", "injectionGuardRejected",
                                                                 "unrelatedFailureRejected", "workspaceRestored")),
                    "status": result.get("status"), "complete": result.get("complete"),
                    "output": str(out), "processReceipts": len(result.get("processReceipts", [])),
                    "peakRssBytes": max_rss})
        (RUN / "run-summary.json").write_text(json.dumps({
            "schema": "ladon-premise-provenance-v3-family-run-v1",
            "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
            "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"],
            "isolationWallSeconds": isolation_wall,
            "isolationReceipt": "isolation-host-receipt.json",
            "isolationReport": "isolation-check-v5.json",
            "cases": result_rows, "adjudicationStatus": "awaiting-independent-review",
            "familyAcceptanceStatus": "running",
        }, indent=2, ensure_ascii=False) + "\n")
        if command_seconds + row["preparationSeconds"] + isolated_seconds > 600:
            raise RuntimeError(f"per-case 600-second budget exceeded: {case_id}")
        if case_id == "premise-provenance-03":
            diagnostic = "constant not found; supply a qualified name: PitfallCases.PremiseProvenance03.h"
            failed = [rec for rec in result.get("processReceipts", []) if rec.get("returncode") != 0]
            if result.get("status") != "unavailable" or result.get("complete") is not False or not failed:
                raise RuntimeError("case 03 probe did not reach the registered unavailable terminal")
            if not any(diagnostic in rec.get("stdout", "") and not rec.get("stderr", "")
                       and not rec.get("timed_out") and not rec.get("memory_limited")
                       and not rec.get("output_limited") for rec in failed):
                raise RuntimeError("case 03 selector diagnostic/stream/resource contract mismatch")
        if case_id != "premise-provenance-03" and not (result.get("status") == "extracted" and result.get("complete")):
            raise RuntimeError(f"proof slice incomplete: {case_id}")

    summary = {"schema": "ladon-premise-provenance-v3-family-run-v1",
               "registrationId": reg["registrationId"], "registrationSha256": registration_hash,
               "runtimeManifestIdentity": reg["runtime"]["manifestIdentity"],
               "batchRunnerSha256": digest(Path(__file__)),
               "isolationWallSeconds": isolation_wall,
               "isolationReceipt": "isolation-host-receipt.json",
               "isolationReport": "isolation-check-v5.json",
               "cases": result_rows,
               "adjudicationStatus": "awaiting-independent-review",
               "familyAcceptanceStatus": "pending-independent-review"}
    (RUN / "run-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "complete-pending-independent-review", "run": str(RUN),
                      "registrationSha256": registration_hash,
                      "cases": [{k: row[k] for k in ("caseId", "status", "complete", "measuredSecondsIncludingPreparation", "peakRssBytes")}
                                for row in result_rows]}, indent=2))


if __name__ == "__main__":
    main()
