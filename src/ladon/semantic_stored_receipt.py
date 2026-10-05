"""Validate stored semantic receipts against their canonical check subjects.

The canonical result and transparent input shapes supply the observation used
by the existing semantic contract validator. Receipt hashes alone cannot bind
an outcome, goal, candidate, or context to that check. Unsupported operations
fail closed when they carry a receipt; legacy artifacts without receipts remain
readable through their existing artifact contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._semantic_observation_contract import validate_observation_semantics, validate_status
from ladon._semantic_observation_support import SCRATCH_STATUSES
from ladon.semantic_application_context import (
    APPLICATION_OBSERVATION_FIELDS,
    validate_application_observation,
)


def validate_stored_observation_receipt(
    artifact: Mapping[str, Any], receipt: Mapping[str, Any],
) -> None:
    """Reject receipt/owner contradictions without executing or changing evidence."""

    payload = artifact['payload']
    operation = payload['operation']
    if operation not in {'exact-candidate-elaboration', 'scratch-compilation'}:
        raise ValueError('stored receipt belongs to an unsupported semantic operation')
    scratch = operation == 'scratch-compilation'
    status = _stored_status(payload['results'], scratch)
    check = _stored_check(artifact)
    if status in {'rejected', 'failed'}:
        check['failureStage'] = _failure_stage(payload['results'])
    provisional = not scratch and receipt['authorityBasis'] == 'process-observation'
    if provisional:
        check['observedStatus'] = status
        status = 'provisional-observation'
    validate_status(status, scratch)
    validate_observation_semantics(
        check, receipt, artifact, receipt['subject'].get('candidate'), status,
        request=None, scratch=scratch,
    )


def _stored_status(results: list[Mapping[str, Any]], scratch: bool) -> str:
    """Decode only registered result combinations; contradictory children reject."""

    values = frozenset(row['result'] for row in results)
    if scratch:
        if values == {'error'}:
            return _scratch_failure_status(results)
        statuses = {frozenset({'accepted'}): 'compiled'}
    else:
        statuses = {
            frozenset({'accepted'}): 'accepted',
            frozenset({'accepted', 'unchecked'}): 'applicable-with-residuals',
            frozenset({'rejected'}): 'rejected',
        }
    if values not in statuses:
        raise ValueError('stored semantic check has contradictory or unsupported terminal results')
    return statuses[values]


def _scratch_failure_status(results: list[Mapping[str, Any]]) -> str:
    """Retain the exact registered resource/process failure classification."""

    codes = {
        diagnostic['code'] for row in results for diagnostic in row.get('diagnostics', [])
        if diagnostic.get('stage') == 'scratch'
    }
    if len(codes) != 1 or not codes <= SCRATCH_STATUSES - {'compiled', 'not-run'}:
        raise ValueError('stored scratch failure has no unique registered outcome')
    return next(iter(codes))


def _stored_check(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Read the exact typed, input-owned application shape without receipt inference."""

    inputs = artifact['payload']['inputs']['subjectRefs']
    applications = _input_owned_applications(artifact, inputs)
    if len(applications) > 1:
        raise ValueError('stored semantic check has ambiguous application subjects')
    if not applications:
        return {}
    shape = applications[0].get('searchShape')
    if not isinstance(shape, Mapping):
        raise TypeError('stored semantic application has no canonical search shape')
    if any(field in shape for field in APPLICATION_OBSERVATION_FIELDS):
        validate_application_observation(shape)
    fields = (
        'applicationTerm', 'substitutions', 'residualPremises', 'dischargedHypotheses',
        'sourceDigest', 'processOutcome', 'applicationObservationVersion',
        'semanticProtocol', 'residualContexts', 'selectedDeclaration',
    )
    return {field: shape[field] for field in fields if field in shape}


def _input_owned_applications(artifact, inputs):
    return [
        row for row in artifact['subjectRefs']
        if row['kind'] == 'candidate-application'
        and {'kind': row['kind'], 'localId': row['localId']} in inputs
    ]


def _failure_stage(results: list[Mapping[str, Any]]) -> str | None:
    """Select the canonical failure diagnostic, leaving validation to its owner."""

    diagnostics = [diagnostic for row in results for diagnostic in row.get('diagnostics', [])]
    ordinary = [row for row in diagnostics if row.get('stage') != 'batch-process']
    if ordinary:
        return ordinary[0].get('stage') or ordinary[0].get('code')
    return None
