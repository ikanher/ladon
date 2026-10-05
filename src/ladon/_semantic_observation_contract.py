"""Authority, request, and subject invariants for semantic observations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._semantic_observation_context import validate_rejected_context
from ladon._semantic_observation_results import validate_check_results
from ladon._semantic_observation_support import (
    CANDIDATE_STATUSES,
    SCRATCH_STATUSES,
    artifact_payload,
    has_candidate_subject,
    has_subject_display,
    mapping,
)
from ladon.semantic_local_context import validate_observed_local_context
from ladon.semantic_projection_core import SemanticProjectionError


def validate_status(status: str, scratch: bool) -> None:
    allowed = SCRATCH_STATUSES if scratch else CANDIDATE_STATUSES
    if status not in allowed:
        kind = "scratch" if scratch else "candidate"
        raise SemanticProjectionError(f"unsupported semantic {kind} status: {status}")


def validate_weak_observation(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    candidate: str,
    status: str,
    request: Mapping[str, Any] | None,
) -> None:
    """Bind a non-checker failure receipt without promoting it to check evidence."""

    weak_statuses = {
        "timeout", "resource-limited", "output-limited", "memory-limited",
        "failed-checker", "invalid-worker-output", "unassessed",
    }
    if status not in weak_statuses:
        raise SemanticProjectionError(
            "semantic weak receipt is attached to a checker-backed status"
        )
    subject = mapping(receipt.get("subject"), "semantic evidence receipt has no subject")
    if subject.get("candidate") != candidate:
        raise SemanticProjectionError(
            "semantic candidate disagrees with its weak observation subject"
        )
    _validate_request_subject(subject, request)
    _validate_context_subject(subject, check, request)
    expected = {
        "operationOutcome": "failed",
        "observationState": "failed",
        "authorityBasis": "not-assessed",
    }
    if any(receipt.get(field) != value for field, value in expected.items()):
        raise SemanticProjectionError(
            "semantic weak failure receipt contradicts its public status"
        )
    if receipt.get("analysisCompleteness") not in {"invalid", "not-assessed"}:
        raise SemanticProjectionError(
            "semantic weak failure receipt overstates analysis completeness"
        )


def validate_observation_semantics(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
    candidate: str,
    status: str,
    *,
    request: Mapping[str, Any] | None,
    scratch: bool,
    parent_check_artifact: Mapping[str, Any] | None = None,
) -> None:
    expected_status = _observed_status(check, status, scratch)
    if receipt.get("operationOutcome") != _expected_outcome(expected_status, scratch):
        raise SemanticProjectionError(
            "semantic result status disagrees with its registered check outcome"
        )
    provisional = status == "provisional-observation"
    _validate_authority_and_completeness(
        receipt, artifact_payload(check_artifact), expected_status, scratch,
        provisional=provisional,
    )
    context_artifact = parent_check_artifact if scratch else check_artifact
    _validate_subject(check, receipt, check_artifact, candidate, request, scratch,
                      context_artifact=context_artifact)
    comparison_receipt = (
        _scratch_comparison_receipt(receipt, check_artifact, parent_check_artifact)
        if scratch else receipt
    )
    validate_check_results(
        check, comparison_receipt, check_artifact, candidate, expected_status, scratch,
        provisional=provisional,
    )
    if expected_status == 'rejected' and not scratch and not provisional:
        validate_rejected_context(check_artifact, receipt)


def validate_scratch_parent(
    check: Mapping[str, Any],
    parent_environment_ref: str | None,
    parent_check_run_id: str | None,
    environment_ref: str,
) -> None:
    if parent_environment_ref != environment_ref:
        raise SemanticProjectionError(
            "scratch check belongs to a different semantic environment"
        )
    parent_ref = check.get("parentCheckRunRef")
    if not isinstance(parent_ref, str) or parent_ref != parent_check_run_id:
        raise SemanticProjectionError(
            "scratch check omits or names a different parent candidate observation"
        )


def _validate_authority_and_completeness(
    receipt: Mapping[str, Any], payload: Mapping[str, Any], status: str,
    scratch: bool, *, provisional: bool,
) -> None:
    guarantee = mapping(
        payload.get("guarantee"), "semantic check artifact has no guarantee"
    )
    authority = receipt.get("authorityBasis")
    if authority != guarantee.get("authorityBasis"):
        raise SemanticProjectionError(
            "semantic result authority disagrees with its registered check artifact"
        )
    _validate_authority_class(authority, scratch, provisional)
    if receipt.get("analysisCompleteness") != _expected_completeness(
        status, scratch, provisional
    ):
        raise SemanticProjectionError(
            "semantic result completeness contradicts its registered check artifact"
        )


def _validate_authority_class(authority: Any, scratch: bool, provisional: bool) -> None:
    if scratch or provisional:
        if authority != "process-observation":
            raise SemanticProjectionError(
                "partial semantic observation has an invalid authority basis"
            )
    elif authority == "process-observation":
        raise SemanticProjectionError(
            "terminal semantic result cannot claim partial process authority"
        )


def _expected_completeness(status: str, scratch: bool, provisional: bool) -> str:
    if scratch or provisional or status == "applicable-with-residuals":
        return "partial"
    return "complete"


def _validate_subject(
    check: Mapping[str, Any], receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any], candidate: str,
    request: Mapping[str, Any] | None, scratch: bool,
    *, context_artifact: Mapping[str, Any] | None,
) -> None:
    subject = mapping(receipt.get("subject"), "semantic evidence receipt has no subject")
    if subject.get("candidate") != candidate:
        raise SemanticProjectionError("semantic candidate disagrees with its check subject")
    _validate_request_subject(subject, request)
    _validate_context_subject(subject, check, request, check_artifact=context_artifact)
    descriptors = check_artifact.get("subjectRefs")
    if not isinstance(descriptors, list):
        raise SemanticProjectionError("semantic check artifact has no subject descriptors")
    _validate_owned_subjects(descriptors, subject, candidate, scratch)


def _validate_owned_subjects(
    descriptors: list[Any], subject: Mapping[str, Any], candidate: str, scratch: bool
) -> None:
    if scratch:
        if not has_subject_display(descriptors, "candidate-application", candidate):
            raise SemanticProjectionError(
                "scratch check artifact owns a different candidate subject"
            )
        return
    _validate_goal_subject(descriptors, subject)
    if not has_candidate_subject(descriptors, candidate):
        raise SemanticProjectionError(
            "semantic check artifact owns a different candidate subject"
        )


def _validate_goal_subject(
    descriptors: list[Any], receipt_subject: Mapping[str, Any]
) -> None:
    goals = [
        row for row in descriptors
        if isinstance(row, Mapping) and row.get("kind") == "statement"
        and isinstance(row.get("searchShape"), Mapping)
        and row["searchShape"].get("role") == "candidate-goal"
    ]
    if len(goals) != 1:
        raise SemanticProjectionError(
            "semantic check artifact has no unique candidate-goal subject"
        )
    shape = goals[0]["searchShape"]
    expected = {
        "module": receipt_subject.get("module"),
        "requestGoal": receipt_subject.get("goal"),
    }
    if any(shape.get(field) != value for field, value in expected.items()):
        raise SemanticProjectionError(
            "semantic check goal subject disagrees with its evidence receipt"
        )


def _validate_request_subject(
    subject: Mapping[str, Any], request: Mapping[str, Any] | None
) -> None:
    if request is None:
        return
    for field in ("module", "goal"):
        expected = request.get(field)
        if expected is not None and subject.get(field) != expected:
            raise SemanticProjectionError(
                f"semantic request {field} disagrees with its check subject"
            )


def _validate_context_subject(
    subject: Mapping[str, Any], check: Mapping[str, Any],
    request: Mapping[str, Any] | None,
    *, check_artifact: Mapping[str, Any] | None = None,
) -> None:
    observed = _observed_context(subject)
    requested = check.get("callerLocalContext")
    if requested is None and request is not None:
        requested = request.get("localContext")
    if requested is None:
        return
    if not isinstance(requested, list):
        raise SemanticProjectionError("semantic request has invalid local context")
    normalized = [dict(row) for row in requested if isinstance(row, Mapping)]
    if len(normalized) != len(requested) or (
        observed[: len(normalized)] != normalized
        and not _owned_context_matches(
            observed, normalized, check_artifact,
            allow_shadowed_names=_check_v4_context_mode(check, check_artifact),
        )
    ):
        raise SemanticProjectionError(
            "semantic observed local context does not preserve the requested prefix"
        )


def _owned_context_matches(observed, requested, artifact, *, allow_shadowed_names=False) -> bool:
    rows = _owned_context_rows(artifact)
    if rows is None:
        return False
    canonical = [{'name': row.get('userName'), 'type': row.get('typeDisplay')} for row in rows]
    if canonical != observed:
        return False
    try:
        validate_observed_local_context(
            rows, requested, allow_shadowed_names=allow_shadowed_names,
        )
    except (TypeError, ValueError, KeyError):
        return False
    return True


def _v4_context_mode(observation) -> bool:
    return (
        isinstance(observation, Mapping)
        and type(observation.get('applicationObservationVersion')) is int
        and observation.get('applicationObservationVersion') == 4
        and isinstance(observation.get('semanticProtocol'), str)
        and observation.get('semanticProtocol') in {
            'ladon-lean-semantic-v4/check-candidate',
            'ladon-lean-semantic-v4/check-candidates',
        }
    )


def _check_v4_context_mode(check, artifact) -> bool:
    return _v4_context_mode(check) or _parent_v4_context_mode(artifact)


def _parent_v4_context_mode(artifact) -> bool:
    if not isinstance(artifact, Mapping):
        return False
    owners = [row for row in artifact.get('subjectRefs', []) if _is_context_owner(row)]
    if len(owners) != 1:
        return False
    if _v4_context_mode(owners[0].get('searchShape')):
        return True
    extensions = artifact.get('extensions')
    return isinstance(extensions, Mapping) and _v4_context_mode(
        extensions.get('ladon.process-observation/v1')
    )


def _scratch_comparison_receipt(receipt, artifact, parent_artifact):
    """Compare scratch spelling only after its resolved parent binds the type.

    Scratch source retains caller spelling while its receipt records the
    elaborated parent context. This comparison view never replaces stored bytes.
    """
    requested = _owned_context_rows(artifact)
    subject = mapping(receipt.get('subject'))
    observed = _observed_context(subject)
    if requested is None or observed[:len(requested)] == requested:
        return receipt
    _validate_scratch_notation(observed, requested, parent_artifact)
    return {**receipt, 'subject': {**subject, 'localContext': requested + observed[len(requested):]}}


def _validate_scratch_notation(observed, requested, parent_artifact):
    if (any(set(row) != {'name', 'type'} for row in requested)
            or not _owned_context_matches(
                observed, requested, parent_artifact,
                allow_shadowed_names=_parent_v4_context_mode(parent_artifact),
            )):
        raise SemanticProjectionError('scratch context has no matching parent structural evidence')


def _owned_context_rows(artifact):
    if artifact is None:
        return None
    owners = [row for row in artifact.get('subjectRefs', []) if _is_context_owner(row)]
    if len(owners) != 1:
        return None
    shape = owners[0].get('searchShape')
    if not isinstance(shape, Mapping):
        return None
    rows = shape.get('localContext', shape.get('orderedLocals'))
    return rows if isinstance(rows, list) and all(isinstance(row, Mapping) for row in rows) else None


def _is_context_owner(row) -> bool:
    return isinstance(row, Mapping) and row.get('kind') in {'candidate-application', 'local-context'}


def _observed_context(subject: Mapping[str, Any]) -> list[Any]:
    observed = subject.get("localContext")
    if not isinstance(observed, list) or any(
        not isinstance(row, Mapping) or set(row) != {"name", "type"}
        for row in observed if isinstance(observed, list)
    ):
        raise SemanticProjectionError("semantic check subject has invalid local context")
    return observed


def _observed_status(check: Mapping[str, Any], status: str, scratch: bool) -> str:
    if scratch or status != "provisional-observation":
        return status
    observed = check.get("observedStatus")
    if observed not in {"accepted", "applicable-with-residuals", "rejected"}:
        raise SemanticProjectionError(
            "provisional observation has no canonical observed status"
        )
    return str(observed)


def _expected_outcome(status: str, scratch: bool) -> str:
    if scratch:
        return "accepted" if status == "compiled" else "failed"
    if status in {"accepted", "applicable-with-residuals"}:
        return "accepted"
    if status == "rejected":
        return "rejected"
    raise SemanticProjectionError(
        f"unsupported checker-backed semantic status: {status}"
    )


__all__ = [
    "validate_observation_semantics", "validate_scratch_parent", "validate_status",
    "validate_weak_observation",
]
