"""Scratch red acceptance tests for the first source-bound application probe."""
from __future__ import annotations

import copy
import json
import sqlite3
import time
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_application_probes/context.json'
TEMPLATE = {
    "familyId": "regularity-boundary",
    "version": "regularity-boundary-v1",
    "direction": "right-to-left",
    "kind": "counterexample",
}


def fixture():
    context = json.loads(FIXTURE.read_text())
    artifacts = context["artifacts"]
    sides = []
    for index in (0, 1):
        contract = next(a for a in artifacts
                        if a['artifactKind'] == 'proofir.contract'
                        and a['payload']['contractId'] == f'contract:reading-{index}')
        correspondence = next(a for a in artifacts
            if a['artifactKind'] == 'proofir.correspondence'
            and a['payload']['interpretationRef']['localId'] == f'reading-{index}')
        sides.append({
            'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                            'localId': contract['payload']['contractId']},
            'correspondenceRef': {'artifactRef': correspondence['artifactId'],
                                  'kind': 'correspondence',
                                  'localId': correspondence['payload']['correspondenceId']},
        })
    return {'context': context, 'sides': sides}


def api():
    from ladon.proof_contract_probe_artifacts import application_probe_artifact
    from ladon.proof_contract_probes import (
        application_probe_profile,
        check_application_probe,
        plan_application_probe,
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
    data = fixture()
    left, right = data["sides"]
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
    request = {"repoRoot": ".",
               "context": data["context"], "left": data["sides"][0],
               "right": data["sides"][1], "template": TEMPLATE,
               "deadlineMonotonic": time.monotonic() + 30, "limits": {}}
    for family in ("constant-uniformity", "witness-dependence", "restricted-domain", "inequality-direction"):
        unsupported = {**request, "template": {**TEMPLATE, "familyId": family,
                                                   "version": family + "-v1"}}
        result = planner(unsupported)
        assert result["status"] == "unsupported"
        assert result.get("checkRunRefs", []) == []
    for template in ({**TEMPLATE, "familyId": "unknown"},
                     {**TEMPLATE, "version": "regularity-boundary-v9"},
                     {**TEMPLATE, "kind": "equivalence"},
                     {**TEMPLATE, "direction": "backwards"}):
        assert planner({**request, "template": template})['status'] == 'rejected' 


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
    result = planner(request)
    assert result['status'] in {'rejected', 'incomplete'}
    assert not Path(request["repoRoot"]).exists()
    assert checker(request, "malformed", {"probe": "by assumption"})['status'] == 'rejected' 


def test_sqlite_projects_probes_stage_and_keeps_foreign_key_closure_on_disposable_db():
    """Root-owned integration test proposal: stage constraint, roundtrip and old-cache refusal."""
    builder, _, _, _ = api()
    from ladon.proofir_sqlite_v3 import (
        create_v3_schema,
        project_envelopes,
        validate_v3_database,
    )
    data = fixture()
    left, right = data['sides']
    analysis = builder(data['context'], left, right, TEMPLATE, analysis_id='analysis:sqlite')
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, [*data['context']['artifacts'], analysis])
    assert connection.execute('SELECT stage FROM proofir_v3_contract_analyses').fetchall() == [('probes',)]
    assert connection.execute('SELECT count(*) FROM proofir_v3_contract_analysis_inputs').fetchone() == (2,)
    validate_v3_database(connection)
    with pytest.raises(sqlite3.IntegrityError), connection:
        connection.execute("UPDATE proofir_v3_contract_analysis_inputs SET contract_local_id='foreign'")
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    plan = connection.execute('EXPLAIN QUERY PLAN SELECT owner_artifact_id FROM '
        'proofir_v3_contract_analysis_inputs WHERE contract_owner=? AND contract_kind=? AND contract_local_id=?',
        (left['contractRef']['artifactRef'], 'contract', left['contractRef']['localId'])).fetchall()
    assert 'idx_v3_contract_analysis_input' in str(plan)
    project_envelopes(connection, data['context']['artifacts'])
    assert connection.execute('SELECT count(*) FROM proofir_v3_contract_analyses').fetchone() == (0,)
    stale = sqlite3.connect(':memory:')
    stale.execute("CREATE TABLE proofir_v3_contract_analyses (stage TEXT CHECK(stage IN ('comparison','propagation','obligations')))")
    with pytest.raises(RuntimeError, match='disposable rebuild'):
        create_v3_schema(stale)
