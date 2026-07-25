"""Reviewer-card derivation from deterministic Ladon atlas graphs."""

from __future__ import annotations

from typing import Any

from ladon.artifact_versions import require_atlas_v1, require_bridge_v1
from ladon.atlas_graph import (
    Edge,
    Node,
    declaration_evidence_summary,
    packet_evidence_summary,
)


def atlas_reviewer_cards(
    atlas: dict[str, Any],
    bridge_reports: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return compact reviewer cards derived from atlas graph rows."""

    require_atlas_v1(atlas, consumer="atlas reviewer-card reader")
    for report in bridge_reports or []:
        require_bridge_v1(
            report,
            consumer="atlas reviewer-card bridge reader",
        )
    nodes = {node["id"]: node for node in atlas.get("nodes", [])}
    edges = atlas.get("edges", [])
    bridge_by_root = bridge_summaries_by_root(bridge_reports or [])
    return [
        reviewer_card(
            report,
            nodes,
            edges,
            bridge_by_root.get(report_root(report)),
        )
        for report in sorted(
            (
                node
                for node in nodes.values()
                if node["kind"] == "report"
            ),
            key=lambda node: node["label"],
        )
    ]


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
    regions = linked_nodes(
        nodes,
        edges,
        report_id,
        "has_review_region",
    )
    warnings = data.get("warnings", [])
    card = {
        "report": report["label"],
        "root": data.get("analysis_root_module", ""),
        "extraction_backend": data.get(
            "extraction_backend",
            "unknown",
        ),
        "top_findings": finding_labels(findings),
        "review_regions": region_labels(regions),
        "declaration_evidence": data.get(
            "declaration_evidence",
            declaration_evidence_summary([]),
        ),
        "packet_evidence": data.get(
            "packet_evidence",
            packet_evidence_summary([]),
        ),
        "bridge_diagnostics": bridge_summary or empty_bridge_summary(),
        "strongest_evidence": strongest_evidence(findings, regions),
        "known_non_claims": (
            warnings if warnings else ["not recorded in atlas"]
        ),
        "source_report_json": report["label"],
        "source_report_text": (
            report["label"].removesuffix(".json") + ".txt"
        ),
    }
    evidence = finding_evidence_summaries(findings)
    if evidence:
        card["finding_evidence"] = evidence
    return card


def report_root(report: Node) -> str:
    """Return the analysis root recorded on a report node."""

    return str(
        report.get("data", {}).get("analysis_root_module", "")
    )


def bridge_summaries_by_root(
    bridge_reports: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
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

    diagnostics = [
        row
        for row in report.get("diagnostics", [])
        if isinstance(row, dict)
    ]
    joins = [
        row
        for row in report.get("joins", [])
        if isinstance(row, dict)
    ]
    route_audit = report.get("routeAudit", {})
    route_summary = (
        route_audit.get("summary", {})
        if isinstance(route_audit, dict)
        else {}
    )
    return {
        "diagnostic_count": len(diagnostics),
        "diagnostic_counts": counts_by_key(diagnostics, "ruleId"),
        "low_confidence_join_count": low_confidence_join_count(joins),
        "unmatched_join_count": sum(
            1
            for row in joins
            if row.get("matchKind") == "unmatched"
        ),
        "route_audit_claim_count": int(
            route_summary.get("claimRouteCount", 0)
        ),
        "route_audit_diagnostic_count": int(
            route_summary.get("diagnosticCount", 0)
        ),
        "trust_rules": sorted(
            str(rule) for rule in report.get("trustRules", [])
        ),
    }


def merge_bridge_summary(
    target: dict[str, Any],
    update: dict[str, Any],
) -> None:
    """Merge a bridge report summary into a root-grouped summary."""

    target["diagnostic_count"] += update["diagnostic_count"]
    target["low_confidence_join_count"] += update[
        "low_confidence_join_count"
    ]
    target["unmatched_join_count"] += update["unmatched_join_count"]
    target["route_audit_claim_count"] += update[
        "route_audit_claim_count"
    ]
    target["route_audit_diagnostic_count"] += update[
        "route_audit_diagnostic_count"
    ]
    for key, count in update["diagnostic_counts"].items():
        target["diagnostic_counts"][key] = (
            target["diagnostic_counts"].get(key, 0) + count
        )
    target["trust_rules"] = sorted(
        set(target["trust_rules"]) | set(update["trust_rules"])
    )


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


def counts_by_key(
    rows: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
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
        if (
            row.get("confidence") in {"low", "none"}
            or row.get("warningOnly") is True
        )
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
        if (
            edge["source"] == source
            and edge["kind"] == kind
            and edge["target"] in nodes
        )
    ]
    return sorted(linked, key=lambda node: node["id"])


def finding_labels(findings: list[Node]) -> list[str]:
    """Return compact finding labels."""

    if not findings:
        return ["none"]
    return [finding["label"] for finding in findings[:5]]


def finding_evidence_summaries(
    findings: list[Node],
) -> list[dict[str, Any]]:
    """Preserve bounded finding identity and evidence contracts in cards."""

    rows: list[dict[str, Any]] = []
    for finding in findings[:5]:
        data = finding.get("data", {})
        if not isinstance(data, dict) or not data.get("id"):
            continue
        rows.append(
            {
                key: data[key]
                for key in (
                    "id",
                    "scope",
                    "authority",
                    "confidence",
                    "priority",
                    "evidenceRefs",
                    "nextCommand",
                    "nonclaim",
                    "nonclaims",
                )
                if key in data
            }
        )
    return rows


def region_labels(regions: list[Node]) -> list[str]:
    """Return compact review-region labels."""

    if not regions:
        return ["none"]
    return [region["label"] for region in regions[:5]]


def strongest_evidence(
    findings: list[Node],
    regions: list[Node],
) -> list[str]:
    """Return the strongest evidence rows visible in the atlas."""

    if findings:
        return [
            f"finding: {finding['label']}"
            for finding in findings[:3]
        ]
    if regions:
        return [
            f"review_region: {region['label']}"
            for region in regions[:3]
        ]
    return ["not recorded in atlas"]
