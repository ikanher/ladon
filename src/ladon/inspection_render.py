"""Text rendering for the canonical inspection page model."""

from __future__ import annotations

import json

from ladon.inspection_models import InspectionPage


def render_inspection_text(page: InspectionPage) -> str:
    """Render the same bounded page represented by inspection JSON."""

    payload = page.to_dict()
    coverage = payload["coverage"]
    collection = coverage["collection"]
    query = payload["query"]
    artifact = payload["artifact"]
    lines = [
        f"Ladon inspection: {query['noun']}",
        (
            f"Artifact: {artifact['kind']} {artifact['schema']} "
            f"{artifact['fingerprint']}"
        ),
        f"Query fingerprint: {query['fingerprint']}",
        (
            f"Rows: {coverage['pageVisible']} visible, "
            f"{coverage['matchingVisibleTotal']} observed matching, "
            f"{coverage['before']} before, {coverage['after']} after"
        ),
        (
            f"Collection: {collection.get('id')} "
            f"({collection.get('completeness')}; "
            f"total={_optional_count(collection.get('total'))}; "
            f"omitted={_optional_count(collection.get('omitted'))})"
        ),
    ]
    for diagnostic in payload["diagnostics"]:
        lines.append(
            f"Diagnostic: {diagnostic.get('code')}: {diagnostic.get('message')}"
        )
    for row in payload["rows"]:
        lines.extend(_render_row(row))
    if payload["nextCursor"] is not None:
        lines.extend(
            (
                f"Next cursor: {payload['nextCursor']}",
                (
                    "Next: ladon inspect "
                    f"{query['noun']} <same artifact and filters> "
                    f"--limit {query['limit']} "
                    f"--cursor {payload['nextCursor']}"
                ),
            )
        )
    return "\n".join(lines) + "\n"


def _render_row(row: dict) -> list[str]:
    anchor = row["sourceAnchor"]
    location = (
        _source_location(anchor)
        if anchor["status"] == "exact"
        else f"unavailable ({anchor['reason']})"
    )
    fields = " ".join(
        f"{key}={_field_text(value)}"
        for key, value in sorted(row["fields"].items())
        if value is not None and value != "" and value != ()
    )
    lines = [
        (
            f"{row['id']} | authority={row['authority']} | "
            f"population={row['population']} | source={location}"
        ),
        f"  canonical: {row['canonicalRef']}",
        f"  coverage: {row['coverageRef']}",
    ]
    if fields:
        lines.append(f"  fields: {fields}")
    for enrichment in row["enrichments"]:
        lines.append(
            "  enrichment: "
            + json.dumps(
                enrichment,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    for nonclaim in row["nonclaims"]:
        lines.append(f"  nonclaim: {nonclaim}")
    return lines


def _source_location(anchor: dict) -> str:
    source_range = anchor.get("range")
    if not isinstance(source_range, dict):
        return str(anchor["path"])
    start = source_range.get("start")
    if not isinstance(start, dict) or start.get("line") is None:
        return str(anchor["path"])
    line = start["line"]
    column = start.get("column")
    suffix = f":{line}" if column is None else f":{line}:{column}"
    return f"{anchor['path']}{suffix}"


def _field_text(value: object) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return str(value)


def _optional_count(value: object) -> str:
    return "unknown" if value is None else str(value)


__all__ = ["render_inspection_text"]
