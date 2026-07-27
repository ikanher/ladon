"""Authority classification for declaration-graph inspection rows."""

from __future__ import annotations

from typing import Any, Mapping


def graph_declaration_authority(
    raw: Mapping[str, Any],
    surface: Mapping[str, Any],
) -> str:
    """Retain explicit parser or Lean authority without inventing a default."""

    explicit = _text(raw.get("authority"))
    if explicit is not None:
        return explicit
    status = _text(surface.get("status"))
    if status in {"complete", "partial"}:
        return "lean_environment"
    if raw.get("resolution") == "resolved_imported_constant":
        return "lean_environment"
    parser_candidates = raw.get("parserCandidates")
    if isinstance(parser_candidates, Mapping):
        parser_authority = _text(parser_candidates.get("authority"))
        if parser_authority is not None:
            return parser_authority
    backend = _text(raw.get("extractionBackend"))
    if backend is not None and backend.startswith("lean_parser"):
        return "lean_parser"
    return backend or "unavailable"


def graph_declaration_status(
    raw: Mapping[str, Any],
    surface: Mapping[str, Any],
) -> str:
    """Classify parser candidates separately from Lean-observed declarations."""

    if (
        surface.get("status") == "complete"
        or raw.get("resolution") == "resolved_imported_constant"
    ):
        return "lean_resolved"
    if surface.get("status") == "partial":
        return "lean_partial"
    if graph_declaration_authority(raw, surface) == "unavailable":
        return "unavailable"
    return "parser_candidate"


def declaration_candidate_relationship(candidate_status: str) -> str:
    """Describe a lexical-to-graph link at its recorded authority."""

    return {
        "lean_resolved": "Lean-resolved declaration candidate",
        "lean_partial": "partially Lean-observed declaration candidate",
        "parser_candidate": "parser declaration candidate",
    }.get(candidate_status, "declaration candidate with unavailable authority")


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = [
    "declaration_candidate_relationship",
    "graph_declaration_authority",
    "graph_declaration_status",
]
