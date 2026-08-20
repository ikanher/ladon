"""Shared declaration-evidence compaction for report construction and projection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from ladon.report_contract import ReportModelError, copy_json

DECLARATION_EVIDENCE_KEYS = frozenset(
    {"authority", "confidence", "nonclaim", "nonclaims"}
)
_RESERVED_EVIDENCE_KEY = "_declarationEvidence"
_RESERVED_EVIDENCE_KEYS = frozenset({_RESERVED_EVIDENCE_KEY})
_COMPACT_ROW_FORBIDDEN_KEYS = DECLARATION_EVIDENCE_KEYS | _RESERVED_EVIDENCE_KEYS
_EVIDENCE_ID_PREFIX = "evidence:"
_EVIDENCE_DIGEST_LENGTH = 24


def compact_declaration_collections(value: Any, *, pointer: str) -> Any:
    """Move repeated declaration evidence into shared referenced dictionaries."""

    if isinstance(value, list):
        return _compact_declaration_list(value, pointer=pointer)
    if not isinstance(value, Mapping):
        return copy_json(value)
    return _compact_declaration_mapping(value, pointer=pointer)


def _compact_declaration_list(
    value: list[Any],
    *,
    pointer: str,
) -> list[Any]:
    """Recursively compact the children of one JSON array."""

    return [
        compact_declaration_collections(
            item,
            pointer=f"{pointer}/{index}",
        )
        for index, item in enumerate(value)
    ]


def _compact_declaration_mapping(
    value: Mapping[str, Any],
    *,
    pointer: str,
) -> dict[str, Any]:
    """Compact one mapping, preserving an existing evidence dictionary."""

    if _RESERVED_EVIDENCE_KEY in value:
        _require_canonical_compact_container(value, pointer=pointer)
        return _copy_canonical_compact_container(value, pointer=pointer)
    return _compact_raw_declaration_mapping(value, pointer=pointer)


def _copy_canonical_compact_container(
    value: Mapping[str, Any],
    *,
    pointer: str,
) -> dict[str, Any]:
    """Copy a compact container without reinterpreting its evidence table."""

    return {
        key: (
            copy_json(item)
            if key == _RESERVED_EVIDENCE_KEY
            else compact_declaration_collections(
                item,
                pointer=f"{pointer}/{pointer_token(key)}",
            )
        )
        for key, item in sorted(value.items())
    }


def _compact_raw_declaration_mapping(
    value: Mapping[str, Any],
    *,
    pointer: str,
) -> dict[str, Any]:
    """Compact declaration collections nested directly in one raw mapping."""

    compacted: dict[str, Any] = {}
    for key in sorted(value):
        item = value[key]
        child_pointer = f"{pointer}/{pointer_token(key)}"
        if key == "declarations" and is_mapping_list(item):
            _store_compacted_declarations(
                compacted,
                source=value,
                rows=item,
                evidence_pointer=f"{pointer}/_declarationEvidence",
            )
            continue
        compacted[key] = compact_declaration_collections(
            item,
            pointer=child_pointer,
        )
    return compacted


def _store_compacted_declarations(
    compacted: dict[str, Any],
    *,
    source: Mapping[str, Any],
    rows: list[Any],
    evidence_pointer: str,
) -> None:
    """Store compacted rows and their optional shared evidence dictionary."""

    compacted_rows, evidence = compact_declaration_rows(
        rows,
        evidence_pointer=evidence_pointer,
    )
    compacted["declarations"] = compacted_rows
    if not evidence:
        return
    if _RESERVED_EVIDENCE_KEY in source:
        raise ReportModelError("source payload uses reserved _declarationEvidence key")
    compacted[_RESERVED_EVIDENCE_KEY] = evidence


def compact_declaration_rows(
    rows: list[Any],
    *,
    evidence_pointer: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Strip repeated evidence keys from rows and deduplicate their dictionaries."""

    compacted_rows: list[dict[str, Any]] = []
    evidence_table: dict[str, Any] = {}
    for raw_row in rows:
        row, fields = _strip_declaration_evidence(raw_row)
        if fields:
            evidence_id = f"evidence:{_json_digest(fields)}"
            evidence_table.setdefault(evidence_id, {"fields": fields})
            row["evidenceRef"] = f"{evidence_pointer}/{pointer_token(evidence_id)}"
        compacted_rows.append(row)
    return compacted_rows, {key: evidence_table[key] for key in sorted(evidence_table)}


def is_compact_declaration_container(value: Mapping[str, Any]) -> bool:
    """Return whether declaration rows form a canonical compact container."""

    return _is_canonical_compact_container(
        value,
        pointer=None,
    )


def is_raw_declaration_container(value: Mapping[str, Any]) -> bool:
    """Return whether a mapping owns uncompressed declaration rows."""

    return _RESERVED_EVIDENCE_KEY not in value and is_mapping_list(
        value.get("declarations")
    )


def pointer_token(value: str) -> str:
    """Escape one RFC 6901 JSON Pointer token."""

    return value.replace("~", "~0").replace("/", "~1")


def is_mapping_list(value: Any) -> bool:
    """Return whether a value is a declaration-row-shaped list."""

    return isinstance(value, list) and all(isinstance(row, Mapping) for row in value)


