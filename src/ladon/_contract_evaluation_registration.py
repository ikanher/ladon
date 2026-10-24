"""Registration, first-report, and adjudication schema validation."""
from __future__ import annotations

import math
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon._contract_evaluation_core import (
    MAX_FINDINGS,
    _counter,
    _digest,
    _fail,
    _file_rows,
    _identity,
    _keys,
    _loads,
    _nullable_int,
    _number,
    _opaque_identifier,
    _walk_bounds,
    canonical_json,
    sha256,
)

REG_SCHEMA = "ladon-contract-evaluation-registration-v1"
REPORT_SCHEMA = "ladon-contract-evaluation-first-report-v1"
RECEIPT_SCHEMA = "ladon-contract-evaluation-first-report-receipt-v1"
ADJ_SCHEMA = "ladon-contract-evaluation-adjudication-v1"
_STATUSES = ("complete", "timeout", "unsupported", "resource-stop", "checker-failure", "extraction-error")
_JUDGMENTS = ("supported", "refuted", "unsupported", "unresolved")
_CLASSES = {
    "A": {"mismatch", "valid", "unknown"},
    "B": {"matching", "discrepancy", "unsupported"},
}

def validate_registration(registration: Mapping[str, Any], artifact_root: str | os.PathLike[str]) -> dict:
    # The fixed population, file identities, and both runtime manifests share one digest boundary.
    r = dict(registration)
    _validate_registration_header(r)
    _validate_track_states(r["trackStates"])
    root = Path(artifact_root)
    global_files = _validate_case_population(r["cases"], root)
    _validate_runtime_manifests(r["runtimes"], root, global_files)
    return r


def _validate_registration_header(registration: dict) -> None:
    _keys(registration, {"schema", "registrationId", "runId", "protocolSha256", "trackStates", "cases", "runtimes", "registrationIdentity"}, where="registration")
    if registration["schema"] != REG_SCHEMA: _fail("invalid registration schema")
    for k in ("registrationId", "runId"):
        if not isinstance(registration[k], str) or not registration[k] or len(registration[k]) > 128: _fail(f"invalid {k}")
    _digest(registration["protocolSha256"], "protocol hash")
    _digest(registration["registrationIdentity"], "registration identity")
    if _identity(registration) != registration["registrationIdentity"]: _fail("registration identity digest mismatch")


def _validate_track_states(states: Any) -> None:
    expected_states = {"A": ("registered", 24), "B": ("registered", 12), "C": ("blocked", 0)}
    _keys(states, set(expected_states), where="trackStates")
    for track, (status, count) in expected_states.items():
        state = states[track]
        _keys(state, {"status", "admittedCases"}, where=f"trackStates.{track}")
        if state != {"status": status, "admittedCases": count}: _fail(f"invalid {track} track population; expected {count}")


def _validate_case_population(cases: Any, root: Path) -> dict[str, tuple[tuple[int, int], bool]]:
    if not isinstance(cases, list) or len(cases) != 36: _fail("registration case count must be 24 A and 12 B")
    ids = set()
    global_files: dict[str, tuple[tuple[int, int], bool]] = {}
    for c in cases:
        cid = _validate_case_row(c, root, global_files)
        if cid in ids: _fail("duplicate caseId")
        ids.add(cid)
    _validate_case_counts(cases)
    return global_files


def _validate_case_counts(cases: list[dict]) -> None:
    if sum(c["track"] == "A" for c in cases) != 24 or sum(c["track"] == "B" for c in cases) != 12: _fail("invalid case population")
    if sum(c["batch"] == "A-1" for c in cases) != 12 or sum(c["batch"] == "A-2" for c in cases) != 12: _fail("invalid A batch population")


