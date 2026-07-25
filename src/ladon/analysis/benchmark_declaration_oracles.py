"""Declaration-surface oracles for portable Lean benchmark fixtures."""

from __future__ import annotations

from typing import Any, Mapping


Oracle = Mapping[str, Any]
Payload = Mapping[str, Any]


def check_declaration_required_fields(
    payload: Payload,
    oracle: Oracle,
) -> tuple[bool, Any]:
    """Check declaration-surface presence and required non-empty fields."""

    row = find_by_key(
        declaration_rows(payload),
        "declaration",
        str(oracle["declaration"]),
    )
    required = tuple(str(field) for field in oracle.get("requiredFields", ()))
    missing = [
        field
        for field in required
        if row is None or nested_value(row, field) in (None, "", [])
    ]
    mismatches = expected_field_mismatches(row, oracle)
    return not missing and not mismatches, {
        "present": row is not None,
        "missingFields": missing,
        "mismatchedFields": mismatches,
    }


def expected_field_mismatches(
    row: Mapping[str, Any] | None,
    oracle: Oracle,
) -> dict[str, Any]:
    """Return observed values that differ from labeled field expectations."""

    return {
        field: nested_value(row, field) if row else None
        for field, expected in oracle.get("expectedFields", {}).items()
        if row is None or nested_value(row, field) != expected
    }


def check_direct_dependency(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check a typed direct dependency without accepting parser candidates."""

    row = find_by_key(
        declaration_rows(payload),
        "declaration",
        str(oracle["declaration"]),
    )
    collection = dependency_collection(row, str(oracle["dependencyKind"]))
    items = collection.get("items", [])
    observed = str(oracle["target"]) in items if isinstance(items, list) else False
    authority = collection.get("authority")
    passed = observed == bool(oracle.get("expected", True))
    if oracle.get("authority"):
        passed = passed and authority == oracle["authority"]
    return passed, {
        "present": observed,
        "authority": authority,
        "parserCandidateOnly": parser_candidate_only(row, oracle),
    }


def dependency_collection(
    row: Mapping[str, Any] | None,
    kind: str,
) -> Mapping[str, Any]:
    """Return the selected typed Lean dependency collection."""

    field = {
        "type": "typeDependencies",
        "value": "valueDependencies",
    }[kind]
    collection = (row or {}).get(field, {})
    return collection if isinstance(collection, Mapping) else {}


def parser_candidate_only(
    row: Mapping[str, Any] | None,
    oracle: Oracle,
) -> bool:
    """Return whether the target occurs only under parser authority."""

    if row is None:
        return False
    parser = row.get("parserCandidates", {})
    if not isinstance(parser, Mapping):
        return False
    items = parser.get("items", [])
    return isinstance(items, list) and str(oracle["target"]) in items


def nested_value(row: Mapping[str, Any], path: str) -> Any:
    """Resolve a dotted report field without inventing missing values."""

    value: Any = row
    for component in path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            return None
        value = value[component]
    return value


def declaration_rows(payload: Payload) -> list[dict[str, Any]]:
    """Return supported declaration rows from canonical report namespaces."""

    graph = payload.get("declaration_graph", {})
    rows = graph.get("declarations", []) if isinstance(graph, Mapping) else []
    if isinstance(rows, list) and rows:
        return dictionary_rows(rows)
    return extension_declaration_rows(payload)


def extension_declaration_rows(payload: Payload) -> list[dict[str, Any]]:
    """Return declaration rows from the elaborated extension envelope."""

    extensions = payload.get("extensions", {})
    if not isinstance(extensions, Mapping):
        return []
    elaborated = extensions.get("elaborated_declarations", {})
    if not isinstance(elaborated, Mapping):
        return []
    data = elaborated.get("data", {})
    if not isinstance(data, Mapping):
        return []
    return dictionary_rows(data.get("declarations", []))


def dictionary_rows(rows: Any) -> list[dict[str, Any]]:
    """Filter an arbitrary value to dictionary report rows."""

    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def find_by_key(
    rows: Any,
    key: str,
    value: str,
) -> dict[str, Any] | None:
    """Return the first dictionary row whose key matches value."""

    return next(
        (row for row in dictionary_rows(rows) if row.get(key) == value),
        None,
    )
