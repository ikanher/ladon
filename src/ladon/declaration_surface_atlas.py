"""Atlas projection for declaration surfaces and typed dependency edges."""

from __future__ import annotations

from typing import Any


Node = dict[str, Any]
Edge = dict[str, Any]


def declaration_node_data(
    repo_key: str,
    row: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return atlas node data for a declaration surface."""

    data: dict[str, Any] = {"repo_key": repo_key}
    if not row:
        return data
    add_source_fields(data, row)
    add_surface_fields(data, row.get("surface"))
    data["imported_stub"] = bool(row.get("importedStub"))
    return data


def add_source_fields(data: dict[str, Any], row: dict[str, Any]) -> None:
    """Attach optional declaration source identity."""

    if row.get("module"):
        data["module"] = row["module"]
    if row.get("confidence"):
        data["evidence_confidence"] = row["confidence"]
    if row.get("sourcePath"):
        data["source_path"] = row["sourcePath"]
    data["has_source_range"] = bool(row.get("sourceRange"))
    data["has_content_hash"] = bool(row.get("contentHash"))


def add_surface_fields(data: dict[str, Any], raw: Any) -> None:
    """Attach bounded statement/trust summary fields."""

    if not isinstance(raw, dict):
        return
    data["surface_status"] = raw.get("status", "unavailable")
    data["rendered_type"] = raw.get("renderedType")
    data["trust_fact_count"] = len(raw.get("trustFacts", []))


def add_declaration_dependency_edges(
    nodes: dict[str, Node],
    edges: list[Edge],
    repo_key: str,
    declaration_graph: dict[str, Any],
) -> None:
    """Export parser and Lean dependencies as distinct atlas edge kinds."""

    evidence = declaration_rows_by_name(declaration_graph.get("declarations"))
    for source, targets in sorted(
        mapping_value(declaration_graph.get("parser_edges")).items()
    ):
        for target in list_value(targets):
            add_dependency_edge(
                nodes,
                edges,
                repo_key,
                str(source),
                str(target),
                "parser_candidate_dependency",
                "lean_parser",
                evidence,
            )
    for row in mapping_rows(declaration_graph.get("elaborated_edges")):
        if row.get("source") and row.get("target"):
            add_dependency_edge(
                nodes,
                edges,
                repo_key,
                str(row["source"]),
                str(row["target"]),
                str(row.get("kind", "elaborated_dependency")),
                str(row.get("authority", "lean_environment")),
                evidence,
            )


def add_dependency_edge(
    nodes: dict[str, Node],
    edges: list[Edge],
    repo_key: str,
    source: str,
    target: str,
    kind: str,
    authority: str,
    evidence: dict[str, dict[str, Any]],
) -> None:
    """Add one declaration dependency edge and named endpoint nodes."""

    source_id = declaration_node_id(repo_key, source)
    target_id = declaration_node_id(repo_key, target)
    add_node(
        nodes,
        source_id,
        source,
        declaration_node_data(repo_key, evidence.get(source)),
    )
    add_node(
        nodes,
        target_id,
        target,
        declaration_node_data(repo_key, evidence.get(target)),
    )
    edges.append(
        {
            "source": source_id,
            "target": target_id,
            "kind": kind,
            "data": {"authority": authority},
        }
    )


def add_node(
    nodes: dict[str, Node],
    node_id: str,
    label: str,
    data: dict[str, Any],
) -> None:
    """Add a declaration node unless an earlier atlas row supplied it."""

    nodes.setdefault(
        node_id,
        {
            "id": node_id,
            "kind": "declaration",
            "label": label,
            "data": dict(sorted(data.items())),
        },
    )


def declaration_rows_by_name(raw: Any) -> dict[str, dict[str, Any]]:
    """Return declaration evidence keyed by fully qualified name."""

    return {
        str(row["declaration"]): row
        for row in mapping_rows(raw)
        if row.get("declaration")
    }


def mapping_rows(raw: Any) -> list[dict[str, Any]]:
    """Return dictionary rows from a JSON array."""

    return [row for row in list_value(raw) if isinstance(row, dict)]


def mapping_value(raw: Any) -> dict[str, Any]:
    """Return one dictionary or an empty mapping."""

    return raw if isinstance(raw, dict) else {}


def list_value(raw: Any) -> list[Any]:
    """Return one list or an empty list."""

    return raw if isinstance(raw, list) else []


def declaration_node_id(repo_key: str, declaration: str) -> str:
    """Return the stable atlas declaration-node identity."""

    return f"declaration:{repo_key}:{declaration}"
