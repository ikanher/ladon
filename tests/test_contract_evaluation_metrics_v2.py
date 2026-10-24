"""Frozen contract tests for task 2.3 report verification and aggregation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ladon.contract_evaluation_metrics import (
    aggregate_case_metrics,
    aggregate_evaluation,
    freeze_first_report,
    validate_registration,
)

REG_SCHEMA = "ladon-contract-evaluation-registration-v1"
REPORT_SCHEMA = "ladon-contract-evaluation-first-report-v1"


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _write(root: Path, rel: str, content: bytes) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return sha(content)


def _registration(root: Path) -> dict:
    cases = []
    for track, count in (("A", 24), ("B", 12)):
        for i in range(count):
            case_id = f"{track}-{i:02d}"
            in_path = f"inputs/{case_id}.json"
            src_path = f"sources/{case_id}.lean"
            in_hash = _write(root, in_path, (case_id + " input").encode())
            src_hash = _write(root, src_path, (case_id + " source").encode())
            cases.append({"caseId": case_id, "track": track,
                          "batch": ("A-1" if i < 12 else "A-2") if track == "A" else "B",
                          "files": [{"role": "input", "path": in_path, "sha256": in_hash},
                                    {"role": "source", "path": src_path, "sha256": src_hash}]})
    runtime_files = []
    for rel in ("runtime/main.py", "runtime/lean-toolchain", "runtime/pyproject.toml"):
        runtime_files.append({"path": rel, "sha256": _write(root, rel, rel.encode())})
    runtime = {"files": runtime_files,
               "toolchain": {"name": "lean", "version": "4.34.1", "sha256": sha(b"lean pin")},
               "dependencies": [{"name": "ladon", "version": "local", "sha256": sha(b"source tree")}]}
    reg = {"schema": REG_SCHEMA, "registrationId": "reg-synthetic-1", "runId": "run-synthetic-1",
           "protocolSha256": sha(b"protocol"),
           "trackStates": {"A": {"status": "registered", "admittedCases": 24},
                           "B": {"status": "registered", "admittedCases": 12},
                           "C": {"status": "blocked", "admittedCases": 0}},
           "cases": cases, "runtimes": {"baseline": runtime, "enhanced": runtime}}
    reg["registrationIdentity"] = sha(canonical(reg))
    return reg


def _report(reg: dict) -> dict:
    return {"schema": REPORT_SCHEMA, "registrationIdentity": reg["registrationIdentity"],
            "registrationId": reg["registrationId"], "runId": reg["runId"], "arm": "baseline",
            "runtimeIdentity": sha(canonical(reg["runtimes"]["baseline"])),
            "wallTimeSeconds": 0.0, "peakRssBytes": None,
            "cases": [{"caseId": c["caseId"], "track": c["track"], "batch": c["batch"],
                       "observedClass": None, "status": "complete", "findingIds": [],
                       "checkerAttempts": 0, "failedProbes": 0, "extractionErrors": 0,
                       "unsupportedSelections": 0, "elapsedSeconds": 0.0,
                       "peakRssBytes": None} for c in reg["cases"]]}


def test_registration_rejects_reduced_production_population(tmp_path):
    reg = _registration(tmp_path)
    reduced = dict(reg)
    reduced["cases"] = reg["cases"][:-1]
    reduced.pop("registrationIdentity")
    reduced["registrationIdentity"] = sha(canonical(reduced))
    with pytest.raises(ValueError, match="population|case count|24|12"):
        validate_registration(reduced, tmp_path)


def test_registration_rejects_changed_input_or_runtime_bytes(tmp_path):
    reg = _registration(tmp_path)
    input_path = tmp_path / next(f["path"] for f in reg["cases"][0]["files"] if f["role"] == "input")
    input_path.write_bytes(b"changed input")
    with pytest.raises(ValueError, match="input|hash|identity|drift"):
        validate_registration(reg, tmp_path)

    reg = _registration(tmp_path / "second")
    runtime_path = tmp_path / "second" / reg["runtimes"]["baseline"]["files"][0]["path"]
    runtime_path.write_bytes(b"changed runtime")
    with pytest.raises(ValueError, match="runtime|hash|identity|drift"):
        validate_registration(reg, tmp_path / "second")


def test_first_report_freeze_rejects_recursive_answer_fields(tmp_path):
    reg = _registration(tmp_path)
    validate_registration(reg, tmp_path)
    report = _report(reg)
    report["cases"][0]["truth"] = "mismatch"
    with pytest.raises(ValueError, match="unknown|field|label|truth|answer"):
        freeze_first_report(canonical(report), reg, tmp_path, tmp_path / "receipt.sha256")


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra"])
def test_first_report_freeze_requires_exact_case_bijection(tmp_path, mutation):
    reg = _registration(tmp_path)
    report = _report(reg)
    if mutation == "duplicate":
        report["cases"].append(dict(report["cases"][0]))
    elif mutation == "missing":
        report["cases"].pop()
    else:
        report["cases"].append({**report["cases"][0], "caseId": "EXTRA"})
    with pytest.raises(ValueError, match="duplicate|missing|extra|population|bijection|case"):
        freeze_first_report(canonical(report), reg, tmp_path, tmp_path / "receipt.sha256")


def test_first_report_freeze_rejects_runtime_identity_drift(tmp_path):
    reg = _registration(tmp_path)
    report = _report(reg)
    report["runtimeIdentity"] = sha(b"wrong runtime")
    with pytest.raises(ValueError, match="runtime|identity|drift"):
        freeze_first_report(canonical(report), reg, tmp_path, tmp_path / "receipt.sha256")


def test_first_report_receipt_is_no_overwrite(tmp_path):
    reg = _registration(tmp_path)
    report_bytes = canonical(_report(reg))
    receipt_path = tmp_path / "receipt.sha256"
    freeze_first_report(report_bytes, reg, tmp_path, receipt_path)
    before = receipt_path.read_bytes()
    with pytest.raises((FileExistsError, ValueError), match="exist|overwrite|receipt"):
        freeze_first_report(report_bytes, reg, tmp_path, receipt_path)
    assert receipt_path.read_bytes() == before


def test_aggregate_keeps_all_failure_states_and_counts_assertion_fp():
    rows = [
        {"caseId": "a", "track": "A", "status": "timeout", "checkerAttempts": 1,
         "failedProbes": 0, "extractionErrors": 0, "unsupportedSelections": 0,
         "elapsedSeconds": 2.0, "peakRssBytes": 10},
        {"caseId": "b", "track": "A", "status": "unsupported", "checkerAttempts": 0,
         "failedProbes": 0, "extractionErrors": 0, "unsupportedSelections": 1,
         "elapsedSeconds": 3.0, "peakRssBytes": None},
        {"caseId": "c", "track": "A", "status": "resource-stop", "checkerAttempts": 1,
         "failedProbes": 1, "extractionErrors": 0, "unsupportedSelections": 0,
         "elapsedSeconds": 4.0, "peakRssBytes": 30},
        {"caseId": "d", "track": "A", "status": "checker-failure", "checkerAttempts": 2,
         "failedProbes": 1, "extractionErrors": 0, "unsupportedSelections": 0,
         "elapsedSeconds": 5.0, "peakRssBytes": 20},
        {"caseId": "e", "track": "A", "status": "extraction-error", "checkerAttempts": 0,
         "failedProbes": 0, "extractionErrors": 1, "unsupportedSelections": 0,
         "elapsedSeconds": 6.0, "peakRssBytes": None},
        {"caseId": "f", "track": "A", "status": "complete", "observedClass": "valid",
         "findingIds": ["claim-1"], "checkerAttempts": 1, "failedProbes": 0, "extractionErrors": 0,
         "unsupportedSelections": 0, "elapsedSeconds": 7.0, "peakRssBytes": 40},
    ]
    adjudications = {"f": {"caseJudgment": "supported",
                           "findings": [{"findingId": "claim-1", "judgment": "refuted"}]}}
    key = {"a": {"expectedClass": "mismatch"}, "b": {"expectedClass": "unknown"},
           "c": {"expectedClass": "mismatch"}, "d": {"expectedClass": "mismatch"},
           "e": {"expectedClass": "mismatch"}, "f": {"expectedClass": "valid"}}
    out = aggregate_case_metrics(rows, adjudications, key)
    a = out["tracks"]["A"]
    assert a["n"] == a["denominator"] == 6
    assert a["falseAccusations"] == 1
    assert a["truePositives"] == 0 and a["missedFaults"] == 4
    assert a["statusCounts"] == {"timeout": 1, "unsupported": 1, "resource-stop": 1,
                                 "checker-failure": 1, "extraction-error": 1, "complete": 1}
    assert a["checkerAttempts"] == 5 and a["failedProbes"] == 2
    assert a["extractionErrors"] == 1 and a["unsupportedSelections"] == 1
    assert a["elapsedSeconds"] == 27.0 and a["peakRssBytes"] == 40


def test_zero_denominator_has_null_ratios():
    out = aggregate_case_metrics([], {}, {})
    assert out["tracks"]["C"]["n"] == 0
    assert out["tracks"]["C"]["falseAccusationRate"] is None


def test_aggregate_does_not_load_key_before_report_digest_and_adjudication_check(tmp_path):
    reg = _registration(tmp_path)
    report_bytes = canonical(_report(reg))
    report_digest = sha(report_bytes)
    receipt = {
        "schema": "ladon-contract-evaluation-first-report-receipt-v1",
        "registrationIdentity": reg["registrationIdentity"],
        "registrationId": reg["registrationId"],
        "runId": reg["runId"],
        "arm": "baseline",
        "runtimeIdentity": sha(canonical(reg["runtimes"]["baseline"])),
        "firstReportSha256": report_digest,
        "caseCount": 36,
    }
    adjudication = {
        "schema": "ladon-contract-evaluation-adjudication-v1",
        "registrationIdentity": reg["registrationIdentity"],
        "firstReportSha256": report_digest,
        "cases": [{"caseId": row["caseId"], "caseJudgment": "unresolved", "findings": []}
                  for row in _report(reg)["cases"]],
    }
    tampered_report = report_bytes + b" "

    class MustNotLoadKey:
        def __call__(self):
            raise AssertionError("key read before report receipt/adjudication validation")

    with pytest.raises(ValueError, match="digest|receipt"):
        aggregate_evaluation(reg, tampered_report, receipt, adjudication, MustNotLoadKey())
