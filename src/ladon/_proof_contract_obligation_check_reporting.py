"""Bounded immutable evidence publication and explicit source-check coverage."""
from __future__ import annotations

import hashlib
import json
import os
import time

from ._proof_contract_obligation_check_inputs import MAX_BYTES, MAX_MESSAGE
from .proof_contract_source_obligations import _plain

_SUMMARY = "ladon-obligation-source-run-v1"


def _finish(out, request, state, started):
    status = ("rejected" if state.get("inputFailure") else
        "incomplete" if state.get("stopped") else
        "rejected" if (state.get("validation") or {}).get("status") == "rejected" else "completed")
    summary = {"schema": _SUMMARY, "status": status,
        "sourceChecks": state["sourceChecks"], "providerSliceRequests": state["providerSliceRequests"],
        "routes": _routes(state), "wholeMethodAuthority": "none",
        "mathematicalFalsity": "not-established", "domainAndConclusionTransfer": "unfinished",
        "validation": state.get("validation"), "stopReason": state.get("stopReason"),
        "diagnostic": state.get("inputFailure"),
        "memoryReportBackRequired": bool(state.get("memoryReportBackRequired")),
        "resourceAccounting": {"elapsedSeconds": time.monotonic()-started,
                                "evidenceBytes": state["bytes"], "evidenceLimitBytes": MAX_BYTES,
                                "proofAttempts": state.get("attempts", 0),
                                "maxCheckAttempts": _reported_attempt_limit(request)}}
    return _publish_summary(out, state, summary)


def _reported_attempt_limit(request):
    value = request.get('maxCheckAttempts')
    return value if type(value) is int and 1 <= value <= 64 else None



def _publish_summary(out, state, summary):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    remaining = MAX_BYTES - state["bytes"]
    if _planned_input_size(summary) + 128 > remaining:
        _compact_summary(summary)
    if out is not None and state.get("outputOwned"):
        summary["summaryPath"] = "summary.json"
        encoded = _accounted_summary(summary, state["bytes"])
        if len(encoded) <= remaining:
            _write_exclusive(out / "summary.json", encoded)
        else:
            summary.pop("summaryPath")
            summary["status"] = "incomplete"
    return summary



def _accounted_summary(summary, before):
    encoded = _json_bytes(summary)
    for _ in range(4):
        summary['resourceAccounting']['evidenceBytes'] = before + len(encoded)
        encoded = _json_bytes(summary)
    return encoded



def _compact_summary(summary):
    summary['status'] = 'incomplete'
    summary['stopReason'] = summary.get('stopReason') or 'aggregate evidence budget exhausted saving coverage'
    summary['omittedCoverage'] = {
        key: len(summary[key]) for key in ('sourceChecks', 'providerSliceRequests', 'routes')}
    summary['omittedCoverage']['planInput'] = 'input.json'
    summary['omittedCoverage']['status'] = 'unresolved'
    for key in ('sourceChecks', 'providerSliceRequests', 'routes'):
        summary[key] = []



def _routes(state):
    out = []
    for coverage in state.get("routeCoverage", []):
        checks = [state["coverageIndex"][(coverage["routeId"], demand)]
                  for demand in coverage["sourceDemandIds"]]
        complete = (bool(checks) and coverage.get("bundleStatus") == "generated"
                    and not coverage.get("pending") and not coverage.get("residuals")
                    and all(row.get("status") == "checked-support" for row in checks))
        out.append({"routeId": coverage["routeId"],
            "describedRoute": coverage["describedRoute"],
            "sourceCheckStatus": "checked" if complete else "unresolved",
            "bundleStatus": coverage.get("bundleStatus"),
            "pending": coverage.get("pending", []),
            "residuals": coverage.get("residuals", [])})
    return out



def _reserve_summary(state):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    skeleton = {"sourceChecks": state["sourceChecks"],
        "routes": _routes(state), "providerSliceRequests": state["providerSliceRequests"],
        "wholeMethodAuthority": "none", "mathematicalFalsity": "not-established"}
    state["summaryReserve"] = min(MAX_BYTES, max(256 * 1024, 2 * _planned_input_size(skeleton)))



def _save_json(out, state, relative, value):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    ceiling = MAX_BYTES - state["summaryReserve"]
    if _planned_input_size(value) + 1 > ceiling - state["bytes"]:
        return False
    data = _json_bytes(value)
    if len(data) + state["bytes"] > ceiling:
        return False
    _write_exclusive(out / relative, data)
    state["files"].append(relative)
    state["bytes"] += len(data)
    return True



def _write_exclusive(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())



def _json_bytes(value):
    return (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")



def _require_fresh_output(path):
    if path.exists():
        raise ValueError("outputDir must name a fresh directory")



def _mkdir(path):
    path.mkdir(parents=True, exist_ok=False)



def _declaration(snapshot):
    selection = snapshot.get("selection", {})
    return selection.get("declaration")



def _contract_declaration(ref):
    return ref.get("localId") if isinstance(ref, dict) else None



def _slug(snapshot):
    return hashlib.sha256(_json_bytes(snapshot)).hexdigest()[:16]



def _bounded_validation_report(value):
    return {"status": str(value.get("status"))[:40],
            "diagnostic": {"code": str((value.get("diagnostic") or {}).get("code"))[:100],
                           "message": str((value.get("diagnostic") or {}).get("message"))[:MAX_MESSAGE]}}
