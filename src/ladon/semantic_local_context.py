"""Ordered caller-local context validation and Lean goal adaptation."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any


def validate_local_context(
    rows: Sequence[Mapping[str, str]],
    *,
    valid_name: Callable[[str], bool],
    validate_type: Callable[[str], None],
) -> None:
    if len(rows) > 256:
        raise ValueError("semantic local context exceeds the row cap")
    total = 0
    names: set[str] = set()
    for row in rows:
        name, type_text = _validate_requested_row(row, valid_name, validate_type, names)
        total += len(name.encode()) + len(type_text.encode())
    if total > 1024 * 1024:
        raise ValueError("semantic local context exceeds the byte cap")


def _validate_requested_row(
    row: Mapping[str, str],
    valid_name: Callable[[str], bool],
    validate_type: Callable[[str], None],
    names: set[str],
) -> tuple[str, str]:
    name, type_text = row.get("name"), row.get("type")
    if not isinstance(name, str) or not valid_name(name):
        raise ValueError("semantic local context contains an invalid name")
    if not isinstance(type_text, str):
        raise TypeError("semantic local context contains an invalid type")
    if name in names:
        raise ValueError("semantic local context contains duplicate names")
    names.add(name)
    if any(token in type_text for token in ("\n", "\r", ":=", ";")) or re.search(
        r"\)\s*[([{]", type_text
    ):
        raise ValueError("semantic local context type contains unsupported binder syntax")
    validate_type(type_text)
    return name, type_text


def goal_with_local_context(goal: str, rows: Sequence[Mapping[str, str]]) -> str:
    if not rows:
        return goal
    binders = " ".join(f"({row['name']} : {row['type']})" for row in rows)
    return f"∀ {binders}, {goal}"


def validate_observed_local_context(
    observed: Sequence[Mapping[str, Any]], requested: Sequence[Mapping[str, str]],
    *, allow_shadowed_names: bool = False,
) -> None:
    prefix = observed[: len(requested)]
    if len(prefix) != len(requested):
        raise ValueError("Lean semantic helper did not elaborate the requested local context")
    for index, (observed_row, requested_row) in enumerate(zip(prefix, requested)):
        _validate_observed_row(observed_row, requested_row, observed[:index])
    _validate_unique_observed_rows(observed, allow_shadowed_names=allow_shadowed_names)


def _validate_observed_row(
    observed_row: Mapping[str, Any], requested_row: Mapping[str, str],
    context: Sequence[Mapping[str, Any]],
) -> None:
    _validate_observed_row_shape(observed_row)
    name = requested_row["name"]
    if observed_row.get("userName") != name:
        raise ValueError("Lean semantic helper returned a reordered local context")
    displayed = _normalize_type(observed_row.get("typeDisplay"))
    requested_type = _normalize_type(requested_row["type"])
    if displayed != requested_type:
        if not _matches_closed_constant_notation(observed_row, requested_type, displayed):
            raise ValueError(f"Lean semantic helper returned a mismatched type for local {name}")
        displayed = requested_type
    _validate_structural_type(observed_row, displayed, name, context)


def _matches_closed_constant_notation(row, requested, displayed) -> bool:
    # Pretty notation is insufficient: require the exact monomorphic constant
    # in Lean's serialized type as well as its recognized display spelling.
    notation = {'Nat': 'ℕ', 'Int': 'ℤ', 'Real': 'ℝ'}
    structural = _normalize_type(row.get('typeStructural'))
    return displayed == notation.get(requested) and structural == f'Lean.Expr.const `{requested} []'


def _validate_structural_type(observed_row, displayed, name, context) -> None:
    structural = _normalize_type(observed_row.get("typeStructural"))
    displayed = _constant_comparison_display(structural, displayed)
    names = lambda value: set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", value))
    if structural.isidentifier() and structural not in displayed.split():
        _raise_structural_mismatch(name)
    if structural.split()[:1] == displayed.split()[:1] and structural != displayed:
        _raise_structural_mismatch(name)
    if (names(structural) and names(displayed) and names(structural).isdisjoint(names(displayed))
            and not _contextual_structural_type(observed_row, displayed, structural, context)):
        _raise_structural_mismatch(name)


def _constant_comparison_display(structural, displayed):
    # A caller may use the printed notation itself. Check a closed constant
    # against its ordinary name so ASCII token extraction cannot ignore ℝ.
    if structural.startswith('Lean.Expr.const ') or structural.isidentifier():
        return {'ℕ': 'Nat', 'ℤ': 'Int', 'ℝ': 'Real'}.get(displayed, displayed)
    return displayed


def _contextual_structural_type(row, displayed, structural, context) -> bool:
    # Lean represents Prop as Sort 0 and dependent types with internal fvar IDs.
    # Their serialized trees need not contain the caller's printed identifiers.
    if displayed == 'Prop' and structural == 'Lean.Expr.sort (Lean.Level.zero)':
        return True
    identifiers = set(re.findall(r'[A-Za-z_][A-Za-z0-9_.]*', displayed))
    expected = {
        item['localId'] for item in context
        if _mentions_local(identifiers, item['userName'])
    }
    # collectFVars follows expression order, which may differ from binder order.
    # Require exact prior membership and reject duplicate side-channel entries.
    dependencies = row['dependencies']
    return (bool(expected) and 'Lean.Expr.fvar' in structural
            and len(dependencies) == len(expected) and set(dependencies) == expected)


def _mentions_local(identifiers: set[str], name: str) -> bool:
    # `point.epoch` refers to the earlier local `point` through a projection.
    return any(token == name or token.startswith(name + '.') for token in identifiers)


def _raise_structural_mismatch(name: str) -> None:
    raise ValueError(
        f"Lean semantic helper returned a structurally mismatched type for local {name}"
    )


def _validate_unique_observed_rows(
    observed: Sequence[Mapping[str, Any]], *, allow_shadowed_names: bool = False,
) -> None:
    local_ids: set[str] = set()
    local_names: set[str] = set()
    for row in observed:
        _validate_observed_row_shape(row)
        if row["localId"] in local_ids or (
            not allow_shadowed_names and row["userName"] in local_names
        ):
            raise ValueError("Lean semantic helper returned duplicate local identity")
        local_ids.add(row["localId"])
        local_names.add(row["userName"])


def _validate_observed_row_shape(row: Mapping[str, Any]) -> None:
    required = {
        "localId",
        "userName",
        "binderInfo",
        "typeDisplay",
        "typeStructural",
        "valueDisplay",
        "valueStructural",
        "dependencies",
        "origin",
    }
    if set(row) != required:
        raise ValueError("Lean semantic helper returned an incomplete local context row")
    if any(not isinstance(row[field], str) for field in required - {"dependencies"}):
        raise TypeError("Lean semantic helper returned malformed local context metadata")
    if not isinstance(row["dependencies"], list) or any(
        not isinstance(item, str) for item in row["dependencies"]
    ):
        raise TypeError("Lean semantic helper returned malformed local dependencies")


def _normalize_type(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


__all__ = [
    "goal_with_local_context",
    "validate_local_context",
    "validate_observed_local_context",
]
