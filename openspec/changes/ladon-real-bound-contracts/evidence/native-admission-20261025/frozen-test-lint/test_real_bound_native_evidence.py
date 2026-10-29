"""Retained evidence must stay complete, scope-bound and explicitly historical."""

import copy
import json

import pytest
from test_real_bound_native_records import FIXTURE, recorded, rehash

from ladon.proofir_v3 import validate_envelope_batch


def test_relabelled_predicate_result_cannot_replace_scalar_goal():
    artifacts = recorded()
    substituted = copy.deepcopy(artifacts[1])
    substituted["payload"]["operation"] = "real-bound:scalar-semantics"
    rehash(substituted)
    contract = copy.deepcopy(artifacts[-1])
    replacement = {"artifactRef": substituted["artifactId"], "kind": "check-run",
                   "localId": substituted["payload"]["checkRunId"]}
    contract["payload"]["checkRunRefs"][1] = replacement
    contract["payload"]["record"]["admission"]["scalarCheckRef"] = replacement
    with pytest.raises(ValueError):
        validate_envelope_batch([artifacts[0], artifacts[1], substituted, rehash(contract)])


def test_limited_supervisor_receipt_cannot_project_a_success():
    from ladon.real_bound_native_artifacts import real_bound_artifacts

    fixture = json.loads(FIXTURE.read_text())
    fixture["check"]["processReceipt"]["memoryLimited"] = True
    with pytest.raises(ValueError):
        real_bound_artifacts(fixture["plan"], fixture["check"], fixture["sourceText"].encode())


def test_native_goal_guarantee_cannot_be_promoted_from_stored_observation():
    artifacts = recorded()
    promoted = copy.deepcopy(artifacts[2])
    promoted["payload"]["guarantee"]["scope"] = "none"
    rehash(promoted)
    contract = copy.deepcopy(artifacts[-1])
    contract["payload"]["checkRunRefs"][1]["artifactRef"] = promoted["artifactId"]
    contract["payload"]["record"]["admission"]["scalarCheckRef"]["artifactRef"] = promoted["artifactId"]
    with pytest.raises(ValueError):
        validate_envelope_batch([artifacts[0], artifacts[1], promoted, rehash(contract)])


def test_past_helper_identity_remains_readable_only_as_history():
    from ladon.real_bound_native_production import inspect_real_bound, recorded_production
    from ladon.proof_contract_source import snapshot_identity

    fixture = json.loads(FIXTURE.read_text())
    plan = fixture["plan"]
    plan["scalarSourceDigest"] = "sha256:" + "a" * 64
    plan["planId"] = snapshot_identity({k: v for k, v in plan.items() if k != "planId"})
    fixture["check"]["result"]["plan"] = copy.deepcopy(plan)
    terms = {r["goal"]["id"]: r["term"] for r in fixture["check"]["result"]["checks"]}
    production = recorded_production(plan, terms, fixture["check"], fixture["sourceText"])
    result = inspect_real_bound(production)
    assert result["status"] == "validated-historical"
    assert result["freshCheck"] is False
