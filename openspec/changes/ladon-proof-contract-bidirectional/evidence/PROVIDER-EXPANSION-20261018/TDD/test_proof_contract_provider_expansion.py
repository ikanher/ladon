"""Pure red contract tests for native obligation provider expansion.

The tests use the real in-repository planner fixture and artifact builders, but
never claim that fixture data is an observed Lean application or proof slice.
The new public module is imported dynamically so absence is an ordinary red.
"""
from __future__ import annotations

import copy
import importlib
import time

import pytest
from support.proof_contract_obligation_planner import repeated_and_case, request_kwargs
from test_proof_contract_obligation_bundles import _request
from test_proof_contract_obligation_check_resources import (
    _mock_native_validation,
    _workflow_request,
)

from ladon.proof_contract_obligation_artifacts import obligations_artifact
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest


def _api():
    return importlib.import_module("ladon.proof_contract_provider_expansion")


def _native(case="shared"):
    if case == "shared":
        fixture, plan_request = _request()
    else:
        fixture = repeated_and_case()
        plan_request = ContractObligationPlanRequest(**request_kwargs(fixture))
    analysis = obligations_artifact(plan_request, analysis_id="analysis:provider-red")
    context = {"artifacts": [plan_request.derivation_artifact,
                              *plan_request.contract_artifacts]}
    result = analysis["payload"]["result"]
    route = result["routeComparisons"][0]
    demand = next(row for row in route["obligationBundle"]["demands"]
                  if row["status"] == "requires-source-check")
    requirement = next(row for row in route["backwardRequirements"]
                       if row["parentWitnessRef"] == demand["witnessRef"])
    return fixture, plan_request, analysis, context, route, demand, requirement


def _limits():
    return {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
            "max_rss_bytes": 12 * 1024**3}


@pytest.mark.parametrize("candidate", [None, [], {}, {"unexpected": True}])
def test_malformed_closed_request_rejects_without_observation(candidate):
    module = _api()
    result = module.expand_obligation_provider(candidate)
    assert result["status"] == "rejected"
    assert result.get("providerSnapshot") is None
    assert result.get("slice") is None


@pytest.mark.parametrize("mutation", ["cycle", "oversize", "expired"])
def test_cyclic_oversized_or_expired_provider_request_stops_before_observation(mutation):
    _, _, analysis, context, _, _, _ = _native()
    source_request = {"status": "not-dispatched", "obligation": "demand:x",
                      "routeId": "route:x", "sourceRef": "witness:x",
                      "contractRef": {"kind": "contract", "localId": "provider:x"},
                      "bounds": _limits(), "schema": "ladon-provider-slice-request-v1",
                      "binding": {}, "sourceSelection": {"availability": "unavailable"}}
    if mutation == "cycle":
        source_request["cycle"] = source_request
    elif mutation == "oversize":
        source_request["untrusted"] = "x" * (8 * 1024**2 + 1)
    outer = {"repoRoot": ".", "analysisArtifact": analysis, "context": context,
             "providerSliceRequest": source_request, "application": {}, "occurrence": {},
             "deadlineMonotonic": time.monotonic() + 30, "limits": _limits()}
    if mutation == "expired":
        outer["deadlineMonotonic"] = time.monotonic() - 1
    module = _api()
    result = module.expand_obligation_provider(outer)
    assert result["status"] in {"rejected", "incomplete"}
    assert result.get("providerSnapshot") is None
    assert result.get("slice") is None
    assert result.get("wholeMethodAuthority", "none") == "none"


def test_missing_provider_request_builder_retains_native_demand_and_anchor_availability():
    _, _, analysis, context, route, demand, requirement = _native()
    builder = _api().make_provider_slice_request
    request = builder(analysis, context, route, demand, requirement,
                      time.monotonic() + 30, _limits())

    _assert_request_identity(request, route, demand, requirement)
    _assert_native_binding(request, route, demand, analysis)
    _assert_source_availability(request)


def _assert_request_identity(request, route, demand, requirement):
    assert request["status"] == "not-dispatched"
    assert request["schema"] == "ladon-provider-slice-request-v1"
    assert request["routeId"] == route["routeId"]
    assert request["obligation"] == demand["demandId"]
    assert request["sourceRef"] == requirement["parentWitnessRef"]
    assert request["contractRef"] == requirement["forwardContractRef"]


def _assert_native_binding(request, route, demand, analysis):
    binding = request["binding"]
    assert binding["demand"] == demand
    assert binding["demandDigest"]
    assert binding["selectedIdentity"]["routeId"] == route["routeId"]
    assert binding["desiredReadingIdentity"] == analysis["payload"]["request"]["desiredReadingIdentity"]
    assert binding["desiredContractDigest"]
    assert len(binding["incomingOccurrences"]) == len(demand["incomingOccurrences"])


def _assert_source_availability(request):
    selection = request.get("sourceSelection")
    diagnostic = request.get("diagnostic")
    assert (selection is not None and selection.get("availability") == "available") or (
        diagnostic and diagnostic.get("code") == "source-anchor-unavailable")


def test_repeated_demand_builder_preserves_every_incoming_occurrence():
    _, _, analysis, context, route, demand, requirement = _native("repeated")
    request = _api().make_provider_slice_request(
        analysis, context, route, demand, requirement, time.monotonic() + 30, _limits())
    assert request["binding"]["demand"] == demand
    assert request["binding"]["incomingOccurrences"] == demand["incomingOccurrences"]


def test_tampered_source_anchor_or_native_demand_rejects_before_observation():
    _, _, analysis, context, route, demand, requirement = _native()
    built = _api().make_provider_slice_request(
        analysis, context, route, demand, requirement, time.monotonic() + 30, _limits())
    outer = {"repoRoot": ".", "analysisArtifact": analysis, "context": context,
             "providerSliceRequest": copy.deepcopy(built), "application": {}, "occurrence": {},
             "deadlineMonotonic": time.monotonic() + 30, "limits": _limits()}
    outer["providerSliceRequest"]["routeId"] = "sha256:" + "0" * 64
    module = _api()
    result = module.expand_obligation_provider(outer)
    assert result["status"] == "rejected"
    assert result.get("providerSnapshot") is None
    assert result.get("slice") is None


def test_missing_provider_in_public_workflow_is_enriched_without_fake_slice(tmp_path, monkeypatch):
    _, plan_request = _request()
    request = _workflow_request(tmp_path, plan_request)
    request["sourceBindings"]["providers"] = []
    _mock_native_validation(monkeypatch, request["analysisArtifact"])

    from ladon.proof_contract_obligation_checks import check_obligation_sources
    result = check_obligation_sources(request)
    assert result["providerSliceRequests"]
    for generated in result["providerSliceRequests"]:
        assert generated["status"] == "not-dispatched"
        assert generated["schema"] == "ladon-provider-slice-request-v1"
        assert generated["binding"]["desiredReadingIdentity"]
        assert generated["binding"]["incomingOccurrences"]
        assert (generated.get("sourceSelection") or generated.get("diagnostic"))
        assert not generated.get("slice")
        assert not generated.get("proofBody")
