"""Prose feature annotations remain attributed and source-bound before matching."""

import hashlib
from copy import deepcopy

import pytest
from support.proof_contract_native import contract_record
from support.proofir_v3_native import ENVIRONMENT

from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_v3 import validate_envelope_batch


def prose_inputs(tmp_path):
    quote = "For each natural u there is a constant c depending only on u; c is positive."
    (tmp_path / "claim.txt").write_text(quote)
    interpretation = {
        "id": "reading:positive", "source": {
            "path": "claim.txt", "startLine": 1, "endLine": 1,
            "quote": quote, "sha256": hashlib.sha256(quote.encode()).hexdigest(),
        },
        "formula": {"tag": "forall", "binder": {"id": "u", "name": "u", "domain": "Nat"},
                    "body": {"tag": "exists", "binder": {"id": "c", "name": "c", "domain": "Nat"},
                             "body": {"tag": "lt", "left": {"tag": "const", "name": "0"},
                                      "right": {"tag": "var", "id": "c"}}}},
        "symbols": {},
    }
    record = contract_record()
    record["telescope"].append({"binderId": "c", "typeId": "Nat", "quantifier": "exists"})
    record["features"]["constantDependencies"]["binderId"] = "c"
    record["features"]["witnessDependencies"] = [
        {"binderId": "c", "state": "known", "allowedBinderIds": ["u"], "reason": None},
    ]
    # Regularity is deliberately unsupported by this passage; a source author
    # cannot promote an unrelated estimate annotation through successful JSON.
    record["features"]["regularity"] = {
        "state": "unknown", "scaleId": "scale:N", "offset": None,
        "reason": "the passage gives no indexed estimate",
    }
    origins = {"regularity": ["/formula"], "constantDependencies": ["/formula/body/binder"],
               "witnessDependencies": ["/formula/body/binder"]}
    return interpretation, record, origins


def produce(tmp_path, interpretation, record, origins, *, alternative_id="reading:a"):
    return produce_prose_contract(
        tmp_path, interpretation, record, origins,
        alternative_id=alternative_id, environment_ref=ENVIRONMENT,
    )


def test_prose_annotation_has_no_extraction_or_fidelity_authority(tmp_path):
    value = produce(tmp_path, *prose_inputs(tmp_path))
    assert value["channel"] == "prose"
    assert value["status"] == "authored"
    assert value["fidelity"] == "attributed-unreviewed"
    assert value["phase"] == "pre-match"
    assert value["contract"]["features"]["regularity"]["state"] == "unknown"
    assert value["coverage"]["providers"] == "not-extracted"
    assert value["snapshotId"].startswith("sha256:")
    validate_envelope_batch(value["artifacts"])


def test_alternative_readings_are_distinct_immutable_snapshots(tmp_path):
    inputs = prose_inputs(tmp_path)
    first = produce(tmp_path, *inputs)
    second = produce(tmp_path, *inputs, alternative_id="reading:b")
    assert first["snapshotId"] != second["snapshotId"]
    inputs[1]["features"]["constantDependencies"]["allowedBinderIds"] = []
    assert first["contract"]["features"]["constantDependencies"]["allowedBinderIds"] == ["u"]


def test_prose_production_rejects_stale_source_before_publication(tmp_path):
    inputs = prose_inputs(tmp_path)
    (tmp_path / "claim.txt").write_text("changed original")
    with pytest.raises(ValueError, match="stale|digest|quote"):
        produce(tmp_path, *inputs)


def test_prose_feature_origins_must_resolve_into_the_original_interpretation(tmp_path):
    interpretation, record, origins = prose_inputs(tmp_path)
    forged = deepcopy(origins)
    forged["constantDependencies"] = ["/formalCounterpart/assumptions"]
    with pytest.raises(ValueError, match="origin|pointer"):
        produce(tmp_path, interpretation, record, forged)
