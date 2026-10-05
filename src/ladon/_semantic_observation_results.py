"""Result ownership, transparent subject shape, and failure attribution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._semantic_observation_support import artifact_payload, mapping
from ladon.semantic_application_context import (
    APPLICATION_OBSERVATION_FIELDS,
    validate_application_observation,
)
from ladon.semantic_projection_core import SemanticProjectionError


def validate_check_results(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
    candidate: str,
    status: str,
    scratch: bool,
    *,
    provisional: bool,
) -> None:
    payload = artifact_payload(check_artifact)
    _validate_operation(payload, scratch)
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise SemanticProjectionError("semantic check artifact has no terminal result")
    expected = _expected_check_result(status, scratch)
    _validate_result_values(results, expected, status)
    candidate_result = _validate_result_subject_ownership(
        check_artifact,
        payload,
        results,
        expected,
        candidate,
        scratch,
        provisional,
    )
    _validate_goal_result(check_artifact, results, status, scratch, provisional)
    _validate_transparent_application_shape(
        check,
        receipt,
        check_artifact,
        results,
        candidate,
        status,
        scratch,
        provisional,
    )
    _validate_residual_shape(check, status)
    _validate_failure_stage(check, candidate_result, status, scratch)


def _validate_operation(payload: Mapping[str, Any], scratch: bool) -> None:
    expected = "scratch-compilation" if scratch else "exact-candidate-elaboration"
    if payload.get("operation") != expected:
        raise SemanticProjectionError(
            "semantic observation resolves to a different check operation"
        )


def _validate_result_values(results: list[Any], expected: str, status: str) -> None:
    values = [row.get("result") for row in results if isinstance(row, Mapping)]
    if expected not in values:
        raise SemanticProjectionError(
            "semantic result status disagrees with its registered check artifact"
        )
    allowed = {expected}
    if status == "applicable-with-residuals":
        allowed.add("unchecked")
    forbidden = {"accepted", "unchecked", "rejected", "unknown", "error"} - allowed
    if any(value in forbidden for value in values):
        raise SemanticProjectionError(
            "semantic check artifact contains contradictory terminal results"
        )


def _expected_check_result(status: str, scratch: bool) -> str:
    if status in {"accepted", "applicable-with-residuals", "compiled"}:
        return "accepted"
    return "error" if scratch else "rejected"


def _validate_result_subject_ownership(
    check_artifact: Mapping[str, Any],
    payload: Mapping[str, Any],
    results: list[Any],
    expected_result: str,
    candidate: str,
    scratch: bool,
    provisional: bool,
) -> Mapping[str, Any]:
    expected_kind = _expected_subject_kind(expected_result, provisional)
    matching = _matching_results(results, expected_result, expected_kind)
    if len(matching) != 1:
        label = "scratch" if scratch else "candidate"
        raise SemanticProjectionError(
            f"semantic {label} result does not own its expected subject kind"
        )
    result_ref = dict(matching[0]["subjectRef"])
    _validate_result_ref_ownership(check_artifact, payload, result_ref)
    if expected_kind == "declaration":
        _validate_result_declaration(check_artifact, result_ref, candidate)
    return matching[0]


def _expected_subject_kind(expected_result: str, provisional: bool) -> str:
    if expected_result != "rejected" or provisional:
        return "candidate-application"
    return "declaration"


def _validate_result_ref_ownership(
    check_artifact: Mapping[str, Any],
    payload: Mapping[str, Any],
    result_ref: Mapping[str, Any],
) -> None:
    if dict(result_ref) not in _input_subject_refs(payload):
        raise SemanticProjectionError(
            "semantic check result subject is not a declared input"
        )
    if dict(result_ref) not in _owned_subject_refs(check_artifact):
        raise SemanticProjectionError(
            "semantic check result subject is not artifact-owned"
        )


def _validate_result_declaration(
    check_artifact: Mapping[str, Any], result_ref: Mapping[str, Any], candidate: str
) -> None:
    matching = _matching_owned_descriptors(check_artifact, result_ref)
    if len(matching) != 1 or matching[0].get("display") != candidate:
        raise SemanticProjectionError(
            "rejected semantic result belongs to a different declaration"
        )


def _matching_owned_descriptors(
    check_artifact: Mapping[str, Any], result_ref: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    descriptors = check_artifact.get("subjectRefs")
    rows = descriptors if isinstance(descriptors, list) else []
    return [
        row
        for row in rows
        if isinstance(row, Mapping)
        and {"kind": row.get("kind"), "localId": row.get("localId")}
        == dict(result_ref)
    ]


def _validate_goal_result(
    check_artifact: Mapping[str, Any],
    results: list[Any],
    status: str,
    scratch: bool,
    provisional: bool,
) -> None:
    if _goal_result_not_required(status, scratch, provisional):
        return
    goal_refs = _candidate_goal_refs(check_artifact)
    expected = "unchecked" if status == "applicable-with-residuals" else "accepted"
    matching = _matching_goal_results(results, goal_refs, expected)
    if len(goal_refs) != 1 or len(matching) != 1:
        raise SemanticProjectionError(
            "semantic candidate result is not bound to its goal observation"
        )


def _goal_result_not_required(status: str, scratch: bool, provisional: bool) -> bool:
    return scratch or provisional or status == "rejected"


def _candidate_goal_refs(check_artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    descriptors = check_artifact.get("subjectRefs")
    rows = descriptors if isinstance(descriptors, list) else []
    return [
        {"kind": row.get("kind"), "localId": row.get("localId")}
        for row in rows
        if isinstance(row, Mapping)
        and isinstance(row.get("searchShape"), Mapping)
        and row["searchShape"].get("role") == "candidate-goal"
    ]


def _matching_goal_results(
    results: list[Any], goal_refs: list[dict[str, Any]], expected: str
) -> list[Mapping[str, Any]]:
    return [
        result
        for result in results
        if isinstance(result, Mapping)
        and result.get("result") == expected
        and result.get("subjectRef") in goal_refs
    ]


def _input_subject_refs(payload: Mapping[str, Any]) -> list[Any]:
    inputs = mapping(payload.get("inputs"), "semantic check artifact has no inputs")
    values = inputs.get("subjectRefs")
    if not isinstance(values, list):
        raise SemanticProjectionError(
            "semantic check artifact has invalid subject inputs"
        )
    return values


def _matching_results(
    results: list[Any], expected_result: str, expected_kind: str
) -> list[Mapping[str, Any]]:
    return [
        result
        for result in results
        if isinstance(result, Mapping)
        and result.get("result") == expected_result
        and isinstance(result.get("subjectRef"), Mapping)
        and result["subjectRef"].get("kind") == expected_kind
    ]


def _owned_subject_refs(check_artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    descriptors = check_artifact.get("subjectRefs")
    if not isinstance(descriptors, list):
        raise SemanticProjectionError("semantic check artifact has no owned subjects")
    return [
        {"kind": row.get("kind"), "localId": row.get("localId")}
        for row in descriptors
        if isinstance(row, Mapping)
    ]


def _validate_transparent_application_shape(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    check_artifact: Mapping[str, Any],
    results: list[Any],
    candidate: str,
    status: str,
    scratch: bool,
    provisional: bool,
) -> None:
    application_refs = _application_result_refs(results, status, scratch)
    if not application_refs:
        return
    matching = _owned_application_subjects(check_artifact, application_refs)
    if len(matching) != 1:
        raise SemanticProjectionError(
            "semantic check result has no unique application subject"
        )
    _validate_application_subject(
        check, receipt, matching[0], candidate, scratch, provisional
    )
    _validate_selected_declaration_owner(matching[0], check_artifact, scratch)


def _validate_selected_declaration_owner(subject, check_artifact, scratch) -> None:
    shape = subject.get("searchShape")
    if not scratch and isinstance(shape, Mapping) and shape.get("applicationObservationVersion") == 4:
        selected = shape.get("selectedDeclaration")
        subjects = check_artifact.get("subjectRefs")
        declarations = [row for row in subjects if _selected_declaration_matches(row, selected)] if isinstance(subjects, list) else []
        if len(declarations) != 1:
            raise SemanticProjectionError("v4 selected declaration is not uniquely owned by the check artifact")


def _selected_declaration_matches(row, selected) -> bool:
    if not isinstance(row, Mapping) or not isinstance(selected, Mapping):
        return False
    shape = row.get("searchShape")
    return (
        row.get("kind") == "declaration"
        and row.get("display") == selected.get("name")
        and isinstance(shape, Mapping)
        and shape.get("renderedType") == selected.get("typeDisplay")
        and shape.get("typeStructural") == selected.get("typeStructural")
    )


def _application_result_refs(
    results: list[Any], status: str, scratch: bool
) -> list[Any]:
    expected = _expected_check_result(status, scratch)
    return [
        row["subjectRef"].get("localId")
        for row in results
        if isinstance(row, Mapping)
        and isinstance(row.get("subjectRef"), Mapping)
        and row["subjectRef"].get("kind") == "candidate-application"
        and row.get("result") == expected
    ]


def _owned_application_subjects(
    check_artifact: Mapping[str, Any], application_refs: list[Any]
) -> list[Mapping[str, Any]]:
    subjects = check_artifact.get("subjectRefs")
    subject_rows = subjects if isinstance(subjects, list) else []
    return [
        subject
        for subject in subject_rows
        if isinstance(subject, Mapping) and subject.get("localId") in application_refs
    ]


def _validate_application_subject(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    subject: Mapping[str, Any],
    candidate: str,
    scratch: bool,
    provisional: bool,
) -> None:
    shape = subject.get("searchShape")
    if not isinstance(shape, Mapping):
        raise SemanticProjectionError(
            "semantic application result has no canonical search shape"
        )
    if shape.get("candidate") != candidate:
        raise SemanticProjectionError(
            "semantic application subject belongs to a different candidate"
        )
    if provisional:
        _require_shape_field(check, shape, "processOutcome")
    if scratch:
        _validate_scratch_shape(check, receipt, shape)
        return
    _validate_candidate_shape(check, receipt, shape)


def _validate_candidate_shape(
    check: Mapping[str, Any], receipt: Mapping[str, Any], shape: Mapping[str, Any]
) -> None:
    for field in (
        "applicationTerm",
        "substitutions",
        "residualPremises",
        "dischargedHypotheses",
    ):
        _require_shape_field(check, shape, field)
    if any(field in shape or field in check for field in APPLICATION_OBSERVATION_FIELDS):
        for field in APPLICATION_OBSERVATION_FIELDS:
            _require_shape_field(check, shape, field)
        try:
            validate_application_observation(shape)
        except (ValueError, TypeError) as error:
            raise SemanticProjectionError(str(error)) from error
    _validate_application_context(receipt, shape, prefix=False)


def _require_shape_field(
    check: Mapping[str, Any], shape: Mapping[str, Any], field: str
) -> None:
    if field not in shape or check.get(field) != shape.get(field):
        raise SemanticProjectionError(
            f"semantic observation {field} disagrees with its check subject"
        )


def _validate_scratch_shape(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    shape: Mapping[str, Any],
) -> None:
    for field in ("applicationTerm", "sourceDigest"):
        _require_shape_field(check, shape, field)
    subject = mapping(receipt.get("subject"), "semantic evidence receipt has no subject")
    if shape.get("module") != subject.get("module"):
        raise SemanticProjectionError(
            "scratch module disagrees with its canonical replay subject"
        )
    if shape.get("goal") != subject.get("goal"):
        raise SemanticProjectionError(
            "scratch goal disagrees with its canonical replay subject"
        )
    _validate_application_context(receipt, shape, prefix=True)


def _validate_application_context(
    receipt: Mapping[str, Any], shape: Mapping[str, Any], *, prefix: bool
) -> None:
    subject = mapping(receipt.get("subject"), "semantic evidence receipt has no subject")
    observed = _observed_context(subject)
    shape_context = shape.get("localContext")
    if not isinstance(shape_context, list):
        raise SemanticProjectionError(
            "semantic application subject has invalid local context"
        )
    canonical = _normalize_application_context(shape_context)
    matches = observed[: len(canonical)] == canonical if prefix else observed == canonical
    if not matches:
        raise SemanticProjectionError(
            "semantic application context disagrees with its evidence receipt"
        )


def _observed_context(subject: Mapping[str, Any]) -> list[Any]:
    observed = subject.get("localContext")
    if not isinstance(observed, list):
        raise SemanticProjectionError("semantic check subject has invalid local context")
    if any(
        not isinstance(row, Mapping) or set(row) != {"name", "type"}
        for row in observed
    ):
        raise SemanticProjectionError("semantic check subject has invalid local context")
    return observed


def _normalize_application_context(rows: list[Any]) -> list[dict[str, str]]:
    if not all(isinstance(row, Mapping) for row in rows):
        raise SemanticProjectionError(
            "semantic application subject has invalid local context"
        )
    return [
        {
            "name": str(row.get("userName", row.get("name", ""))),
            "type": str(row.get("typeDisplay", row.get("type", ""))),
        }
        for row in rows
    ]


def _validate_residual_shape(check: Mapping[str, Any], status: str) -> None:
    residuals = check.get("residualPremises")
    if isinstance(residuals, list) and bool(residuals) != (
        status == "applicable-with-residuals"
    ):
        raise SemanticProjectionError(
            "semantic observation status disagrees with its residual-premise evidence"
        )


def _validate_failure_stage(
    check: Mapping[str, Any],
    result: Mapping[str, Any],
    status: str,
    scratch: bool,
) -> None:
    stage = check.get("failureStage")
    if status in {"accepted", "applicable-with-residuals", "compiled"} and stage:
        raise SemanticProjectionError(
            "accepted semantic observation carries a failure stage"
        )
    diagnostics = _result_diagnostics(result)
    if scratch and status != "compiled":
        _validate_scratch_failure(status, stage, diagnostics)
        return
    _validate_process_outcome(check.get("processOutcome"), diagnostics)
    if status == "rejected":
        _validate_rejected_stage(stage, diagnostics)


def _validate_process_outcome(
    outcome: Any, diagnostics: list[Mapping[str, Any]]
) -> None:
    if outcome is not None and not any(
        diagnostic.get("code") == outcome for diagnostic in diagnostics
    ):
        raise SemanticProjectionError(
            "semantic process outcome disagrees with its registered check artifact"
        )


def _validate_rejected_stage(
    stage: Any, diagnostics: list[Mapping[str, Any]]
) -> None:
    if not isinstance(stage, str) or not stage:
        raise SemanticProjectionError(
            "rejected semantic observation omits its failure stage"
        )
    if not any(
        stage in {diagnostic.get("stage"), diagnostic.get("code")}
        for diagnostic in diagnostics
    ):
        raise SemanticProjectionError(
            "candidate failure stage disagrees with its registered check artifact"
        )


def _result_diagnostics(result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        diagnostic
        for diagnostic in result.get("diagnostics", [])
        if isinstance(diagnostic, Mapping)
    ]


def _validate_scratch_failure(
    status: str, stage: Any, diagnostics: list[Mapping[str, Any]]
) -> None:
    if not any(
        diagnostic.get("stage") == "scratch" and diagnostic.get("code") == status
        for diagnostic in diagnostics
    ):
        raise SemanticProjectionError(
            "scratch failure status disagrees with its check diagnostics"
        )
    if stage and not any(
        stage in {diagnostic.get("stage"), diagnostic.get("code")}
        for diagnostic in diagnostics
    ):
        raise SemanticProjectionError(
            "scratch failure stage disagrees with its registered check artifact"
        )


__all__ = ["validate_check_results"]
