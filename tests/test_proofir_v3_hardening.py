from __future__ import annotations

import copy
from pathlib import Path

import pytest
from support.proofir_v3_native import claim_artifact, environment_artifact, native_artifacts

from ladon.proofir_v3 import (
    MAX_ARTIFACT_BYTES,
    MAX_ARTIFACTS,
    MAX_BATCH_BYTES,
    ProofIRV3Error,
    canonical_bytes,
    detached_content_id,
    validate_envelope,
    validate_envelope_batch,
)


def _reidentify(value: dict) -> dict:
    value["artifactId"] = detached_content_id(value)
    return value


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("prover", 7),
        ("toolchain", []),
        ("dependencies", {}),
        ("compiledModules", {"module": "Main"}),
        ("options", "autoImplicit=false"),
        ("trust", "unsafe"),
        ("fingerprintScheme", 3),
    ],
)
def test_environment_nested_types_are_closed(field: str, replacement: object) -> None:
    artifact = environment_artifact()
    artifact["payload"][field] = replacement
    _reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.stage == "kind-schema-valid"
    assert captured.value.diagnostic.code == "invalid-payload-field"


@pytest.mark.parametrize("field", ["claimId", "statementRef", "assertionState"])
def test_claim_nested_types_are_closed(field: str) -> None:
    artifact = claim_artifact()
    artifact["payload"][field] = [] if field != "assertionState" else 9
    _reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.stage == "kind-schema-valid"
    assert captured.value.diagnostic.code == "invalid-payload-field"


@pytest.mark.parametrize(
    ("kind", "path", "replacement"),
    [
        ("proofir.source-map", ("anchors", 0, "sourcePath"), 4),
        ("proofir.source-map", ("anchors", 0, "start"), "line 1"),
        ("proofir.governance-observation", ("observationId",), []),
        ("proofir.governance-observation", ("details",), "opaque"),
    ],
)
def test_source_and_observation_nested_types_are_closed(
    kind: str, path: tuple[object, ...], replacement: object
) -> None:
    artifact = copy.deepcopy(native_artifacts()[kind])
    target = artifact["payload"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement
    _reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "invalid-payload-field"


def test_invalid_unicode_has_a_stable_diagnostic() -> None:
    with pytest.raises(ProofIRV3Error) as captured:
        canonical_bytes("bad\ud800")
    diagnostic = captured.value.diagnostic
    assert (diagnostic.stage, diagnostic.code, diagnostic.pointer) == (
        "envelope-valid",
        "invalid-unicode",
        "",
    )


def test_batch_bounds_are_independent() -> None:
    first = claim_artifact()
    artifacts = []
    for index in range(3):
        value = copy.deepcopy(first)
        value["producer"]["name"] = f"producer-{index}"
        artifacts.append(_reidentify(value))
    one_size = len(canonical_bytes(artifacts[0]))
    assert one_size < MAX_ARTIFACT_BYTES
    validate_envelope_batch(
        artifacts,
        max_artifact_bytes=MAX_ARTIFACT_BYTES,
        max_batch_bytes=max(MAX_BATCH_BYTES, one_size * 3 + 1),
        max_artifacts=max(MAX_ARTIFACTS, 3),
    )
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope_batch(
            artifacts,
            max_artifact_bytes=MAX_ARTIFACT_BYTES,
            max_batch_bytes=one_size * 2,
            max_artifacts=3,
        )
    assert captured.value.diagnostic.code == "batch-byte-limit"


def test_batch_count_bound_is_distinct_from_collection_item_bound() -> None:
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope_batch([], max_artifacts=0)
    assert captured.value.diagnostic.code == "invalid-bound"


def test_corpus_inventory_names_every_registered_kind_and_freeze_seams() -> None:
    inventory = Path("docs/proofir-v3-corpus-inventory.md").read_text(encoding="utf-8")
    for kind in (
        "proofir.environment",
        "proofir.claim",
        "proofir.derivation",
        "proofir.plan",
        "proofir.attempt-log",
        "proofir.check-run",
        "proofir.source-map",
        "proofir.attachment-set",
        "proofir.governance-observation",
    ):
        assert kind in inventory
    for seam in ("References", "Projection", "Queries", "Canonical profile", "Resource bounds"):
        assert seam in inventory


def test_source_map_can_carry_exact_declaration_identity() -> None:
    artifact = copy.deepcopy(native_artifacts()["proofir.source-map"])
    anchor = artifact["payload"]["anchors"][0]
    anchor["declarationRef"] = "declaration:Fixture.goal"
    anchor["declarationFingerprint"] = "sha256:" + "f" * 64
    artifact["artifactId"] = detached_content_id(artifact)
    assert validate_envelope(artifact).to_dict() == artifact


def test_validation_authority_has_one_dispatch_entry_per_registered_kind() -> None:
    authority = Path("docs/proofir-v3-validation-authority.md").read_text(encoding="utf-8")
    for kind in (
        "proofir.environment",
        "proofir.claim",
        "proofir.derivation",
        "proofir.plan",
        "proofir.attempt-log",
        "proofir.check-run",
        "proofir.source-map",
        "proofir.attachment-set",
        "proofir.governance-observation",
    ):
        assert authority.count(f"`{kind}`") == 1


def test_check_results_must_be_declared_inputs_and_unique() -> None:
    artifact = copy.deepcopy(native_artifacts()["proofir.check-run"])
    extra = {"kind": "candidate-application", "localId": "application:extra"}
    artifact["subjectRefs"].append(extra)
    artifact["payload"]["results"].append(
        {"subjectRef": extra, "result": "accepted", "diagnostics": []}
    )
    _reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "result-subject-not-in-inputs"

    artifact = copy.deepcopy(native_artifacts()["proofir.check-run"])
    artifact["payload"]["results"].append(
        copy.deepcopy(artifact["payload"]["results"][0])
    )
    _reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "duplicate-check-result"
