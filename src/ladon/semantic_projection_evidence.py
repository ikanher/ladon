"""Reference closure for compact semantic-result evidence.

Compact projections contain references rather than ProofIR artifact bodies.
This module reconciles the redundant canonical references, locates their
owning artifacts, and verifies those artifacts against a caller-owned resolver.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import SemanticProjectionError

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_CHECK_REF = re.compile(r"check:[0-9a-f]{64}")


def evidence_refs(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """Resolve the environment and check-run references for one observation."""

    artifacts = _artifact_rows(check.get("artifacts"))
    environment_ref = check.get("environmentRef") or receipt.get("environmentRef")
    qualified = _qualified_check_reference(check.get("checkRunRef"))
    check_ref = _canonical_check_ref(check, receipt, qualified)
    environment_artifact = _find_environment_artifact(artifacts, environment_ref)
    check_artifact = _find_check_artifact(artifacts, check_ref)
    environment = _environment_reference(environment_ref, environment_artifact, registry)
    check_run = _check_reference(check_ref, check_artifact, registry)
    _validate_supplied_qualified_reference(qualified, check_run)
    return environment, check_run


def _artifact_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _qualified_check_reference(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _canonical_check_ref(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    qualified: Mapping[str, Any] | None,
) -> Any:
    qualified_local_id = qualified.get("localId") if qualified is not None else None
    string_check_ref = check.get("checkRunRef")
    candidates = (
        check.get("checkRunId"),
        receipt.get("checkRunRef"),
        string_check_ref if isinstance(string_check_ref, str) else None,
        qualified_local_id,
    )
    refs = [value for value in candidates if value is not None]
    if not refs:
        return None
    if any(value != refs[0] for value in refs[1:]):
        raise SemanticProjectionError("semantic result contains contradictory check-run references")
    return refs[0]


def _find_environment_artifact(
    artifacts: list[Mapping[str, Any]], environment_ref: Any
) -> Mapping[str, Any] | None:
    return next(
        (
            row
            for row in artifacts
            if row.get("artifactKind") == "proofir.environment"
            and (environment_ref is None or row.get("environmentRef") == environment_ref)
        ),
        None,
    )


def _find_check_artifact(
    artifacts: list[Mapping[str, Any]], check_ref: Any
) -> Mapping[str, Any] | None:
    return next(
        (
            row
            for row in artifacts
            if row.get("artifactKind") == "proofir.check-run"
            and _artifact_owns_check_ref(row, check_ref)
        ),
        None,
    )


def _artifact_owns_check_ref(artifact: Mapping[str, Any], check_ref: Any) -> bool:
    if check_ref is None:
        return True
    payload = artifact.get("payload")
    return isinstance(payload, Mapping) and payload.get("checkRunId") == check_ref


def _environment_reference(
    environment_ref: Any,
    artifact: Mapping[str, Any] | None,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, str] | None:
    if environment_ref is None and artifact is None:
        return None
    if not isinstance(environment_ref, str) or _DIGEST.fullmatch(environment_ref) is None:
        raise SemanticProjectionError("semantic result has an invalid environment reference")
    if artifact is None:
        raise SemanticProjectionError("semantic result environment reference is unresolved")
    artifact_id = _registered_artifact(artifact, "proofir.environment", registry)
    if artifact.get("environmentRef") != environment_ref:
        raise SemanticProjectionError("semantic result environment artifact is mismatched")
    return {"environmentRef": environment_ref, "artifactRef": artifact_id}


def _check_reference(
    check_ref: Any,
    artifact: Mapping[str, Any] | None,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, str] | None:
    if check_ref is None and artifact is None:
        return None
    if not isinstance(check_ref, str) or _CHECK_REF.fullmatch(check_ref) is None:
        raise SemanticProjectionError("semantic result has an invalid check-run reference")
    if artifact is None:
        raise SemanticProjectionError("semantic result check-run reference is unresolved")
    artifact_id = _registered_artifact(artifact, "proofir.check-run", registry)
    payload = artifact.get("payload")
    if not isinstance(payload, Mapping) or payload.get("checkRunId") != check_ref:
        raise SemanticProjectionError("semantic result check-run artifact is mismatched")
    return {"artifactRef": artifact_id, "kind": "check-run", "localId": check_ref}


def _registered_artifact(
    artifact: Mapping[str, Any],
    expected_kind: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> str:
    artifact_id = artifact.get("artifactId")
    if not isinstance(artifact_id, str) or _DIGEST.fullmatch(artifact_id) is None:
        raise SemanticProjectionError("semantic result contains an invalid artifact identity")
    registered = registry.get(artifact_id)
    if not isinstance(registered, Mapping):
        raise SemanticProjectionError(f"semantic evidence artifact is not registered: {artifact_id}")
    if registered.get("artifactId", artifact_id) != artifact_id:
        raise SemanticProjectionError("semantic artifact resolver returned a mismatched identity")
    _validate_artifact_kind(artifact, registered, expected_kind)
    return artifact_id


def _validate_artifact_kind(
    artifact: Mapping[str, Any],
    registered: Mapping[str, Any],
    expected_kind: str,
) -> None:
    if artifact.get("artifactKind") != expected_kind:
        raise SemanticProjectionError("semantic artifact resolver returned a mismatched kind")
    if registered.get("artifactKind", expected_kind) != expected_kind:
        raise SemanticProjectionError("semantic artifact resolver returned a mismatched kind")


def _validate_supplied_qualified_reference(
    supplied: Mapping[str, Any] | None,
    resolved: Mapping[str, Any] | None,
) -> None:
    if supplied is not None and dict(supplied) != resolved:
        raise SemanticProjectionError(
            "semantic result artifact-qualified check-run reference is mismatched"
        )


__all__ = ["evidence_refs"]
