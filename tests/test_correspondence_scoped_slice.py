"""Actual nested contexts and ordered providers, not dependency-name matches."""

from pathlib import Path

from ladon.proof_slice import extract_proof_slice
from ladon.proof_slice_validation import validate_slice_shape

ROOT = Path(__file__).parent / "fixtures/correspondence_m1"


def test_witness_context_is_opened_at_the_actual_application():
    result = extract_proof_slice(
        ROOT, "Scoped.lean", "Scoped", "Scoped.witness", "Scoped.bridge", scoped=True
    )
    assert result["complete"] is True
    validate_slice_shape(result)
    locals_by_name = {row["name"]: row for row in result["localContext"]}
    assert {"h", "k", "hk"} <= locals_by_name.keys()
    assert locals_by_name["k"]["isProp"] is False
    assert locals_by_name["hk"]["isProp"] is True
    provider = result["nodes"][0]["premises"][0]
    assert provider["providerStatus"] == "scoped-boundary"
    assert provider["providerObservation"]["localId"] == locals_by_name["hk"]["localId"]
    assert result["helper"]["profile"] == "scoped-identity-transport-v2"


def test_branch_occurrences_keep_distinct_context_and_instantiation():
    results = [extract_proof_slice(
        ROOT, "Scoped.lean", "Scoped", "Scoped.branches", "Scoped.bridge", i,
        scoped=True,
    ) for i in range(2)]
    for result in results:
        assert result["complete"] is True
        validate_slice_shape(result)
    assert {r["name"] for r in results[0]["localContext"]} == {"n", "m", "h", "hn"}
    assert {r["name"] for r in results[1]["localContext"]} == {"n", "m", "h", "hm"}
    assert results[0]["nodes"][0]["arguments"][0] != results[1]["nodes"][0]["arguments"][0]
    assert results[0]["sliceId"] != results[1]["sliceId"]


def test_ordered_and_providers_retain_local_have_values():
    result = extract_proof_slice(
        ROOT, "Scoped.lean", "Scoped", "Scoped.chain", "Scoped.combine", scoped=True
    )
    assert result["complete"] is True
    validate_slice_shape(result)
    premises = result["nodes"][0]["premises"]
    assert [p["occurrence"] for p in premises] == [2, 3]
    assert [p["providerStatus"] for p in premises] == ["scoped-local-value"] * 2
    for p in premises:
        assert p["providerObservation"]["value"] is not None
        assert p["providerObservation"]["closedType"]
        assert p["providerObservation"]["closedProof"]
