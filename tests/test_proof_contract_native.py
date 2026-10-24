"""Trust-boundary contracts for the new native mathematical summaries."""

import copy
import json
import sqlite3
import subprocess
import sys

import pytest
from support.proof_contract_native import contract_artifact

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import detached_content_id, validate_envelope, validate_envelope_batch


def rehash(value):
    value["artifactId"] = detached_content_id(value)
    return value


def test_contract_native_round_trip_is_detached_and_does_not_claim_proof():
    source = contract_artifact()
    checked = validate_envelope(source)
    assert checked.to_dict() == source
    source["payload"]["record"]["features"]["regularity"]["offset"] = 100
    assert checked.to_dict()["payload"]["record"]["features"]["regularity"]["offset"] == 3
    assert checked.to_dict()["payload"]["provenance"]["checkerAuthority"] == "none"


@pytest.mark.parametrize("field,value", [
    ("profileDigest", "sha256:" + "a" * 64),
    ("contractId", "unowned:contract"),
    ("sourceMapRefs", []),
    ("conclusionRef", {"kind": "statement", "localId": "wrong"}),
    ("assumptionRefs", []),
    ("unregisteredMeaning", "unchecked"),
])
def test_native_contract_rejects_forged_meaning_or_identity(field, value):
    source = contract_artifact()
    source["payload"][field] = value
    with pytest.raises(ValueError):
        validate_envelope(rehash(source))


def test_native_contract_cannot_promote_authored_features_to_checker_authority():
    source = contract_artifact()
    source["payload"]["provenance"]["checkerAuthority"] = "lean-worker"
    with pytest.raises(ValueError):
        validate_envelope(rehash(source))


def test_external_contract_sources_need_exact_batch_closure():
    source = contract_artifact()
    source["payload"]["sourceMapRefs"][0]["artifactRef"] = "sha256:" + "f" * 64
    rehash(source)
    validate_envelope(source)
    with pytest.raises(ValueError, match="external"):
        validate_envelope_batch([source])


def test_contract_projects_with_foreign_keys_and_indexed_subject_lookup():
    source = contract_artifact()
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [source])
    validate_v3_database(connection)
    row = connection.execute(
        "SELECT contract_id,profile_digest FROM proofir_v3_contracts WHERE owner_artifact_id=?",
        (source["artifactId"],),
    ).fetchone()
    assert row == ("contract:f", source["payload"]["profileDigest"])
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    plan = connection.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM proofir_v3_contracts "
        "WHERE statement_owner=? AND statement_kind=? AND statement_local_id=?",
        (source["artifactId"], "statement", "statement:f"),
    ).fetchall()
    assert any("INDEX" in row[3] for row in plan)


def test_obsolete_kind_inventory_requires_disposable_rebuild():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA user_version=9")
    with pytest.raises(RuntimeError, match="rebuild"):
        project_envelopes(connection, [contract_artifact()])


def test_ordinary_cli_validates_and_inspects_contract(tmp_path):
    source = contract_artifact()
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(source))
    for operation in ("validate", "inspect"):
        result = subprocess.run(
            [sys.executable, "-m", "ladon.entrypoint", "proofir", operation, str(path)],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        assert source["artifactId"] in json.dumps(output)


def test_contract_analysis_recomputes_comparison_instead_of_trusting_a_label():
    from ladon.proof_contract_artifacts import comparison_artifact

    left, right = contract_artifact(), contract_artifact()
    right["payload"]["record"]["features"]["regularity"]["offset"] = 5
    rehash(right)
    analysis = comparison_artifact(left, right, analysis_id="analysis:compare")
    batch = [left, right, analysis]
    validate_envelope_batch(batch)
    assert analysis["payload"]["result"]["relation"] == "dominates"
    forged = copy.deepcopy(analysis)
    forged["payload"]["result"]["relation"] = "equivalent"
    with pytest.raises(ValueError, match="compar"):
        validate_envelope_batch([left, right, rehash(forged)])
