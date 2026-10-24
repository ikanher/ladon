"""Scratch red acceptance tests for the first source-bound application probe."""
from __future__ import annotations

import copy
import json
import math
import sqlite3
from pathlib import Path

import pytest


ROOT = Path.cwd()
FIXTURE = ROOT / ".codex/state/proof-contract-analysis/application-probes/feasibility"
TEMPLATE = {
    "familyId": "regularity-boundary",
    "version": "regularity-boundary-v1",
    "direction": "right-to-left",
    "kind": "counterexample",
}


def fixture():
    request = json.loads((FIXTURE / "request.json").read_text())
    snapshots = json.loads((FIXTURE / "snapshots.json").read_text())
    artifacts = request["context"]["artifacts"]
    contracts = {a["payload"]["contractId"]: a for a in artifacts
                 if a["artifactKind"] == "proofir.contract"}
    correspondences = {a["payload"]["correspondenceId"]: a for a in artifacts
                       if a["artifactKind"] == "proofir.correspondence"}
    sides = []
    for snapshot in snapshots:
        interpretation_id = snapshot["interpretation"]["id"]
        contract = next(a for a in contracts.values()
                        if a["payload"]["record"]["conclusionId"] ==
                        snapshot["contract"]["conclusionId"])
        correspondence = next(
            a for a in correspondences.values()
            if a["payload"]["interpretationRef"]["localId"] == interpretation_id
        )
        sides.append({
            "contractRef": {"artifactRef": contract["artifactId"], "kind": "contract",
                            "localId": contract["payload"]["contractId"]},
            "correspondenceRef": {"artifactRef": correspondence["artifactId"],
                                  "kind": "correspondence",
                                  "localId": correspondence["payload"]["correspondenceId"]},
        })
    return {"context": {"artifacts": artifacts}, "sides": sides}


def api():
    from ladon.proof_contract_probe_artifacts import application_probe_artifact
    from ladon.proof_contract_probes import (
        application_probe_profile, check_application_probe, plan_application_probe,
    )
    return application_probe_artifact, application_probe_profile, plan_application_probe, check_application_probe


def test_profile_and_native_plan_are_closed_source_bound_probes():
    builder, profile, _, _ = api()
    fixture_data = fixture()
    left, right = fixture_data["sides"]
    catalog = profile()
    assert catalog["regularity-boundary"]["version"] == "regularity-boundary-v1"
    artifact = builder(fixture_data["context"], left, right, TEMPLATE,
                       analysis_id="analysis:red-regularity")
    payload = artifact["payload"]
    assert artifact["artifactKind"] == "proofir.contract-analysis"
    assert set(payload) == {"analysisId", "profileDigest", "stage", "contractRefs",
                            "correspondenceRefs", "template", "result", "checkRunRefs", "residuals"}
    assert payload["stage"] == "probes"
    assert payload["contractRefs"] == [left["contractRef"], right["contractRef"]]
    assert payload["correspondenceRefs"] == [left["correspondenceRef"], right["correspondenceRef"]]
    assert payload["checkRunRefs"] == []
    goals = payload["result"]["goals"]
    assert [goal["goalId"] for goal in goals] == ["formal-reading", "probe"]
    assert "↔" in goals[0]["goal"] and "∀" in goals[0]["goal"]
    assert "∧" in goals[1]["goal"] and "¬" in goals[1]["goal"]
    assert "Nat.add" in goals[0]["goal"] and "Nat.mul" in goals[0]["goal"]
    assert payload["result"].get("checkerAuthority", "none") == "none"
    assert payload["result"].get("wholeMethodAuthority", "none") == "none"


