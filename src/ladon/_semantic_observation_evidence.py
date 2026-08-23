"""Content-addressed evidence resolution for compact semantic observations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon._semantic_observation_support import (
    CHECKER_AUTHORITIES,
    CHECKER_TERMINAL_STATUSES,
    artifact_payload,
    artifact_receipt,
    artifact_rows,
    mapping,
    non_null_values,
    singleton_string,
)
from ladon.evidence_receipt import build_evidence_receipt
from ladon.proofir_v3 import ProofIRV3Error, validate_envelope_batch
from ladon.semantic_projection_core import SemanticProjectionError


@dataclass(frozen=True)
class ResolvedObservationEvidence:
    check_run_id: str
    check_artifact: Mapping[str, Any]
    environment_ref: str
    environment_artifact: Mapping[str, Any]


def requires_canonical_evidence(
    check: Mapping[str, Any],
    status: str,
    receipt: Mapping[str, Any] | None,
    scratch: bool,
) -> bool:
    referenced = _check_referenced(check)
    has_check_artifact = bool(artifact_rows(check, "proofir.check-run"))
    if scratch:
        return not _unattributed_scratch_failure(
            status, receipt, referenced, has_check_artifact
        )
    if status in CHECKER_TERMINAL_STATUSES:
        return True
    if referenced or has_check_artifact or _receipt_referenced(receipt):
        return True
    return bool(receipt and receipt.get("authorityBasis") in CHECKER_AUTHORITIES)


def _check_referenced(check: Mapping[str, Any]) -> bool:
    return any(
        check.get(field) is not None
        for field in ("environmentRef", "checkRunId", "checkRunRef")
    )


def _receipt_referenced(receipt: Mapping[str, Any] | None) -> bool:
    return bool(
        receipt
        and (
            receipt.get("environmentRef") is not None
            or receipt.get("checkRunRef") is not None
        )
    )


def _unattributed_scratch_failure(
    status: str,
    receipt: Mapping[str, Any] | None,
    referenced: bool,
    has_check_artifact: bool,
) -> bool:
    return (
        status == "failed"
        and receipt is None
        and not referenced
        and not has_check_artifact
    )


def validate_canonical_receipt(receipt: Mapping[str, Any]) -> None:
    subject = mapping(receipt.get("subject"), "semantic evidence receipt has no subject")
    limitations = _receipt_limitations(receipt)
    try:
        canonical = build_evidence_receipt(
            subject=subject,
            execution_binding=str(receipt.get("executionBinding")),
            observation_state=str(receipt.get("observationState")),
            operation_outcome=str(receipt.get("operationOutcome")),
            authority_basis=str(receipt.get("authorityBasis")),
            analysis_completeness=str(receipt.get("analysisCompleteness")),
            source_freshness=str(receipt.get("sourceFreshness")),
            environment_match=str(receipt.get("environmentMatch")),
            environment_ref=receipt.get("environmentRef"),
            check_run_ref=receipt.get("checkRunRef"),
            limitations=limitations,
        )
    except (TypeError, ValueError) as error:
        raise SemanticProjectionError(
            f"semantic evidence receipt is invalid: {error}"
        ) from error
    if dict(receipt) != canonical:
        raise SemanticProjectionError("semantic evidence receipt is not canonical")


def _receipt_limitations(receipt: Mapping[str, Any]) -> list[str]:
    limitations = receipt.get("limitations")
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) for item in limitations
    ):
        raise SemanticProjectionError("semantic evidence receipt has invalid limitations")
    return limitations


def resolve_observation_evidence(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> ResolvedObservationEvidence:
    check_run_id, check_artifact = _resolve_check_artifact(check, receipt, registry)
    environment_ref, environment = _resolve_environment_artifact(
        check, receipt, check_artifact, registry
    )
    _validate_registered_pair(environment, check_artifact)
    _validate_receipt_binding(check, receipt, check_artifact)
    return ResolvedObservationEvidence(
        check_run_id,
        check_artifact,
        environment_ref,
        environment,
    )


def _resolve_check_artifact(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[str, Mapping[str, Any]]:
    qualified = check.get("checkRunRef")
    qualified_row = qualified if isinstance(qualified, Mapping) else None
    check_run_id = _check_run_identity(check, receipt, qualified, qualified_row)
    embedded = _embedded_check_artifacts(check, check_run_id)
    artifact_ref = _check_artifact_identity(qualified_row, embedded)
    registered = _registered_check_artifact(registry, artifact_ref, check_run_id)
    _require_embedded_matches_registered(embedded, registered, "check")
    return check_run_id, registered


def _check_run_identity(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    qualified: Any,
    qualified_row: Mapping[str, Any] | None,
) -> str:
    return singleton_string(
        non_null_values(
            check.get("checkRunId"),
            receipt.get("checkRunRef"),
            qualified if isinstance(qualified, str) else None,
            qualified_row.get("localId") if qualified_row else None,
        ),
        "check-run identities",
    )


def _embedded_check_artifacts(
    check: Mapping[str, Any], check_run_id: str
) -> list[Mapping[str, Any]]:
    return [
        artifact
        for artifact in artifact_rows(check, "proofir.check-run")
        if artifact_payload(artifact).get("checkRunId") == check_run_id
    ]


def _check_artifact_identity(
    qualified: Mapping[str, Any] | None,
    embedded: list[Mapping[str, Any]],
) -> str:
    artifact_refs = non_null_values(
        qualified.get("artifactRef") if qualified else None,
        *(artifact.get("artifactId") for artifact in embedded),
    )
    if qualified is not None and embedded and len(set(artifact_refs)) != 1:
        raise SemanticProjectionError(
            "semantic result artifact-qualified check-run reference is mismatched"
        )
    return singleton_string(artifact_refs, "check artifact identities")


def _registered_check_artifact(
    registry: Mapping[str, Mapping[str, Any]],
    artifact_ref: str,
    check_run_id: str,
) -> Mapping[str, Any]:
    registered = registry.get(artifact_ref)
    if not isinstance(registered, Mapping):
        raise SemanticProjectionError(
            f"semantic evidence artifact is unresolved or not registered: {artifact_ref}"
        )
    if registered.get("artifactKind") != "proofir.check-run":
        raise SemanticProjectionError(
            "semantic check reference resolves to a mismatched kind"
        )
    if registered.get("artifactId") != artifact_ref:
        raise SemanticProjectionError(
            "semantic check resolver returned a mismatched identity"
        )
    if artifact_payload(registered).get("checkRunId") != check_run_id:
        raise SemanticProjectionError(
            "semantic check artifact owns a different check-run identity"
        )
    return registered


def _resolve_environment_artifact(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[str, Mapping[str, Any]]:
    inputs = mapping(
        artifact_payload(check_artifact).get("inputs"),
        "semantic check artifact has no inputs",
    )
    embedded = artifact_rows(check, "proofir.environment")
    environment_ref = _environment_identity(
        check, receipt, check_artifact, inputs, embedded
    )
    input_refs = _input_artifact_refs(inputs)
    artifact_ref = _environment_artifact_identity(embedded, input_refs, registry)
    environment = _registered_environment(registry, artifact_ref, environment_ref)
    _require_embedded_matches_registered(embedded, environment, "environment")
    return environment_ref, environment


def _environment_identity(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
    inputs: Mapping[str, Any],
    embedded: list[Mapping[str, Any]],
) -> str:
    return singleton_string(
        non_null_values(
            check.get("environmentRef"),
            receipt.get("environmentRef"),
            check_artifact.get("environmentRef"),
            inputs.get("environmentRef"),
            artifact_receipt(check_artifact).get("environmentRef"),
            *(artifact.get("environmentRef") for artifact in embedded),
        ),
        "semantic environment identities",
    )


def _input_artifact_refs(inputs: Mapping[str, Any]) -> list[str]:
    values = inputs.get("artifactRefs")
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise SemanticProjectionError(
            "semantic check artifact has invalid input artifact references"
        )
    return values


def _environment_artifact_identity(
    embedded: list[Mapping[str, Any]],
    input_refs: list[str],
    registry: Mapping[str, Mapping[str, Any]],
) -> str:
    registered = [
        registry[artifact_ref]
        for artifact_ref in input_refs
        if isinstance(registry.get(artifact_ref), Mapping)
        and registry[artifact_ref].get("artifactKind") == "proofir.environment"
    ]
    artifact_ref = singleton_string(
        non_null_values(
            *(artifact.get("artifactId") for artifact in embedded),
            *(artifact.get("artifactId") for artifact in registered),
        ),
        "environment artifact identities",
    )
    if artifact_ref not in input_refs:
        raise SemanticProjectionError(
            "semantic check does not reference its environment artifact"
        )
    return artifact_ref


def _registered_environment(
    registry: Mapping[str, Mapping[str, Any]],
    artifact_ref: str,
    environment_ref: str,
) -> Mapping[str, Any]:
    environment = registry.get(artifact_ref)
    if not isinstance(environment, Mapping) or environment.get(
        "artifactKind"
    ) != "proofir.environment":
        raise SemanticProjectionError("semantic environment reference is unresolved")
    if environment.get("artifactId") != artifact_ref:
        raise SemanticProjectionError(
            "semantic environment resolver returned a mismatched identity"
        )
    if environment.get("environmentRef") != environment_ref:
        raise SemanticProjectionError(
            "semantic environment artifact owns a different environment"
        )
    return environment


def _validate_registered_pair(
    environment: Mapping[str, Any], check: Mapping[str, Any]
) -> None:
    try:
        validate_envelope_batch([dict(environment), dict(check)])
    except (ProofIRV3Error, TypeError, ValueError) as error:
        raise SemanticProjectionError(
            f"registered semantic check/environment evidence is invalid: {error}"
        ) from error


def _validate_receipt_binding(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
) -> None:
    if dict(receipt) != dict(artifact_receipt(check_artifact)):
        raise SemanticProjectionError(
            "semantic result receipt disagrees with its registered check artifact"
        )
    outer = check.get("analysisCompleteness")
    if outer is not None and outer != receipt.get("analysisCompleteness"):
        raise SemanticProjectionError(
            "semantic result completeness disagrees with its registered check artifact"
        )


def _require_embedded_matches_registered(
    embedded: list[Mapping[str, Any]],
    registered: Mapping[str, Any],
    label: str,
) -> None:
    matching = [
        row
        for row in embedded
        if row.get("artifactId") == registered.get("artifactId")
    ]
    if len(matching) != 1 or dict(matching[0]) != dict(registered):
        raise SemanticProjectionError(
            f"embedded semantic {label} artifact disagrees with registered evidence"
        )


__all__ = [
    "ResolvedObservationEvidence",
    "requires_canonical_evidence",
    "resolve_observation_evidence",
    "validate_canonical_receipt",
]
