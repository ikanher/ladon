"""Snapshot ownership and full-batch validation contract regressions."""

from __future__ import annotations

import copy

import pytest
from support.proofir_v3_native import check_run_artifact, claim_artifact, native_artifacts

from ladon.proofir_v3 import (
    ProofIRV3Error,
    canonical_bytes,
    detached_content_id,
    validate_envelope,
    validate_envelope_batch,
)


def _error(call):
    with pytest.raises(ProofIRV3Error) as caught:
        call()
    return caught.value.diagnostic


def test_result_is_detached_and_next_call_observes_input_mutation():
    raw = claim_artifact()
    first = validate_envelope_batch([raw])[0]
    original_id = first.content_id
    raw["extensions"]["example.fixture/v1"]["note"] = "changed"
    raw["artifactId"] = detached_content_id(raw)
    assert first.content_id == original_id
    assert first.to_dict()["extensions"]["example.fixture/v1"]["note"] == "opaque"
    second = validate_envelope_batch([raw])[0]
    assert second.content_id == raw["artifactId"] != original_id
    detached = second.to_dict()
    detached["extensions"]["example.fixture/v1"]["note"] = "returned mutation"
    assert second.to_dict()["extensions"]["example.fixture/v1"]["note"] == "changed"
    assert (
        validate_envelope_batch([raw])[0].to_dict()["extensions"]["example.fixture/v1"]["note"]
        == "changed"
    )


def test_duplicate_multiplicity_counts_toward_aggregate_bytes():
    artifact = claim_artifact()
    size = len(canonical_bytes(artifact))
    assert len(validate_envelope_batch([artifact, artifact], max_batch_bytes=2 * size)) == 2
    diag = _error(
        lambda: validate_envelope_batch([artifact, artifact], max_batch_bytes=2 * size - 1)
    )
    assert (diag.stage, diag.code) == ("reference-valid", "batch-byte-limit")


def test_conflicting_duplicate_declaration_precedes_declared_id_check():
    left = claim_artifact()
    right = copy.deepcopy(left)
    right["producer"]["name"] = "different"
    # Deliberately retain the same declared artifactId: duplicate conflict is a preflight error.
    diag = _error(lambda: validate_envelope_batch([left, right]))
    assert (diag.stage, diag.code, diag.pointer) == (
        "reference-valid",
        "duplicate-batch-artifact-id",
        "/artifactId",
    )


def test_later_malformed_artifact_precedes_earlier_external_closure_failure():
    first = check_run_artifact()
    first["payload"]["inputs"]["artifactRefs"] = ["sha256:" + "f" * 64]
    first["artifactId"] = detached_content_id(first)
    later = {"proofirVersion": "3.0"}
    diag = _error(lambda: validate_envelope_batch([first, later]))
    assert diag.message.startswith("v3 envelope missing keys:")
    assert diag.stage == "envelope-valid"


def test_legacy_max_bytes_sets_both_limits_and_invalid_limit_precedes_batch_count():
    artifacts = [claim_artifact(), claim_artifact()]
    diag = _error(lambda: validate_envelope_batch(artifacts, max_bytes=0, max_artifacts=1))
    assert (diag.stage, diag.code) == ("reference-valid", "invalid-bound")
    # Legacy max_bytes limits aggregate bytes as well as each individual artifact.
    one = len(canonical_bytes(artifacts[0]))
    diag = _error(lambda: validate_envelope_batch(artifacts, max_bytes=one))
    assert diag.code == "batch-byte-limit"


def test_independent_artifact_and_batch_limits():
    artifact = claim_artifact()
    size = len(canonical_bytes(artifact))
    assert (
        len(validate_envelope_batch([artifact], max_artifact_bytes=size, max_batch_bytes=size)) == 1
    )
    assert (
        "canonical payload exceeds byte limit"
        in _error(lambda: validate_envelope_batch([artifact], max_artifact_bytes=size - 1)).message
    )
    assert (
        _error(
            lambda: validate_envelope_batch(
                [artifact], max_artifact_bytes=size, max_batch_bytes=size - 1
            )
        ).code
        == "batch-byte-limit"
    )


