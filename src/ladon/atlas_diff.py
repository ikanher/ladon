"""Deterministic diffs for Ladon atlas JSON artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AtlasRow:
    """Comparable atlas row used by the diff engine."""

    category: str
    key: str
    payload: tuple[tuple[str, str], ...]

    def to_json(self) -> dict[str, Any]:
        """Return a stable JSON representation."""

        return {
            "category": self.category,
            "key": self.key,
            "payload": {key: value for key, value in self.payload},
        }


def diff_atlases(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Return added, removed, and changed normalized atlas rows."""

    before_rows = atlas_row_map(before)
    after_rows = atlas_row_map(after)
    before_keys = set(before_rows)
    after_keys = set(after_rows)
    added = [after_rows[key].to_json() for key in sorted(after_keys - before_keys)]
    removed = [before_rows[key].to_json() for key in sorted(before_keys - after_keys)]
    changed = [
        {
            "category": before_rows[key].category,
            "key": before_rows[key].key,
            "before": before_rows[key].to_json()["payload"],
            "after": after_rows[key].to_json()["payload"],
        }
        for key in sorted(before_keys & after_keys)
        if before_rows[key].payload != after_rows[key].payload
    ]
    return {
        "schema": "ladon-atlas-diff-v1",
        "summary": diff_summary(added, removed, changed),
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def atlas_row_map(atlas: dict[str, Any]) -> dict[tuple[str, str], AtlasRow]:
    """Flatten relevant atlas graph rows into comparable rows."""

    nodes = {node["id"]: node for node in atlas.get("nodes", [])}
    rows: list[AtlasRow] = []
    rows.extend(report_rows(nodes.values()))
    rows.extend(evidence_rows(nodes.values()))
    rows.extend(bridge_diagnostic_rows(nodes.values()))
    rows.extend(edge_rows(nodes, atlas.get("edges", [])))
    return {(row.category, row.key): row for row in rows}


def report_rows(nodes: Any) -> list[AtlasRow]:
    """Return report summary rows."""

    rows = []
    for node in nodes:
        if node["kind"] != "report":
            continue
        data = node.get("data", {})
        rows.append(
            row(
                "reports",
                node["label"],
                {
                    "analysis_root_module": data.get("analysis_root_module", ""),
                    "module_count": data.get("module_count", 0),
                    "declaration_count": data.get("declaration_count", 0),
                    "finding_count": data.get("finding_count", 0),
                    "review_region_count": data.get("review_region_count", 0),
                },
            )
        )
    return rows


def evidence_rows(nodes: Any) -> list[AtlasRow]:
    """Return comparable packet/declaration evidence status rows."""

    rows = []
    for node in nodes:
        if node["kind"] != "report":
            continue
        data = node.get("data", {})
        packet = data.get("packet_evidence", {})
        declaration = data.get("declaration_evidence", {})
        rows.append(
            row(
                "evidence_status",
                node["label"],
                {
                    "packet_incomplete": packet.get("incomplete", 0),
                    "packet_stale": packet.get("stale", 0),
                    "declaration_rows": declaration.get("rows", 0),
                    "declaration_hashes": declaration.get("content_hashes", 0),
                },
            )
        )
    return rows


def bridge_diagnostic_rows(nodes: Any) -> list[AtlasRow]:
    """Return comparable optional bridge diagnostic rows."""

    rows = []
    for node in nodes:
        if node["kind"] != "report":
            continue
        diagnostics = node.get("data", {}).get("bridge_diagnostics", {}).get("diagnostic_counts", {})
        for rule_id, count in sorted(diagnostics.items()):
            rows.append(
                row(
                    "bridge_diagnostics",
                    f"{node['label']}|{rule_id}",
                    {"count": count},
                )
            )
    return rows


def edge_rows(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> list[AtlasRow]:
    """Return rows derived from graph edges and endpoint data."""

    rows: list[AtlasRow] = []
    for edge in edges:
        target = nodes.get(edge["target"])
        if target is None:
            continue
        match edge["kind"]:
            case "has_finding":
                rows.append(finding_row(edge["source"], target))
            case "has_review_region":
                rows.append(review_region_row(edge["source"], target))
            case "has_signal":
                rows.append(signal_row(nodes, edge["source"], target))
            case "highlights_declaration":
                rows.append(highlight_row("declaration_highlights", edge["source"], target, edge))
            case "highlights_module":
                rows.append(highlight_row("module_highlights", edge["source"], target, edge))
    return rows


def finding_row(report_id: str, finding: dict[str, Any]) -> AtlasRow:
    """Return one comparable finding row."""

    data = finding.get("data", {})
    kind = data.get("kind", "")
    subject = data.get("subject", "")
    return row(
        finding_category(kind),
        f"{report_label(report_id)}|{kind}|{subject}",
        {"count": data.get("count", 0)},
    )


def review_region_row(report_id: str, region: dict[str, Any]) -> AtlasRow:
    """Return one comparable review-region row."""

    data = region.get("data", {})
    kind = data.get("kind", "")
    return row(
        "review_regions",
        f"{report_label(report_id)}|{kind}",
        {"title": region.get("label", ""), "signal_count": data.get("signal_count", 0)},
    )


def signal_row(
    nodes: dict[str, dict[str, Any]],
    region_id: str,
    signal: dict[str, Any],
) -> AtlasRow:
    """Return one comparable signal row."""

    data = signal.get("data", {})
    kind = data.get("kind", "")
    subject = data.get("subject", "")
    return row(
        signal_category(kind),
        f"{report_label(report_for_region(nodes, region_id))}|{kind}|{subject}",
        {"count": data.get("count", 0), "region": region_kind(region_id)},
    )


def highlight_row(
    category: str,
    report_id: str,
    target: dict[str, Any],
    edge: dict[str, Any],
) -> AtlasRow:
    """Return one comparable highlight row."""

    data = edge.get("data", {})
    metric = data.get("metric", "")
    return row(
        category,
        f"{report_label(report_id)}|{metric}|{target['label']}",
        {"rank": data.get("rank", 0), "value": data.get("value", 0)},
    )


def row(category: str, key: str, payload: dict[str, Any]) -> AtlasRow:
    """Build a comparable row with stringified stable payload values."""

    return AtlasRow(
        category=category,
        key=key,
        payload=tuple(sorted((str(item_key), str(item_value)) for item_key, item_value in payload.items())),
    )


def finding_category(kind: str) -> str:
    """Return specialized categories for known finding classes."""

    if "unresolved_reference" in kind:
        return "unresolved_reference_classes"
    if "root_scope" in kind:
        return "root_scope_shifts"
    return "findings"


def signal_category(kind: str) -> str:
    """Return specialized categories for known signal classes."""

    if "unresolved_reference" in kind:
        return "unresolved_reference_classes"
    if "root_scope" in kind:
        return "root_scope_shifts"
    if "proof_family" in kind:
        return "proof_family_pressure"
    return "signals"


def report_for_region(nodes: dict[str, dict[str, Any]], region_id: str) -> str:
    """Infer owning report ID from a region node ID."""

    if not region_id.startswith("region:"):
        return ""
    relative = region_id.removeprefix("region:").rsplit(":", 1)[0]
    report_id = f"report:{relative}"
    return report_id if report_id in nodes else ""


def report_label(report_id: str) -> str:
    """Return report path label from a report node ID."""

    return report_id.removeprefix("report:")


def region_kind(region_id: str) -> str:
    """Return region kind from a region node ID."""

    return region_id.rsplit(":", 1)[-1]


def diff_summary(
    added: list[dict[str, Any]],
    removed: list[dict[str, Any]],
    changed: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize diff row counts."""

    rows = {"added": added, "removed": removed, "changed": changed}
    return {
        "added": len(added),
        "removed": len(removed),
        "changed": len(changed),
        "by_category": {
            category: {
                "added": count_rows(added, category),
                "removed": count_rows(removed, category),
                "changed": count_rows(changed, category),
            }
            for category in sorted({row["category"] for values in rows.values() for row in values})
        },
    }


def count_rows(rows: list[dict[str, Any]], category: str) -> int:
    """Count rows for one diff category."""

    return sum(1 for row in rows if row["category"] == category)


def render_atlas_diff_markdown(diff: dict[str, Any]) -> str:
    """Render a compact Markdown diff report."""

    summary = diff["summary"]
    lines = [
        "# Ladon Atlas Diff",
        "",
        "## Summary",
        f"- added: {summary['added']}",
        f"- removed: {summary['removed']}",
        f"- changed: {summary['changed']}",
        "",
    ]
    lines.extend(category_summary_lines(summary["by_category"]))
    for section in ("added", "removed", "changed"):
        lines.extend(diff_section_lines(section.title(), diff[section]))
    return "\n".join(lines).rstrip() + "\n"


def category_summary_lines(by_category: dict[str, dict[str, int]]) -> list[str]:
    """Render category-level counts."""

    if not by_category:
        return []
    lines = ["## Categories", "", "| Category | Added | Removed | Changed |", "| --- | ---: | ---: | ---: |"]
    for category, counts in by_category.items():
        lines.append(f"| {category} | {counts['added']} | {counts['removed']} | {counts['changed']} |")
    return [*lines, ""]


def diff_section_lines(title: str, rows: list[dict[str, Any]]) -> list[str]:
    """Render a short row sample for one diff section."""

    if not rows:
        return []
    lines = [f"## {title}"]
    for row in rows[:10]:
        lines.append(f"- {row['category']}: `{row['key']}`")
    return [*lines, ""]


def load_atlas(path: Path) -> dict[str, Any]:
    """Load an atlas JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))
