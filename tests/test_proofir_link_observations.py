from __future__ import annotations

import pytest

from ladon.proofir_link_observations import manifest_link_observation


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def test_manifest_link_is_attributable_but_not_semantic_authority() -> None:
    row = manifest_link_observation(
        source_path="replay.json",
        target_path="surface.json",
        kind="replays",
        declared_source_artifact_id=_digest("a"),
        declared_target_artifact_id=_digest("b"),
        resolved_source_artifact_id=_digest("a"),
        resolved_target_artifact_id=_digest("b"),
    )
    assert row["observationId"].startswith("sha256:")
    assert row["observer"] == {
        "name": "ladon-manifest-link-resolver",
        "version": "proofir-manifest-link-v1",
    }
    assert row["linkResult"] == "bound-observation"
    assert row["semanticAcceptance"] is False
    assert row["limitations"][0]["id"] == "manifest-link-is-not-semantic-authority"


def test_missing_endpoint_is_unbound_and_attributable() -> None:
    row = manifest_link_observation(
        source_path="replay.json",
        target_path="missing.json",
        kind="replays",
        declared_source_artifact_id=_digest("a"),
        declared_target_artifact_id=None,
        resolved_source_artifact_id=_digest("a"),
        resolved_target_artifact_id=None,
    )
    assert row["linkResult"] == "unbound"
    assert row["diagnostics"] == ["missing-target-endpoint"]


def test_declared_and_resolved_content_id_drift_is_diagnosed() -> None:
    row = manifest_link_observation(
        source_path="replay.json",
        target_path="surface.json",
        kind="replays",
        declared_source_artifact_id=_digest("a"),
        declared_target_artifact_id=_digest("b"),
        resolved_source_artifact_id=_digest("c"),
        resolved_target_artifact_id=_digest("b"),
    )
    assert row["linkResult"] == "drifted"
    assert row["diagnostics"] == ["source-content-id-drift"]


@pytest.mark.parametrize("field", ["declared_source_artifact_id", "resolved_target_artifact_id"])
def test_non_content_addressed_endpoint_is_rejected(field: str) -> None:
    arguments = {
        "source_path": "replay.json",
        "target_path": "surface.json",
        "kind": "replays",
        "declared_source_artifact_id": _digest("a"),
        "declared_target_artifact_id": _digest("b"),
        "resolved_source_artifact_id": _digest("a"),
        "resolved_target_artifact_id": _digest("b"),
    }
    arguments[field] = "not-a-content-id"
    with pytest.raises(ValueError, match="sha256 content ID"):
        manifest_link_observation(**arguments)
