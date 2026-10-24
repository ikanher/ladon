"""Digest-gated evaluation replay and custodian-key join."""
from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from ladon._contract_evaluation_core import (
    MAX_OUTPUT,
    _fail,
    _keys,
    _loads,
    _normalize_python_json,
    canonical_json,
    sha256,
)
from ladon._contract_evaluation_registration import (
    RECEIPT_SCHEMA,
    _adjudication_map,
    _report_validate,
    validate_registration,
)
from ladon._contract_evaluation_scoring import aggregate_case_metrics

_ARTIFACT_ROOT: ContextVar[Path | None] = ContextVar("contract_artifact_root", default=None)

def aggregate_evaluation(registration: Mapping[str, Any], report_bytes: bytes, receipt: Mapping[str, Any], adjudication: Mapping[str, Any], key_loader: Callable[[], Any]) -> dict:
    # Do not invoke the custodian loader until report, registration, and adjudication identities validate.
    report, digest = _validate_first_report_binding(report_bytes, receipt)
    artifact_root = _ARTIFACT_ROOT.get() or Path.cwd()
    r = validate_registration(registration, artifact_root)
    _report_validate(report, r)
    _validate_receipt_identity(receipt, r, report, digest)
    adj, adjmap = _validate_adjudication_binding(adjudication, report, digest)
    key_map = _load_and_validate_key(key_loader, r)
    result = aggregate_case_metrics(report["cases"], adjmap, key_map)
    return _bind_metrics(result, r, report, digest, adj)


def _validate_first_report_binding(report_bytes: bytes, receipt: Mapping[str, Any]) -> tuple[dict, str]:
    report = _loads(report_bytes, "first report")
    digest = sha256(bytes(report_bytes))
    _keys(dict(receipt), {"schema", "registrationIdentity", "registrationId", "runId", "arm", "runtimeIdentity", "firstReportSha256", "caseCount"}, where="receipt")
    if receipt["schema"] != RECEIPT_SCHEMA or receipt["firstReportSha256"] != digest:
        _fail("first report digest does not match receipt")
    return report, digest


def _validate_receipt_identity(receipt, registration, report, digest) -> None:
    expected = {
        "schema": RECEIPT_SCHEMA,
        "registrationIdentity": registration["registrationIdentity"],
        "registrationId": registration["registrationId"],
        "runId": registration["runId"],
        "arm": report["arm"],
        "runtimeIdentity": report["runtimeIdentity"],
        "firstReportSha256": digest,
        "caseCount": 36,
    }
    if dict(receipt) != expected: _fail("receipt identity mismatch")


def _validate_adjudication_binding(adjudication, report, digest) -> tuple[dict, dict]:
    parsed = _loads(canonical_json(dict(adjudication)), "adjudication")
    return parsed, _adjudication_map(parsed, report, digest)


def _load_and_validate_key(key_loader, registration) -> dict[str, dict[str, str]]:
    key = _normalize_key_value(key_loader())
    _keys(key, {"schema", "registrationIdentity", "cases"}, where="key")
    if key["schema"] != "ladon-contract-evaluation-key-v1": _fail("invalid key schema")
    if key["registrationIdentity"] != registration["registrationIdentity"]: _fail("key registration identity mismatch")
    if not isinstance(key["cases"], list) or len(key["cases"]) != 36: _fail("key population mismatch")
    return _key_case_map(key["cases"], registration)


def _normalize_key_value(value):
    if isinstance(value, (bytes, bytearray)): return _loads(value, "key")
    if not isinstance(value, Mapping): _fail("key must be an object")
    normalized = _normalize_python_json(value)
    try:
        return _loads(canonical_json(normalized), "key")
    except (TypeError, ValueError, OverflowError) as error:
        if isinstance(error, ValueError): raise
        _fail(f"key is not valid bounded JSON: {error}")


def _key_case_map(rows: list, registration: dict) -> dict[str, dict[str, str]]:
    km = {}
    case_tracks = {c["caseId"]: c["track"] for c in registration["cases"]}
    for row in rows:
        _keys(row, {"caseId", "expectedClass"}, where="key case")
        cid = row["caseId"]
        if not isinstance(cid, str) or cid in km: _fail("duplicate key case")
        expected_class = row["expectedClass"]
        if cid not in case_tracks: _fail("extra key case")
        allowed = {"A": {"mismatch", "valid", "unknown"}, "B": {"matching", "discrepancy", "unsupported"}}[case_tracks[cid]]
        if not isinstance(expected_class, str) or expected_class not in allowed: _fail("invalid key expectedClass")
        km[cid] = {"expectedClass": expected_class}
    if set(km) != {c["caseId"] for c in registration["cases"]}: _fail("key case population mismatch")
    return km


def _bind_metrics(result, registration, report, digest, adjudication):
    for metrics in result["tracks"].values():
        metrics["wallTimeSeconds"] = report["wallTimeSeconds"]
        if report["peakRssBytes"] is not None:
            metrics["peakRssBytes"] = max(metrics["peakRssBytes"] or 0, report["peakRssBytes"])
    result.update({
        "registrationIdentity": registration["registrationIdentity"],
        "registrationId": registration["registrationId"],
        "runId": registration["runId"],
        "arm": report["arm"],
        "runtimeIdentity": report["runtimeIdentity"],
        "firstReportSha256": digest,
        "adjudicationSha256": sha256(canonical_json(adjudication)),
        "wallTimeSeconds": report["wallTimeSeconds"],
        "peakRssBytes": report["peakRssBytes"],
    })
    if len(canonical_json(result)) > MAX_OUTPUT: _fail("aggregate output exceeds limit")
    return result


@contextmanager
def artifact_root_context(root: str | os.PathLike[str]):
    """Bind the explicit artifact root for API calls that lack a root parameter."""
    resolved = Path(root).resolve(strict=True)
    token = _ARTIFACT_ROOT.set(resolved)
    try:
        yield
    finally:
        _ARTIFACT_ROOT.reset(token)
