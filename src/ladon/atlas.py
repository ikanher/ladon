"""Deterministic atlas export for Ladon report directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Node = dict[str, Any]
Edge = dict[str, Any]


def build_report_atlas(reports_root: Path) -> dict[str, Any]:
    """Build a compact reviewer-facing graph from report JSON files."""

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    for report_path in sorted(reports_root.rglob("*.json")):
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if not is_ladon_report_payload(payload):
            continue
        relative_path = report_path.relative_to(reports_root).as_posix()
        add_report_payload(nodes, edges, relative_path, payload)
    ordered_nodes = sorted(nodes.values(), key=lambda node: node["id"])
    ordered_edges = sorted(edges, key=edge_sort_key)
    return {
        "schema": "ladon-report-atlas-v1",
        "summary": atlas_summary(ordered_nodes, ordered_edges),
        "nodes": ordered_nodes,
        "edges": ordered_edges,
    }


def is_ladon_report_payload(payload: dict[str, Any]) -> bool:
    """Return whether a JSON payload is a Ladon report, not an auxiliary cache."""

    return isinstance(payload.get("metadata"), dict) and isinstance(payload.get("module_dag"), dict)


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
    add_node(
        nodes,
        report_id,
        "report",
        relative_path,
        {
            "analysis_root_module": metadata.get("analysis_root_module", ""),
            "module_count": module_dag.get("module_count", 0),
            "declaration_count": declaration_graph.get("declaration_count", 0),
            "finding_count": len(findings),
            "review_region_count": len(regions),
            "extraction_backend": metadata.get("extraction_backend", "unknown"),
            "declaration_evidence": declaration_evidence_summary(declaration_rows),
            "packet_evidence": packet_evidence_summary(packet_evidence),
            "warning_count": len(warnings),
            "warnings": warnings[:3],
        },
    )
    add_root_module(nodes, edges, report_id, repo_key, metadata)
    add_module_highlights(nodes, edges, report_id, repo_key, module_dag)
    add_declaration_highlights(nodes, edges, report_id, repo_key, declaration_graph)
    add_findings(nodes, edges, report_id, relative_path, findings)
    add_review_regions(nodes, edges, report_id, relative_path, regions)


def declaration_evidence_summary(rows: Any) -> dict[str, Any]:
    """Summarize declaration source-evidence confidence for atlas cards."""

    if not isinstance(rows, list):
        rows = []
    valid_rows = [row for row in rows if isinstance(row, dict)]
    return {
        "rows": len(valid_rows),
        "source_ranges": sum(1 for row in valid_rows if row.get("sourceRange")),
        "content_hashes": sum(1 for row in valid_rows if row.get("contentHash")),
        "confidence_counts": confidence_counts(valid_rows),
    }


def packet_evidence_summary(rows: Any) -> dict[str, Any]:
    """Summarize packet evidence gaps for atlas cards."""

    valid_rows = valid_packet_rows(rows)
    return {
        "rows": len(valid_rows),
        "incomplete": sum(1 for row in valid_rows if packet_incomplete(row)),
        "missing": sum(1 for row in valid_rows if row.get("status") == "missing"),
        "partial": sum(1 for row in valid_rows if row.get("status") == "partial"),
        "stale": sum(1 for row in valid_rows if packet_stale(row)),
    }


def valid_packet_rows(rows: Any) -> list[dict[str, Any]]:
    """Return packet evidence rows that have dictionary shape."""

    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def packet_incomplete(row: dict[str, Any]) -> bool:
    """Return whether a packet evidence row is incomplete."""

    return row.get("status") != "complete" or row.get("profile_status") not in {None, "complete"}


def packet_stale(row: dict[str, Any]) -> bool:
    """Return whether a packet evidence row reports stale status."""

    return "stale" in str(row.get("status", "")) or "stale" in str(row.get("profile_status", ""))


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

    for metric, value_key in (("module_fan_in", "fan_in"), ("module_fan_out", "fan_out")):
        for rank, row in enumerate(module_dag.get(top_key(metric), [])[:5], start=1):
            module = row.get("module")
            if module:
                add_metric_module(nodes, edges, report_id, repo_key, str(module), metric, row, rank, value_key)
    for rank, row in enumerate(module_dag.get("root_direct_import_closures", [])[:5], start=1):
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
            {"metric": metric, "rank": rank, "value": row.get(value_key, 0)},
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

    evidence_rows = declaration_rows_by_name(declaration_graph.get("declarations", []))
    for metric, value_key in (("declaration_fan_in", "fan_in"), ("declaration_fan_out", "fan_out")):
        for rank, row in enumerate(declaration_graph.get(top_key(metric), [])[:5], start=1):
            declaration = row.get("declaration")
            if declaration:
                node_id = declaration_node_id(repo_key, str(declaration))
                add_node(
                    nodes,
                    node_id,
                    "declaration",
                    str(declaration),
                    declaration_node_data(repo_key, evidence_rows.get(str(declaration))),
                )
                edges.append(
                    edge(
                        report_id,
                        node_id,
                        "highlights_declaration",
                        {"metric": metric, "rank": rank, "value": row.get(value_key, 0)},
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


def declaration_node_data(repo_key: str, row: dict[str, Any] | None) -> dict[str, Any]:
    """Return atlas node data for a declaration highlight."""

    data: dict[str, Any] = {"repo_key": repo_key}
    if not row:
        return data
    if row.get("module"):
        data["module"] = row["module"]
    if row.get("confidence"):
        data["evidence_confidence"] = row["confidence"]
    if row.get("sourcePath"):
        data["source_path"] = row["sourcePath"]
    data["has_source_range"] = bool(row.get("sourceRange"))
    data["has_content_hash"] = bool(row.get("contentHash"))
    return data


def add_findings(
    nodes: dict[str, Node],
    edges: list[Edge],
    report_id: str,
    relative_path: str,
    findings: list[dict[str, Any]],
) -> None:
    """Add finding nodes scoped by report path."""

    for index, finding in enumerate(findings):
        node_id = f"finding:{relative_path}:{index}"
        label = f"{finding.get('kind', 'finding')}: {finding.get('subject', '')}".strip()
        add_node(
            nodes,
            node_id,
            "finding",
            label,
            {
                "kind": finding.get("kind", ""),
                "subject": finding.get("subject", ""),
                "count": finding.get("count", 0),
            },
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
        region_id = f"region:{relative_path}:{region.get('kind', 'region')}"
        add_node(
            nodes,
            region_id,
            "review_region",
            str(region.get("title", region.get("kind", "region"))),
            {"kind": region.get("kind", ""), "signal_count": region.get("signal_count", 0)},
        )
        edges.append(edge(report_id, region_id, "has_review_region"))
        for index, signal in enumerate(region.get("signals", [])):
            add_region_signal(nodes, edges, region_id, relative_path, index, signal)


def add_region_signal(
    nodes: dict[str, Node],
    edges: list[Edge],
    region_id: str,
    relative_path: str,
    index: int,
    signal: dict[str, Any],
) -> None:
    """Add one review-region signal node."""

    node_id = f"signal:{relative_path}:{region_id.rsplit(':', 1)[-1]}:{index}"
    label = f"{signal.get('kind', 'signal')}: {signal.get('subject', '')}".strip()
    add_node(
        nodes,
        node_id,
        "signal",
        label,
        {"kind": signal.get("kind", ""), "subject": signal.get("subject", ""), "count": signal.get("count", 0)},
    )
    edges.append(edge(region_id, node_id, "has_signal"))


def render_atlas_markdown(atlas: dict[str, Any]) -> str:
    """Render a compact Markdown summary for an atlas graph."""

    lines = ["# Ladon Report Atlas", ""]
    lines.extend(summary_lines(atlas["summary"]))
    lines.extend(report_table_lines(atlas["nodes"]))
    return "\n".join(lines) + "\n"


def atlas_reviewer_cards(
    atlas: dict[str, Any],
    bridge_reports: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return compact reviewer cards derived from atlas graph rows."""

    nodes = {node["id"]: node for node in atlas.get("nodes", [])}
    edges = atlas.get("edges", [])
    bridge_by_root = bridge_summaries_by_root(bridge_reports or [])
    cards = [
        reviewer_card(report, nodes, edges, bridge_by_root.get(report_root(report)))
        for report in sorted(
            (node for node in nodes.values() if node["kind"] == "report"),
            key=lambda node: node["label"],
        )
    ]
    return cards


