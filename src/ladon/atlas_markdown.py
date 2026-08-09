"""Markdown rendering for atlas summaries and reviewer cards."""

from __future__ import annotations

from typing import Any

from ladon.atlas_cards import atlas_reviewer_cards
from ladon.atlas_graph import Node


def render_atlas_markdown(atlas: dict[str, Any]) -> str:
    """Render a compact Markdown summary for an atlas graph."""

    lines = ["# Ladon Report Atlas", ""]
    lines.extend(summary_lines(atlas["summary"]))
    lines.extend(
        workflow_diagnostic_lines(
            atlas.get("workflowDiagnostics", []),
        )
    )
    lines.extend(report_table_lines(atlas["nodes"]))
    return "\n".join(lines) + "\n"


def render_reviewer_cards_markdown(
    atlas: dict[str, Any],
    external_evidence: list[dict[str, Any]] | None = None,
) -> str:
    """Render reviewer cards as compact Markdown."""

    lines = ["# Ladon Atlas Reviewer Cards", ""]
    for card in atlas_reviewer_cards(atlas, external_evidence):
        lines.extend(reviewer_card_lines(card))
    return "\n".join(lines).rstrip() + "\n"


def reviewer_card_lines(card: dict[str, Any]) -> list[str]:
    """Render one reviewer card."""

    return [
        f"## `{card['report']}`",
        "",
        f"- root: {card['root']}",
        f"- extraction backend: {card['extraction_backend']}",
        (
            "- declaration evidence: "
            f"{format_declaration_evidence(card['declaration_evidence'])}"
        ),
        (
            "- packet evidence: "
            f"{format_packet_evidence(card['packet_evidence'])}"
        ),
        (
            "- bridge diagnostics: "
            f"{format_bridge_diagnostics(card['bridge_diagnostics'])}"
        ),
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
        *[
            f"  - {item}"
            for item in bridge_trust_notes(
                card["bridge_diagnostics"]
            )
        ],
        "",
    ]


def format_declaration_evidence(summary: dict[str, Any]) -> str:
    """Render one compact declaration-evidence summary for reviewer cards."""

    counts = summary.get("confidence_counts", {})
    confidence = ", ".join(
        f"{key}={value}" for key, value in sorted(counts.items())
    )
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
    diagnostics = ", ".join(
        f"{key}={value}" for key, value in sorted(counts.items())
    )
    suffix = f" diagnostics({diagnostics})" if diagnostics else ""
    return (
        f"diagnostics={summary.get('diagnostic_count', 0)} "
        "low_confidence_joins="
        f"{summary.get('low_confidence_join_count', 0)} "
        f"unmatched={summary.get('unmatched_join_count', 0)} "
        f"route_audit_claims={summary.get('route_audit_claim_count', 0)} "
        "route_audit_diagnostics="
        f"{summary.get('route_audit_diagnostic_count', 0)}"
        f"{suffix}"
    )


def bridge_trust_notes(
    summary: dict[str, Any],
) -> list[str]:
    """Return visible bridge trust notes or a stable no-input marker."""

    notes = summary.get("trust_rules", [])
    return notes if notes else ["no bridge report supplied"]


def summary_lines(summary: dict[str, int]) -> list[str]:
    """Render atlas summary counts."""

    lines = ["## Summary"]
    for key in sorted(summary):
        lines.append(f"- {key}: {summary[key]}")
    return [*lines, ""]


def workflow_diagnostic_lines(rows: Any) -> list[str]:
    """Render bundle entries that ended without analysis reports."""

    valid = [row for row in rows if isinstance(row, dict)]
    if not valid:
        return []
    lines = [
        "## Bundle Workflow Diagnostics",
        "",
        "| Entry | Root | State | Required | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in valid:
        lines.append(
            "| "
            f"`{row.get('entryId', '')}` | "
            f"{row.get('root', '')} | "
            f"{row.get('state', '')} | "
            f"{str(row.get('required', False)).lower()} | "
            f"{row.get('reason', '')} |"
        )
    lines.extend(
        [
            "",
            f"- authority: {valid[0].get('authority', '')}",
            f"- nonclaim: {valid[0].get('nonclaim', '')}",
        ]
    )
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
