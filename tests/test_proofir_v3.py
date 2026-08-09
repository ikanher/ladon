from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from support.proofir_v3_native import native_artifacts

from ladon import proofir_v3
from ladon.proofir_v3 import (
    MAX_COLLECTION_ITEMS,
    ProofIRV3Error,
    canonical_bytes,
    detached_content_id,
    validate_envelope,
    validate_envelope_batch,
)

CANONICAL_VECTORS = Path("tests/fixtures/proofir_v3_parity/canonical-vectors-v1.json")


def test_v3_identity_is_order_independent_and_detached() -> None:
    first = validate_envelope(native_artifacts()["proofir.claim"])
    reordered = json.loads(json.dumps(first.to_dict()))
    payload = json.loads(json.dumps(first.to_dict()["payload"]))
    reordered["payload"] = dict(reversed(list(payload.items())))
    assert validate_envelope(reordered).content_id == first.content_id
    altered = first.to_dict()
    altered["payload"]["assertionState"] = "denied"
    with pytest.raises(ProofIRV3Error, match="artifactId"):
        validate_envelope(altered)


def test_v3_rejects_missing_identity_and_nonfinite_values() -> None:
    with pytest.raises(ProofIRV3Error, match="missing keys"):
        validate_envelope({"proofirVersion": "3.0"})
    with pytest.raises(ProofIRV3Error, match="canonically representable"):
        canonical_bytes({"value": float("nan")})


def test_unknown_extensions_round_trip_without_altering_core_claim_fields() -> None:
    source = native_artifacts()["proofir.claim"]
    altered = copy.deepcopy(source)
    altered["extensions"] = {"unknown.example/v9": {"assertionState": "accepted"}}
    altered["artifactId"] = detached_content_id(altered)

    first = validate_envelope(source).to_dict()
    second = validate_envelope(altered).to_dict()
    assert second["extensions"] == altered["extensions"]
    assert second["payload"] == first["payload"]
    assert second["subjectRefs"] == first["subjectRefs"]
    assert second["coverage"] == first["coverage"]
    assert second["artifactId"] != first["artifactId"]


def test_v3_bounds_reject_deep_and_oversized_values() -> None:
    deep: object = 0
    for _ in range(65):
        deep = [deep]
    with pytest.raises(ProofIRV3Error, match="nesting limit"):
        canonical_bytes(deep)
    with pytest.raises(ProofIRV3Error, match="string exceeds"):
        canonical_bytes("x" * (1024 * 1024 + 1))


def test_canonical_vectors_freeze_bytes_hashes_and_numeric_profile() -> None:
    vectors = json.loads(CANONICAL_VECTORS.read_text(encoding="utf-8"))
    assert vectors["format"] == "proofir-canonical-vectors-v1"
    assert vectors["profile"] == "proofir-json-integer-v1"
    for row in vectors["valid"]:
        encoded = canonical_bytes(row["value"])
        assert encoded.decode("utf-8") == row["canonicalJson"]
        assert "sha256:" + hashlib.sha256(encoded).hexdigest() == row["sha256"]
    for row in vectors["invalid"]:
        with pytest.raises(ProofIRV3Error, match=row["messageContains"]):
            canonical_bytes(row["value"])


def test_batch_bound_is_checked_before_reference_work() -> None:
    artifact = native_artifacts()["proofir.claim"]
    oversized = [artifact] * (MAX_COLLECTION_ITEMS + 1)
    with pytest.raises(ProofIRV3Error, match="batch exceeds item limit"):
        validate_envelope_batch(oversized)


def test_batch_aggregate_byte_bound_precedes_reference_closure(monkeypatch) -> None:
    first = native_artifacts()["proofir.claim"]
    second = copy.deepcopy(first)
    second["producer"]["name"] = "second-producer"
    second["artifactId"] = detached_content_id(second)
    one_size = len(canonical_bytes(first))

    def forbidden_reference_work(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("reference closure ran before aggregate budget preflight")

    monkeypatch.setattr(
        proofir_v3, "_validate_external_references", forbidden_reference_work
    )
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope_batch([first, second], max_bytes=one_size + 1)
    assert captured.value.diagnostic.code == "batch-byte-limit"
    assert captured.value.diagnostic.stage == "reference-valid"
