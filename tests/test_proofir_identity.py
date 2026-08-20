from __future__ import annotations

import pytest

from ladon.proofir_identity import (
    ContentArtifactId,
    ExternalSubjectRef,
    FileDigest,
    LocalSubjectRef,
    QualifiedSubjectRef,
    content_id,
    observation_id,
    require_content_artifact_id,
    require_file_digest,
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


def test_file_and_detached_artifact_ids_are_distinct_domains() -> None:
    spelling = "sha256:" + "a" * 64
    file_digest = FileDigest(spelling)
    artifact_id = ContentArtifactId(spelling)
    assert file_digest == artifact_id
    assert type(file_digest) is not type(artifact_id)
    assert require_file_digest(file_digest) is file_digest
    assert require_content_artifact_id(artifact_id) is artifact_id
    with pytest.raises(TypeError):
        require_file_digest(artifact_id)
    with pytest.raises(TypeError):
        require_content_artifact_id(file_digest)
