"""Typed source-index state and deterministic cache payload codec."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ladon.ir import (
    LeanImport,
    LeanLexicalMarker,
    LeanModule,
    LeanTextDeclaration,
)


SOURCE_INDEX_SCHEMA = "ladon-source-index-v1"
SOURCE_INDEX_FINGERPRINT_VERSION = "ladon-source-index-fingerprint-v1"
CACHE_OUTCOMES = frozenset({"hit", "miss", "bypass", "invalidation"})
INDEX_STATUSES = frozenset({"complete", "partial"})
SOURCE_FAILURE_DIAGNOSTIC = "source_index.source_failed"


class SourceIndexError(ValueError):
    """Raised when a sound source index cannot be constructed."""


@dataclass(frozen=True)
class SourceIndexEntry:
    """One content-addressed module record in the source index."""

    module: LeanModule
    content_sha256: str
    source_bytes: int

    @property
    def name(self) -> str:
        """Return the normalized Lean module name."""

        return self.module.name

    @property
    def path(self) -> str:
        """Return the repository-relative source path."""

        return self.module.path

    def to_payload(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""

        return {
            "module": _module_payload(self.module),
            "contentSha256": self.content_sha256,
            "sourceBytes": self.source_bytes,
        }


@dataclass(frozen=True)
class SourceIndex:
    """One deterministic lexical inventory and its validity manifest."""

    repo_root: Path
    fingerprint: str
    fingerprint_manifest: Mapping[str, Any]
    layout_status: str
    source_roots: tuple[Mapping[str, Any], ...]
    entries: tuple[SourceIndexEntry, ...]
    options: Mapping[str, Any]
    index_status: str = "complete"
    diagnostics: tuple[Mapping[str, Any], ...] = ()
    schema: str = SOURCE_INDEX_SCHEMA

    def __post_init__(self) -> None:
        if self.index_status not in INDEX_STATUSES:
            raise SourceIndexError(
                f"unsupported source-index status {self.index_status!r}"
            )
        _validate_index_population(self)

    @property
    def modules(self) -> dict[str, LeanModule]:
        """Return modules ordered by normalized module identity."""

        return {entry.name: entry.module for entry in self.entries}

    @property
    def paths(self) -> dict[str, str]:
        """Return the module-to-repository-relative-path mapping."""

        return {entry.name: entry.path for entry in self.entries}

    @property
    def phase_status(self) -> str:
        """Return the discover-phase completion state for pipeline callers."""

        return self.index_status

    @property
    def discovery_status(self) -> str:
        """Return a backend discovery status that exposes partial indexing."""

        return "partial" if self.index_status == "partial" else self.layout_status

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic cache/report-neutral payload."""

        return {
            "schema": self.schema,
            "indexStatus": self.index_status,
            "fingerprint": self.fingerprint,
            "fingerprintManifest": dict(self.fingerprint_manifest),
            "layout": {
                "status": self.layout_status,
                "indexStatus": self.index_status,
                "sourceRoots": [dict(row) for row in self.source_roots],
            },
            "options": dict(self.options),
            "entries": [entry.to_payload() for entry in self.entries],
            "diagnostics": [dict(row) for row in self.diagnostics],
        }

    @classmethod
    def from_payload(
        cls,
        repo_root: Path,
        payload: Mapping[str, Any],
        *,
        expected_fingerprint: str,
    ) -> SourceIndex:
        """Decode one cache payload only when its identity is exact."""

        _validate_payload_header(payload, expected_fingerprint)
        raw_layout = _required_mapping(
            payload.get("layout"),
            "source-index cache layout is malformed",
        )
        raw_manifest = _required_mapping(
            payload.get("fingerprintManifest"),
            "source-index cache manifest is malformed",
        )
        return cls(
            repo_root=repo_root,
            fingerprint=expected_fingerprint,
            fingerprint_manifest=dict(raw_manifest),
            layout_status=str(raw_layout.get("status", "unknown")),
            source_roots=_mapping_tuple(
                raw_layout.get("sourceRoots", []),
                "source-index cache roots are malformed",
            ),
            entries=_decoded_entries(payload.get("entries")),
            options=dict(
                _required_mapping(
                    payload.get("options", {}),
                    "source-index cache options are malformed",
                )
            ),
            index_status=_decoded_index_status(payload, raw_layout),
            diagnostics=_mapping_tuple(
                payload.get("diagnostics", []),
                "source-index cache diagnostics are malformed",
            ),
        )


