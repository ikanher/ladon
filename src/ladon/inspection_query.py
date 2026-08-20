"""Finite filters, exact lookup, and fingerprint-bound inspection pages."""

from __future__ import annotations

import base64
import binascii
import bisect
import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from ladon.inspection_models import (
    INSPECTION_CURSOR_SCHEMA,
    INSPECTION_NOUNS,
    InspectionCompatibilityError,
    InspectionDataset,
    InspectionInvocationError,
    InspectionNotFoundError,
    InspectionPage,
    InspectionQuery,
    InspectionRow,
)

DEFAULT_INSPECTION_LIMIT = 50
MAX_INSPECTION_LIMIT = 500
FILTERS_BY_NOUN: Mapping[str, frozenset[str]] = {
    "modules": frozenset(
        {
            "module",
            "path",
            "tag",
            "role",
            "population",
            "authority",
            "status",
            "integrity-group",
        }
    ),
    "declarations": frozenset(
        {
            "module",
            "name",
            "kind",
            "candidate-status",
            "candidate-name",
            "privacy",
            "locality",
            "namespace",
            "section",
            "modifier",
            "population",
            "authority",
            "candidate-family",
            "integrity-group",
        }
    ),
    "imports": frozenset(
        {
            "module",
            "target",
            "path",
            "boundary",
            "population",
            "authority",
        }
    ),
    "audits": frozenset(
        {
            "module",
            "kind",
            "subject",
            "status",
            "result-status",
            "population",
            "authority",
        }
    ),
    "options": frozenset(
        {
            "module",
            "option",
            "option-class",
            "scope",
            "status",
            "population",
            "authority",
        }
    ),
    "resources": frozenset(
        {
            "module",
            "option",
            "scope",
            "status",
            "meaning",
            "pressure",
            "population",
            "authority",
        }
    ),
    "proof-mechanisms": frozenset(
        {
            "module",
            "declaration",
            "mechanism",
            "kind",
            "attribute",
            "candidate-family",
            "population",
            "authority",
        }
    ),
}


def parse_inspection_filter(value: str) -> tuple[str, str]:
    """Parse one finite ``FIELD=VALUE`` expression."""

    field, separator, selected = value.partition("=")
    field = field.strip().lower().replace("_", "-")
    selected = selected.strip()
    if not separator or not field or not selected:
        raise InspectionInvocationError(
            "inspection filters must use non-empty FIELD=VALUE syntax"
        )
    return field, selected


