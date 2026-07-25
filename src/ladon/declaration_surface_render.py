"""Text rendering for bounded elaborated declaration surfaces."""

from __future__ import annotations

from typing import Any


def declaration_surface_lines(summary: dict[str, Any]) -> list[str]:
    """Render bounded root statements with explicit Lean/unavailable state."""

    rows = {
        str(row.get("declaration")): row
        for row in summary.get("declarations", [])
        if isinstance(row, dict) and row.get("declaration")
    }
    roots = [
        rows[name]
        for name in summary.get("chosen_roots", [])[:8]
        if name in rows
    ]
    state = summary.get("elaborated_surface", {})
    lines = [
        "Root Declaration Surfaces",
        f"- status: {state.get('status', 'skipped')}",
    ]
    if state.get("reason"):
        lines.append(f"- reason: {state['reason']}")
    for row in roots:
        lines.extend(one_declaration_surface_lines(row))
    lines.append(
        "- nonclaim: surfaces locate Lean artifacts; Ladon does not "
        "independently verify theorem truth"
    )
    return [*lines, ""]


def one_declaration_surface_lines(row: dict[str, Any]) -> list[str]:
    """Render one finite declaration statement row."""

    surface = row.get("surface", {})
    name = row.get("declaration", "<unnamed>")
    kind = row.get("kind", "declaration")
    location = declaration_location(row)
    if surface.get("status") != "complete":
        reason = surface.get("reason") or "elaborated surface unavailable"
        return [f"- {name} ({kind}, {location}): {reason}"]
    lines = [f"- {name} ({kind}, {location})"]
    if surface.get("renderedType"):
        suffix = " [truncated]" if surface.get("renderedTypeTruncated") else ""
        lines.append(f"  statement: {surface['renderedType']}{suffix}")
    conclusion = surface.get("conclusion")
    if conclusion:
        lines.append(f"  conclusion: {conclusion}")
    premises = surface.get("premises", {})
    if premises.get("items"):
        lines.append("  premises: " + "; ".join(premises["items"][:5]))
    if surface.get("bodyTruncated"):
        lines.append("  body: present; source surface truncated")
    return lines


def declaration_location(row: dict[str, Any]) -> str:
    """Return one compact source location."""

    path = str(row.get("sourcePath", "source unavailable"))
    source_range = row.get("sourceRange")
    if isinstance(source_range, dict) and source_range.get("startLine"):
        return f"{path}:{source_range['startLine']}"
    return path


def declaration_trust_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render direct trust evidence without a transitive-footprint claim."""

    facts = [
        (row.get("declaration", "<unnamed>"), fact)
        for row in rows
        if isinstance(row, dict)
        for fact in row.get("surface", {}).get("trustFacts", [])
        if isinstance(fact, dict)
    ][:12]
    if not facts:
        return []
    lines = ["Direct Lean Trust Footprint"]
    lines.extend(trust_fact_line(name, fact) for name, fact in facts)
    lines.append(
        "- nonclaim: direct expression traversal only; no transitive axiom "
        "closure or proof verdict"
    )
    return [*lines, ""]


def trust_fact_line(name: str, fact: dict[str, Any]) -> str:
    """Render one direct trust row with its evidence authority."""

    return (
        f"- {name}: {fact.get('kind')} scope={fact.get('scope')} "
        f"target={fact.get('target') or '-'} authority={fact.get('authority')}"
    )
