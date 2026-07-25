"""Text rendering for declaration graph and elaborated evidence sections."""

from __future__ import annotations

from typing import Any

from ladon.declaration_surface_render import (
    declaration_surface_lines,
    declaration_trust_lines,
)


def declaration_graph_lines(summary: dict[str, Any] | None) -> list[str]:
    """Render declaration graph summary when declaration IR was available."""

    if summary is None:
        return []
    lines = [
        "Declaration Graph",
        f"- declarations: {summary['declaration_count']}",
        f"- edges: {summary['edge_count']}",
        f"- unresolved references: {summary['unresolved_reference_count']}",
        "",
    ]
    lines.extend(declaration_evidence_lines(summary.get("declarations", [])))
    lines.extend(declaration_surface_lines(summary))
    lines.extend(declaration_trust_lines(summary.get("declarations", [])))
    lines.extend(
        declaration_fan_lines(
            "Top Declaration Fan-In",
            summary.get("top_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        declaration_fan_lines(
            "Top Declaration Fan-Out",
            summary.get("top_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(
        declaration_family_lines(summary.get("declaration_name_families", []))
    )
    lines.extend(
        proof_family_similarity_lines(
            summary.get("proof_family_similarity_candidates", [])
        )
    )
    lines.extend(
        unresolved_reference_class_lines(
            summary.get("unresolved_reference_classes", [])
        )
    )
    lines.extend(
        unresolved_reference_lines(
            summary.get("top_unresolved_references", [])
        )
    )
    lines.extend(
        actionable_unresolved_reference_lines(
            summary.get("top_actionable_unresolved_references", [])
        )
    )
    return lines


def declaration_evidence_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render declaration source-evidence coverage without proof overclaims."""

    if not rows:
        return []
    confidences = confidence_counts(rows)
    lines = [
        "Declaration Evidence",
        f"- rows: {len(rows)}",
        f"- source ranges: {count_present(rows, 'sourceRange')}",
        f"- content hashes: {count_present(rows, 'contentHash')}",
    ]
    lines.extend(
        f"- confidence {name}: {count}"
        for name, count in sorted(confidences.items())
    )
    lines.append(
        "- trust: source evidence is attachment confidence, not proof truth"
    )
    return [*lines, ""]


def confidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count declaration evidence rows by explicit confidence label."""

    counts: dict[str, int] = {}
    for row in rows:
        confidence = str(row.get("confidence", "unspecified"))
        counts[confidence] = counts.get(confidence, 0) + 1
    return counts


def count_present(rows: list[dict[str, Any]], key: str) -> int:
    """Count rows that expose one optional evidence field."""

    return sum(1 for row in rows if row.get(key) is not None)


def declaration_fan_lines(
    title: str,
    rows: list[dict[str, Any]],
    metric: str,
) -> list[str]:
    """Render declaration graph fan-in or fan-out hotspots."""

    visible = [row for row in rows if row.get(metric, 0) > 0][:5]
    if not visible:
        return []
    lines = [title]
    lines.extend(f"- {row['declaration']}: {row[metric]}" for row in visible)
    return [*lines, ""]


def unresolved_reference_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render common unresolved reference candidates."""

    visible = [row for row in rows if row.get("count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Top Unresolved References"]
    lines.extend(unresolved_reference_line(row) for row in visible)
    return [*lines, ""]


def unresolved_reference_class_lines(
    rows: list[dict[str, Any]],
) -> list[str]:
    """Render unresolved reference occurrence counts by class."""

    if not rows:
        return []
    lines = ["Unresolved Reference Classes"]
    lines.extend(
        f"- {row['classification']}: {row['count']}"
        for row in rows[:6]
    )
    return [*lines, ""]


def declaration_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render declaration name family groups."""

    visible = [row for row in rows if row.get("count", 0) > 1][:5]
    if not visible:
        return []
    lines = ["Declaration Name Families"]
    lines.extend(f"- {row['suffix']}: {row['count']}" for row in visible)
    return [*lines, ""]


def proof_family_similarity_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render deterministic proof-family similarity candidates."""

    if not rows:
        return []
    lines = ["Proof Family Similarity Candidates"]
    lines.extend(proof_family_similarity_line(row) for row in rows[:5])
    return [*lines, ""]


def proof_family_similarity_line(row: dict[str, Any]) -> str:
    """Render one proof-family similarity row without clone claims."""

    pair = " | ".join(row.get("best_pair", []))
    promoted = row.get(
        "promoted",
        float(row.get("similarity_score", 0.0)) >= 0.75,
    )
    state = "promoted" if promoted else "below-promotion"
    evidence = ",".join(row.get("evidence_basis", []))
    evidence_suffix = f" evidence={evidence}" if evidence else ""
    return (
        f"- {row['suffix']}: similar proof-family candidate "
        f"score={row['similarity_score']} state={state} pair={pair}"
        f"{evidence_suffix}"
    )


def unresolved_reference_line(row: dict[str, Any]) -> str:
    """Render one unresolved reference row with an optional classification."""

    classification = row.get("classification")
    suffix = f" ({classification})" if classification else ""
    return f"- {row['candidate']}: {row['count']}{suffix}"


def actionable_unresolved_reference_lines(
    rows: list[dict[str, Any]],
) -> list[str]:
    """Render unresolved candidates worth human follow-up."""

    visible = [row for row in rows if row.get("count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Top Actionable Unresolved References"]
    lines.extend(f"- {row['candidate']}: {row['count']}" for row in visible)
    return [*lines, ""]
