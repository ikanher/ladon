"""Check execution selection against the original input-owned environment.

Only recorded bytes are inspected. Redacted context identity is retained as an
opaque digest; this reader cannot reconstruct the original process environment
or authenticate a producer. Absent context metadata supplies no binding evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.evidence_receipt import project_evidence_receipt
from ladon.proofir_v3 import validate_envelope_batch
from ladon.semantic_projection_core import SemanticProjectionError

UNRECORDED_EXECUTION = 'Historical execution binding has no independent recorded toolchain context.'


def project_recorded_execution_receipt(
    receipt: Mapping[str, Any], *, recorded: bool, projection_kind: str,
) -> dict[str, Any]:
    """Preserve recorded binding or project an unbound historical observation.

    A live state requires executed binding in the closed evidence model. Without
    independent recording, pass through the stored-read transition before any
    renderer or aggregate transition; never relax that model invariant.
    """
    if not recorded:
        receipt = project_evidence_receipt(
            receipt, projection_kind="sqlite-row", execution_binding="none",
            limitations=(UNRECORDED_EXECUTION,),
        )
    return project_evidence_receipt(receipt, projection_kind=projection_kind)


def validate_recorded_execution_binding(
    check: Mapping[str, Any], receipt: Mapping[str, Any],
    environments: Sequence[Mapping[str, Any]],
) -> bool:
    """Reject recorded contradictions; return false for missing historical evidence."""

    if not environments:
        return False
    if len(environments) != 1:
        raise SemanticProjectionError('execution binding has ambiguous environment inputs')
    environment = environments[0]
    _validate_environment_input(check, environment)
    options = environment['payload']['options']
    worker_recorded = _validate_observed_worker_identity(check, options)
    if 'toolchainContext' not in options or options['toolchainContext'] == 'ambient-unbound':
        return False
    recorded = options['toolchainContext']
    context = _recorded_context(recorded)
    _validate_pinned_worker_context(context, options)
    expected = {'explicit': 'explicit-pinned', 'ambient': 'ambient-observed'}[context['selectionMode']]
    if receipt['executionBinding'] != expected:
        raise SemanticProjectionError('receipt execution binding contradicts recorded selection mode')
    return _validate_worker_identity(check, context, worker_recorded)


def _validate_environment_input(check: Mapping[str, Any], environment: Mapping[str, Any]) -> None:
    inputs = check['payload']['inputs']
    if (
        environment.get('artifactKind') != 'proofir.environment'
        or environment.get('artifactId') not in inputs['artifactRefs']
        or environment.get('environmentRef') != check['environmentRef']
        or inputs['environmentRef'] != check['environmentRef']
    ):
        raise SemanticProjectionError('execution environment is not the exact declared input owner')
    validate_envelope_batch([dict(environment), dict(check)])


def _recorded_context(recorded: Any) -> Mapping[str, Any]:
    try:
        context = json.loads(recorded, object_pairs_hook=_unique_object)
    except (TypeError, ValueError, RecursionError) as error:
        raise SemanticProjectionError('recorded execution context is invalid JSON') from error
    mode = context.get('selectionMode') if isinstance(context, Mapping) else None
    if not isinstance(mode, str) or mode not in {'explicit', 'ambient'}:
        raise SemanticProjectionError('recorded execution context has no supported selection mode')
    _validate_context_digests(context)
    _validate_context_pin(context)
    return context


def _validate_context_digests(context: Mapping[str, Any]) -> None:
    for field in ('leanIdentity', 'lakeIdentity', 'pinDigest', 'sourceTreeIdentity', 'contextIdentity'):
        value = context.get(field)
        if not isinstance(value, str) or re.fullmatch(r'sha256:[0-9a-f]{64}', value) is None:
            raise SemanticProjectionError('recorded execution context has invalid content identities')


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate execution context key')
        result[key] = value
    return result


def _validate_context_pin(context: Mapping[str, Any]) -> None:
    content = context.get('pinContent')
    if not isinstance(content, str) or not content:
        raise SemanticProjectionError('recorded execution context has no pin content')
    expected = 'sha256:' + hashlib.sha256(content.encode()).hexdigest()
    if expected != context['pinDigest']:
        raise SemanticProjectionError('recorded execution pin content contradicts its digest')


def _validate_worker_identity(
    check: Mapping[str, Any], context: Mapping[str, Any], worker_recorded: bool,
) -> bool:
    executable = check['payload']['checker']['executableDigest']
    selected_identity = (
        context['selectionMode'] == 'explicit'
        or check['payload']['guarantee']['authorityBasis'] == 'process-observation'
    )
    if selected_identity and executable != context['leanIdentity']:
        raise SemanticProjectionError('check execution identity contradicts selected Lean toolchain')
    if not worker_recorded:
        # Legacy ambient contexts may identify an elan launcher rather than the
        # worker binary. Without a recorded runtime identity that relation is unknown.
        return executable == context['leanIdentity']
    return True


def _validate_observed_worker_identity(check: Mapping[str, Any], options: Mapping[str, Any]) -> bool:
    # Scratch and interrupted batch receipts record the selected process/toolchain,
    # not another elaborator check. Runtime evidence belongs to the observed frame.
    if check['payload']['guarantee']['authorityBasis'] == 'process-observation':
        return False
    if 'observedLeanExecutableDigest' not in options:
        return False
    if options['observedLeanExecutableDigest'] != check['payload']['checker']['executableDigest']:
        raise SemanticProjectionError('check execution identity contradicts recorded Lean worker')
    return True


def _validate_pinned_worker_context(context: Mapping[str, Any], options: Mapping[str, Any]) -> None:
    if (
        context['selectionMode'] == 'explicit'
        and 'observedLeanExecutableDigest' in options
        and options['observedLeanExecutableDigest'] != context['leanIdentity']
    ):
        raise SemanticProjectionError('recorded execution worker contradicts explicit selection')