def reviewer_card(
    report: Node,
    nodes: dict[str, Node],
    edges: list[Edge],
    bridge_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one reviewer card for a report node."""

    report_id = report["id"]
    data = report.get("data", {})
    findings = linked_nodes(nodes, edges, report_id, "has_finding")
    regions = linked_nodes(nodes, edges, report_id, "has_review_region")
    warnings = data.get("warnings", [])
    return {
        "report": report["label"],
        "root": data.get("analysis_root_module", ""),
        "extraction_backend": data.get("extraction_backend", "unknown"),
        "top_findings": finding_labels(findings),
        "review_regions": region_labels(regions),
        "declaration_evidence": data.get("declaration_evidence", declaration_evidence_summary([])),
        "packet_evidence": data.get("packet_evidence", packet_evidence_summary([])),
        "bridge_diagnostics": bridge_summary or empty_bridge_summary(),
        "strongest_evidence": strongest_evidence(findings, regions),
        "known_non_claims": warnings if warnings else ["not recorded in atlas"],
        "source_report_json": report["label"],
        "source_report_text": report["label"].removesuffix(".json") + ".txt",
    }


def report_root(report: Node) -> str:
    """Return the analysis root recorded on a report node."""

    return str(report.get("data", {}).get("analysis_root_module", ""))


def bridge_summaries_by_root(bridge_reports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group optional ProofIR bridge diagnostics by reviewer-card root."""

    grouped: dict[str, dict[str, Any]] = {}
    for report in bridge_reports:
        root = bridge_root(report)
        if not root:
            continue
        summary = grouped.setdefault(root, empty_bridge_summary())
        merge_bridge_summary(summary, bridge_report_summary(report))
    return grouped


def bridge_root(report: dict[str, Any]) -> str:
    """Return the first root named by a bridge reviewer card, if present."""

    cards = report.get("reviewerCards", [])
    if isinstance(cards, list):
        for card in cards:
            if isinstance(card, dict) and card.get("root"):
                return str(card["root"])
    return ""


def bridge_report_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Summarize one optional ProofIR bridge report for atlas cards."""

    diagnostics = [row for row in report.get("diagnostics", []) if isinstance(row, dict)]
    joins = [row for row in report.get("joins", []) if isinstance(row, dict)]
    route_audit = report.get("routeAudit", {})
    route_summary = route_audit.get("summary", {}) if isinstance(route_audit, dict) else {}
    return {
        "diagnostic_count": len(diagnostics),
        "diagnostic_counts": counts_by_key(diagnostics, "ruleId"),
        "low_confidence_join_count": low_confidence_join_count(joins),
        "unmatched_join_count": sum(1 for row in joins if row.get("matchKind") == "unmatched"),
        "route_audit_claim_count": int(route_summary.get("claimRouteCount", 0)),
        "route_audit_diagnostic_count": int(route_summary.get("diagnosticCount", 0)),
        "trust_rules": sorted(str(rule) for rule in report.get("trustRules", [])),
    }


def merge_bridge_summary(target: dict[str, Any], update: dict[str, Any]) -> None:
    """Merge a bridge report summary into a root-grouped summary."""

    target["diagnostic_count"] += update["diagnostic_count"]
    target["low_confidence_join_count"] += update["low_confidence_join_count"]
    target["unmatched_join_count"] += update["unmatched_join_count"]
    target["route_audit_claim_count"] += update["route_audit_claim_count"]
    target["route_audit_diagnostic_count"] += update["route_audit_diagnostic_count"]
    for key, count in update["diagnostic_counts"].items():
        target["diagnostic_counts"][key] = target["diagnostic_counts"].get(key, 0) + count
    target["trust_rules"] = sorted(set(target["trust_rules"]) | set(update["trust_rules"]))


def empty_bridge_summary() -> dict[str, Any]:
    """Return the stable bridge summary shape for cards without bridge input."""

    return {
        "diagnostic_count": 0,
        "diagnostic_counts": {},
        "low_confidence_join_count": 0,
        "unmatched_join_count": 0,
        "route_audit_claim_count": 0,
        "route_audit_diagnostic_count": 0,
        "trust_rules": [],
    }


def counts_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count dictionaries by one string key."""

    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def low_confidence_join_count(joins: list[dict[str, Any]]) -> int:
    """Count bridge joins that should remain review warnings."""

    return sum(
        1
        for row in joins
        if row.get("confidence") in {"low", "none"} or row.get("warningOnly") is True
    )


def linked_nodes(
    nodes: dict[str, Node],
    edges: list[Edge],
    source: str,
    kind: str,
) -> list[Node]:
    """Return nodes linked from one source by edge kind."""

    linked = [
        nodes[edge["target"]]
        for edge in edges
        if edge["source"] == source and edge["kind"] == kind and edge["target"] in nodes
    ]
    return sorted(linked, key=lambda node: node["id"])


def finding_labels(findings: list[Node]) -> list[str]:
    """Return compact finding labels."""

    if not findings:
        return ["none"]
    return [finding["label"] for finding in findings[:5]]


def region_labels(regions: list[Node]) -> list[str]:
    """Return compact review-region labels."""

    if not regions:
        return ["none"]
    return [region["label"] for region in regions[:5]]


def strongest_evidence(findings: list[Node], regions: list[Node]) -> list[str]:
    """Return the strongest evidence rows visible in the atlas."""

    if findings:
        return [f"finding: {finding['label']}" for finding in findings[:3]]
    if regions:
        return [f"review_region: {region['label']}" for region in regions[:3]]
    return ["not recorded in atlas"]


def render_reviewer_cards_markdown(
    atlas: dict[str, Any],
    bridge_reports: list[dict[str, Any]] | None = None,
) -> str:
    """Render reviewer cards as compact Markdown."""

    lines = ["# Ladon Atlas Reviewer Cards", ""]
    for card in atlas_reviewer_cards(atlas, bridge_reports):
        lines.extend(reviewer_card_lines(card))
    return "\n".join(lines).rstrip() + "\n"


def reviewer_card_lines(card: dict[str, Any]) -> list[str]:
    """Render one reviewer card."""

    lines = [
        f"## `{card['report']}`",
        "",
        f"- root: {card['root']}",
        f"- extraction backend: {card['extraction_backend']}",
        f"- declaration evidence: {format_declaration_evidence(card['declaration_evidence'])}",
        f"- packet evidence: {format_packet_evidence(card['packet_evidence'])}",
        f"- bridge diagnostics: {format_bridge_diagnostics(card['bridge_diagnostics'])}",
        f"- source JSON: `{card['source_report_json']}`",
        f"- source text: `{card['source_report_text']}`",
        "- top findings:",
        *[f"  - {item}" for item in card["top_findings"]],
        "- review regions:",
        *[f"  - {item}" for item in card["review_regions"]],
        "- strongest evidence:",
        *[f"  - {item}" for item in card["strongest_evidence"]],
        "- known non-claims:",
        *[f"  - {item}" for item in card["known_non_claims"]],
        "- bridge trust notes:",
        *[f"  - {item}" for item in bridge_trust_notes(card["bridge_diagnostics"])],
        "",
    ]
    return lines


def format_declaration_evidence(summary: dict[str, Any]) -> str:
    """Render one compact declaration-evidence summary for reviewer cards."""

    counts = summary.get("confidence_counts", {})
    confidence = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    suffix = f" confidence({confidence})" if confidence else ""
    return (
        f"rows={summary.get('rows', 0)} "
        f"ranges={summary.get('source_ranges', 0)} "
        f"hashes={summary.get('content_hashes', 0)}"
        f"{suffix}"
    )


def format_packet_evidence(summary: dict[str, Any]) -> str:
    """Render one compact packet-evidence summary for reviewer cards."""

    return (
        f"rows={summary.get('rows', 0)} "
        f"incomplete={summary.get('incomplete', 0)} "
        f"missing={summary.get('missing', 0)} "
        f"stale={summary.get('stale', 0)}"
    )


def format_bridge_diagnostics(summary: dict[str, Any]) -> str:
    """Render one compact bridge-diagnostic summary for reviewer cards."""

    counts = summary.get("diagnostic_counts", {})
    diagnostics = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    suffix = f" diagnostics({diagnostics})" if diagnostics else ""
    return (
        f"diagnostics={summary.get('diagnostic_count', 0)} "
        f"low_confidence_joins={summary.get('low_confidence_join_count', 0)} "
        f"unmatched={summary.get('unmatched_join_count', 0)} "
        f"route_audit_claims={summary.get('route_audit_claim_count', 0)} "
        f"route_audit_diagnostics={summary.get('route_audit_diagnostic_count', 0)}"
        f"{suffix}"
    )


def bridge_trust_notes(summary: dict[str, Any]) -> list[str]:
    """Return visible bridge trust notes or a stable no-input marker."""

    notes = summary.get("trust_rules", [])
    return notes if notes else ["no bridge report supplied"]


def summary_lines(summary: dict[str, int]) -> list[str]:
    """Render atlas summary counts."""

    lines = ["## Summary"]
    for key in sorted(summary):
        lines.append(f"- {key}: {summary[key]}")
    return [*lines, ""]


def report_table_lines(nodes: list[Node]) -> list[str]:
    """Render report nodes as a small table."""

    reports = [node for node in nodes if node["kind"] == "report"]
    if not reports:
        return []
    lines = [
        "## Reports",
        "",
        "| Report | Root | Findings | Regions |",
        "| --- | --- | ---: | ---: |",
    ]
    for node in reports:
        data = node.get("data", {})
        lines.append(
            "| "
            f"`{node['label']}` | "
            f"{data.get('analysis_root_module', '')} | "
            f"{data.get('finding_count', 0)} | "
            f"{data.get('review_region_count', 0)} |"
        )
    return [*lines, ""]


def atlas_summary(nodes: list[Node], edges: list[Edge]) -> dict[str, int]:
    """Return node-kind counts and total edge count."""

    summary = {"edges": len(edges)}
    for node in nodes:
        key = plural_key(str(node["kind"]))
        summary[key] = summary.get(key, 0) + 1
    return dict(sorted(summary.items()))


def add_node(nodes: dict[str, Node], node_id: str, kind: str, label: str, data: dict[str, Any]) -> None:
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


def edge(source: str, target: str, kind: str, data: dict[str, Any] | None = None) -> Edge:
    """Build one atlas edge."""

    row: Edge = {"source": source, "target": target, "kind": kind}
    if data:
        row["data"] = dict(sorted(data.items()))
    return row


def edge_sort_key(row: Edge) -> tuple[str, str, str, str]:
    """Return stable edge ordering."""

    return (row["source"], row["kind"], row["target"], json.dumps(row.get("data", {}), sort_keys=True))


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