def _strip_declaration_evidence(
    row: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return one compact row and a path-indexed evidence dictionary."""

    if _contains_any_key(row, _RESERVED_EVIDENCE_KEYS):
        raise ReportModelError("source payload uses reserved _declarationEvidence key")
    fields: dict[str, Any] = {}

    def visit(value: Any, path: str) -> Any:
        if isinstance(value, list):
            return [visit(item, f"{path}/{index}") for index, item in enumerate(value)]
        if not isinstance(value, Mapping):
            return copy_json(value)
        result: dict[str, Any] = {}
        for key in sorted(value):
            item = value[key]
            item_path = f"{path}/{pointer_token(key)}"
            if key in DECLARATION_EVIDENCE_KEYS:
                fields[item_path] = copy_json(item)
            else:
                result[key] = visit(item, item_path)
        return result

    return visit(row, ""), fields


def _require_canonical_compact_container(
    value: Mapping[str, Any],
    *,
    pointer: str,
) -> None:
    """Reject reserved evidence dictionaries outside their canonical shape."""

    if _is_canonical_compact_container(value, pointer=pointer):
        return
    raise ReportModelError(
        "source payload uses reserved _declarationEvidence key "
        "outside a canonical declaration container"
    )


def _is_canonical_compact_container(
    value: Mapping[str, Any],
    *,
    pointer: str | None,
) -> bool:
    """Validate compact rows, evidence entries, and their local references."""

    rows = value.get("declarations")
    evidence = value.get(_RESERVED_EVIDENCE_KEY)
    if not is_mapping_list(rows) or not isinstance(evidence, Mapping):
        return False
    if not _is_canonical_evidence_table(evidence):
        return False
    if any(_contains_any_key(row, _COMPACT_ROW_FORBIDDEN_KEYS) for row in rows):
        return False
    references = _canonical_evidence_references(
        rows,
        evidence=evidence,
        pointer=pointer,
    )
    return references is not None and references == set(evidence)


def _is_canonical_evidence_table(value: Mapping[Any, Any]) -> bool:
    """Return whether every compact evidence entry has canonical structure."""

    return all(
        _is_canonical_evidence_entry(evidence_id, entry)
        for evidence_id, entry in value.items()
    )


def _is_canonical_evidence_entry(evidence_id: Any, entry: Any) -> bool:
    """Return whether one evidence-table entry has canonical fields."""

    if not _is_canonical_evidence_id(evidence_id):
        return False
    if not isinstance(entry, Mapping) or set(entry) != {"fields"}:
        return False
    fields = entry["fields"]
    return (
        isinstance(fields, Mapping)
        and bool(fields)
        and all(_is_canonical_evidence_path(path) for path in fields)
    )


def _is_canonical_evidence_id(value: Any) -> bool:
    """Return whether a value is one generated declaration-evidence ID."""

    if not isinstance(value, str) or not value.startswith(_EVIDENCE_ID_PREFIX):
        return False
    digest = value.removeprefix(_EVIDENCE_ID_PREFIX)
    return len(digest) == _EVIDENCE_DIGEST_LENGTH and all(
        character in "0123456789abcdef" for character in digest
    )


def _is_canonical_evidence_path(value: Any) -> bool:
    """Return whether a field path terminates at a stripped evidence key."""

    if not isinstance(value, str) or not value.startswith("/"):
        return False
    token = value.rsplit("/", maxsplit=1)[-1]
    decoded = _decode_pointer_token(token)
    return pointer_token(decoded) == token and decoded in DECLARATION_EVIDENCE_KEYS


def _canonical_evidence_references(
    rows: list[Any],
    *,
    evidence: Mapping[Any, Any],
    pointer: str | None,
) -> set[str] | None:
    """Return resolved evidence IDs, or ``None`` for any invalid reference."""

    references: set[str] = set()
    for row in rows:
        reference = row.get("evidenceRef")
        if reference is None:
            continue
        evidence_id = _evidence_id_from_reference(
            reference,
            pointer=pointer,
        )
        if evidence_id is None or evidence_id not in evidence:
            return None
        references.add(evidence_id)
    return references


def _evidence_id_from_reference(
    value: Any,
    *,
    pointer: str | None,
) -> str | None:
    """Resolve one canonical local evidence reference to its table key."""

    if not isinstance(value, str):
        return None
    parent, separator, token = value.rpartition("/")
    if not separator:
        return None
    expected_parent = f"{pointer}/{_RESERVED_EVIDENCE_KEY}"
    if pointer is None:
        if not parent.endswith(f"/{_RESERVED_EVIDENCE_KEY}"):
            return None
    elif parent != expected_parent:
        return None
    decoded = _decode_pointer_token(token)
    return decoded if pointer_token(decoded) == token else None


def _contains_any_key(value: Any, keys: frozenset[str]) -> bool:
    """Return whether a nested JSON value contains any reserved key."""

    if isinstance(value, list):
        return any(_contains_any_key(item, keys) for item in value)
    if not isinstance(value, Mapping):
        return False
    if any(key in value for key in keys):
        return True
    return any(_contains_any_key(item, keys) for item in value.values())


def _decode_pointer_token(value: str) -> str:
    """Decode one RFC 6901 JSON Pointer token."""

    return value.replace("~1", "/").replace("~0", "~")


def _json_digest(value: Any) -> str:
    """Return the compact digest suffix used by declaration evidence IDs."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


__all__ = [
    "compact_declaration_collections",
    "compact_declaration_rows",
    "is_compact_declaration_container",
    "is_raw_declaration_container",
]
