"""Typed finding evidence construction and local-reference validation."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class DanglingFindingEvidenceError(ValueError):
    """A finding evidence reference does not resolve in its owning report."""


def finding_evidence_refs(
    row: Mapping[str, Any],
    module_metadata: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return exact owner-supplied or source evidence without vague fallbacks."""

    explicit = explicit_evidence_refs(row)
    sources = source_evidence_refs(
        row,
        {} if explicit else module_metadata,
    )
    resolved = deduplicate_evidence_refs([*explicit, *sources])
    if resolved:
        return resolved
    return [
        {
            "type": "unavailable",
            "reason": (
                "the owning analysis supplied no exact canonical-row, "
                "aggregate-value, external-artifact, or source identity"
            ),
        }
    ]


def deduplicate_evidence_refs(
    references: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate typed evidence rows without discarding nested metadata."""

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reference in references:
        row = dict(reference)
        identity = json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if identity not in seen:
            seen.add(identity)
            selected.append(row)
    return selected


def explicit_evidence_refs(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Copy typed evidence references already resolved by the owning analysis."""

    raw = row.get("evidenceRefs", [])
    if not isinstance(raw, list):
        return []
    return [
        dict(reference)
        for reference in raw
        if isinstance(reference, Mapping)
    ]


def source_evidence_refs(
    row: Mapping[str, Any],
    module_metadata: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return every truthful source location carried by one finding."""

    path_sites = row.get("pathImportSites")
    if isinstance(path_sites, list):
        references = [
            source_reference(site, row)
            for site in path_sites
            if isinstance(site, Mapping)
        ]
        selected = [
            reference for reference in references if reference is not None
        ]
        if selected:
            return selected
    direct = source_evidence_ref(row, module_metadata)
    return [direct] if direct is not None else []


def source_evidence_ref(
    row: Mapping[str, Any],
    module_metadata: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Resolve direct path evidence from the finding or its module subject."""

    direct = source_reference(row, row)
    if direct is not None:
        return direct
    subject = str(row.get("subject", ""))
    module_row = module_metadata.get(subject)
    return (
        source_reference(module_row, row)
        if isinstance(module_row, Mapping)
        else None
    )


def source_reference(
    location: Mapping[str, Any],
    finding: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Normalize one source reference while preserving supplied metadata."""

    path = (
        location.get("sourcePath")
        or location.get("repositoryPath")
        or location.get("path")
    )
    if not isinstance(path, str) or not path:
        return None
    reference: dict[str, Any] = {
        "type": "source",
        "path": path,
        "authority": str(
            location.get("sourceAuthority")
            or location.get("authority")
            or finding.get("authority")
            or "lexical_text"
        ),
    }
    source_range = location.get("sourceRange") or location.get("range")
    if isinstance(source_range, Mapping):
        reference["range"] = dict(source_range)
    else:
        add_line_range(reference, location)
    copy_source_metadata(reference, location, finding)
    return reference


def canonical_row_evidence(
    section: str,
    collection: str,
    index: int,
    *,
    identity: Mapping[str, Any],
    authority: str,
) -> dict[str, Any]:
    """Reference one exact indexed row in a canonical full report section."""

    return {
        "type": "canonical-row",
        "section": section,
        "collection": collection,
        "index": index,
        "pointer": (
            f"#/sections/{json_pointer_token(section)}/"
            f"{json_pointer_token(collection)}/{index}"
        ),
        "identity": {
            key: value
            for key, value in identity.items()
            if value is not None and value != ""
        },
        "authority": authority,
    }


def aggregate_value_evidence(
    section: str,
    field: str,
    *,
    authority: str,
) -> dict[str, Any]:
    """Reference one exact scalar aggregate in a canonical full report."""

    return {
        "type": "aggregate",
        "section": section,
        "field": field,
        "pointer": (
            f"#/sections/{json_pointer_token(section)}/"
            f"{json_pointer_token(field)}"
        ),
        "authority": authority,
    }


def json_pointer_token(value: str) -> str:
    """Escape one RFC 6901 JSON-pointer token."""

    return value.replace("~", "~0").replace("/", "~1")


def add_line_range(
    reference: dict[str, Any],
    location: Mapping[str, Any],
) -> None:
    """Add a flat source range only when the owner supplied a source line."""

    line = location.get("line")
    if not isinstance(line, int) or line <= 0:
        return
    end_line = location.get("endLine")
    source_range: dict[str, Any] = {
        "startLine": line,
        "endLine": (
            end_line
            if isinstance(end_line, int) and end_line >= line
            else line
        ),
    }
    column = location.get("column")
    if isinstance(column, int) and column >= 0:
        source_range["startColumn"] = column
    end_column = location.get("endColumn")
    if isinstance(end_column, int) and end_column >= 0:
        source_range["endColumn"] = end_column
    reference["range"] = source_range


def copy_source_metadata(
    reference: dict[str, Any],
    location: Mapping[str, Any],
    finding: Mapping[str, Any],
) -> None:
    """Retain optional hash, confidence, selection, and location evidence."""

    for target, keys in (
        (
            "contentHash",
            ("sourceContentHash", "contentHash", "sourceHash"),
        ),
        (
            "confidence",
            ("sourceConfidence", "confidence", "confidenceLabel"),
        ),
    ):
        value = first_source_string(location, finding, keys)
        if value is not None:
            reference[target] = value
    for source_key, target_key in (
        ("selectionRange", "selectionRange"),
        ("sourceLocation", "location"),
        ("location", "location"),
    ):
        value = location.get(source_key)
        if isinstance(value, Mapping):
            reference[target_key] = dict(value)


def first_source_string(
    location: Mapping[str, Any],
    finding: Mapping[str, Any],
    keys: Sequence[str],
) -> str | None:
    """Return the first non-empty source metadata string from either owner."""

    for source in (location, finding):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def validate_finding_evidence(
    payload: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> None:
    """Reject malformed or dangling evidence before projecting a finding view."""

    for index, finding in enumerate(findings):
        references = finding.get("evidenceRefs")
        identity = str(finding.get("id") or f"row {index}")
        if not isinstance(references, list) or not references:
            raise DanglingFindingEvidenceError(
                f"finding {identity} has no typed evidence reference"
            )
        validate_evidence_rows(payload, references, identity)


def validate_evidence_rows(
    payload: Mapping[str, Any],
    references: Sequence[Any],
    finding_identity: str,
) -> None:
    """Validate the ordered evidence rows belonging to one finding."""

    for reference_index, reference in enumerate(references):
        if not isinstance(reference, Mapping):
            raise DanglingFindingEvidenceError(
                f"finding {finding_identity} evidence "
                f"{reference_index} is not an object"
            )
        validate_evidence_reference(
            payload,
            reference,
            finding_identity=finding_identity,
            reference_index=reference_index,
        )


def validate_evidence_reference(
    payload: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    finding_identity: str,
    reference_index: int,
) -> None:
    """Validate one supported evidence type and any local JSON pointer."""

    evidence_type = reference.get("type")
    location = f"finding {finding_identity} evidence {reference_index}"
    required_field = {
        "source": "path",
        "unavailable": "reason",
    }.get(str(evidence_type))
    if required_field is not None:
        require_nonempty_evidence_string(reference, required_field, location)
        return
    if evidence_type in {"external", "external-artifact"}:
        validate_external_reference(reference, location)
        return
    if evidence_type in {"canonical-row", "aggregate"}:
        validate_local_reference(payload, reference, location)
        return
    raise DanglingFindingEvidenceError(
        f"{location} has unsupported type {evidence_type!r}"
    )


def validate_external_reference(
    reference: Mapping[str, Any],
    location: str,
) -> None:
    """Require a quoted external artifact to carry a stable name."""

    named = any(
        isinstance(reference.get(field), str) and reference[field]
        for field in ("artifact", "name", "path", "uri")
    )
    if not named:
        raise DanglingFindingEvidenceError(
            f"{location} does not name its external artifact"
        )


def validate_local_reference(
    payload: Mapping[str, Any],
    reference: Mapping[str, Any],
    location: str,
) -> None:
    """Resolve one local pointer and check canonical-row identity."""

    pointer = require_nonempty_evidence_string(reference, "pointer", location)
    try:
        target = resolve_local_json_pointer(payload, pointer)
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise DanglingFindingEvidenceError(
            f"{location} has dangling pointer {pointer!r}"
        ) from exc
    if reference.get("type") == "canonical-row":
        validate_canonical_identity(reference, target, location)


def validate_canonical_identity(
    reference: Mapping[str, Any],
    target: Any,
    location: str,
) -> None:
    """Require a canonical-row pointer to resolve to its quoted identity."""

    if not isinstance(target, Mapping):
        raise DanglingFindingEvidenceError(
            f"{location} canonical-row pointer does not resolve to an object"
        )
    expected = reference.get("identity", {})
    if not isinstance(expected, Mapping):
        raise DanglingFindingEvidenceError(
            f"{location} canonical-row identity is not an object"
        )
    mismatches = [
        key for key, value in expected.items() if target.get(key) != value
    ]
    if mismatches:
        raise DanglingFindingEvidenceError(
            f"{location} canonical-row identity mismatch at "
            + ", ".join(str(key) for key in mismatches)
        )


def require_nonempty_evidence_string(
    reference: Mapping[str, Any],
    field: str,
    location: str,
) -> str:
    """Return one required evidence string or raise a contextual diagnostic."""

    value = reference.get(field)
    if not isinstance(value, str) or not value:
        raise DanglingFindingEvidenceError(
            f"{location} requires a non-empty {field}"
        )
    return value


def resolve_local_json_pointer(payload: Any, pointer: str) -> Any:
    """Resolve a local RFC 6901 pointer without accepting URI references."""

    if pointer == "#":
        return payload
    if not pointer.startswith("#/"):
        raise ValueError("evidence pointer is not a local JSON pointer")
    value = payload
    for raw_token in pointer[2:].split("/"):
        value = resolve_pointer_token(value, decode_json_pointer_token(raw_token))
    return value


def resolve_pointer_token(value: Any, token: str) -> Any:
    """Resolve one decoded pointer token against an object or array."""

    if isinstance(value, Mapping):
        return value[token]
    if isinstance(value, list):
        if not token.isdigit() or (token.startswith("0") and token != "0"):
            raise ValueError("invalid JSON array index")
        return value[int(token)]
    raise TypeError("JSON pointer traverses a scalar")


def decode_json_pointer_token(token: str) -> str:
    """Decode one RFC 6901 token while rejecting malformed escape sequences."""

    decoded: list[str] = []
    index = 0
    while index < len(token):
        if token[index] != "~":
            decoded.append(token[index])
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
            raise ValueError("invalid JSON pointer escape")
        decoded.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(decoded)
