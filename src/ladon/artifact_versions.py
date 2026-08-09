"""Explicit version dispatch for report-derived reader artifacts."""

from __future__ import annotations

from typing import Any, Mapping


ATLAS_SCHEMA = "ladon-report-atlas-v1"
ATLAS_DIFF_SCHEMA = "ladon-atlas-diff-v1"
ATLAS_WORKFLOW_SCHEMA = "ladon-atlas-workflow-v1"


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
    """Reject retired ProofIR bridge inputs at atlas boundaries."""

    raise UnsupportedArtifactVersionError(
        f"{consumer} no longer accepts retired ProofIR bridge artifacts"
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
