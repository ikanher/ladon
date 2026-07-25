"""Explicit version dispatch for report-derived reader artifacts."""

from __future__ import annotations

from typing import Any, Mapping


ATLAS_SCHEMA = "ladon-report-atlas-v1"
ATLAS_DIFF_SCHEMA = "ladon-atlas-diff-v1"
ATLAS_WORKFLOW_SCHEMA = "ladon-atlas-workflow-v1"
BRIDGE_ARTIFACT_KINDS = frozenset(
    {
        "ladon_proofir_bridge_report",
        "ladon_proofir_bridge_snapshot",
    }
)


class UnsupportedArtifactVersionError(ValueError):
    """Raised when a derived-artifact reader cannot dispatch an input."""


def require_atlas_v1(payload: Mapping[str, Any], *, consumer: str) -> None:
    """Require the current atlas major at a consuming boundary."""

    _require_named_schema(
        payload,
        expected=ATLAS_SCHEMA,
        consumer=consumer,
        artifact="Ladon atlas",
    )


def require_atlas_diff_v1(payload: Mapping[str, Any], *, consumer: str) -> None:
    """Require the current atlas-diff major at a consuming boundary."""

    _require_named_schema(
        payload,
        expected=ATLAS_DIFF_SCHEMA,
        consumer=consumer,
        artifact="Ladon atlas diff",
    )


def require_atlas_workflow_v1(
    payload: Mapping[str, Any],
    *,
    consumer: str,
) -> None:
    """Require the current atlas-workflow major at a consuming boundary."""

    _require_named_schema(
        payload,
        expected=ATLAS_WORKFLOW_SCHEMA,
        consumer=consumer,
        artifact="Ladon atlas workflow",
    )


def require_bridge_v1(payload: Mapping[str, Any], *, consumer: str) -> None:
    """Require a known bridge artifact kind and schema major.

    Unlabeled bridge dictionaries are accepted as legacy v1 fixtures during
    the same bounded transition as `clean-core-1`.
    """

    kind = payload.get("artifactKind")
    version = payload.get("schemaVersion")
    if kind not in BRIDGE_ARTIFACT_KINDS and kind is not None:
        raise UnsupportedArtifactVersionError(
            f"{consumer} cannot read bridge artifact kind {kind!r}; "
            f"supported kinds are {sorted(BRIDGE_ARTIFACT_KINDS)}"
        )
    if version not in {None, 1}:
        raise UnsupportedArtifactVersionError(
            f"{consumer} cannot read bridge schemaVersion {version!r}; "
            "supported schemaVersion is 1"
        )


def _require_named_schema(
    payload: Mapping[str, Any],
    *,
    expected: str,
    consumer: str,
    artifact: str,
) -> None:
    actual = payload.get("schema")
    if actual != expected:
        raise UnsupportedArtifactVersionError(
            f"{consumer} cannot read {artifact} schema {actual!r}; "
            f"supported schema is {expected!r}"
        )
