"""Deterministic graph construction for Ladon report atlases."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.atlas_report_reader import (
    atlas_report_view,
    is_ladon_report_payload,
)
from ladon.declaration_surface_atlas import (
    add_declaration_dependency_edges,
    declaration_node_data,
)


Node = dict[str, Any]
Edge = dict[str, Any]


def build_report_atlas(
    reports_root: Path,
    *,
    workflow_diagnostics: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build a compact reviewer-facing graph from report JSON files."""

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    for report_path in sorted(reports_root.rglob("*.json")):
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if not is_ladon_report_payload(payload):
            continue
        payload = atlas_report_view(payload, report_path)
        relative_path = report_path.relative_to(reports_root).as_posix()
        add_report_payload(nodes, edges, relative_path, payload)
    ordered_nodes = sorted(nodes.values(), key=lambda node: node["id"])
    ordered_edges = sorted(edges, key=edge_sort_key)
    workflow_rows = normalized_workflow_diagnostics(workflow_diagnostics)
    summary = atlas_summary(ordered_nodes, ordered_edges)
    summary["workflow_diagnostics"] = len(workflow_rows)
    summary["unreported_entries"] = len(workflow_rows)
    return {
        "schema": "ladon-report-atlas-v1",
        "summary": dict(sorted(summary.items())),
        "workflowDiagnostics": workflow_rows,
        "nodes": ordered_nodes,
        "edges": ordered_edges,
    }


