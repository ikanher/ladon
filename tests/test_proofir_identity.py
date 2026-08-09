from __future__ import annotations

from ladon.proofir_identity import (
    ExternalSubjectRef,
    LocalSubjectRef,
    QualifiedSubjectRef,
    content_id,
    observation_id,
)


def test_content_id_is_stable_but_observation_id_is_generation_scoped() -> None:
    payload = {"artifactKind": "proofir.claim", "payload": {"answer": 42}}
    artifact = content_id(payload)
    assert artifact == content_id(
        {"payload": {"answer": 42}, "artifactKind": "proofir.claim"}
    )
    first = observation_id(
        generation_id="g1", relative_path="proof.json", content_artifact_id=artifact
    )
    second = observation_id(
        generation_id="g2", relative_path="proof.json", content_artifact_id=artifact
    )
    assert first != second


def test_local_and_external_subject_identity_are_typed() -> None:
    owner = "sha256:" + "1" * 64
    local = LocalSubjectRef("statement", "local.1")
    external = ExternalSubjectRef(owner, "statement", "local.1")
    assert local.to_dict() == {"kind": "statement", "localId": "local.1"}
    assert external.to_dict()["artifactRef"] == owner


def test_local_spelling_does_not_join_across_owner_scopes() -> None:
    environment = "sha256:" + "2" * 64
    left = QualifiedSubjectRef("sha256:" + "3" * 64, environment, "claim", "root")
    right = QualifiedSubjectRef("sha256:" + "4" * 64, environment, "claim", "root")
    assert left.local_id == right.local_id
    assert left.owner_content_artifact_id != right.owner_content_artifact_id


def test_external_subject_round_trip_preserves_exact_scope() -> None:
    subject = ExternalSubjectRef("sha256:" + "5" * 64, "statement", "s")
    encoded = subject.to_dict()
    assert (
        ExternalSubjectRef(encoded["artifactRef"], encoded["kind"], encoded["localId"])
        == subject
    )
