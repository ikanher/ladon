"""Report-backed proof-mechanism rows with separate quoted authority."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.inspection_adapter_common import (
    additive_row,
    mapping_rows,
    optional_mapping,
    optional_text,
    stable_id,
    text,
    with_enrichment,
)
from ladon.inspection_models import ArtifactIdentity, InspectionRow
from ladon.report_coverage import PROOF_XRAY_ROWS_COVERAGE


def merge_quoted_proof_rows(
    sections: Mapping[str, Any],
    artifact: ArtifactIdentity,
    lexical: Sequence[InspectionRow],
    *,
    lexical_available: bool,
    scope: str,
) -> tuple[list[InspectionRow], bool]:
    """Add optional proof-xray classifications without upgrading lexical rows."""

    proof_xray = optional_mapping(sections.get("proof_xray"))
    adapted = [
        _proof_xray_row(raw)
        for raw in mapping_rows(proof_xray.get("rows"))
    ]
    quoted = [
        additive_row(
            artifact,
            "proof-mechanisms",
            raw,
            {},
            canonical_ref=f"#/sections/proof_xray/rows/{index}",
            coverage_ref=PROOF_XRAY_ROWS_COVERAGE,
            scope=scope,
        )
        for index, raw in enumerate(_unique_row_ids(adapted))
    ]
    linked = _link_proof_xray_enrichments(lexical, quoted)
    return [*linked, *quoted], lexical_available or "rows" in proof_xray


def _proof_xray_row(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Flatten quoted evidence only enough for navigation and joining."""

    evidence = optional_mapping(raw.get("evidence"))
    authority = _xray_value(raw, evidence, "authority")
    return {
        **dict(raw),
        "id": _xray_identifier(raw, evidence),
        "declarationName": _xray_declaration(raw, evidence),
        "module": _xray_value(raw, evidence, "module"),
        "path": _xray_value(raw, evidence, "sourcePath"),
        "sourceRange": _xray_value(raw, evidence, "sourceRange"),
        "authority": authority,
        "leanEnrichment": _xray_enrichment(raw, evidence, authority),
    }


def _unique_row_ids(
    rows: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Disambiguate malformed duplicate provider IDs by canonical row content."""

    bases = [_row_id_base(row) for row in rows]
    counts = Counter(bases)
    return [
        (
            {**row, "id": stable_id("proof_xray_classification", base, str(index))}
            if counts[base] > 1
            else {**row, "id": base}
        )
        for index, (row, base) in enumerate(zip(rows, bases, strict=True))
    ]


def _row_id_base(row: Mapping[str, Any]) -> str:
    """Return a provider identity or a deterministic content fallback."""

    identifier = optional_text(row.get("id"))
    if identifier is not None:
        return identifier
    encoded = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return stable_id("proof_xray_classification", encoded)


def _xray_value(
    raw: Mapping[str, Any],
    evidence: Mapping[str, Any],
    key: str,
) -> Any:
    return raw.get(key) or evidence.get(key)


def _xray_identifier(
    raw: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> Any:
    base = _xray_value(raw, evidence, "rowId") or raw.get("id")
    kind = optional_text(raw.get("kind"))
    if not isinstance(base, str) or not base or kind is None:
        return base
    suffix = f":{kind}"
    return base if base.endswith(suffix) else f"{base}{suffix}"


def _xray_declaration(
    raw: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> Any:
    return _xray_value(raw, evidence, "declarationName") or raw.get("subject")


def _xray_enrichment(
    raw: Mapping[str, Any],
    evidence: Mapping[str, Any],
    authority: Any,
) -> Mapping[str, Any]:
    return {
        "status": "available",
        "authority": authority,
        "backend": _xray_value(raw, evidence, "backend"),
        "toolchain": _xray_value(raw, evidence, "toolVersion"),
        "quotedOnly": True,
    }


def _link_proof_xray_enrichments(
    lexical: Sequence[InspectionRow],
    quoted: Sequence[InspectionRow],
) -> list[InspectionRow]:
    by_declaration = {
        text(row.fields.get("declaration")): row
        for row in quoted
        if row.fields.get("declaration")
    }
    return [_linked_proof_row(row, by_declaration) for row in lexical]


def _linked_proof_row(
    row: InspectionRow,
    quoted: Mapping[str, InspectionRow],
) -> InspectionRow:
    matched = quoted.get(text(row.fields.get("declaration")))
    if matched is None:
        return row
    return with_enrichment(
        row,
        {
            "noun": "proof-mechanisms",
            "id": matched.identifier,
            "relationship": "quoted proof-xray evidence",
            "authority": matched.authority,
        },
    )


__all__ = ["merge_quoted_proof_rows"]