def normalized_workflow_diagnostics(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Detach deterministic bundle-state rows from their source manifest."""

    return [
        {
            str(key): detached_workflow_value(value)
            for key, value in sorted(row.items())
        }
        for row in sorted(
            rows,
            key=lambda row: (
                str(row.get("entryId", "")),
                str(row.get("state", "")),
            ),
        )
    ]


def detached_workflow_value(value: Any) -> Any:
    """Copy JSON-compatible workflow state without inventing analysis data."""

    if isinstance(value, Mapping):
        return {
            str(key): detached_workflow_value(row)
            for key, row in sorted(value.items())
        }
    if isinstance(value, list):
        return [detached_workflow_value(row) for row in value]
    return value


def add_report_payload(
    nodes: dict[str, Node],
    edges: list[Edge],
    relative_path: str,
    payload: dict[str, Any],
) -> None:
    """Add one report payload to the atlas graph."""

    repo_key = repo_key_from_path(relative_path)
    report_id = report_node_id(relative_path)
    metadata = payload.get("metadata", {})
    module_dag = payload.get("module_dag", {})
    declaration_graph = payload.get("declaration_graph", {})
    declaration_rows = declaration_graph.get("declarations", [])
    packet_evidence = payload.get("packet_evidence", [])
    findings = payload.get("findings", [])
    regions = payload.get("review_regions", [])
    warnings = payload.get("warnings", [])
    projection = payload.get("projection", {})
    selected_modules = int(module_dag.get("module_count", 0))
    source_index = module_dag.get("source_index", {})
    inventory_modules = (
        int(source_index.get("inventoryModuleCount", selected_modules))
        if isinstance(source_index, dict)
        else selected_modules
    )
    add_node(
        nodes,
        report_id,
        "report",
        relative_path,
        {
            "analysis_root_module": metadata.get("analysis_root_module", ""),
            "module_count": selected_modules,
            "selected_module_count": selected_modules,
            "inventory_module_count": inventory_modules,
            "declaration_count": declaration_graph.get(
                "declaration_count",
                0,
            ),
            "finding_count": projected_collection_count(
                findings,
                projection,
                "#/sections/findings",
            ),
            "review_region_count": projected_collection_count(
                regions,
                projection,
                "#/sections/review_regions",
            ),
            "extraction_backend": metadata.get(
                "extraction_backend",
                "unknown",
            ),
            "declaration_evidence": declaration_evidence_summary(
                declaration_rows
            ),
            "packet_evidence": packet_evidence_summary(packet_evidence),
            "warning_count": len(warnings),
            "warnings": warnings[:3],
        },
    )
    add_root_module(nodes, edges, report_id, repo_key, metadata)
    add_module_highlights(nodes, edges, report_id, repo_key, module_dag)
    add_declaration_highlights(
        nodes,
        edges,
        report_id,
        repo_key,
        declaration_graph,
    )
    add_declaration_dependency_edges(
        nodes,
        edges,
        repo_key,
        declaration_graph,
    )
    add_findings(nodes, edges, report_id, relative_path, findings)
    add_review_regions(nodes, edges, report_id, relative_path, regions)


def projected_collection_count(
    visible_rows: Any,
    projection: Any,
    pointer: str,
) -> int:
    """Recover a projected collection total from its exact omission row."""

    visible = len(visible_rows) if isinstance(visible_rows, list) else 0
    if not isinstance(projection, dict):
        return visible
    omissions = projection.get("omissions", [])
    if not isinstance(omissions, list):
        return visible
    omitted = sum(
        int(row.get("omitted_count", 0))
        for row in omissions
        if isinstance(row, dict) and row.get("pointer") == pointer
    )
    return visible + omitted


def declaration_evidence_summary(rows: Any) -> dict[str, Any]:
    """Summarize declaration source-evidence confidence for atlas cards."""

    if not isinstance(rows, list):
        rows = []
    valid_rows = [row for row in rows if isinstance(row, dict)]
    return {
        "rows": len(valid_rows),
        "source_ranges": sum(
            1 for row in valid_rows if row.get("sourceRange")
        ),
        "content_hashes": sum(
            1 for row in valid_rows if row.get("contentHash")
        ),
        "confidence_counts": confidence_counts(valid_rows),
    }


def packet_evidence_summary(rows: Any) -> dict[str, Any]:
    """Summarize packet evidence gaps for atlas cards."""

    valid_rows = valid_packet_rows(rows)
    return {
        "rows": len(valid_rows),
        "incomplete": sum(
            1 for row in valid_rows if packet_incomplete(row)
        ),
        "missing": sum(
            1 for row in valid_rows if row.get("status") == "missing"
        ),
        "partial": sum(
            1 for row in valid_rows if row.get("status") == "partial"
        ),
        "stale": sum(1 for row in valid_rows if packet_stale(row)),
    }


def valid_packet_rows(rows: Any) -> list[dict[str, Any]]:
    """Return packet evidence rows that have dictionary shape."""

    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def packet_incomplete(row: dict[str, Any]) -> bool:
    """Return whether a packet evidence row is incomplete."""

    return (
        row.get("status") != "complete"
        or row.get("profile_status") not in {None, "complete"}
    )


def packet_stale(row: dict[str, Any]) -> bool:
    """Return whether a packet evidence row reports stale status."""

    return (
        "stale" in str(row.get("status", ""))
        or "stale" in str(row.get("profile_status", ""))
    )


def confidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count declaration rows by confidence label."""

    counts: dict[str, int] = {}
    for row in rows:
        confidence = str(row.get("confidence", "unspecified"))
        counts[confidence] = counts.get(confidence, 0) + 1
    return dict(sorted(counts.items()))


def add_root_module(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    repo_key: str,
    metadata: dict[str, Any],
) -> None:
    """Link a report to its analysis root module when present."""

    root = metadata.get("analysis_root_module")
    if not root:
        return
    root_id = module_node_id(repo_key, str(root))
    add_node(nodes, root_id, "module", str(root), {"repo_key": repo_key})
    edges.append(edge(report_id, root_id, "analyzes_root"))


def add_module_highlights(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    repo_key: str,
    module_dag: dict[str, Any],
) -> None:
    """Add highlighted module rows without duplicating the full DAG."""

    for metric, value_key in (
        ("module_fan_in", "fan_in"),
        ("module_fan_out", "fan_out"),
    ):
        for rank, row in enumerate(
            module_dag.get(top_key(metric), [])[:5],
            start=1,
        ):
            module = row.get("module")
            if module:
                add_metric_module(
                    nodes,
                    edges,
                    report_id,
                    repo_key,
                    str(module),
                    metric,
                    row,
                    rank,
                    value_key,
                )
    for rank, row in enumerate(
        module_dag.get("root_direct_import_closures", [])[:5],
        start=1,
    ):
        direct_import = row.get("direct_import")
        if direct_import:
            add_metric_module(
                nodes,
                edges,
                report_id,
                repo_key,
                str(direct_import),
                "root_import_closure",
                row,
                rank,
                "reachable_module_count",
            )


def add_metric_module(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    repo_key: str,
    module: str,
    metric: str,
    row: dict[str, Any],
    rank: int,
    value_key: str,
) -> None:
    """Add one module node and a report-to-module metric edge."""

    node_id = module_node_id(repo_key, module)
    add_node(nodes, node_id, "module", module, {"repo_key": repo_key})
    edges.append(
        edge(
            report_id,
            node_id,
            "highlights_module",
            {
                "metric": metric,
                "rank": rank,
                "value": row.get(value_key, 0),
            },
        )
    )


def add_declaration_highlights(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    repo_key: str,
    declaration_graph: dict[str, Any],
) -> None:
    """Add highlighted declaration fan rows."""

    evidence_rows = declaration_rows_by_name(
        declaration_graph.get("declarations", [])
    )
    for metric, value_key in (
        ("declaration_fan_in", "fan_in"),
        ("declaration_fan_out", "fan_out"),
    ):
        for rank, row in enumerate(
            declaration_graph.get(top_key(metric), [])[:5],
            start=1,
        ):
            declaration = row.get("declaration")
            if declaration:
                node_id = declaration_node_id(
                    repo_key,
                    str(declaration),
                )
                add_node(
                    nodes,
                    node_id,
                    "declaration",
                    str(declaration),
                    declaration_node_data(
                        repo_key,
                        evidence_rows.get(str(declaration)),
                    ),
                )
                edges.append(
                    edge(
                        report_id,
                        node_id,
                        "highlights_declaration",
                        {
                            "metric": metric,
                            "rank": rank,
                            "value": row.get(value_key, 0),
                        },
                    )
                )


def declaration_rows_by_name(rows: Any) -> dict[str, dict[str, Any]]:
    """Return explicit declaration rows keyed by declaration name."""

    if not isinstance(rows, list):
        return {}
    return {
        str(row["declaration"]): row
        for row in rows
        if isinstance(row, dict) and row.get("declaration")
    }


def add_findings(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    relative_path: str,
    findings: list[dict[str, Any]],
) -> None:
    """Add finding nodes scoped by report path."""

    for index, finding in enumerate(findings):
        stable_id = finding.get("id")
        suffix = str(stable_id) if stable_id else str(index)
        node_id = f"finding:{relative_path}:{suffix}"
        label = (
            f"{finding.get('kind', 'finding')}: "
            f"{finding.get('subject', '')}"
        ).strip()
        add_node(
            nodes,
            node_id,
            "finding",
            label,
            dict(finding),
        )
        edges.append(edge(report_id, node_id, "has_finding"))


def add_review_regions(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    relative_path: str,
    regions: list[dict[str, Any]],
) -> None:
    """Add review region and signal nodes."""

    for region in regions:
        region_id = (
            f"region:{relative_path}:{region.get('kind', 'region')}"
        )
        add_node(
            nodes,
            region_id,
            "review_region",
            str(region.get("title", region.get("kind", "region"))),
            {
                "kind": region.get("kind", ""),
                "signal_count": region.get("signal_count", 0),
            },
        )
        edges.append(edge(report_id, region_id, "has_review_region"))
        for index, signal in enumerate(region.get("signals", [])):
            add_region_signal(
                nodes,
                edges,
                region_id,
                relative_path,
                index,
                signal,
            )


def add_region_signal(
    nodes: dict[str, Node],
    edges: list[Edge],
    region_id: str,
    relative_path: str,
    index: int,
    signal: dict[str, Any],
) -> None:
    """Add one review-region signal node."""

    kind = region_id.rsplit(":", 1)[-1]
    node_id = f"signal:{relative_path}:{kind}:{index}"
    label = (
        f"{signal.get('kind', 'signal')}: "
        f"{signal.get('subject', '')}"
    ).strip()
    add_node(
        nodes,
        node_id,
        "signal",
        label,
        {
            "kind": signal.get("kind", ""),
            "subject": signal.get("subject", ""),
            "count": signal.get("count", 0),
        },
    )
    edges.append(edge(region_id, node_id, "has_signal"))


def atlas_summary(
    nodes: list[Node],
    edges: list[Edge],
) -> dict[str, int]:
    """Return node-kind counts with explicit inventory/highlight terminology."""

    summary = {"edges": len(edges)}
    for node in nodes:
        key = plural_key(str(node["kind"]))
        summary[key] = summary.get(key, 0) + 1
    summary["highlighted_modules"] = summary.get("modules", 0)
    summary["inventory_modules"] = sum(
        int(node.get("data", {}).get("inventory_module_count", 0))
        for node in nodes
        if node.get("kind") == "report"
    )
    summary["selected_modules"] = sum(
        int(node.get("data", {}).get("selected_module_count", 0))
        for node in nodes
        if node.get("kind") == "report"
    )
    return dict(sorted(summary.items()))


def add_node(
    nodes: dict[str, Node],
    node_id: str,
    kind: str,
    label: str,
    data: dict[str, Any],
) -> None:
    """Add a node unless an equivalent node already exists."""

    nodes.setdefault(
        node_id,
        {
            "id": node_id,
            "kind": kind,
            "label": label,
            "data": dict(sorted(data.items())),
        },
    )


def edge(
    source: str,
    target: str,
    kind: str,
    data: dict[str, Any] | None = None,
) -> Edge:
    """Build one atlas edge."""

    row: Edge = {"source": source, "target": target, "kind": kind}
    if data:
        row["data"] = dict(sorted(data.items()))
    return row


def edge_sort_key(row: Edge) -> tuple[str, str, str, str]:
    """Return stable edge ordering."""

    return (
        row["source"],
        row["kind"],
        row["target"],
        json.dumps(row.get("data", {}), sort_keys=True),
    )


def repo_key_from_path(relative_path: str) -> str:
    """Return the first report path component as repo key."""

    return relative_path.split("/", 1)[0]


def report_node_id(relative_path: str) -> str:
    """Return stable report node ID."""

    return f"report:{relative_path}"


def module_node_id(repo_key: str, module: str) -> str:
    """Return stable module node ID scoped by repo key."""

    return f"module:{repo_key}:{module}"


def declaration_node_id(repo_key: str, declaration: str) -> str:
    """Return stable declaration node ID scoped by repo key."""

    return f"declaration:{repo_key}:{declaration}"


def top_key(metric: str) -> str:
    """Map metric names to report row keys."""

    return "top_fan_in" if metric.endswith("fan_in") else "top_fan_out"


def plural_key(kind: str) -> str:
    """Return summary key for a node kind."""

    return f"{kind}s"
