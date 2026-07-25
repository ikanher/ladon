"""Focused report-surface oracles used by the portable benchmark harness."""

from __future__ import annotations

from typing import Any, Mapping


Oracle = Mapping[str, Any]
Payload = Mapping[str, Any]


def check_fan_population_count(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check one named fan-table population and count."""

    table = str(oracle["table"])
    module = str(oracle["module"])
    row = find_by_key(payload.get("module_dag", {}).get(table, []), "module", module)
    observed = fan_population_observation(row)
    expected = fan_population_expectation(oracle)
    passed = all(observed.get(key) == value for key, value in expected.items())
    return passed, observed


def fan_population_observation(row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return stable observed fan-population fields."""

    return {
        "count": int(row.get("fan_in", 0)) if row else 0,
        "population": row.get("population") if row else None,
        "authority": row.get("authority") if row else None,
    }


def fan_population_expectation(oracle: Oracle) -> dict[str, Any]:
    """Return explicitly constrained fan-population fields."""

    expected = {
        "count": int(oracle["expected"]),
        "population": oracle.get("population"),
        "authority": oracle.get("authority"),
    }
    return {key: value for key, value in expected.items() if value is not None}


def check_missing_internal_import(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check whether one target appears in the internal-missing import table."""

    row = find_by_key(
        payload.get("module_dag", {}).get("missing_internal_imports", []),
        "targetModule",
        str(oracle["targetModule"]),
    )
    observed = row is not None
    if row is not None and oracle.get("authority"):
        observed = row.get("authority") == oracle["authority"]
    return observed == bool(oracle.get("expected", True)), observed


def check_text_declaration(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check a bounded text declaration name and optional kind."""

    metadata = (
        payload.get("module_dag", {})
        .get("module_metadata", {})
        .get(str(oracle["module"]), {})
    )
    row = find_by_key(metadata.get("textDeclarations", []), "name", str(oracle["name"]))
    observed = text_declaration_matches(row, oracle)
    return observed == bool(oracle.get("expected", True)), observed


def text_declaration_matches(
    row: Mapping[str, Any] | None,
    oracle: Oracle,
) -> bool:
    """Return whether an existing text declaration satisfies optional fields."""

    if row is None:
        return False
    if oracle.get("kind") and row.get("kind") != oracle["kind"]:
        return False
    return not oracle.get("authority") or row.get("authority") == oracle["authority"]


def check_lexical_marker(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check one lexical marker with source-authority metadata."""

    rows = payload.get("module_dag", {}).get("lexical_markers", [])
    row = lexical_marker_match(rows, oracle)
    observed = row is not None
    if row is not None and oracle.get("authority"):
        observed = row.get("authority") == oracle["authority"]
    return observed == bool(oracle.get("expected", True)), observed


def lexical_marker_match(rows: Any, oracle: Oracle) -> dict[str, Any] | None:
    """Return the lexical-marker row selected by one oracle."""

    if not isinstance(rows, list):
        return None
    return next(
        (
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("module") == oracle.get("module")
            and row.get("kind") == oracle.get("kind")
        ),
        None,
    )


def check_finding_count(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check promoted finding count with optional population and subject."""

    rows = [
        row
        for row in payload.get("findings", [])
        if finding_matches(row, oracle)
    ]
    observed = len(rows)
    return observed == int(oracle.get("expected", 0)), observed


def finding_matches(row: Mapping[str, Any], oracle: Oracle) -> bool:
    """Return whether one finding matches all selected semantic fields."""

    if row.get("kind") != oracle.get("kind"):
        return False
    if oracle.get("subject") and row.get("subject") != oracle["subject"]:
        return False
    population = oracle.get("promotionPopulation")
    return not population or row.get("promotion_population") == population


def check_namespace_drift(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check one aggregated namespace/module drift row."""

    rows = payload.get("module_readiness", {}).get("rows", [])
    row = namespace_drift_match(rows, oracle)
    observed = {
        "present": row is not None,
        "declarationCount": row.get("declarationCount") if row else None,
        "authority": row.get("authority") if row else None,
    }
    return namespace_drift_matches_expectation(row, oracle), observed


def namespace_drift_match(rows: Any, oracle: Oracle) -> dict[str, Any] | None:
    """Return the namespace-drift row selected by one oracle."""

    if not isinstance(rows, list):
        return None
    return next(
        (
            item
            for item in rows
            if isinstance(item, dict)
            and item.get("kind") == "namespace_module_drift"
            and item.get("module") == oracle.get("module")
            and item.get("namespace") == oracle.get("namespace")
        ),
        None,
    )


def namespace_drift_matches_expectation(
    row: Mapping[str, Any] | None,
    oracle: Oracle,
) -> bool:
    """Return whether a namespace-drift row satisfies optional fields."""

    if (row is not None) != bool(oracle.get("expected", True)):
        return False
    if row is None:
        return True
    if not drift_count_matches(row, oracle):
        return False
    return not oracle.get("authority") or row.get("authority") == oracle["authority"]


def drift_count_matches(row: Mapping[str, Any], oracle: Oracle) -> bool:
    """Return whether an optional aggregate declaration count matches."""

    return (
        "declarationCount" not in oracle
        or row.get("declarationCount") == oracle["declarationCount"]
    )


def check_proof_similarity_state(payload: Payload, oracle: Oracle) -> tuple[bool, Any]:
    """Check the evidence and promotion state for one proof-family suffix."""

    rows = payload.get("declaration_graph", {}).get(
        "proof_family_similarity_candidates",
        [],
    )
    row = find_by_key(rows, "suffix", str(oracle["suffix"]))
    fields = tuple(oracle.get("fields", ()))
    observed = {field: row.get(field) if row else None for field in fields}
    return row is not None and observed == oracle.get("expected", {}), observed


def dictionary_rows(rows: Any) -> list[dict[str, Any]]:
    """Filter an arbitrary value to dictionary report rows."""

    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def find_by_key(rows: Any, key: str, value: str) -> dict[str, Any] | None:
    """Return the first dictionary row whose key matches value."""

    return next(
        (row for row in dictionary_rows(rows) if row.get(key) == value),
        None,
    )