def _validate_case_row(case: Any, root: Path, global_files: dict) -> str:
    _keys(case, {"caseId", "track", "batch", "files"}, where="case")
    cid, track = _opaque_identifier(case["caseId"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", "caseId"), case["track"]
    if track not in ("A", "B"): _fail("C cannot have admitted case rows")
    if case["batch"] not in (("A-1", "A-2") if track == "A" else ("B",)): _fail("invalid case batch")
    files = case["files"]
    _file_rows(files, root, roles={"input", "source"}, label=f"case {cid}", global_files=global_files)
    if {item["role"] for item in files} != {"input", "source"}: _fail("each case needs one input and one source")
    if len({item["role"] for item in files}) != len(files): _fail("duplicate case file role")
    return cid


def _validate_runtime_manifests(runtimes: Any, root: Path, global_files: dict) -> None:
    _keys(runtimes, {"baseline", "enhanced"}, where="runtimes")
    for arm, runtime in runtimes.items():
        _validate_runtime_manifest(arm, runtime, root, global_files)


def _validate_runtime_manifest(arm: str, runtime: Any, root: Path, global_files: dict) -> None:
    _keys(runtime, {"files", "toolchain", "dependencies"}, where=f"runtime {arm}")
    _file_rows(runtime["files"], root, label=f"runtime {arm}", global_files=global_files, allow_shared=True)
    _validate_toolchain(runtime["toolchain"])
    _validate_dependencies(runtime["dependencies"])


def _validate_toolchain(toolchain: Any) -> None:
    if not isinstance(toolchain, dict) or not toolchain: _fail("toolchain identity required")
    _walk_bounds(toolchain)
    valid_values = all(
        isinstance(value, (str, int, float, bool))
        and not (isinstance(value, float) and not math.isfinite(value))
        for value in toolchain.values()
    )
    if not valid_values: _fail("invalid toolchain identity")


def _validate_dependencies(dependencies: Any) -> None:
    if not isinstance(dependencies, list) or not dependencies or len(dependencies) > 128:
        _fail("invalid dependencies")
    names = set()
    for dependency in dependencies:
        _validate_dependency(dependency, names)


def _validate_dependency(dependency: Any, names: set[str]) -> None:
    _keys(dependency, {"name", "version", "sha256"}, where="dependency")
    name = dependency["name"]
    if not isinstance(name, str) or not name or name in names: _fail("invalid/duplicate dependency")
    names.add(name)
    version = dependency["version"]
    if not isinstance(version, str) or not version or len(version) > 256: _fail("invalid dependency version")
    _digest(dependency["sha256"], "dependency hash")


def _report_validate(report: dict, registration: dict) -> None:
    # First reports have a closed vocabulary and preserve the preregistered arm ordering.
    _keys(report, {"schema", "registrationIdentity", "registrationId", "runId", "arm", "runtimeIdentity", "wallTimeSeconds", "peakRssBytes", "cases"}, where="first report")
    if report["schema"] != REPORT_SCHEMA: _fail("invalid first report schema")
    for k in ("registrationIdentity", "registrationId", "runId"):
        if report[k] != registration[k]: _fail(f"first report {k} mismatch")
    if report["arm"] not in ("baseline", "enhanced"): _fail("invalid report arm")
    runtime_identity = sha256(canonical_json(registration["runtimes"][report["arm"]]))
    if report["runtimeIdentity"] != runtime_identity: _fail("runtime identity drift")
    _number(report["wallTimeSeconds"], "wallTimeSeconds")
    _nullable_int(report["peakRssBytes"], "peakRssBytes")
    rows = report["cases"]
    if not isinstance(rows, list) or len(rows) != 36: _fail("report case population mismatch")
    _validate_report_cases(rows, registration)


def _validate_report_cases(rows: list, registration: dict) -> None:
    expected = {item["caseId"]: item for item in registration["cases"]}
    expected_order = [item["caseId"] for item in registration["cases"]]
    if [row.get("caseId") if isinstance(row, dict) else None for row in rows] != expected_order:
        _fail("first report case order differs from frozen registration")
    seen = set()
    for row in rows:
        _validate_report_case(row, expected, seen)
    if seen != expected.keys(): _fail("missing report cases")


def _validate_report_case(row: Any, expected: dict, seen: set[str]) -> None:
    forbidden = {"truth", "label", "expectedClass", "answer", "verdict", "judgment", "adjudication", "key", "rationale"}
    required = {"caseId", "track", "batch", "observedClass", "status", "findingIds", "checkerAttempts", "failedProbes", "extractionErrors", "unsupportedSelections", "elapsedSeconds", "peakRssBytes"}
    _keys(row, required, where="first report case")
    if any(name.lower() in forbidden for name in row): _fail("label/answer field in first report")
    cid = _opaque_identifier(row["caseId"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", "report caseId")
    if cid in seen: _fail("duplicate report case")
    if cid not in expected: _fail("extra report case")
    seen.add(cid)
    _validate_report_case_identity(row, expected[cid])
    _validate_report_case_measurements(row)


def _validate_report_case_identity(row: dict, expected: dict) -> None:
    if row["track"] != expected["track"] or row["batch"] != expected["batch"]:
        _fail("report case identity mismatch")
    if row["status"] not in _STATUSES: _fail("invalid case status")
    allowed = _CLASSES[expected["track"]]
    observed = row["observedClass"]
    if observed is not None and (not isinstance(observed, str) or observed not in allowed):
        _fail("invalid observedClass")


def _validate_report_case_measurements(row: dict) -> None:
    ids = row["findingIds"]
    if not isinstance(ids, list) or len(ids) > MAX_FINDINGS:
        _fail("findingIds must be a bounded array")
    for item in ids:
        _opaque_identifier(item, r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", "findingId")
    if len(set(ids)) != len(ids): _fail("duplicate findingId")
    for name in ("checkerAttempts", "failedProbes", "extractionErrors", "unsupportedSelections"):
        _counter(row[name], name)
    _number(row["elapsedSeconds"], "elapsedSeconds")
    _nullable_int(row["peakRssBytes"], "peakRssBytes")


def freeze_first_report(report_bytes: bytes, registration: Mapping[str, Any], artifact_root: str | os.PathLike[str], receipt_path: str | os.PathLike[str]) -> dict:
    r = validate_registration(registration, artifact_root)
    report = _loads(report_bytes, "first report")
    _report_validate(report, r)
    digest = sha256(bytes(report_bytes))
    receipt = {"schema": RECEIPT_SCHEMA, "registrationIdentity": r["registrationIdentity"],
               "registrationId": r["registrationId"], "runId": r["runId"], "arm": report["arm"],
               "runtimeIdentity": report["runtimeIdentity"], "firstReportSha256": digest, "caseCount": 36}
    target = Path(receipt_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(receipt) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as f: f.write(payload); f.flush(); os.fsync(f.fileno())
    except BaseException:
        try: target.unlink()
        except OSError: pass
        raise
    return receipt


def _adjudication_map(adjudication: dict, report: dict, digest: str) -> dict:
    _keys(adjudication, {"schema", "registrationIdentity", "firstReportSha256", "cases"}, where="adjudication")
    if adjudication["schema"] != ADJ_SCHEMA or adjudication["registrationIdentity"] != report["registrationIdentity"] or adjudication["firstReportSha256"] != digest: _fail("adjudication digest/identity mismatch")
    if not isinstance(adjudication["cases"], list) or len(adjudication["cases"]) != len(report["cases"]): _fail("adjudication population mismatch")
    findings = {row["caseId"]: set(row["findingIds"]) for row in report["cases"]}
    out = _map_adjudication_cases(adjudication["cases"], findings)
    if set(out) != set(findings): _fail("missing adjudication case")
    return out


def _map_adjudication_cases(cases: list, findings: dict[str, set[str]]) -> dict:
    out = {}
    for item in cases:
        cid, case_judgment, finding_rows = _adjudication_case_fields(item)
        if cid not in findings or cid in out: _fail("adjudication duplicate/extra case")
        judgments = _map_finding_judgments(finding_rows, findings[cid])
        out[cid] = {"caseJudgment": case_judgment, "findings": judgments}
    return out


def _adjudication_case_fields(item: Any) -> tuple[str, str, list]:
    _keys(item, {"caseId", "caseJudgment", "findings"}, where="adjudication case")
    cid, case_judgment, finding_rows = item["caseId"], item["caseJudgment"], item["findings"]
    if not isinstance(cid, str): _fail("invalid adjudication caseId")
    if case_judgment not in _JUDGMENTS: _fail("invalid case judgment")
    if not isinstance(finding_rows, list): _fail("findings must be an array")
    return cid, case_judgment, finding_rows


def _map_finding_judgments(rows: list, expected: set[str]) -> dict[str, str]:
    judgments = {}
    for item in rows:
        one = _map_one_finding_judgment(item, expected)
        finding_id, judgment = next(iter(one.items()))
        if finding_id in judgments: _fail("duplicate adjudication finding")
        judgments[finding_id] = judgment
    if set(judgments) != expected: _fail("adjudication finding population mismatch")
    return judgments


def _map_one_finding_judgment(item: Any, expected: set[str]) -> dict[str, str]:
    _keys(item, {"findingId", "judgment"}, where="finding adjudication")
    finding_id, judgment = item["findingId"], item["judgment"]
    if not isinstance(finding_id, str) or finding_id not in expected:
        _fail("adjudication finding mismatch")
    if judgment not in _JUDGMENTS: _fail("invalid finding judgment")
    return {finding_id: judgment}


