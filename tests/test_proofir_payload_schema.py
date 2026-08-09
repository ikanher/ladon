from __future__ import annotations

import copy

import pytest
from support.proofir_v3_native import (
    ENVIRONMENT,
    claim_artifact,
    derivation_artifact,
    environment_artifact,
    native_artifacts,
    ref,
)

from ladon.proofir_v3 import (
    SUPPORTED_ARTIFACT_KINDS,
    ProofIRV3Error,
    detached_content_id,
    validate_envelope,
)

EXPECTED_KINDS = frozenset(
    {
        "proofir.environment",
        "proofir.claim",
        "proofir.derivation",
        "proofir.plan",
        "proofir.attempt-log",
        "proofir.check-run",
        "proofir.source-map",
        "proofir.attachment-set",
        "proofir.governance-observation",
    }
)


def reidentify(artifact: dict[str, object]) -> None:
    artifact["artifactId"] = detached_content_id(artifact)


def assert_diagnostic(
    artifact: dict[str, object], *, stage: str, code: str, pointer: str
) -> None:
    reidentify(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    diagnostic = captured.value.diagnostic
    assert diagnostic.stage == stage
    assert diagnostic.code == code
    assert diagnostic.pointer == pointer


def test_native_kind_registry_is_closed_and_all_payloads_validate() -> None:
    assert SUPPORTED_ARTIFACT_KINDS == EXPECTED_KINDS
    artifacts = native_artifacts()
    assert artifacts.keys() == EXPECTED_KINDS
    for artifact in artifacts.values():
        checked = validate_envelope(artifact)
        assert checked.to_dict() == artifact
        assert checked.content_id == artifact["artifactId"]


@pytest.mark.parametrize("kind", sorted(EXPECTED_KINDS))
def test_each_payload_is_closed(kind: str) -> None:
    artifact = copy.deepcopy(native_artifacts()[kind])
    artifact["payload"]["unexpected"] = True  # type: ignore[index]
    assert_diagnostic(
        artifact,
        stage="kind-schema-valid",
        code="unexpected-payload-key",
        pointer="/payload/unexpected",
    )


def test_claim_requires_exact_statement_and_assertion_state() -> None:
    missing = claim_artifact()
    del missing["payload"]["statementRef"]
    assert_diagnostic(
        missing,
        stage="kind-schema-valid",
        code="missing-payload-key",
        pointer="/payload/statementRef",
    )

    invalid = claim_artifact()
    invalid["payload"]["assertionState"] = "verified"
    assert_diagnostic(
        invalid,
        stage="kind-schema-valid",
        code="invalid-enum",
        pointer="/payload/assertionState",
    )


def test_environment_payload_is_closed_and_bound_to_environment_ref() -> None:
    mismatched = environment_artifact()
    mismatched["environmentRef"] = "sha256:" + "f" * 64
    assert_diagnostic(
        mismatched,
        stage="semantic-valid",
        code="environment-digest-mismatch",
        pointer="/environmentRef",
    )

    missing = environment_artifact()
    del missing["payload"]["fingerprintScheme"]
    assert_diagnostic(
        missing,
        stage="kind-schema-valid",
        code="missing-payload-key",
        pointer="/payload/fingerprintScheme",
    )


def test_common_producer_coverage_limitations_and_extensions_are_closed() -> None:
    bad_producer = claim_artifact()
    del bad_producer["producer"]["buildDigest"]
    assert_diagnostic(
        bad_producer,
        stage="envelope-valid",
        code="missing-producer-key",
        pointer="/producer/buildDigest",
    )

    bad_coverage = claim_artifact()
    bad_coverage["coverage"]["projected"] = -1
    assert_diagnostic(
        bad_coverage,
        stage="envelope-valid",
        code="invalid-coverage-counter",
        pointer="/coverage/projected",
    )

    bad_limitation = claim_artifact()
    bad_limitation["limitations"] = [{"message": "missing id"}]
    assert_diagnostic(
        bad_limitation,
        stage="envelope-valid",
        code="invalid-limitation",
        pointer="/limitations/0/id",
    )

    bad_extension = claim_artifact()
    bad_extension["extensions"] = {"unversioned": {}}
    assert_diagnostic(
        bad_extension,
        stage="envelope-valid",
        code="invalid-extension-namespace",
        pointer="/extensions/unversioned",
    )


def test_environment_and_digest_fields_use_exact_sha256_shape() -> None:
    artifact = claim_artifact()
    artifact["environmentRef"] = "env"
    for subject in artifact["subjectRefs"]:
        subject["environmentRef"] = "env"
    assert_diagnostic(
        artifact,
        stage="envelope-valid",
        code="invalid-content-digest",
        pointer="/environmentRef",
    )

    artifact = claim_artifact()
    artifact["producer"]["buildDigest"] = "sha256:not-hex"
    assert_diagnostic(
        artifact,
        stage="envelope-valid",
        code="invalid-content-digest",
        pointer="/producer/buildDigest",
    )


def test_derivation_step_shape_and_reference_kinds_are_closed() -> None:
    extra = derivation_artifact()
    extra["payload"]["steps"][0]["extra"] = True
    assert_diagnostic(
        extra,
        stage="kind-schema-valid",
        code="unexpected-step-key",
        pointer="/payload/steps/0/extra",
    )

    wrong_kind = derivation_artifact()
    wrong_kind["payload"]["steps"][0]["conclusionRef"]["kind"] = "term"
    assert_diagnostic(
        wrong_kind,
        stage="reference-valid",
        code="unexpected-reference-kind",
        pointer="/payload/steps/0/conclusionRef/kind",
    )


@pytest.mark.parametrize(
    ("kind", "pointer", "replacement"),
    [
        ("proofir.plan", "/payload/goalRefs/0", ref("statement", "missing")),
        (
            "proofir.attempt-log",
            "/payload/summary/residualPremiseRefs/0",
            ref("statement", "missing"),
        ),
        (
            "proofir.check-run",
            "/payload/results/0/subjectRef",
            ref("statement", "missing"),
        ),
        (
            "proofir.source-map",
            "/payload/anchors/0/subjectRef",
            ref("statement", "missing"),
        ),
        (
            "proofir.attachment-set",
            "/payload/attachments/0/selectedSourceRef",
            ref("surface", "missing"),
        ),
        (
            "proofir.governance-observation",
            "/payload/subjectRef",
            ref("statement", "missing"),
        ),
    ],
)
def test_every_nested_semantic_reference_is_closed(
    kind: str, pointer: str, replacement: dict[str, str]
) -> None:
    artifact = copy.deepcopy(native_artifacts()[kind])
    target: object = artifact
    parts = pointer.removeprefix("/").split("/")
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]  # type: ignore[index]
    if isinstance(target, list):
        target[int(parts[-1])] = replacement
    else:
        target[parts[-1]] = replacement  # type: ignore[index]
        assert_diagnostic(
            artifact,
            stage="reference-valid",
            code="dangling-local-reference",
            pointer=pointer,
        )


