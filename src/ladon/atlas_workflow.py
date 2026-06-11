"""Reviewer workflow summaries derived from atlas JSON and optional bridge reports."""

from __future__ import annotations

from typing import Any

from ladon.atlas import atlas_reviewer_cards
from ladon.atlas_diff import diff_atlases


def build_atlas_workflow(
    atlas: dict[str, Any],
    *,
    before_atlas: dict[str, Any] | None = None,
    bridge_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the combined reviewer workflow surface."""

    bridges = bridge_reports or []
    diff = diff_atlases(before_atlas, atlas) if before_atlas is not None else empty_diff()
    return {
        "schema": "ladon-atlas-workflow-v1",
        "canonicalMachineReadableSurface": "atlas_json",
        "canonicalAtlasSchema": atlas.get("schema", ""),
        "inputs": {
            "beforeAtlasPresent": before_atlas is not None,
            "bridgeReportCount": len(bridges),
        },
        "sections": {
            "changedRows": changed_rows(diff),
            "recurringHotspots": recurring_hotspots(atlas),
            "reviewPriorityRoots": review_priority_roots(atlas, bridges),
            "lowConfidenceJoins": low_confidence_joins(bridges),
            "incompleteOrStaleEvidence": incomplete_or_stale_evidence(atlas, bridges),
        },
        "reviewerCards": atlas_reviewer_cards(atlas, bridges),
    }


def empty_diff() -> dict[str, Any]:
    """Return the stable no-before-atlas diff shape."""

    return {
        "schema": "ladon-atlas-diff-v1",
        "summary": {"added": 0, "removed": 0, "changed": 0, "by_category": {}},
        "added": [],
        "removed": [],
        "changed": [],
    }


def changed_rows(diff: dict[str, Any]) -> dict[str, Any]:
    """Return compact changed-row context for workflow output."""

    return {
        "summary": diff["summary"],
        "added": diff.get("added", [])[:10],
        "removed": diff.get("removed", [])[:10],
        "changed": diff.get("changed", [])[:10],
    }


def recurring_hotspots(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    """Return finding subjects that recur across reports."""

    occurrences: dict[tuple[str, str], set[str]] = {}
    totals: dict[tuple[str, str], int] = {}
    nodes = {node["id"]: node for node in atlas.get("nodes", [])}
    for edge in atlas.get("edges", []):
        if edge.get("kind") != "has_finding":
            continue
        finding = nodes.get(edge.get("target", ""))
        if not finding:
            continue
        data = finding.get("data", {})
        key = (str(data.get("kind", "")), str(data.get("subject", "")))
        occurrences.setdefault(key, set()).add(str(edge.get("source", "")))
        totals[key] = totals.get(key, 0) + int(data.get("count", 0))
    rows = [
        {
            "kind": kind,
            "subject": subject,
            "reportCount": len(reports),
            "totalCount": totals[(kind, subject)],
        }
        for (kind, subject), reports in occurrences.items()
        if subject and len(reports) > 1
    ]
    return sorted(rows, key=lambda row: (-row["reportCount"], -row["totalCount"], row["subject"]))[:10]


def review_priority_roots(
    atlas: dict[str, Any],
    bridge_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank roots by review pressure visible in atlas and bridge summaries."""

    bridge_pressure = bridge_pressure_by_root(bridge_reports)
    rows = []
    for report in report_nodes(atlas):
        data = report.get("data", {})
        root = str(data.get("analysis_root_module", ""))
        packet = data.get("packet_evidence", {})
        score = (
            int(data.get("finding_count", 0)) * 3
            + int(data.get("review_region_count", 0)) * 2
            + int(data.get("warning_count", 0))
            + int(packet.get("incomplete", 0)) * 2
            + bridge_pressure.get(root, 0)
        )
        rows.append(
            {
                "report": report["label"],
                "root": root,
                "score": score,
                "findingCount": int(data.get("finding_count", 0)),
                "reviewRegionCount": int(data.get("review_region_count", 0)),
                "packetIncomplete": int(packet.get("incomplete", 0)),
                "bridgePressure": bridge_pressure.get(root, 0),
            }
        )
    return sorted(rows, key=lambda row: (-row["score"], row["report"]))[:10]


def bridge_pressure_by_root(bridge_reports: list[dict[str, Any]]) -> dict[str, int]:
    """Return simple bridge pressure counts by root."""

    pressure: dict[str, int] = {}
    for report in bridge_reports:
        root = bridge_report_root(report)
        if not root:
            continue
        pressure[root] = pressure.get(root, 0) + len(low_confidence_joins([report]))
        pressure[root] += len(report.get("diagnostics", []))
    return pressure


def low_confidence_joins(bridge_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return optional ProofIR joins that should remain warning routes."""

    rows = []
    for report in bridge_reports:
        root = bridge_report_root(report)
        for join in report.get("joins", []):
            if not isinstance(join, dict):
                continue
            if not is_low_confidence_join(join):
                continue
            rows.append(
                {
                    "root": root,
                    "surfaceId": str(join.get("surfaceId", "")),
                    "declarationName": str(join.get("declarationName", "")),
                    "matchKind": str(join.get("matchKind", "")),
                    "confidence": str(join.get("confidence", "")),
                    "warningOnly": join.get("warningOnly") is True,
                }
            )
    return sorted(rows, key=lambda row: (row["root"], row["surfaceId"], row["declarationName"]))[:25]


def is_low_confidence_join(join: dict[str, Any]) -> bool:
    """Return whether a bridge join belongs in warning-oriented workflow rows."""

    return (
        join.get("confidence") in {"low", "none"}
        or join.get("warningOnly") is True
        or join.get("matchKind") == "unmatched"
    )


def incomplete_or_stale_evidence(
    atlas: dict[str, Any],
    bridge_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return packet or bridge evidence rows that need review."""

    rows = packet_evidence_gaps(atlas)
    rows.extend(bridge_stale_evidence(bridge_reports))
    return sorted(rows, key=lambda row: (row["kind"], row["subject"]))[:25]


def packet_evidence_gaps(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    """Return report-level packet evidence gaps."""

    rows = []
    for report in report_nodes(atlas):
        packet = report.get("data", {}).get("packet_evidence", {})
        if not packet:
            continue
        if int(packet.get("incomplete", 0)) == 0 and int(packet.get("stale", 0)) == 0:
            continue
        rows.append(
            {
                "kind": "packet_evidence",
                "subject": report["label"],
                "incomplete": int(packet.get("incomplete", 0)),
                "missing": int(packet.get("missing", 0)),
                "stale": int(packet.get("stale", 0)),
            }
        )
    return rows


def bridge_stale_evidence(bridge_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return stale-source bridge diagnostics."""

    rows = []
    for report in bridge_reports:
        root = bridge_report_root(report)
        for diagnostic in report.get("diagnostics", []):
            if not isinstance(diagnostic, dict):
                continue
            if diagnostic.get("ruleId") != "proofir.packet_stale_source":
                continue
            rows.append(
                {
                    "kind": "bridge_stale_source",
                    "subject": str(diagnostic.get("subject", "")),
                    "root": root,
                    "level": str(diagnostic.get("level", "")),
                }
            )
    return rows


def report_nodes(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    """Return report nodes from an atlas."""

    return sorted(
        (node for node in atlas.get("nodes", []) if node.get("kind") == "report"),
        key=lambda node: node["label"],
    )


def bridge_report_root(report: dict[str, Any]) -> str:
    """Return the first root visible in a bridge reviewer card."""

    for card in report.get("reviewerCards", []):
        if isinstance(card, dict) and card.get("root"):
            return str(card["root"])
    return ""


def render_atlas_workflow_markdown(workflow: dict[str, Any]) -> str:
    """Render the combined reviewer workflow as compact Markdown."""

    sections = workflow["sections"]
    lines = [
        "# Ladon Atlas Review Workflow",
        "",
        f"- canonical machine-readable surface: {workflow['canonicalMachineReadableSurface']}",
        f"- bridge reports: {workflow['inputs']['bridgeReportCount']}",
        "",
    ]
    lines.extend(changed_rows_lines(sections["changedRows"]))
    lines.extend(row_section_lines("Recurring Hotspots", sections["recurringHotspots"], "subject"))
    lines.extend(row_section_lines("Review Priority Roots", sections["reviewPriorityRoots"], "root"))
    lines.extend(row_section_lines("Low Confidence Joins", sections["lowConfidenceJoins"], "surfaceId"))
    lines.extend(
        row_section_lines(
            "Incomplete Or Stale Evidence",
            sections["incompleteOrStaleEvidence"],
            "subject",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def changed_rows_lines(section: dict[str, Any]) -> list[str]:
    """Render changed-row summary."""

    summary = section["summary"]
    return [
        "## Changed Rows",
        f"- added: {summary['added']}",
        f"- removed: {summary['removed']}",
        f"- changed: {summary['changed']}",
        "",
    ]


def row_section_lines(title: str, rows: list[dict[str, Any]], label_key: str) -> list[str]:
    """Render one compact workflow row section."""

    lines = [f"## {title}"]
    if not rows:
        return [*lines, "- none", ""]
    for row in rows[:10]:
        lines.append(f"- {row.get(label_key, '')}: {compact_row_payload(row, label_key)}")
    return [*lines, ""]


def compact_row_payload(row: dict[str, Any], label_key: str) -> str:
    """Render the non-label keys for one workflow row."""

    return ", ".join(
        f"{key}={value}"
        for key, value in sorted(row.items())
        if key != label_key and value not in {"", None}
    )