@dataclass(frozen=True)
class SourceIndexCacheOutcome:
    """Inspectible result of one source-index cache decision."""

    status: str
    reason: str
    fingerprint_version: str
    fingerprint: str
    cache_path: Path | None
    committed: bool = False
    reused_entries: int = 0
    rebuilt_entries: int = 0
    failed_entries: int = 0

    def __post_init__(self) -> None:
        if self.status not in CACHE_OUTCOMES:
            raise ValueError(
                f"unsupported source-index cache outcome {self.status!r}"
            )
        _validate_cache_counters(self)


@dataclass(frozen=True)
class SourceIndexResult:
    """A source index paired with the cache decision that produced it."""

    index: SourceIndex
    cache: SourceIndexCacheOutcome

    @property
    def phase_status(self) -> str:
        """Expose the state a discover-phase owner should publish."""

        return self.index.phase_status


def _validate_cache_counters(outcome: SourceIndexCacheOutcome) -> None:
    counters = (
        outcome.reused_entries,
        outcome.rebuilt_entries,
        outcome.failed_entries,
    )
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for value in counters
    ):
        raise ValueError(
            "source-index cache counters must be non-negative integers"
        )


def _validate_payload_header(
    payload: Mapping[str, Any],
    expected_fingerprint: str,
) -> None:
    if payload.get("schema") != SOURCE_INDEX_SCHEMA:
        raise SourceIndexError("source-index cache schema is unsupported")
    if payload.get("fingerprint") != expected_fingerprint:
        raise SourceIndexError("source-index cache fingerprint does not match")


def _decoded_index_status(
    payload: Mapping[str, Any],
    layout: Mapping[str, Any],
) -> str:
    direct = payload.get("indexStatus")
    nested = layout.get("indexStatus")
    if direct is not None and nested is not None and direct != nested:
        raise SourceIndexError("source-index status fields disagree")
    status = direct if direct is not None else nested
    return str(status) if status is not None else "complete"


def _validate_index_population(index: SourceIndex) -> None:
    states = _manifest_source_states(index.fingerprint_manifest)
    entries = _index_entry_map(index.entries)
    _validate_entry_population(entries, states)
    _validate_index_completeness(index, entries, states)


def _index_entry_map(
    entries: tuple[SourceIndexEntry, ...],
) -> dict[str, SourceIndexEntry]:
    result = {entry.name: entry for entry in entries}
    if len(result) != len(entries):
        raise SourceIndexError("source index contains duplicate modules")
    return result


def _validate_entry_population(
    entries: Mapping[str, SourceIndexEntry],
    states: Mapping[str, Mapping[str, Any]],
) -> None:
    if not set(entries).issubset(states):
        raise SourceIndexError("source index contains modules outside its manifest")
    for name, entry in entries.items():
        _validate_entry_identity(name, entry, states[name])


def _validate_entry_identity(
    name: str,
    entry: SourceIndexEntry,
    state: Mapping[str, Any],
) -> None:
    identity = (entry.path, entry.source_bytes, entry.content_sha256)
    expected = (
        state.get("path"),
        state.get("bytes"),
        state.get("sha256"),
    )
    if identity != expected:
        raise SourceIndexError(
            f"source-index entry identity does not match manifest for {name}"
        )


def _validate_index_completeness(
    index: SourceIndex,
    entries: Mapping[str, SourceIndexEntry],
    states: Mapping[str, Mapping[str, Any]],
) -> None:
    missing = set(states) - set(entries)
    failed = _failed_modules(index.diagnostics)
    if index.index_status == "complete" and (missing or failed):
        raise SourceIndexError(
            "complete source index does not cover its full manifest"
        )
    if index.index_status == "partial" and (not missing or failed != missing):
        raise SourceIndexError(
            "partial source index failures do not match missing modules"
        )


def _failed_modules(
    diagnostics: tuple[Mapping[str, Any], ...],
) -> set[str]:
    return {
        str(row.get("module"))
        for row in diagnostics
        if row.get("id") == SOURCE_FAILURE_DIAGNOSTIC
    }