def test_diagnostic_records_are_ordered_and_attempts_are_not_proof() -> None:
    artifact = native_artifacts()["proofir.attempt-log"]
    artifact["payload"]["attempts"][0]["diagnostics"][0]["order"] = -1
    assert_diagnostic(
        artifact,
        stage="kind-schema-valid",
        code="invalid-diagnostic-order",
        pointer="/payload/attempts/0/diagnostics/0/order",
    )

    checked = validate_envelope(native_artifacts()["proofir.attempt-log"])
    assert checked.payload["artifactKind"] == "proofir.attempt-log"
    assert checked.payload["limitations"][0]["id"] == "not-proof"


def test_empty_attachment_set_requires_an_explicit_limitation() -> None:
    artifact = native_artifacts()["proofir.attachment-set"]
    artifact["payload"]["attachments"] = []
    artifact["limitations"] = []
    assert_diagnostic(
        artifact,
        stage="semantic-valid",
        code="empty-evidence-without-limitation",
        pointer="/limitations",
    )

    artifact["limitations"] = [
        {"id": "no-match", "message": "The resolver found no candidate."}
    ]
    reidentify(artifact)
    assert validate_envelope(artifact).content_id == artifact["artifactId"]


def test_attachment_selection_is_explicit_and_never_semantic_acceptance() -> None:
    artifact = native_artifacts()["proofir.attachment-set"]
    attachment = artifact["payload"]["attachments"][0]
    assert attachment["selectionDecision"] == "selected"
    assert attachment["selectedCandidateId"] == "declaration:Fixture.goal"
    assert attachment["semanticAcceptance"] is False
    assert attachment["candidates"][0]["decisiveEvidence"]

    attachment["semanticAcceptance"] = True
    assert_diagnostic(
        artifact,
        stage="semantic-valid",
        code="attachment-cannot-accept-semantics",
        pointer="/payload/attachments/0/semanticAcceptance",
    )


def test_unselected_attachment_cannot_retain_selected_identity() -> None:
    artifact = native_artifacts()["proofir.attachment-set"]
    attachment = artifact["payload"]["attachments"][0]
    attachment["selectionDecision"] = "ambiguous"
    assert_diagnostic(
        artifact,
        stage="semantic-valid",
        code="contradictory-attachment-decision",
        pointer="/payload/attachments/0",
    )


def test_check_input_environment_matches_and_subject_descriptors_are_owner_local() -> (
    None
):
    artifact = native_artifacts()["proofir.check-run"]
    artifact["payload"]["inputs"]["environmentRef"] = "sha256:" + "f" * 64
    assert_diagnostic(
        artifact,
        stage="reference-valid",
        code="reference-environment-mismatch",
        pointer="/payload/inputs/environmentRef",
    )

    artifact = claim_artifact()
    artifact["subjectRefs"][0]["environmentRef"] = "sha256:" + "f" * 64
    assert_diagnostic(
        artifact,
        stage="reference-valid",
        code="invalid-subject-descriptor",
        pointer="/subjectRefs/0/environmentRef",
    )


def test_fixture_environment_is_the_shared_environment() -> None:
    for kind, artifact in native_artifacts().items():
        if kind != "proofir.environment":
            assert artifact["environmentRef"] == ENVIRONMENT
