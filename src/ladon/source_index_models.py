"""Typed source-index state and deterministic cache payload codec."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    CoverageRegistry,
)
from ladon.ir import (
    LeanImport,
    LeanLexicalMarker,
    LeanModule,
    LeanTextDeclaration,
)
from ladon.lexical_command_skeleton import (
    command_skeleton_evidence_complete,
)
from ladon.source_index_audit import (
    SOURCE_INDEX_AUDITS_COVERAGE,
    audit_command_coverage,
    audit_commands_complete_field,
    validate_audit_command_rows,
)
from ladon.source_index_errors import SourceIndexError
from ladon.source_index_navigation_codec import (
    decode_audit_commands,
    decode_command_skeletons,
    decode_context_commands,
    decode_mechanisms,
    decode_options,
    decode_resources,
    decode_scope_contexts,
    module_navigation_payload,
    source_index_collection_mapping,
)

SOURCE_INDEX_SCHEMA = "ladon-source-index-v3"
SOURCE_INDEX_FINGERPRINT_VERSION = (
    "ladon-source-index-audit-command-source-shape-v2-fingerprint-v4"
)
CACHE_OUTCOMES = frozenset({"hit", "miss", "bypass", "invalidation"})
INDEX_STATUSES = frozenset({"complete", "partial"})
SOURCE_FAILURE_DIAGNOSTIC = "source_index.source_failed"
SOURCE_INDEX_COVERAGE_POINTER = "#/entries"
SOURCE_INDEX_MODULES_COVERAGE = "source_index.modules"
SOURCE_INDEX_IMPORTS_COVERAGE = "source_index.imports"
SOURCE_INDEX_DECLARATIONS_COVERAGE = "source_index.declarations"
SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE = "source_index.scope_contexts"
SOURCE_INDEX_OPTIONS_COVERAGE = "source_index.options"
SOURCE_INDEX_RESOURCES_COVERAGE = "source_index.resources"
SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE = "source_index.proof_mechanisms"
SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE = "source_index.command_skeletons"


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
    def discovered_module_paths(self) -> dict[str, str]:
        """Return every manifest-discovered module identity and source path.

        Unlike :attr:`paths`, this population includes source units whose
        lexical entry could not be constructed.  The fingerprint manifest
        remains authoritative for discovered module membership even when
        dependent lexical collections are partial.
        """

        paths: dict[str, str] = {}
        for name, state in sorted(
            _manifest_source_states(self.fingerprint_manifest).items()
        ):
            path = state.get("path")
            if not isinstance(path, str) or not path:
                raise SourceIndexError(
                    f"source-index manifest path is malformed for {name}"
                )
            paths[name] = path
        return paths

    @property
    def phase_status(self) -> str:
        """Return the discover-phase completion state for pipeline callers."""

        return self.index_status

    @property
    def discovery_status(self) -> str:
        """Return a backend discovery status that exposes partial indexing."""

        return "partial" if self.index_status == "partial" else self.layout_status

    def coverage_registry(self) -> CoverageRegistry:
        """Return truthful coverage for canonical source-index populations.

        The manifest fixes the module inventory cardinality even when an entry
        cannot be extracted. Import and declaration cardinalities depend on the
        contents of every source, so a missing entry leaves only an observed
        lower bound for those populations.
        """

        inventory_total = len(_manifest_source_states(self.fingerprint_manifest))
        causes = _source_failure_coverage_causes(self.diagnostics)
        registry = CoverageRegistry().register(
            CollectionCoverage.exact(
                identity=SOURCE_INDEX_MODULES_COVERAGE,
                pointer=SOURCE_INDEX_COVERAGE_POINTER,
                visible=len(self.entries),
                total=inventory_total,
                population="discovered_internal_modules",
                scope="source_index_inventory",
                authority="source_index_manifest",
                causes=causes,
                source_fingerprint=self.fingerprint,
            )
        )
        registry = registry.register(
            _source_index_dependent_coverage(
                index=self,
                identity=SOURCE_INDEX_IMPORTS_COVERAGE,
                visible=sum(len(entry.module.imports) for entry in self.entries),
                population="lexical_import_occurrences",
                authority="lexical_text",
                causes=causes,
            )
        )
        registry = registry.register(
            _source_index_dependent_coverage(
                index=self,
                identity=SOURCE_INDEX_DECLARATIONS_COVERAGE,
                visible=sum(
                    len(entry.module.declaration_evidence) for entry in self.entries
                ),
                population="lexical_declaration_evidence",
                authority="lexical_text",
                causes=causes,
            )
        )
        dependent_collections = (
            (
                SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE,
                sum(len(entry.module.scope_contexts) for entry in self.entries),
                "lexical_scope_contexts",
            ),
            (
                SOURCE_INDEX_OPTIONS_COVERAGE,
                sum(len(entry.module.option_rows) for entry in self.entries),
                "lexical_option_commands",
            ),
            (
                SOURCE_INDEX_RESOURCES_COVERAGE,
                sum(len(entry.module.resource_settings) for entry in self.entries),
                "lexical_resource_settings",
            ),
            (
                SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
                sum(len(entry.module.proof_mechanisms) for entry in self.entries),
                "lexical_proof_mechanism_occurrences",
            ),
        )
        for identity, visible, population in dependent_collections:
            registry = registry.register(
                _source_index_dependent_coverage(
                    index=self,
                    identity=identity,
                    visible=visible,
                    population=population,
                    authority="lexical_text",
                    causes=causes,
                )
            )
        registry = registry.register(audit_command_coverage(self, causes=causes))
        registry = registry.register(_command_skeleton_coverage(self, causes=causes))
        return registry

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
            raise ValueError(f"unsupported source-index cache outcome {self.status!r}")
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
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in counters
    ):
        raise ValueError("source-index cache counters must be non-negative integers")


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
        validate_audit_command_rows(entry.module)


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
        raise SourceIndexError("complete source index does not cover its full manifest")
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


def _source_failure_coverage_causes(
    diagnostics: tuple[Mapping[str, Any], ...],
) -> tuple[CoverageCause, ...]:
    failures = sorted(
        (row for row in diagnostics if row.get("id") == SOURCE_FAILURE_DIAGNOSTIC),
        key=lambda row: (
            str(row.get("module", "")),
            str(row.get("path", "")),
            str(row.get("cause", "")),
            str(row.get("detail", "")),
        ),
    )
    return tuple(
        CoverageCause(
            kind="extraction",
            identifier=SOURCE_FAILURE_DIAGNOSTIC,
            detail=_source_failure_coverage_detail(row),
        )
        for row in failures
    )


def _source_failure_coverage_detail(row: Mapping[str, Any]) -> str:
    message = row.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    module = str(row.get("module", "<unknown module>"))
    cause = str(row.get("cause", "source extraction failure"))
    return f"Source-index extraction failed for {module}: {cause}."


def _source_index_dependent_coverage(
    *,
    index: SourceIndex,
    identity: str,
    visible: int,
    population: str,
    authority: str,
    causes: tuple[CoverageCause, ...],
) -> CollectionCoverage:
    if index.index_status == "complete":
        return CollectionCoverage.exact(
            identity=identity,
            pointer=SOURCE_INDEX_COVERAGE_POINTER,
            visible=visible,
            total=visible,
            population=population,
            scope="source_index_inventory",
            authority=authority,
            source_fingerprint=index.fingerprint,
        )
    return CollectionCoverage.unknown(
        identity=identity,
        pointer=SOURCE_INDEX_COVERAGE_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness="partial",
        population=population,
        scope="source_index_inventory",
        authority=authority,
        causes=causes,
        source_fingerprint=index.fingerprint,
    )


def _command_skeleton_coverage(
    index: SourceIndex,
    *,
    causes: tuple[CoverageCause, ...],
) -> CollectionCoverage:
    """Report missing additive command-shape rows as unknown, never empty."""

    visible = sum(len(entry.module.command_skeletons) for entry in index.entries)
    unavailable = tuple(
        entry.name
        for entry in index.entries
        if not command_skeleton_evidence_complete(entry.module)
    )
    if not unavailable:
        return _source_index_dependent_coverage(
            index=index,
            identity=SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE,
            visible=visible,
            population="lexical_command_skeletons",
            authority="lexical_text",
            causes=causes,
        )
    unavailable_cause = CoverageCause(
        kind="compatibility",
        identifier="source_index.command_skeletons_unavailable",
        detail=(
            "Command-skeleton availability is unknown for modules: "
            + ", ".join(unavailable)
            + "."
        ),
    )
    return CollectionCoverage.unknown(
        identity=SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE,
        pointer=SOURCE_INDEX_COVERAGE_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness="partial",
        population="lexical_command_skeletons",
        scope="source_index_inventory",
        authority="lexical_text",
        causes=(*causes, unavailable_cause),
        source_fingerprint=index.fingerprint,
    )


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
    payload = {
        "name": module.name,
        "path": module.path,
        "imports": list(module.imports),
        "importSites": _import_payload(module),
        "lineCount": module.line_count,
        "tags": list(module.tags),
        "lexicalMarkers": _marker_payload(module),
        "declarations": (
            [] if evidence_names == module.declarations else list(module.declarations)
        ),
        "declarationEvidence": [
            _compact_declaration_evidence(row) for row in module.declaration_evidence
        ],
    }
    payload.update(module_navigation_payload(module))
    return payload


def _import_payload(module: LeanModule) -> list[dict[str, Any]]:
    return [
        {"module": row.module, "line": row.line, "text": row.text}
        for row in module.import_sites
    ]


def _marker_payload(module: LeanModule) -> list[dict[str, Any]]:
    return [
        {"kind": row.kind, "line": row.line, "text": row.text}
        for row in module.lexical_markers
    ]


def _compact_declaration_evidence(row: LeanTextDeclaration) -> list[Any]:
    """Encode common lexical rows without repeated field names/default prose."""

    return [
        row.name,
        row.kind,
        row.line,
        row.column,
        row.start_offset,
        row.end_offset,
        row.identifier,
        list(row.namespace_stack),
        list(row.section_stack),
        list(row.modifiers),
        row.privacy,
        row.locality,
        row.candidate_name,
        row.candidate_status,
        row.block_start_offset,
        row.block_end_offset,
        row.normalized_block_sha256,
        row.block_normalization_version,
        row.normalized_source_shape_sha256,
        row.source_shape_normalization_version,
        row.authority,
        row.confidence,
        row.nonclaim,
        row.scope_context_id,
        row.scope_context_status,
    ]


def _entry_from_payload(raw: Any) -> SourceIndexEntry:
    if not isinstance(raw, Mapping):
        raise SourceIndexError("source-index entry is not an object")
    module = _module_from_payload(raw.get("module"))
    digest = raw.get("contentSha256")
    source_bytes = raw.get("sourceBytes")
    if not isinstance(digest, str) or len(digest) != 64:
        raise SourceIndexError(f"source-index digest is malformed for {module.name}")
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
        scope_context_commands=decode_context_commands(
            row.get("scopeContextCommands", []),
            module=name,
            path=path,
        ),
        scope_contexts=decode_scope_contexts(
            row.get("scopeContextRows", []),
            module=name,
            path=path,
        ),
        option_rows=decode_options(
            row.get("optionRows", []),
            module=name,
            path=path,
        ),
        resource_settings=decode_resources(
            row.get("resourceSettings", []),
            module=name,
            path=path,
        ),
        proof_mechanisms=decode_mechanisms(
            row.get("proofMechanisms", []),
            module=name,
            path=path,
        ),
        audit_commands=decode_audit_commands(
            row.get("auditCommands", []),
            module=name,
            path=path,
        ),
        audit_commands_complete=audit_commands_complete_field(row),
        command_skeletons=decode_command_skeletons(
            row.get("commandSkeletons", []),
            module=name,
            path=path,
        ),
        command_skeletons_complete=_command_skeletons_complete(row),
    )


def _command_skeletons_complete(row: Mapping[str, Any]) -> bool:
    """Decode additive availability without upgrading a missing collection."""

    explicit = row.get("commandSkeletonsComplete")
    present = "commandSkeletons" in row
    if explicit is None:
        return present
    if not isinstance(explicit, bool):
        raise SourceIndexError(
            "source-index command-skeleton completeness is malformed"
        )
    if explicit and not present:
        raise SourceIndexError("complete source-index command skeletons are absent")
    return explicit


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
    """Decode current compact rows and legacy scope-unavailable rows."""

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
        identifier=_optional_string(row.get("id")) or _legacy_evidence_id(row),
        namespace_stack=_string_tuple(row.get("namespaceStack", [])),
        section_stack=_string_tuple(row.get("sectionStack", [])),
        modifiers=_string_tuple(row.get("modifiers", [])),
        privacy=str(row.get("privacy", "unknown")),
        locality=str(row.get("locality", "unknown")),
        candidate_name=_optional_string(row.get("candidateName")),
        candidate_status=str(row.get("candidateStatus", "scope_unavailable")),
        block_start_offset=_optional_nonnegative_int(
            row.get("blockStartOffset"),
            "declaration block start",
        ),
        block_end_offset=_optional_nonnegative_int(
            row.get("blockEndOffset"),
            "declaration block end",
        ),
        normalized_block_sha256=_optional_string(row.get("normalizedBlockSha256")),
        block_normalization_version=_optional_string(
            row.get("blockNormalizationVersion")
        ),
        normalized_source_shape_sha256=_optional_string(
            row.get("normalizedSourceShapeSha256")
        ),
        source_shape_normalization_version=_optional_string(
            row.get("sourceShapeNormalizationVersion")
        ),
        authority=str(row.get("authority", "lexical_text")),
        confidence=str(row.get("confidence", "bounded_lexical_scan")),
        nonclaim=str(
            row.get(
                "nonclaim",
                LeanTextDeclaration.__dataclass_fields__["nonclaim"].default,
            )
        ),
        scope_context_id=_optional_string(row.get("scopeContextId")),
        scope_context_status=str(row.get("scopeContextStatus", "unavailable")),
    )


def _compact_evidence_from_payload(raw: list[Any]) -> LeanTextDeclaration:
    if len(raw) == 25:
        return _current_compact_evidence(raw)
    if len(raw) == 23:
        return _v3_compact_evidence(raw)
    if len(raw) == 21:
        return _v2_compact_evidence(raw)
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
        identifier=_legacy_evidence_id(raw),
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


def _current_compact_evidence(raw: list[Any]) -> LeanTextDeclaration:
    """Decode the current shape/context row with one validated construction."""

    return LeanTextDeclaration(
        name=_sequence_string(raw, 0, "declaration name"),
        kind=_sequence_string(raw, 1, "declaration kind"),
        line=_nonnegative_int(raw[2], "declaration line"),
        column=_nonnegative_int(raw[3], "declaration column"),
        start_offset=_nonnegative_int(raw[4], "declaration start"),
        end_offset=_nonnegative_int(raw[5], "declaration end"),
        identifier=_sequence_string(raw, 6, "declaration identifier"),
        namespace_stack=_sequence_string_tuple(
            raw[7],
            "declaration namespace stack",
        ),
        section_stack=_sequence_string_tuple(
            raw[8],
            "declaration section stack",
        ),
        modifiers=_sequence_string_tuple(
            raw[9],
            "declaration modifiers",
        ),
        privacy=_sequence_string(raw, 10, "declaration privacy"),
        locality=_sequence_string(raw, 11, "declaration locality"),
        candidate_name=_optional_string(raw[12]),
        candidate_status=_sequence_string(
            raw,
            13,
            "declaration candidate status",
        ),
        block_start_offset=_optional_nonnegative_int(
            raw[14],
            "declaration block start",
        ),
        block_end_offset=_optional_nonnegative_int(
            raw[15],
            "declaration block end",
        ),
        normalized_block_sha256=_optional_string(raw[16]),
        block_normalization_version=_optional_string(raw[17]),
        normalized_source_shape_sha256=_optional_string(raw[18]),
        source_shape_normalization_version=_optional_string(raw[19]),
        authority=_sequence_string(raw, 20, "declaration authority"),
        confidence=_sequence_string(raw, 21, "declaration confidence"),
        nonclaim=_sequence_string(raw, 22, "declaration nonclaim"),
        scope_context_id=_optional_string(raw[23]),
        scope_context_status=_sequence_string(
            raw,
            24,
            "declaration scope-context status",
        ),
    )


def _v2_compact_evidence(raw: list[Any]) -> LeanTextDeclaration:
    """Decode the source-index-v2 compact lexical declaration row."""

    return LeanTextDeclaration(
        name=_sequence_string(raw, 0, "declaration name"),
        kind=_sequence_string(raw, 1, "declaration kind"),
        line=_nonnegative_int(raw[2], "declaration line"),
        column=_nonnegative_int(raw[3], "declaration column"),
        start_offset=_nonnegative_int(raw[4], "declaration start"),
        end_offset=_nonnegative_int(raw[5], "declaration end"),
        identifier=_sequence_string(raw, 6, "declaration identifier"),
        namespace_stack=_sequence_string_tuple(
            raw[7],
            "declaration namespace stack",
        ),
        section_stack=_sequence_string_tuple(
            raw[8],
            "declaration section stack",
        ),
        modifiers=_sequence_string_tuple(
            raw[9],
            "declaration modifiers",
        ),
        privacy=_sequence_string(raw, 10, "declaration privacy"),
        locality=_sequence_string(raw, 11, "declaration locality"),
        candidate_name=_optional_string(raw[12]),
        candidate_status=_sequence_string(
            raw,
            13,
            "declaration candidate status",
        ),
        block_start_offset=_optional_nonnegative_int(
            raw[14],
            "declaration block start",
        ),
        block_end_offset=_optional_nonnegative_int(
            raw[15],
            "declaration block end",
        ),
        normalized_block_sha256=_optional_string(raw[16]),
        block_normalization_version=_optional_string(raw[17]),
        authority=_sequence_string(raw, 18, "declaration authority"),
        confidence=_sequence_string(raw, 19, "declaration confidence"),
        nonclaim=_sequence_string(raw, 20, "declaration nonclaim"),
    )


def _v3_compact_evidence(raw: list[Any]) -> LeanTextDeclaration:
    """Decode v3 context identity without changing the v2 field prefix."""

    legacy = _v2_compact_evidence(raw[:21])
    return LeanTextDeclaration(
        **{
            field: getattr(legacy, field)
            for field in LeanTextDeclaration.__dataclass_fields__
            if field not in {"scope_context_id", "scope_context_status"}
        },
        scope_context_id=_optional_string(raw[21]),
        scope_context_status=_sequence_string(
            raw,
            22,
            "declaration scope-context status",
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


def _legacy_evidence_id(raw: Mapping[str, Any] | list[Any]) -> str:
    """Derive a stable adapter identity without claiming scope availability."""

    if isinstance(raw, Mapping):
        identity = {
            "name": raw.get("name"),
            "kind": raw.get("kind"),
            "line": raw.get("line"),
            "column": raw.get("column"),
            "startOffset": raw.get("startOffset"),
            "endOffset": raw.get("endOffset"),
        }
    else:
        identity = {
            "name": raw[0],
            "kind": raw[1],
            "line": raw[2],
            "column": raw[3],
            "startOffset": raw[4],
            "endOffset": raw[5],
        }
    encoded = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        f"ladon.lexical_declaration.legacy.{hashlib.sha256(encoded).hexdigest()[:20]}"
    )


def _required_mapping(raw: Any, message: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise SourceIndexError(message)
    return raw


def _mapping_tuple(
    raw: Any,
    message: str,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, list) or not all(isinstance(row, Mapping) for row in raw):
        raise SourceIndexError(message)
    return tuple(dict(row) for row in raw)


def _mapping_list(raw: Any) -> list[Mapping[str, Any]]:
    if not isinstance(raw, list) or not all(isinstance(row, Mapping) for row in raw):
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


def _sequence_string_tuple(raw: Any, label: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(row, str) for row in raw):
        raise SourceIndexError(f"source-index {label} is malformed")
    return tuple(raw)


def _optional_string(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise SourceIndexError("source-index optional string is malformed")
    return raw


def _optional_nonnegative_int(raw: Any, label: str) -> int | None:
    if raw is None:
        return None
    return _nonnegative_int(raw, label)


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


def source_index_declaration_mapping(raw: Any) -> dict[str, Any]:
    """Expand one compact declaration row for artifact inspection."""

    row = _declaration_evidence_from_payload(raw)
    return {
        "name": row.name,
        "kind": row.kind,
        "line": row.line,
        "column": row.column,
        "startOffset": row.start_offset,
        "endOffset": row.end_offset,
        "id": row.identifier,
        "namespaceStack": list(row.namespace_stack),
        "sectionStack": list(row.section_stack),
        "modifiers": list(row.modifiers),
        "privacy": row.privacy,
        "locality": row.locality,
        "candidateName": row.candidate_name,
        "candidateStatus": row.candidate_status,
        "blockStartOffset": row.block_start_offset,
        "blockEndOffset": row.block_end_offset,
        "normalizedBlockSha256": row.normalized_block_sha256,
        "blockNormalizationVersion": row.block_normalization_version,
        "normalizedSourceShapeSha256": row.normalized_source_shape_sha256,
        "sourceShapeNormalizationVersion": (row.source_shape_normalization_version),
        "authority": row.authority,
        "confidence": row.confidence,
        "nonclaim": row.nonclaim,
        "scopeContextId": row.scope_context_id,
        "scopeContextStatus": row.scope_context_status,
    }


__all__ = [
    "CACHE_OUTCOMES",
    "INDEX_STATUSES",
    "SOURCE_FAILURE_DIAGNOSTIC",
    "SOURCE_INDEX_AUDITS_COVERAGE",
    "SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE",
    "SOURCE_INDEX_COVERAGE_POINTER",
    "SOURCE_INDEX_DECLARATIONS_COVERAGE",
    "SOURCE_INDEX_FINGERPRINT_VERSION",
    "SOURCE_INDEX_IMPORTS_COVERAGE",
    "SOURCE_INDEX_MODULES_COVERAGE",
    "SOURCE_INDEX_OPTIONS_COVERAGE",
    "SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE",
    "SOURCE_INDEX_RESOURCES_COVERAGE",
    "SOURCE_INDEX_SCHEMA",
    "SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE",
    "SourceIndex",
    "SourceIndexCacheOutcome",
    "SourceIndexEntry",
    "SourceIndexError",
    "SourceIndexResult",
    "source_index_collection_mapping",
    "source_index_declaration_mapping",
]
