"""Pure closed-boundary red tests for the native original-context bridge.

Only deliberately incomplete owner inputs are exercised. No source extraction,
Lean call, fabricated correspondence artifact, or positive observation appears
in this suite.
"""
from __future__ import annotations

import importlib
import time

import pytest


def _api():
    return importlib.import_module("ladon.proof_contract_context_bridge")


def _limits():
    return {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
            "max_rss_bytes": 12 * 1024**3}


def _request():
    return {"repoRoot": ".",
            "correspondenceRef": {"artifactRef": "sha256:" + "a" * 64,
                                  "kind": "correspondence", "localId": "correspondence:missing"},
            "context": {"artifacts": []},
            "deadlineMonotonic": time.monotonic() + 30,
            "limits": _limits()}


def _assert_no_authority_promotion(result):
    assert result["wholeMethodAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    assert result.get("sourceFidelity", "attributed-unreviewed") == "attributed-unreviewed"
    assert result.get("checkedGoals", []) == []


@pytest.mark.parametrize("bad", [None, [], {}, {"repoRoot": ".", "extra": True}])
def test_plan_rejects_nonclosed_request_without_authority(bad):
    result = _api().plan_context_bridge(bad)
    assert result["status"] == "rejected"
    _assert_no_authority_promotion(result)


@pytest.mark.parametrize("extra", [
    {"assumptions": ["h"], "goals": [], "sourceSelection": {}},
    {"interpretation": {"readingId": "reading:caller"}},
    {"objectMap": {"arbitrary": "mapping"}, "prefix": "caller-controlled"},
])
def test_plan_rejects_caller_authored_context_goals_or_owners(extra):
    request = _request()
    request.update(extra)
    result = _api().plan_context_bridge(request)
    assert result["status"] == "rejected"
    _assert_no_authority_promotion(result)


@pytest.mark.parametrize("mutation", ["cycle", "oversize", "expired", "bad-limits"])
def test_plan_rejects_boundedness_and_expiry_failures(mutation):
    request = _request()
    if mutation == "cycle":
        loop = {}
        loop["self"] = loop
        request["context"]["artifacts"].append(loop)
    elif mutation == "oversize":
        request["context"]["artifacts"].append({"untrusted": "x" * (8 * 1024**2 + 1)})
    elif mutation == "expired":
        request["deadlineMonotonic"] = time.monotonic() - 1
    else:
        request["limits"] = {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
                              "max_rss_bytes": 12 * 1024**3, "extra": True}
    result = _api().plan_context_bridge(request)
    assert result["status"] in {"rejected", "incomplete"}
    _assert_no_authority_promotion(result)


def test_unknown_native_correspondence_owner_fails_closed():
    result = _api().plan_context_bridge(_request())
    assert result["status"] == "rejected"
    assert result.get("planId") is None
    assert result.get("goals", []) == []
    _assert_no_authority_promotion(result)