def test_no_partial_return_when_later_artifact_fails_id_validation():
    values = [claim_artifact(), claim_artifact()]
    values[1]["artifactId"] = "sha256:" + "0" * 64
    diag = _error(lambda: validate_envelope_batch(values))
    assert str(diag.message) == "artifactId does not match detached canonical content"
    # Assignment completes only on success; callers never receive a prefix tuple.


def test_closed_check_input_rejects_cross_environment_target():
    check = check_run_artifact()
    target = claim_artifact()
    target["environmentRef"] = "sha256:" + "a" * 64
    target["artifactId"] = detached_content_id(target)
    check["payload"]["inputs"]["artifactRefs"] = [target["artifactId"]]
    check["artifactId"] = detached_content_id(check)
    diag = _error(lambda: validate_envelope_batch([check, target]))
    assert diag.code == "external-reference-environment-mismatch"


def test_external_descriptor_reference_must_exist_on_target():
    native = native_artifacts()
    check = copy.deepcopy(native["proofir.check-run"])
    derivation = copy.deepcopy(native["proofir.derivation"])
    step = derivation["payload"]["steps"][0]
    step["checkRunRef"] = {
        "artifactRef": check["artifactId"],
        "kind": "check-run",
        "localId": "check:missing-descriptor",
    }
    derivation["artifactId"] = detached_content_id(derivation)
    diag = _error(lambda: validate_envelope_batch([check, derivation]))
    assert diag.code == "external-subject-not-found"


@pytest.mark.parametrize(
    "validator",
    [
        validate_envelope,
        lambda artifact: validate_envelope_batch([artifact])[0],
    ],
    ids=["single", "batch"],
)
@pytest.mark.parametrize("location", ["top-dict", "nested-dict", "nested-list"])
def test_hostile_deepcopy_cannot_replace_validated_payload(validator, location):
    class EvilDict(dict):
        def __deepcopy__(self, memo):
            return {"proofirVersion": "bad"}

    class EvilList(list):
        def __deepcopy__(self, memo):
            return []

    raw = claim_artifact()
    if location == "top-dict":
        raw = EvilDict(raw)
    elif location == "nested-dict":
        raw["producer"] = EvilDict(raw["producer"])
    else:
        raw["subjectRefs"] = EvilList(raw["subjectRefs"])
    raw["artifactId"] = detached_content_id(raw)
    try:
        validated = validator(raw)
    except ProofIRV3Error:
        # Rejecting hostile container subclasses at the ownership boundary is safe.
        return
    returned = validated.to_dict()
    assert returned == raw
    assert detached_content_id(returned) == returned["artifactId"]


def test_dangling_closure_precedes_final_declared_id_validation():
    check = check_run_artifact()
    check["payload"]["inputs"]["artifactRefs"] = ["sha256:" + "f" * 64]
    # Leave artifactId stale: reference closure historically runs before the final ID check.
    diag = _error(lambda: validate_envelope_batch([check]))
    assert diag.code == "external-artifact-not-in-batch"


@pytest.mark.parametrize(
    "validator",
    [validate_envelope, lambda artifact: validate_envelope_batch([artifact])[0]],
    ids=["single", "batch"],
)
def test_serialization_hook_cannot_introduce_unchecked_producer(validator):
    class AlternateItems(dict):
        def items(self):
            return [(key, 0 if key == "producer" else value) for key, value in dict.items(self)]

    raw = AlternateItems(claim_artifact())
    try:
        checked = validator(raw)
    except ProofIRV3Error:
        return
    returned = checked.to_dict()
    assert isinstance(returned["producer"], dict)
    assert detached_content_id(returned) == checked.content_id


def test_missing_shape_precedes_invalid_canonical_value():
    diag = _error(lambda: validate_envelope_batch([{"other": float("inf")}]))
    assert diag.message.startswith("v3 envelope missing keys:")
    assert diag.stage == "envelope-valid"
