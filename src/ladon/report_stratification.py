"""Deterministic evidence-stratum selection for bounded report projections."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def stratified_selection(
    value: list[Any],
    *,
    limit: int,
    pointer: str,
    strata: list[dict[str, Any]],
) -> list[Any]:
    """Select a bounded deterministic allowance from every present stratum."""

    if not _stratifiable_rows(value):
        return value[:limit]
    grouped: dict[
        tuple[str, str, str, str, str],
        list[Mapping[str, Any]],
    ] = {}
    for row in value:
        descriptor = _stratum_descriptor(row)
        key = tuple(descriptor.values())
        grouped.setdefault(key, []).append(row)
    for rows in grouped.values():
        rows.sort(key=_projection_row_key)
    ordered_keys = sorted(grouped, key=_stratum_sort_key)
    selected, visible = _bounded_stratum_rows(grouped, ordered_keys, limit)
    strata.extend(
        _stratum_rows(
            pointer=pointer,
            grouped=grouped,
            ordered_keys=ordered_keys,
            visible=visible,
        )
    )
    return list(selected)


def stratifiable_rows(value: list[Any]) -> bool:
    """Return whether a list is a typed evidence-record population."""

    if not value or not all(isinstance(row, Mapping) for row in value):
        return False
    discriminator_keys = {
        "auditCommands",
        "evidenceKind",
        "kind",
        "severity",
        "status",
        "resultStatus",
        "candidateStatus",
        "population",
        "promotion_population",
        "role",
        "roles",
        "resourceDirectives",
        "subtype",
    }
    return any(
        not discriminator_keys.isdisjoint(row)
        for row in value
        if isinstance(row, Mapping)
    )


def projection_stratum_key(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the exact key used by bounded evidence-stratum selection."""

    return tuple(_stratum_descriptor(row).values())


def _bounded_stratum_rows(
    grouped: Mapping[
        tuple[str, str, str, str, str],
        list[Mapping[str, Any]],
    ],
    ordered_keys: list[tuple[str, str, str, str, str]],
    limit: int,
) -> tuple[
    list[Mapping[str, Any]],
    dict[tuple[str, str, str, str, str], int],
]:
    """Take up to the per-stratum allowance without erasing later strata."""

    selected: list[Mapping[str, Any]] = []
    visible: dict[tuple[str, str, str, str, str], int] = {}
    for key in ordered_keys:
        retained = grouped[key][:limit]
        selected.extend(retained)
        visible[key] = len(retained)
    return selected, visible


def _stratum_rows(
    *,
    pointer: str,
    grouped: Mapping[
        tuple[str, str, str, str, str],
        list[Mapping[str, Any]],
    ],
    ordered_keys: list[tuple[str, str, str, str, str]],
    visible: Mapping[tuple[str, str, str, str, str], int],
) -> list[dict[str, Any]]:
    """Return exact total/visible descriptors for every selected population."""

    fields = (
        "evidenceKind",
        "severity",
        "status",
        "population",
        "role",
    )
    return [
        {
            "pointer": pointer,
            "descriptor": dict(zip(fields, key)),
            "visible": visible[key],
            "total": len(grouped[key]),
        }
        for key in ordered_keys
    ]


def _stratifiable_rows(value: list[Any]) -> bool:
    """Compatibility alias for the shared public predicate."""

    return stratifiable_rows(value)


def _stratum_descriptor(row: Mapping[str, Any]) -> dict[str, str]:
    """Return the fixed five-axis stratum descriptor for one evidence row."""

    return {
        "evidenceKind": _evidence_kind(row),
        "severity": _first_text(row, ("severity",)),
        "status": _first_text(
            row,
            ("status", "resultStatus", "candidateStatus"),
        ),
        "population": _first_text(
            row,
            ("population", "promotion_population", "containingPopulation"),
        ),
        "role": _role_text(row),
    }


def _first_text(
    row: Mapping[str, Any],
    keys: tuple[str, ...],
) -> str:
    """Return the first non-empty scalar discriminator."""

    for key in keys:
        value = row.get(key)
        if not isinstance(value, (list, Mapping)) and value is not None and value != "":
            return str(value)
    return "unspecified"


def _role_text(row: Mapping[str, Any]) -> str:
    """Return a stable scalar role discriminator."""

    command_only = row.get("commandOnly")
    if isinstance(command_only, bool):
        return "command_only" if command_only else "declaration_bearing"
    scalar = _first_text(row, ("role", "subtype"))
    if scalar != "unspecified":
        return scalar
    roles = row.get("roles")
    if isinstance(roles, list):
        values = sorted(str(value) for value in roles if value)
        if values:
            return "|".join(values)
    return "unspecified"


def _evidence_kind(row: Mapping[str, Any]) -> str:
    """Classify nested audit surfaces without changing their canonical wire."""

    direct = _first_text(row, ("evidenceKind", "kind", "option"))
    if direct != "unspecified":
        return direct
    audits = row.get("auditCommands")
    resources = row.get("resourceDirectives")
    has_audits = isinstance(audits, list) and bool(audits)
    has_resources = isinstance(resources, list) and bool(resources)
    if has_audits and has_resources:
        return "audit_and_resource_surface"
    if has_audits:
        return "audit_surface"
    if has_resources:
        return "resource_surface"
    return "unspecified"


def _stratum_sort_key(
    key: tuple[str, str, str, str, str],
) -> tuple[int, tuple[str, str, str, str, str]]:
    """Prioritize severe strata, then use the complete descriptor."""

    severity = key[1]
    priority = {"error": 0, "warning": 1, "info": 2}.get(severity, 3)
    return priority, key


def _projection_row_key(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Return a stable tie-break key independent of input list order."""

    identity = next(
        (
            str(row[key])
            for key in (
                "id",
                "stable_key",
                "module",
                "declaration",
                "subject",
                "path",
                "name",
            )
            if row.get(key) is not None
            and row.get(key) != ""
            and not isinstance(row.get(key), (list, Mapping))
        ),
        "",
    )
    encoded = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return identity, encoded
