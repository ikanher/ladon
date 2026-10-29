"""Closed historical Real records preserve source/evidence without fresh authority."""

import copy
import json
import sqlite3
from pathlib import Path

import pytest
from support.proof_contract_native import contract_artifact

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import detached_content_id, validate_envelope, validate_envelope_batch

FIXTURE = Path(__file__).parent / "fixtures/real_bound_native/recorded-admission.json"


def recorded():
    from ladon.real_bound_native_artifacts import real_bound_artifacts

    value = json.loads(FIXTURE.read_text())
    return real_bound_artifacts(value["plan"], value["check"], value["sourceText"].encode())


def rehash(value):
    value["artifactId"] = detached_content_id(value)
    return value


def test_real_native_round_trip_is_recorded_and_preserves_typed_scope():
    artifacts = recorded()
    validate_envelope_batch(artifacts)
    contract = artifacts[-1]
    record = contract["payload"]["record"]
    assert record["profileId"] == "real-bound-v1"
    assert record["loss"] == 0
    assert record["admission"]["state"] == "recorded-checked"
    assert contract["payload"]["provenance"]["checkerAuthority"] == "none"
    assert len(contract["payload"]["checkRunRefs"]) == 2
    assert all("typeRef" in binder for binder in record["telescope"])
    assert validate_envelope(contract).to_dict() == contract


@pytest.mark.parametrize("field,value", [("profileId", "real-bound-v999"),
                                        ("loss", -1), ("unregisteredMeaning", True)])
def test_real_record_rejects_unknown_or_malformed_meaning(field, value):
    artifact = recorded()[-1]
    artifact["payload"]["record"][field] = value
    with pytest.raises(ValueError):
        validate_envelope(rehash(artifact))


def test_missing_scalar_evidence_owner_rejects_batch():
    artifacts = recorded()
    with pytest.raises(ValueError):
        validate_envelope_batch([artifacts[0], artifacts[1], artifacts[-1]])


def test_substituted_check_cannot_satisfy_both_obligations():
    artifacts = recorded()
    contract = copy.deepcopy(artifacts[-1])
    refs = contract["payload"]["checkRunRefs"]
    refs[1] = copy.deepcopy(refs[0])
    contract["payload"]["record"]["admission"]["scalarCheckRef"] = copy.deepcopy(refs[0])
    with pytest.raises(ValueError):
        validate_envelope_batch([*artifacts[:-1], rehash(contract)])


def test_record_cannot_claim_live_checker_authority():
    artifact = recorded()[-1]
    artifact["payload"]["provenance"]["checkerAuthority"] = "lean-worker"
    with pytest.raises(ValueError):
        validate_envelope(rehash(artifact))


def test_real_record_projects_into_existing_disposable_tables():
    artifacts = recorded()
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, artifacts)
    validate_v3_database(connection)
    row = connection.execute("SELECT record_json,provenance_json FROM proofir_v3_contracts").fetchone()
    assert json.loads(row[0]) == artifacts[-1]["payload"]["record"]
    assert json.loads(row[1])["checkerAuthority"] == "none"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_historical_nat_artifact_identity_is_unchanged():
    artifact = contract_artifact()
    assert validate_envelope(artifact).to_dict() == artifact
    assert detached_content_id(artifact) == artifact["artifactId"]


def test_legacy_comparison_rejects_real_profile():
    from ladon.proof_contract_artifacts import comparison_artifact

    artifact = recorded()[-1]
    with pytest.raises(ValueError):
        comparison_artifact(artifact, artifact, analysis_id="unsupported:real")


def test_wrong_check_operation_cannot_be_relabelled_by_reference():
    artifacts = recorded()
    check = copy.deepcopy(artifacts[2])
    check["payload"]["operation"] = "unrelated-check"
    rehash(check)
    contract = copy.deepcopy(artifacts[-1])
    contract["payload"]["checkRunRefs"][1]["artifactRef"] = check["artifactId"]
    contract["payload"]["record"]["admission"]["scalarCheckRef"]["artifactRef"] = check["artifactId"]
    with pytest.raises(ValueError):
        validate_envelope_batch([artifacts[0], artifacts[1], check, rehash(contract)])


def test_constant_permissions_cannot_reach_later_inputs():
    artifact = recorded()[-1]
    record = artifact["payload"]["record"]
    record["constant"]["permittedBinderIds"].append(record["roles"]["function"])
    with pytest.raises(ValueError):
        validate_envelope(rehash(artifact))


def test_source_bytes_are_required_for_exact_native_anchor():
    from ladon.real_bound_native_artifacts import real_bound_artifacts

    value = json.loads(FIXTURE.read_text())
    with pytest.raises(ValueError, match="source|digest"):
        real_bound_artifacts(value["plan"], value["check"], b"def unrelated := True")


def test_missing_scalar_receipt_cannot_become_recorded_evidence():
    from ladon.real_bound_native_artifacts import real_bound_artifacts

    value = json.loads(FIXTURE.read_text())
    value["check"]["result"]["checks"].pop()
    with pytest.raises(ValueError, match="check|evidence|scalar"):
        real_bound_artifacts(value["plan"], value["check"], value["sourceText"].encode())