def positive_inspection_limit(value: str) -> int:
    """Parse a bounded page size for argparse and library callers."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise InspectionInvocationError("inspection limit must be an integer") from exc
    if not 1 <= parsed <= MAX_INSPECTION_LIMIT:
        raise InspectionInvocationError(
            f"inspection limit must be between 1 and {MAX_INSPECTION_LIMIT}"
        )
    return parsed


def inspect_dataset(
    dataset: InspectionDataset,
    *,
    filters: Iterable[tuple[str, str]] = (),
    identifier: str | None = None,
    cursor: str | None = None,
    limit: int = DEFAULT_INSPECTION_LIMIT,
) -> InspectionPage:
    """Select one stable page without reading any source checkout."""

    query = normalized_query(
        dataset.noun,
        filters=filters,
        identifier=identifier,
        limit=limit,
    )
    if identifier is not None:
        return _exact_page(dataset, query, cursor=cursor)
    unavailable_fields = _unavailable_filter_fields(dataset, query.filters)
    matching = tuple(
        row
        for row in sorted(dataset.rows, key=lambda value: value.order_key)
        if not unavailable_fields and _row_matches(row, query.filters)
    )
    start = _cursor_start(dataset, query, matching, cursor)
    selected = matching[start : start + query.limit]
    after = len(matching) - start - len(selected)
    next_cursor = (
        _encode_cursor(dataset, query, selected[-1].order_key)
        if selected and after
        else None
    )
    diagnostics = _query_diagnostics(
        dataset.unavailable_reason,
        unavailable_fields,
    )
    return InspectionPage(
        artifact=dataset.artifact,
        query=query,
        collection_coverage=dataset.coverage,
        rows=selected,
        matching_total=len(matching),
        before_count=start,
        after_count=after,
        next_cursor=next_cursor,
        diagnostics=diagnostics,
    )


def _unavailable_filter_fields(
    dataset: InspectionDataset,
    filters: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    """Identify supported predicates absent from represented backend rows."""

    special = {"authority", "population"}
    return tuple(
        field
        for field, _value in filters
        if field not in special
        and dataset.rows
        and not any(field in row.fields for row in dataset.rows)
    )


def _query_diagnostics(
    unavailable_collection: str | None,
    unavailable_fields: tuple[str, ...],
) -> tuple[Mapping[str, Any], ...]:
    diagnostics: list[Mapping[str, Any]] = []
    if unavailable_collection:
        diagnostics.append(
            {
                "code": "inspection.collection_unavailable",
                "message": unavailable_collection,
            }
        )
    if unavailable_fields:
        diagnostics.append(
            {
                "code": "inspection.filter_field_unavailable",
                "message": (
                    "selected backend rows do not contain filter field(s): "
                    + ", ".join(unavailable_fields)
                ),
                "fields": list(unavailable_fields),
            }
        )
    return tuple(diagnostics)


def normalized_query(
    noun: str,
    *,
    filters: Iterable[tuple[str, str]],
    identifier: str | None,
    limit: int,
) -> InspectionQuery:
    """Validate and fingerprint one semantically normalized query."""

    if noun not in INSPECTION_NOUNS:
        raise InspectionInvocationError(f"unsupported inspection noun: {noun}")
    normalized = _normalized_filters(filters)
    _validate_filters(noun, normalized, identifier)
    selected_limit = positive_inspection_limit(str(limit))
    fingerprint = _query_fingerprint(noun, normalized, identifier)
    return InspectionQuery(
        noun=noun,
        filters=normalized,
        identifier=identifier,
        limit=selected_limit,
        fingerprint=fingerprint,
    )


def _normalized_filters(
    filters: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    """Canonicalize order, spelling, and duplicate predicates."""

    return tuple(
        sorted(
            {
                (field.strip().lower().replace("_", "-"), value.strip())
                for field, value in filters
            }
        )
    )


def _validate_filters(
    noun: str,
    normalized: tuple[tuple[str, str], ...],
    identifier: str | None,
) -> None:
    """Reject fields outside the finite noun vocabulary."""

    invalid = sorted({field for field, _value in normalized} - FILTERS_BY_NOUN[noun])
    if invalid:
        supported = ", ".join(sorted(FILTERS_BY_NOUN[noun]))
        raise InspectionInvocationError(
            f"unsupported {noun} filter(s): {', '.join(invalid)}; "
            f"supported filters: {supported}"
        )
    if any(not field or not value for field, value in normalized):
        raise InspectionInvocationError(
            "inspection filters require non-empty fields and values"
        )
    if identifier is not None and (not identifier.strip() or normalized):
        raise InspectionInvocationError(
            "exact --id lookup cannot be combined with --filter"
        )


def _query_fingerprint(
    noun: str,
    filters: tuple[tuple[str, str], ...],
    identifier: str | None,
) -> str:
    """Bind normalized semantics independently of argument ordering."""

    payload = {
        "noun": noun,
        "filters": [list(row) for row in filters],
        "id": identifier,
        "ordering": "noun-stable-key-v1",
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _exact_page(
    dataset: InspectionDataset,
    query: InspectionQuery,
    *,
    cursor: str | None,
) -> InspectionPage:
    """Resolve one exact canonical stable identity."""

    if cursor is not None:
        raise InspectionInvocationError(
            "exact --id lookup cannot be combined with --cursor"
        )
    selected = tuple(row for row in dataset.rows if row.identifier == query.identifier)
    if not selected:
        if dataset.coverage.get("completeness") != "complete":
            raise InspectionCompatibilityError(
                f"cannot establish absence of {query.identifier}; "
                f"{dataset.noun} coverage is "
                f"{dataset.coverage.get('completeness', 'unknown')}"
            )
        raise InspectionNotFoundError(
            f"{dataset.noun} identity not found: {query.identifier}"
        )
    if len(selected) != 1:
        raise InspectionCompatibilityError(
            f"duplicate canonical {dataset.noun} identity: {query.identifier}"
        )
    return InspectionPage(
        artifact=dataset.artifact,
        query=query,
        collection_coverage=dataset.coverage,
        rows=selected,
        matching_total=1,
        before_count=0,
        after_count=0,
        next_cursor=None,
    )


def _row_matches(
    row: InspectionRow,
    filters: tuple[tuple[str, str], ...],
) -> bool:
    """Apply exact finite-vocabulary predicates to one normalized row."""

    for field, selected in filters:
        if not _field_matches(row, field, selected):
            return False
    return True


def _field_matches(row: InspectionRow, field: str, selected: str) -> bool:
    if field == "authority":
        value: Any = row.authority
    elif field == "population":
        value = row.population
    else:
        value = row.fields.get(field)
    if isinstance(value, (list, tuple, set, frozenset)):
        return selected in {str(item) for item in value}
    if isinstance(value, bool):
        return selected.lower() == str(value).lower()
    return value is not None and str(value) == selected


def _cursor_start(
    dataset: InspectionDataset,
    query: InspectionQuery,
    rows: tuple[InspectionRow, ...],
    cursor: str | None,
) -> int:
    if cursor is None:
        return 0
    payload = _decode_cursor(cursor)
    _validate_cursor_binding(payload, dataset, query)
    raw_key = payload.get("lastKey")
    if not isinstance(raw_key, list) or not all(
        isinstance(value, str) for value in raw_key
    ):
        raise InspectionCompatibilityError("inspection cursor last key is malformed")
    last_key = tuple(raw_key)
    keys = [row.order_key for row in rows]
    index = bisect.bisect_right(keys, last_key)
    if index == 0 or keys[index - 1] != last_key:
        raise InspectionCompatibilityError(
            "inspection cursor last key is absent from selected evidence"
        )
    return index


def _encode_cursor(
    dataset: InspectionDataset,
    query: InspectionQuery,
    last_key: tuple[str, ...],
) -> str:
    body = {
        "schema": INSPECTION_CURSOR_SCHEMA,
        "artifactFingerprint": dataset.artifact.fingerprint,
        "liveFingerprint": dataset.artifact.live_fingerprint,
        "queryFingerprint": query.fingerprint,
        "limit": query.limit,
        "lastKey": list(last_key),
    }
    payload = {
        **body,
        "checksum": _cursor_checksum(body),
    }
    return base64.urlsafe_b64encode(_canonical_bytes(payload)).decode("ascii")


def _decode_cursor(cursor: str) -> Mapping[str, Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        decoded = base64.urlsafe_b64decode((cursor + padding).encode("ascii"))
        payload = json.loads(decoded)
    except (binascii.Error, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise InspectionCompatibilityError("inspection cursor is malformed") from exc
    if not isinstance(payload, Mapping):
        raise InspectionCompatibilityError("inspection cursor is malformed")
    checksum = payload.get("checksum")
    body = {key: value for key, value in payload.items() if key != "checksum"}
    if checksum != _cursor_checksum(body):
        raise InspectionCompatibilityError("inspection cursor checksum does not match")
    return payload


def _validate_cursor_binding(
    payload: Mapping[str, Any],
    dataset: InspectionDataset,
    query: InspectionQuery,
) -> None:
    expected = {
        "schema": INSPECTION_CURSOR_SCHEMA,
        "artifactFingerprint": dataset.artifact.fingerprint,
        "liveFingerprint": dataset.artifact.live_fingerprint,
        "queryFingerprint": query.fingerprint,
        "limit": query.limit,
    }
    mismatches = [key for key, value in expected.items() if payload.get(key) != value]
    if mismatches:
        raise InspectionCompatibilityError(
            "stale inspection cursor; mismatched " + ", ".join(sorted(mismatches))
        )


def _cursor_checksum(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        INSPECTION_CURSOR_SCHEMA.encode("ascii") + b"\0" + _canonical_bytes(payload)
    ).hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


__all__ = [
    "DEFAULT_INSPECTION_LIMIT",
    "FILTERS_BY_NOUN",
    "MAX_INSPECTION_LIMIT",
    "inspect_dataset",
    "normalized_query",
    "parse_inspection_filter",
    "positive_inspection_limit",
]