def test_native_builder_is_deterministic_and_rejects_rehashed_owner_and_summary_tampering():
    builder, _, _, _ = api()
    from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
    data = fixture(); left, right = data["sides"]
    one = builder(data["context"], left, right, TEMPLATE, analysis_id="analysis:stable")
    two = builder(data["context"], left, right, TEMPLATE, analysis_id="analysis:stable")
    assert one == two
    validate_envelope_batch([*data["context"]["artifacts"], one])

    forged = copy.deepcopy(one)
    forged["payload"]["result"]["goals"][1]["goal"] += " ∧ True"
    forged["artifactId"] = detached_content_id(forged)
    with pytest.raises((ValueError, TypeError)):
        validate_envelope_batch([*data["context"]["artifacts"], forged])

    crossed = copy.deepcopy(right)
    crossed["correspondenceRef"] = copy.deepcopy(left["correspondenceRef"])
    with pytest.raises((ValueError, TypeError)):
        builder(data["context"], left, crossed, TEMPLATE, analysis_id="analysis:crossed")

    changed_context = copy.deepcopy(data["context"])
    changed_contract = next(a for a in changed_context["artifacts"]
                            if a["artifactId"] == left["contractRef"]["artifactRef"])
    changed_contract["payload"]["record"]["features"]["regularity"]["offset"] = 77
    changed_contract["artifactId"] = detached_content_id(changed_contract)
    changed_left = copy.deepcopy(left)
    changed_left["contractRef"]["artifactRef"] = changed_contract["artifactId"]
    with pytest.raises((ValueError, TypeError)):
        builder(changed_context, changed_left, right, TEMPLATE, analysis_id="analysis:offset")

    bad_map_context = copy.deepcopy(data["context"])
    left_owner = next(a for a in bad_map_context["artifacts"]
                      if a["artifactId"] == left["contractRef"]["artifactRef"])
    other_map = next(a for a in bad_map_context["artifacts"]
                     if a["artifactKind"] == "proofir.source-map"
                     and a["artifactId"] != left_owner["payload"]["sourceMapRefs"][0]["artifactRef"])
    left_owner["payload"]["sourceMapRefs"] = [{
        "artifactRef": other_map["artifactId"], "kind": "source-map",
        "localId": other_map["payload"]["sourceMapId"],
    }]
    left_owner["artifactId"] = detached_content_id(left_owner)
    bad_left = copy.deepcopy(left)
    bad_left["contractRef"]["artifactRef"] = left_owner["artifactId"]
    with pytest.raises((ValueError, TypeError)):
        builder(bad_map_context, bad_left, right, TEMPLATE, analysis_id="analysis:wrong-map")


def test_other_registered_families_stay_unsupported_and_invalid_selectors_fail_closed():
    _, _, planner, _ = api()
    data = fixture()
    request = {"repoRoot": data["context"]["artifacts"][0]["payload"].get("repoRoot", str(ROOT)),
               "context": data["context"], "left": data["sides"][0],
               "right": data["sides"][1], "template": TEMPLATE,
               "deadlineMonotonic": math.inf, "limits": {}}
    for family in ("constant-uniformity", "witness-dependence", "restricted-domain", "inequality-direction"):
        unsupported = {**request, "template": {**TEMPLATE, "familyId": family,
                                                   "version": family + "-v1"}}
        result = planner(unsupported)
        assert result["status"] == "unsupported"
        assert result.get("checkRunRefs", []) == []
    for template in ({**TEMPLATE, "familyId": "unknown"},
                     {**TEMPLATE, "version": "regularity-boundary-v9"},
                     {**TEMPLATE, "kind": "equivalence"},
                     {**TEMPLATE, "direction": "left-to-right"}):
        with pytest.raises((ValueError, TypeError)):
            planner({**request, "template": template})


@pytest.mark.parametrize("mutation", [
    lambda r: {**r, "deadlineMonotonic": 0.0},
    lambda r: {**r, "deadlineMonotonic": float("nan")},
    lambda r: {**r, "formula": "True"},
    lambda r: {**r, "terms": {"formal-reading": "cached receipt"}},
    lambda r: {**r, "context": {"artifacts": [None] * 1000000}},
])
def test_public_planning_boundaries_fail_closed_before_work(mutation, tmp_path):
    _, _, planner, checker = api()
    data = fixture()
    request = {"repoRoot": str(tmp_path / "must-not-be-created"), "context": data["context"],
               "left": data["sides"][0], "right": data["sides"][1], "template": TEMPLATE,
               "deadlineMonotonic": 1e100, "limits": {}}
    request = mutation(request)
    with pytest.raises((ValueError, TypeError, TimeoutError)):
        planner(request)
    assert not Path(request["repoRoot"]).exists()
    with pytest.raises((ValueError, TypeError)):
        checker(request, "malformed", {"probe": "by assumption"})


def test_sqlite_projects_probes_stage_and_keeps_foreign_key_closure_on_disposable_db():
    """Root-owned integration test proposal: stage constraint, roundtrip and old-cache refusal."""
    builder, _, _, _ = api()
    from ladon.proof_contract_sqlite import project_analysis
    from ladon.proofir_sqlite_v3 import create_v3_schema
    data = fixture(); left, right = data["sides"]
    analysis = builder(data["context"], left, right, TEMPLATE, analysis_id="analysis:sqlite")
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_v3_schema(connection)
    # Minimal owner/input tables are supplied by the disposable projection fixture in integration.
    with pytest.raises(sqlite3.IntegrityError):
        project_analysis(connection, analysis)
    stale = sqlite3.connect(":memory:")
    stale.execute("CREATE TABLE proofir_v3_contract_analyses (stage TEXT CHECK(stage IN ('comparison','propagation','obligations')))")
    with pytest.raises(RuntimeError, match="disposable rebuild"):
        create_v3_schema(stale)
