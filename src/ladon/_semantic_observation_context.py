"""Bind rejected observations to their recorded typed local-context input.

Older rejected checks omitted this input. Its absence preserves compatibility,
but does not establish independent context correspondence. When either side of
the input/owner pair exists, both sides and one complete ordered shape are required.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._semantic_observation_results import _validate_application_context
from ladon.semantic_projection_core import SemanticProjectionError


def validate_rejected_context(
    artifact: Mapping[str, Any], receipt: Mapping[str, Any],
) -> None:
    """Check independent context evidence using the shared exact-context contract."""

    inputs = _context_rows(artifact['payload']['inputs']['subjectRefs'])
    owners = _context_rows(artifact['subjectRefs'])
    if not inputs and not owners:
        return
    if len(inputs) != 1 or len(owners) != 1 or dict(inputs[0]) != {
        'kind': owners[0]['kind'], 'localId': owners[0]['localId'],
    }:
        raise SemanticProjectionError('rejected context has no unique typed input owner')
    shape = owners[0].get('searchShape')
    if not isinstance(shape, Mapping):
        raise SemanticProjectionError('rejected context has no canonical search shape')
    _validate_application_context(receipt, {'localContext': shape.get('orderedLocals')}, prefix=False)


def _context_rows(rows: list[Any]) -> list[Mapping[str, Any]]:
    return [
        row for row in rows
        if isinstance(row, Mapping) and row.get('kind') == 'local-context'
    ]
