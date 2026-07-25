"""Version-aware Ladon report views used by atlas construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ladon.report_adapters import report_version
from ladon.report_v2 import supported_report_view
from ladon.report_v3 import REPORT_V3_VERSION


def is_ladon_report_payload(payload: dict[str, Any]) -> bool:
    """Return whether a JSON payload is a Ladon report, not an auxiliary cache."""

    return (
        isinstance(payload, dict)
        and isinstance(payload.get("metadata"), dict)
        and (
            isinstance(payload.get("module_dag"), dict)
            or isinstance(payload.get("phases"), dict)
        )
    )


def atlas_report_view(
    payload: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    """Return a v1/v2/v3 consumer view without guessing unknown versions."""

    if report_version(payload) != REPORT_V3_VERSION:
        return supported_report_view(
            payload,
            consumer=f"atlas report reader ({report_path})",
        )
    sections = payload.get("sections")
    metadata = payload.get("metadata")
    projection = payload.get("projection")
    if not all(
        isinstance(value, dict)
        for value in (sections, metadata, projection)
    ):
        raise ValueError(f"malformed report v3 input: {report_path}")
    if projection.get("name") == "summary":
        raise ValueError(
            "atlas construction requires a Ladon report-v3 review or full "
            f"projection because summary omits graph rows: {report_path}"
        )
    return {
        "metadata": dict(metadata),
        "warnings": list(payload.get("warnings", [])),
        "projection": dict(projection),
        **{
            str(name): inflate_declaration_evidence(value)
            for name, value in sections.items()
        },
    }


def inflate_declaration_evidence(value: Any) -> Any:
    """Join report-v3 declaration evidence for existing atlas consumers."""

    if isinstance(value, list):
        return [inflate_declaration_evidence(row) for row in value]
    if not isinstance(value, dict):
        return value
    evidence = value.get("_declarationEvidence")
    declarations = value.get("declarations")
    inflated = {
        key: inflate_declaration_evidence(row)
        for key, row in value.items()
        if key != "_declarationEvidence"
    }
    if not isinstance(evidence, dict) or not isinstance(declarations, list):
        return inflated
    rows: list[Any] = []
    for declaration in declarations:
        if not isinstance(declaration, dict):
            rows.append(declaration)
            continue
        rows.append(_inflate_declaration_row(declaration, evidence))
    inflated["declarations"] = rows
    return inflated


def _inflate_declaration_row(
    declaration: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Apply one report-v3 path-indexed evidence entry to its declaration."""

    row = inflate_declaration_evidence(declaration)
    reference = declaration.get("evidenceRef")
    if not isinstance(reference, str):
        return row
    evidence_key = _pointer_token_value(reference.rsplit("/", maxsplit=1)[-1])
    attached = evidence.get(evidence_key)
    if not isinstance(attached, dict):
        return row
    fields = attached.get("fields")
    if not isinstance(fields, dict):
        return row
    for pointer, field_value in sorted(fields.items()):
        _set_pointer_value(
            row,
            str(pointer),
            inflate_declaration_evidence(field_value),
        )
    return row


def _set_pointer_value(target: Any, pointer: str, value: Any) -> None:
    """Set one RFC 6901-style path already present in a compact declaration."""

    if not pointer.startswith("/") or pointer == "/":
        raise ValueError(
            f"malformed declaration evidence pointer: {pointer!r}"
        )
    tokens = [_pointer_token_value(token) for token in pointer[1:].split("/")]
    owner = target
    for token in tokens[:-1]:
        owner = owner[int(token)] if isinstance(owner, list) else owner[token]
    final = tokens[-1]
    if isinstance(owner, list):
        owner[int(final)] = value
    else:
        owner[final] = value


def _pointer_token_value(token: str) -> str:
    """Decode one JSON pointer token."""

    return token.replace("~1", "/").replace("~0", "~")