def _manifest_source_states(
    manifest: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    raw = manifest.get("sources")
    if not isinstance(raw, list):
        raise SourceIndexError("source-index manifest sources are malformed")
    states: dict[str, Mapping[str, Any]] = {}
    for row in raw:
        _add_manifest_source(states, row)
    return states


def _add_manifest_source(
    states: dict[str, Mapping[str, Any]],
    row: Any,
) -> None:
    if not isinstance(row, Mapping) or not isinstance(row.get("module"), str):
        raise SourceIndexError("source-index manifest source is malformed")
    name = str(row["module"])
    if name in states:
        raise SourceIndexError("source-index manifest has duplicate modules")
    states[name] = row


def _module_payload(module: LeanModule) -> dict[str, Any]:
    evidence_names = tuple(row.name for row in module.declaration_evidence)
    return {
        "name": module.name,
        "path": module.path,
        "imports": list(module.imports),
        "importSites": [
            {"module": row.module, "line": row.line, "text": row.text}
            for row in module.import_sites
        ],
        "lineCount": module.line_count,
        "tags": list(module.tags),
        "lexicalMarkers": [
            {"kind": row.kind, "line": row.line, "text": row.text}
            for row in module.lexical_markers
        ],
        "declarations": (
            []
            if evidence_names == module.declarations
            else list(module.declarations)
        ),
        "declarationEvidence": [
            _compact_declaration_evidence(row)
            for row in module.declaration_evidence
        ],
    }


def _compact_declaration_evidence(row: LeanTextDeclaration) -> list[Any]:
    """Encode common lexical rows without repeated field names/default prose."""

    values: list[Any] = [
        row.name,
        row.kind,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
    ]
    defaults = LeanTextDeclaration.__dataclass_fields__
    optional = (row.authority, row.confidence, row.nonclaim)
    default_values = (
        defaults["authority"].default,
        defaults["confidence"].default,
        defaults["nonclaim"].default,
    )
    if optional != default_values:
        values.extend(optional)
    return values


def _entry_from_payload(raw: Any) -> SourceIndexEntry:
    if not isinstance(raw, Mapping):
        raise SourceIndexError("source-index entry is not an object")
    module = _module_from_payload(raw.get("module"))
    digest = raw.get("contentSha256")
    source_bytes = raw.get("sourceBytes")
    if not isinstance(digest, str) or len(digest) != 64:
        raise SourceIndexError(
            f"source-index digest is malformed for {module.name}"
        )
    if not isinstance(source_bytes, int) or source_bytes < 0:
        raise SourceIndexError(
            f"source-index byte count is malformed for {module.name}"
        )
    return SourceIndexEntry(module, digest, source_bytes)


def _decoded_entries(raw: Any) -> tuple[SourceIndexEntry, ...]:
    if not isinstance(raw, list):
        raise SourceIndexError("source-index cache entries are malformed")
    entries = tuple(
        sorted(
            (_entry_from_payload(row) for row in raw),
            key=lambda row: row.name,
        )
    )
    if len({entry.name for entry in entries}) != len(entries):
        raise SourceIndexError("source-index cache contains duplicate modules")
    return entries


def _module_from_payload(raw: Any) -> LeanModule:
    row = _required_mapping(raw, "source-index module is not an object")
    name = _required_string(row, "name")
    path = _required_string(row, "path")
    evidence = _decoded_declaration_evidence(row)
    declarations = _decoded_declaration_names(row, evidence)
    return LeanModule(
        name=name,
        path=path,
        imports=_string_tuple(row.get("imports", [])),
        import_sites=_decoded_imports(row.get("importSites", [])),
        line_count=_nonnegative_int(row.get("lineCount", 0), "lineCount"),
        tags=_string_tuple(row.get("tags", [])),
        lexical_markers=_decoded_markers(row.get("lexicalMarkers", [])),
        declarations=declarations,
        declaration_evidence=evidence,
    )


def _decoded_declaration_evidence(
    raw: Mapping[str, Any],
) -> tuple[LeanTextDeclaration, ...]:
    return tuple(
        _declaration_evidence_from_payload(row)
        for row in _sequence_list(raw.get("declarationEvidence", []))
    )


def _decoded_declaration_names(
    raw: Mapping[str, Any],
    evidence: tuple[LeanTextDeclaration, ...],
) -> tuple[str, ...]:
    declarations = _string_tuple(raw.get("declarations", []))
    return declarations or tuple(row.name for row in evidence)


def _decoded_imports(raw: Any) -> tuple[LeanImport, ...]:
    return tuple(
        LeanImport(
            module=str(row["module"]),
            line=row.get("line") if isinstance(row.get("line"), int) else None,
            text=row.get("text") if isinstance(row.get("text"), str) else None,
        )
        for row in _mapping_list(raw)
        if isinstance(row.get("module"), str)
    )


def _decoded_markers(raw: Any) -> tuple[LeanLexicalMarker, ...]:
    return tuple(
        LeanLexicalMarker(
            kind=_required_string(row, "kind"),
            line=_nonnegative_int(row.get("line"), "marker line"),
            text=_required_string(row, "text"),
        )
        for row in _mapping_list(raw)
    )


def _declaration_evidence_from_payload(raw: Any) -> LeanTextDeclaration:
    """Decode compact v2 rows and the original mapping representation."""

    if isinstance(raw, list):
        return _compact_evidence_from_payload(raw)
    row = _required_mapping(raw, "declaration evidence is malformed")
    return LeanTextDeclaration(
        name=_required_string(row, "name"),
        kind=_required_string(row, "kind"),
        line=_nonnegative_int(row.get("line"), "declaration line"),
        column=_nonnegative_int(row.get("column"), "declaration column"),
        start_offset=_nonnegative_int(
            row.get("startOffset"),
            "declaration start",
        ),
        end_offset=_nonnegative_int(row.get("endOffset"), "declaration end"),
        authority=str(row.get("authority", "lexical_text")),
        confidence=str(row.get("confidence", "bounded_lexical_scan")),
        nonclaim=str(
            row.get(
                "nonclaim",
                LeanTextDeclaration.__dataclass_fields__["nonclaim"].default,
            )
        ),
    )


def _compact_evidence_from_payload(raw: list[Any]) -> LeanTextDeclaration:
    if len(raw) not in {6, 9}:
        raise SourceIndexError("compact declaration evidence is malformed")
    defaults = LeanTextDeclaration.__dataclass_fields__
    extended = len(raw) == 9
    return LeanTextDeclaration(
        name=_sequence_string(raw, 0, "declaration name"),
        kind=_sequence_string(raw, 1, "declaration kind"),
        line=_nonnegative_int(raw[2], "declaration line"),
        column=_nonnegative_int(raw[3], "declaration column"),
        start_offset=_nonnegative_int(raw[4], "declaration start"),
        end_offset=_nonnegative_int(raw[5], "declaration end"),
        authority=_optional_evidence_text(
            raw,
            6,
            "declaration authority",
            defaults["authority"].default,
            extended,
        ),
        confidence=_optional_evidence_text(
            raw,
            7,
            "declaration confidence",
            defaults["confidence"].default,
            extended,
        ),
        nonclaim=_optional_evidence_text(
            raw,
            8,
            "declaration nonclaim",
            defaults["nonclaim"].default,
            extended,
        ),
    )


def _optional_evidence_text(
    raw: list[Any],
    index: int,
    label: str,
    default: Any,
    extended: bool,
) -> str:
    return _sequence_string(raw, index, label) if extended else str(default)


def _required_mapping(raw: Any, message: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise SourceIndexError(message)
    return raw


def _mapping_tuple(
    raw: Any,
    message: str,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, list) or not all(
        isinstance(row, Mapping) for row in raw
    ):
        raise SourceIndexError(message)
    return tuple(dict(row) for row in raw)


def _mapping_list(raw: Any) -> list[Mapping[str, Any]]:
    if not isinstance(raw, list) or not all(
        isinstance(row, Mapping) for row in raw
    ):
        raise SourceIndexError("source-index collection is malformed")
    return list(raw)


def _sequence_list(raw: Any) -> list[Any]:
    if not isinstance(raw, list):
        raise SourceIndexError("source-index sequence is malformed")
    return raw


def _sequence_string(raw: list[Any], index: int, label: str) -> str:
    value = raw[index]
    if not isinstance(value, str):
        raise SourceIndexError(f"source-index {label} is malformed")
    return value


def _string_tuple(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(row, str) for row in raw):
        raise SourceIndexError("source-index string collection is malformed")
    return tuple(raw)


def _required_string(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise SourceIndexError(f"source-index {key} is malformed")
    return value


def _nonnegative_int(raw: Any, label: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise SourceIndexError(f"source-index {label} is malformed")
    return raw


__all__ = [
    "CACHE_OUTCOMES",
    "INDEX_STATUSES",
    "SOURCE_FAILURE_DIAGNOSTIC",
    "SOURCE_INDEX_FINGERPRINT_VERSION",
    "SOURCE_INDEX_SCHEMA",
    "SourceIndex",
    "SourceIndexCacheOutcome",
    "SourceIndexEntry",
    "SourceIndexError",
    "SourceIndexResult",
]
