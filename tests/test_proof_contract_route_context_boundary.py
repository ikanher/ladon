"""Pure malformed-input red tests for the frozen route-context bridge API.

All requests here lack native owners. These tests exercise only fail-closed
input handling and never assert a positive plan, source observation, or Lean
receipt.
"""
from __future__ import annotations

import importlib
import time

import pytest


def _api():
    return importlib.import_module("ladon.proof_contract_route_context")


def _limits():
    return {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
            "max_rss_bytes": 12 * 1024**3}


def _request():
    return {
        "repoRoot": ".",
        "analysisArtifact": {},
        "context": {"artifacts": []},
        "selectedIdentity": {},
        "sourceBindings": {
            "parentSnapshot": {}, "providerSnapshot": {},
            "parentInterpretationRef": {
                "artifactRef": "sha256:" + "a" * 64,
                "kind": "interpretation", "localId": "reading:unowned"},
            "correspondenceRef": {
                "artifactRef": "sha256:" + "b" * 64,
                "kind": "correspondence", "localId": "correspondence:unowned"},
        },
        "deadlineMonotonic": time.monotonic() + 30,
        "limits": _limits(),
    }


def _assert_nonpromotion(result):
    assert result["wholeMethodAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    assert result.get("demandDischarged", False) is False
    assert result.get("checkedGoals", []) == []


@pytest.mark.parametrize("candidate", [None, [], {}, {"repoRoot": ".", "extra": True}])
def test_plan_requires_closed_top_level_request(candidate):
    result = _api().plan_route_context_bridge(candidate)
    assert result["status"] == "rejected"
    _assert_nonpromotion(result)


@pytest.mark.parametrize("extra", [
    {"formula": "True"},
    {"goals": [{"goal": "True"}]},
    {"assumptions": ["missing premise"]},
    {"objectMap": {"caller": "chosen map"}},
    {"prefix": "caller source"},
    {"planResult": {"routeComparisons": []}},
])
def test_plan_rejects_caller_authored_goals_context_or_native_replacements(extra):
    request = _request()
    request.update(extra)
    result = _api().plan_route_context_bridge(request)
    assert result["status"] == "rejected"
    _assert_nonpromotion(result)


@pytest.mark.parametrize("bindings", [
    {},
    {"parentSnapshot": {}, "providerSnapshot": {}, "parentInterpretationRef": {}},
    {"parentSnapshot": {}, "providerSnapshot": {}, "parentInterpretationRef": {},
     "correspondenceRef": {}, "extra": True},
])
def test_plan_rejects_malformed_source_bindings_before_owner_acceptance(bindings):
    request = _request()
    request["sourceBindings"] = bindings
    result = _api().plan_route_context_bridge(request)
    assert result["status"] == "rejected"
    _assert_nonpromotion(result)


@pytest.mark.parametrize("clock", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_monotonic_deadline_is_rejected(clock):
    request = _request()
    request["deadlineMonotonic"] = clock
    result = _api().plan_route_context_bridge(request)
    assert result["status"] == "rejected"
    _assert_nonpromotion(result)


@pytest.mark.parametrize("mutation", ["cycle", "oversize", "expired", "oversized-terms"])
def test_cycles_caps_and_expiry_fail_closed_before_support(mutation):
    request = _request()
    terms = {}
    if mutation == "cycle":
        cyclic = {}
        cyclic["self"] = cyclic
        request["context"]["artifacts"].append(cyclic)
    elif mutation == "oversize":
        request["analysisArtifact"] = {"untrusted": "x" * (8 * 1024**2 + 1)}
    elif mutation == "expired":
        request["deadlineMonotonic"] = time.monotonic() - 1
    else:
        terms["goal:source-reading"] = "x" * (8 * 1024**2 + 1)
    if mutation == "oversized-terms":
        result = _api().check_route_context_bridge(request, "sha256:" + "c" * 64, terms)
    else:
        result = _api().plan_route_context_bridge(request)
    assert result["status"] in {"rejected", "incomplete"}
    _assert_nonpromotion(result)


@pytest.mark.parametrize("plan_id", [None, "", {}, "sha256:" + "0" * 63])
def test_malformed_or_forged_checkpoint_never_promotes_support(plan_id):
    result = _api().check_route_context_bridge(_request(), plan_id, {})
    assert result["status"] in {"rejected", "incomplete", "unresolved"}
    assert result.get("planId") is None
    _assert_nonpromotion(result)


@pytest.mark.parametrize("terms", [
    None,
    [],
    {"unknown-goal": "by assumption"},
    {"source-requirement": "by assumption"},
    {"goal:premise:0": 42},
])
def test_malformed_terms_and_caller_source_goal_injection_do_not_check(terms):
    result = _api().check_route_context_bridge(
        _request(), "sha256:" + "d" * 64, terms)
    assert result["status"] in {"rejected", "incomplete", "unresolved"}
    _assert_nonpromotion(result)


def test_cyclic_terms_and_unowned_native_refs_fail_without_receipts():
    terms = {}
    terms["goal:premise:0"] = terms
    cyclic = _api().check_route_context_bridge(
        _request(), "sha256:" + "e" * 64, terms)
    assert cyclic["status"] in {"rejected", "incomplete", "unresolved"}
    assert cyclic.get("processReceipts", []) == []
    _assert_nonpromotion(cyclic)

    unknown_owner = _api().plan_route_context_bridge(_request())
    assert unknown_owner["status"] == "rejected"
    assert unknown_owner.get("planId") is None
    assert unknown_owner.get("processReceipts", []) == []
    _assert_nonpromotion(unknown_owner)
