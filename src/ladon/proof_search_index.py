"""Persistent, scope-aware navigation index for interactive Lean proof work.

Version one deliberately indexes project-owned lexical evidence. Its schema has
places for elaborated binders and declaration dependencies, but empty Lean-backed
collections remain explicitly unavailable until a helper supplies them.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.extraction import parse_import_sites, parse_text_declarations
from ladon.lean_layout import LeanSourceMap, discover_lean_source_map, root_for_path
from ladon.lexical_mask import mask_lean_source
from ladon.proof_search_query import query_database
from ladon.proof_search_schema import (
    EXPECTED_FOREIGN_KEYS,
    PROOF_SEARCH_HELPER_IDENTITY,
    PROOF_SEARCH_INDEX_SCHEMA,
    PROOF_SEARCH_INDEX_SCHEMA_VERSION,
    PROOF_SEARCH_SCHEMA_GENERATION,
    REQUIRED_LOOKUP_INDEX_COLUMNS,
    REQUIRED_LOOKUP_INDEXES,
    REQUIRED_QUERY_SURFACES,
    create_proof_search_schema,
    schema_foreign_keys,
    schema_index_columns,
    schema_lookup_indexes,
    schema_query_surfaces,
)

PROOF_SEARCH_RESULT_SCHEMA = "ladon-proof-search-index-result-v1"
DEFAULT_INDEX_RELATIVE_PATH = Path(".ladon/index/proof-search.sqlite")
DEFAULT_MAX_INDEX_BYTES = 512 * 1024 * 1024
SUPPORTED_INDEX_SCOPES = frozenset(
    {
        "repository",
        "module",
        "imports",
        "closure",
        "namespace",
        "file",
        "neighborhood",
        "project",
        "external",
    }
)
_CONFIGURATION_NAMES = (
    "lean-toolchain",
    "lakefile.toml",
    "lakefile.lean",
    "lake-manifest.json",
)
_MAX_LEXICAL_TYPE_BYTES = 16 * 1024


class ProofSearchIndexError(RuntimeError):
    """A v1 index could not be built, opened, or queried safely."""


@dataclass(frozen=True)
class IndexedSource:
    """One immutable source observation used to identify an index generation."""

    module: str
    path: Path
    relative_path: str
    package: str
    generated: bool
    sha256: str
    source_bytes: int

    def identity_payload(self) -> dict[str, Any]:
        """Return stable generation-identity fields for this source."""

        return {
            "module": self.module,
            "path": self.relative_path,
            "package": self.package,
            "generated": self.generated,
            "sha256": self.sha256,
            "bytes": self.source_bytes,
        }


@dataclass(frozen=True)
class RepositorySnapshot:
    """Source, configuration, layout, and toolchain identity for one checkout."""

    repo_root: Path
    layout: LeanSourceMap
    sources: tuple[IndexedSource, ...]
    toolchain_identity: str
    configuration_fingerprint: str
    source_fingerprint: str
    generation_identity: str


@dataclass(frozen=True)
class IndexBuildResult:
    """Canonical observable result of one atomic index build."""

    payload: Mapping[str, Any]

    @property
    def index_path(self) -> Path:
        """Return the materialized database path."""

        return Path(str(self.payload["indexPath"]))


def default_proof_search_index_path(repo_root: Path) -> Path:
    """Return the repository-local generated index path."""

    return repo_root.resolve() / DEFAULT_INDEX_RELATIVE_PATH


def capture_repository_snapshot(repo_root: Path) -> RepositorySnapshot:
    """Hash the supported project source/configuration population."""

    root = repo_root.resolve()
    if not root.is_dir():
        raise ProofSearchIndexError(f"repository does not exist: {root}")
    layout = discover_lean_source_map(root)
    sources = tuple(
        _indexed_source(root, layout, module, path)
        for module, path in sorted(layout.modules.items())
    )
    toolchain = _toolchain_identity(root)
    configuration = _configuration_fingerprint(root)
    source_fingerprint = _stable_digest(
        [source.identity_payload() for source in sources]
    )
    generation = _stable_digest(
        {
            "schema": PROOF_SEARCH_INDEX_SCHEMA,
            "schemaGeneration": PROOF_SEARCH_SCHEMA_GENERATION,
            "helper": PROOF_SEARCH_HELPER_IDENTITY,
            "toolchain": toolchain,
            "configuration": configuration,
            "layout": layout.status,
            "sources": source_fingerprint,
        }
    )
    return RepositorySnapshot(
        repo_root=root,
        layout=layout,
        sources=sources,
        toolchain_identity=toolchain,
        configuration_fingerprint=configuration,
        source_fingerprint=source_fingerprint,
        generation_identity=generation,
    )


def build_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    max_index_bytes: int = DEFAULT_MAX_INDEX_BYTES,
) -> IndexBuildResult:
    """Build and atomically replace one repository's v1 query index."""

    if max_index_bytes < 64 * 1024:
        raise ProofSearchIndexError("maximum index size must be at least 64 KiB")
    started = time.monotonic()
    snapshot = capture_repository_snapshot(repo_root)
    destination = _resolved_index_path(snapshot.repo_root, index_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_database_path(destination)
    counts: dict[str, int]
    try:
        counts = _write_database(
            temporary,
            snapshot,
            max_index_bytes=max_index_bytes,
        )
        if temporary.stat().st_size > max_index_bytes:
            raise ProofSearchIndexError(
                f"index exceeds configured limit of {max_index_bytes} bytes"
            )
        _durable_replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    visible = _version_control_visible(snapshot.repo_root, destination)
    elapsed = time.monotonic() - started
    payload = _build_result_payload(
        snapshot,
        destination,
        counts,
        elapsed_seconds=elapsed,
        version_control_visible=visible,
        max_index_bytes=max_index_bytes,
    )
    return IndexBuildResult(payload)


def inspect_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    verify_sources: bool = True,
) -> dict[str, Any]:
    """Return schema, coverage, and optional live freshness evidence."""

    root = repo_root.resolve()
    database = _resolved_index_path(root, index_path)
    if not database.is_file():
        return _unavailable_status(root, database, "index_missing")
    started = time.monotonic()
    try:
        with _open_readonly(database) as connection:
            metadata = _metadata(connection)
            counts = _database_counts(connection)
            indexes = schema_lookup_indexes(connection)
            index_columns = schema_index_columns(connection)
            query_surfaces = schema_query_surfaces(connection)
            foreign_keys = schema_foreign_keys(connection)
    except (OSError, sqlite3.Error, ValueError) as exc:
        return _unavailable_status(root, database, f"index_unreadable: {exc}")
    freshness, current_generation = _freshness(
        root,
        metadata,
        verify_sources=verify_sources,
    )
    version_control_visible = _version_control_visible(root, database)
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "status",
        "status": "available",
        "indexPath": str(database),
        "repository": str(root),
        "indexSchema": metadata.get("indexSchema"),
        "schemaVersion": _integer_metadata(metadata, "schemaVersion"),
        "schemaGeneration": metadata.get("schemaGeneration"),
        "generationIdentity": metadata.get("generationIdentity"),
        "currentGenerationIdentity": current_generation,
        "freshness": freshness,
        "evidenceStatus": metadata.get("evidenceStatus", "unknown"),
        "toolchainIdentity": metadata.get("toolchainIdentity"),
        "configurationFingerprint": metadata.get("configurationFingerprint"),
        "sourceFingerprint": metadata.get("sourceFingerprint"),
        "counts": counts,
        "lookupIndexes": sorted(indexes),
        "lookupIndexColumns": {
            name: list(columns) for name, columns in sorted(index_columns.items())
        },
        "requiredLookupIndexesPresent": REQUIRED_LOOKUP_INDEXES <= indexes,
        "requiredLookupIndexDefinitionsPresent": all(
            index_columns.get(name) == columns
            for name, columns in REQUIRED_LOOKUP_INDEX_COLUMNS.items()
        ),
        "querySurfaces": sorted(query_surfaces),
        "requiredQuerySurfacesPresent": REQUIRED_QUERY_SURFACES <= query_surfaces,
        "foreignKeys": [list(row) for row in sorted(foreign_keys)],
        "requiredForeignKeysPresent": EXPECTED_FOREIGN_KEYS <= foreign_keys,
        "unconstrainedExternalReferences": [
            "module_imports.target",
            "declaration_dependencies.source",
            "declaration_dependencies.target",
            "aliases.source",
            "aliases.target",
        ],
        "databaseBytes": database.stat().st_size,
        "versionControlVisible": version_control_visible,
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _index_nonclaim(),
    }


def query_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    text: str | None = None,
    scope: str = "repository",
    roots: Sequence[str] = (),
    limit: int = 20,
) -> dict[str, Any]:
    """Run one deterministic bounded metadata query."""

    if scope not in SUPPORTED_INDEX_SCOPES:
        expected = ", ".join(sorted(SUPPORTED_INDEX_SCOPES))
        raise ProofSearchIndexError(f"unsupported scope {scope!r}; expected {expected}")
    if limit < 1 or limit > 1000:
        raise ProofSearchIndexError("query limit must be between 1 and 1000")
    root = repo_root.resolve()
    database = _resolved_index_path(root, index_path)
    if not database.is_file():
        raise ProofSearchIndexError(f"proof-search index does not exist: {database}")
    started = time.monotonic()
    try:
        with _open_readonly(database) as connection:
            metadata = _metadata(connection)
            rows, truncated, selected_module_count, scope_omissions = query_database(
                connection,
                text=text,
                scope=scope,
                roots=tuple(roots),
                limit=limit,
            )
    except ValueError as exc:
        raise ProofSearchIndexError(str(exc)) from exc
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "query",
        "status": "available",
        "indexPath": str(database),
        "generationIdentity": metadata.get("generationIdentity"),
        "freshness": "unchecked",
        "evidenceStatus": metadata.get("evidenceStatus", "unknown"),
        "query": {
            "text": text,
            "scope": scope,
            "roots": list(roots),
            "limit": limit,
        },
        "scope": {
            "kind": scope,
            "roots": list(roots),
            "includedModules": selected_module_count,
            "omissions": scope_omissions,
        },
        "rows": rows,
        "returned": len(rows),
        "truncated": truncated,
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _index_nonclaim(),
    }


def _write_database(
    path: Path,
    snapshot: RepositorySnapshot,
    *,
    max_index_bytes: int,
) -> dict[str, int]:
    """Populate a constrained fresh database and return collection counts."""

    try:
        return _write_database_connection(path, snapshot, max_index_bytes)
    except sqlite3.Error as exc:
        raise ProofSearchIndexError(f"SQLite index build failed: {exc}") from exc


def _write_database_connection(
    path: Path,
    snapshot: RepositorySnapshot,
    max_index_bytes: int,
) -> dict[str, int]:
    """Own one SQLite connection for a complete unpublished generation."""

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        create_proof_search_schema(connection)
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        max_pages = max(1, max_index_bytes // page_size)
        connection.execute(f"PRAGMA max_page_count = {max_pages}")
        connection.execute(f"PRAGMA user_version = {PROOF_SEARCH_INDEX_SCHEMA_VERSION}")
        _insert_metadata(connection, snapshot, max_index_bytes=max_index_bytes)
        _insert_source_roots(connection, snapshot)
        declaration_count = 0
        import_count = 0
        structure_count = 0
        type_truncation_count = 0
        for source in snapshot.sources:
            module_counts = _insert_source(connection, source)
            declaration_count += module_counts[0]
            import_count += module_counts[1]
            structure_count += module_counts[2]
            type_truncation_count += module_counts[3]
        _insert_layout_omissions(connection, snapshot.layout)
        _insert_coverage(
            connection,
            modules=len(snapshot.sources),
            declarations=declaration_count,
            imports=import_count,
            structures=structure_count,
        )
        connection.commit()
        _validate_database(connection)
    return {
        "modules": len(snapshot.sources),
        "declarations": declaration_count,
        "moduleImports": import_count,
        "structures": structure_count,
        "declarationDependencies": 0,
        "binders": 0,
        "structureFields": 0,
        "lineageClosures": 0,
        "lineageNodes": 0,
        "lineageEdges": 0,
        "lineageTrust": 0,
        "lineageSccMembers": 0,
        "lineageOmissions": 0,
        "typeTextTruncations": type_truncation_count,
    }


def _insert_source(
    connection: sqlite3.Connection,
    source: IndexedSource,
) -> tuple[int, int, int, int]:
    """Parse and insert one source while checking the captured bytes."""

    raw = source.path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source.sha256:
        raise ProofSearchIndexError(
            f"Lean source changed while building index: {source.relative_path}"
        )
    text = raw.decode("utf-8")
    masks = mask_lean_source(text)
    masked = masks.lexical.rstrip()
    imports = parse_import_sites(text, masked_text=masked)
    declarations = parse_text_declarations(
        text,
        masked_text=masked,
        module=source.module,
        source_path=source.relative_path,
    )
    connection.execute(
        """
        INSERT INTO modules(
            name, path, package, generated, source_sha256, source_bytes,
            line_count, evidence_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source.module,
            source.relative_path,
            source.package,
            int(source.generated),
            source.sha256,
            source.source_bytes,
            text.count("\n") + int(bool(text)),
            "lexical-fallback",
        ),
    )
    _insert_imports(connection, source.module, imports)
    structure_count, truncation_count = _insert_declarations(
        connection,
        source,
        text,
        masked,
        declarations,
    )
    return len(declarations), len(imports), structure_count, truncation_count


def _insert_imports(
    connection: sqlite3.Connection,
    module: str,
    imports: Iterable[Any],
) -> None:
    """Insert direct lexical import evidence for one module."""

    connection.executemany(
        """
        INSERT OR IGNORE INTO module_imports(
            source, target, line, column_number, authority
        ) VALUES (?, ?, ?, ?, 'lexical_text')
        """,
        (
            (
                module,
                imported.module,
                getattr(imported, "line", None),
                getattr(imported, "column", None),
            )
            for imported in imports
        ),
    )


def _insert_declarations(
    connection: sqlite3.Connection,
    source: IndexedSource,
    text: str,
    masked: str,
    declarations: Iterable[Any],
) -> tuple[int, int]:
    """Insert bounded lexical declaration and token rows."""

    structures = 0
    truncations = 0
    for declaration in declarations:
        candidate = declaration.candidate_name
        namespace = ".".join(declaration.namespace_stack)
        type_text, type_bytes, type_truncated = _lexical_type_text(
            text,
            masked,
            declaration,
        )
        structure_name = (
            candidate if declaration.kind in {"structure", "class"} else None
        )
        connection.execute(
            """
            INSERT INTO declarations(
                id, name, candidate_name, namespace, kind, module, package,
                path, line, column_number, start_offset, end_offset,
                block_sha256, type_text, type_text_bytes, type_text_truncated,
                type_status, authority, privacy, locality, structure_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                declaration.identifier,
                declaration.name,
                candidate,
                namespace,
                declaration.kind,
                source.module,
                source.package,
                source.relative_path,
                declaration.line,
                declaration.column,
                declaration.start_offset,
                declaration.end_offset,
                declaration.normalized_block_sha256,
                type_text,
                type_bytes,
                int(type_truncated),
                "lexical-signature" if type_text else "unavailable",
                "lexical_text",
                declaration.privacy,
                declaration.locality,
                structure_name,
            ),
        )
        if type_truncated:
            truncations += 1
            connection.execute(
                "INSERT INTO omissions VALUES ('declaration', ?, 'lexical_type_truncated', ?)",
                (
                    declaration.identifier,
                    json.dumps(
                        {"observedBytes": type_bytes, "storedBytes": _MAX_LEXICAL_TYPE_BYTES},
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
        _insert_search_row(
            connection,
            declaration.identifier,
            candidate or declaration.name,
            type_text,
        )
        if structure_name is not None:
            structures += 1
            connection.execute(
                "INSERT INTO structures VALUES (?, ?, ?, 'lexical_text')",
                (declaration.identifier, structure_name, source.module),
            )
    return structures, truncations


def _insert_search_row(
    connection: sqlite3.Connection,
    declaration_id: str,
    name: str,
    type_text: str | None,
) -> None:
    """Insert one compact FTS row linked to the declaration's private rowid."""

    connection.execute(
        """
        INSERT INTO declaration_search(rowid, candidate_name, type_text)
        SELECT rowid, ?, ? FROM declarations WHERE id = ?
        """,
        (name, type_text or "", declaration_id),
    )


def _lexical_type_text(
    text: str,
    masked: str,
    declaration: Any,
) -> tuple[str | None, int, bool]:
    """Return a bounded lexical signature without claiming elaboration."""

    finish = declaration.block_end_offset or declaration.end_offset
    raw_tail = text[declaration.end_offset:finish]
    masked_tail = masked[declaration.end_offset:finish]
    boundaries = [position for position in (masked_tail.find(":="),) if position >= 0]
    where_match = re.search(r"(?m)^[ \t]*where\b", masked_tail)
    if where_match is not None:
        boundaries.append(where_match.start())
    equation_match = re.search(r"(?m)^[ \t]*\|", masked_tail)
    if equation_match is not None:
        boundaries.append(equation_match.start())
    end = min(boundaries, default=len(raw_tail))
    signature = " ".join(raw_tail[:end].split())
    encoded = signature.encode("utf-8")
    if len(encoded) <= _MAX_LEXICAL_TYPE_BYTES:
        return signature or None, len(encoded), False
    bounded = encoded[:_MAX_LEXICAL_TYPE_BYTES].decode("utf-8", errors="ignore")
    return bounded, len(encoded), True


def _insert_metadata(
    connection: sqlite3.Connection,
    snapshot: RepositorySnapshot,
    *,
    max_index_bytes: int,
) -> None:
    """Insert stable generation metadata."""

    values = {
        "indexSchema": PROOF_SEARCH_INDEX_SCHEMA,
        "schemaVersion": str(PROOF_SEARCH_INDEX_SCHEMA_VERSION),
        "schemaGeneration": PROOF_SEARCH_SCHEMA_GENERATION,
        "helperIdentity": PROOF_SEARCH_HELPER_IDENTITY,
        "repository": str(snapshot.repo_root),
        "layoutStatus": snapshot.layout.status,
        "toolchainIdentity": snapshot.toolchain_identity,
        "configurationFingerprint": snapshot.configuration_fingerprint,
        "sourceFingerprint": snapshot.source_fingerprint,
        "generationIdentity": snapshot.generation_identity,
        "freshness": "fresh",
        "evidenceStatus": "lexical-fallback",
        "maxIndexBytes": str(max_index_bytes),
        "maxLexicalTypeBytes": str(_MAX_LEXICAL_TYPE_BYTES),
    }
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?)",
        sorted(values.items()),
    )


def _insert_source_roots(
    connection: sqlite3.Connection,
    snapshot: RepositorySnapshot,
) -> None:
    """Persist the Lake-declared source-root authority."""

    connection.executemany(
        "INSERT INTO source_roots VALUES (?, ?, ?, ?, ?)",
        (
            (
                _relative_or_absolute(snapshot.repo_root, root.path),
                root.library,
                root.origin,
                int(root.generated),
                json.dumps(list(root.module_roots), separators=(",", ":")),
            )
            for root in snapshot.layout.roots
        ),
    )


def _insert_layout_omissions(
    connection: sqlite3.Connection,
    layout: LeanSourceMap,
) -> None:
    """Retain layout diagnostics as omission evidence."""

    connection.executemany(
        "INSERT OR IGNORE INTO omissions VALUES ('module', ?, ?, ?)",
        (
            (
                str(row.get("subject", "layout")),
                str(row.get("id", "layout_diagnostic")),
                json.dumps(row, sort_keys=True, separators=(",", ":")),
            )
            for row in layout.diagnostics
        ),
    )


def _insert_coverage(
    connection: sqlite3.Connection,
    *,
    modules: int,
    declarations: int,
    imports: int,
    structures: int,
) -> None:
    """Record complete lexical and unavailable Lean-backed populations."""

    rows = (
        ("modules", "complete", "lake_layout", None, modules, 1),
        ("module_imports", "complete", "lexical_text", None, imports, 1),
        ("declarations", "complete", "lexical_text", None, declarations, 1),
        ("structures", "partial", "lexical_text", "fields unavailable", structures, 0),
        ("binders", "unavailable", "lean_environment", "not extracted by v1", 0, 0),
        (
            "declaration_dependencies",
            "unavailable",
            "lean_environment",
            "not extracted by v1",
            0,
            0,
        ),
        (
            "structure_fields",
            "unavailable",
            "lean_environment",
            "not extracted by v1",
            0,
            0,
        ),
        (
            "lineage",
            "unavailable",
            "lean_environment",
            "not_ingested",
            0,
            0,
        ),
    )
    connection.executemany(
        "INSERT INTO evidence_coverage VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )


def _indexed_source(
    repo_root: Path,
    layout: LeanSourceMap,
    module: str,
    path: Path,
) -> IndexedSource:
    """Capture one module source without retaining its bytes."""

    raw = path.read_bytes()
    owner = root_for_path(path, layout.roots)
    return IndexedSource(
        module=module,
        path=path,
        relative_path=_relative_or_absolute(repo_root, path),
        package=owner.library if owner is not None else "unknown",
        generated=bool(owner.generated) if owner is not None else False,
        sha256=hashlib.sha256(raw).hexdigest(),
        source_bytes=len(raw),
    )


def _build_result_payload(
    snapshot: RepositorySnapshot,
    destination: Path,
    counts: Mapping[str, int],
    *,
    elapsed_seconds: float,
    version_control_visible: bool | None,
    max_index_bytes: int,
) -> dict[str, Any]:
    """Build a canonical public result without exposing table details."""

    warnings = []
    if version_control_visible is True:
        warnings.append(
            {
                "id": "proof_search.index.version_control_visible",
                "message": "generated .ladon/index state is not ignored",
            }
        )
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "build",
        "status": "complete",
        "indexPath": str(destination),
        "repository": str(snapshot.repo_root),
        "indexSchema": PROOF_SEARCH_INDEX_SCHEMA,
        "schemaVersion": PROOF_SEARCH_INDEX_SCHEMA_VERSION,
        "schemaGeneration": PROOF_SEARCH_SCHEMA_GENERATION,
        "generationIdentity": snapshot.generation_identity,
        "freshness": "fresh",
        "evidenceStatus": "lexical-fallback",
        "toolchainIdentity": snapshot.toolchain_identity,
        "configurationFingerprint": snapshot.configuration_fingerprint,
        "sourceFingerprint": snapshot.source_fingerprint,
        "counts": dict(counts),
        "databaseBytes": destination.stat().st_size,
        "limits": {
            "maxIndexBytes": max_index_bytes,
            "maxLexicalTypeBytes": _MAX_LEXICAL_TYPE_BYTES,
            "maxQueryRows": 1000,
        },
        "elapsedSeconds": round(elapsed_seconds, 6),
        "versionControlVisible": version_control_visible,
        "warnings": warnings,
        "nonclaim": _index_nonclaim(),
    }


def _freshness(
    repo_root: Path,
    metadata: Mapping[str, str],
    *,
    verify_sources: bool,
) -> tuple[str, str | None]:
    """Compare a database generation with current source/configuration bytes."""

    if not verify_sources:
        return "unchecked", None
    snapshot = capture_repository_snapshot(repo_root)
    recorded_schema = metadata.get("indexSchema")
    if recorded_schema != PROOF_SEARCH_INDEX_SCHEMA:
        return "incompatible-schema", snapshot.generation_identity
    if metadata.get("schemaGeneration") != PROOF_SEARCH_SCHEMA_GENERATION:
        return "incompatible-schema", snapshot.generation_identity
    if metadata.get("toolchainIdentity") != snapshot.toolchain_identity:
        return "incompatible-toolchain", snapshot.generation_identity
    if metadata.get("configurationFingerprint") != snapshot.configuration_fingerprint:
        return "stale-configuration", snapshot.generation_identity
    if metadata.get("sourceFingerprint") != snapshot.source_fingerprint:
        return "stale-source", snapshot.generation_identity
    return "fresh", snapshot.generation_identity


def _database_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return fixed safe collection counts."""

    tables = (
        "modules",
        "module_imports",
        "declarations",
        "binders",
        "declaration_dependencies",
        "structures",
        "structure_fields",
        "declaration_search",
        "omissions",
        "lineage_closures",
        "lineage_nodes",
        "lineage_edges",
        "lineage_trust",
        "lineage_scc_members",
        "lineage_omissions",
    )
    return {
        table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in tables
    }


def _validate_database(connection: sqlite3.Connection) -> None:
    """Reject an unpublished database that violates SQLite integrity."""

    integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity != "ok":
        raise ProofSearchIndexError(f"SQLite integrity check failed: {integrity}")
    foreign_key_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_rows:
        raise ProofSearchIndexError(
            f"SQLite foreign-key check reported {len(foreign_key_rows)} violation(s)"
        )
    declared = schema_foreign_keys(connection)
    missing = sorted(EXPECTED_FOREIGN_KEYS - declared)
    if missing:
        raise ProofSearchIndexError(f"SQLite schema is missing foreign keys: {missing}")
    index_columns = schema_index_columns(connection)
    malformed_indexes = sorted(
        name
        for name, columns in REQUIRED_LOOKUP_INDEX_COLUMNS.items()
        if index_columns.get(name) != columns
    )
    if malformed_indexes:
        raise ProofSearchIndexError(
            f"SQLite schema has missing or malformed indexes: {malformed_indexes}"
        )


def _metadata(connection: sqlite3.Connection) -> dict[str, str]:
    """Read and validate the private metadata table."""

    rows = connection.execute("SELECT key, value FROM metadata")
    metadata = {str(key): str(value) for key, value in rows}
    if "indexSchema" not in metadata:
        raise ProofSearchIndexError("database has no proof-search schema identity")
    return metadata


def _open_readonly(path: Path) -> sqlite3.Connection:
    """Open one database without permitting accidental mutation."""

    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _resolved_index_path(repo_root: Path, index_path: Path | None) -> Path:
    """Resolve the default or explicit database destination."""

    if index_path is None:
        return default_proof_search_index_path(repo_root)
    return index_path.expanduser().resolve()


def _temporary_database_path(destination: Path) -> Path:
    """Reserve a same-directory path suitable for atomic replacement."""

    descriptor, raw_path = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    return Path(raw_path)


def _durable_replace(temporary: Path, destination: Path) -> None:
    """Sync and atomically publish a complete database."""

    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, destination)
    directory = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _toolchain_identity(repo_root: Path) -> str:
    """Return exact pinned toolchain text or an explicit absence label."""

    path = repo_root / "lean-toolchain"
    if not path.is_file():
        return "unavailable:no-lean-toolchain"
    return path.read_text(encoding="utf-8").strip() or "unavailable:empty-lean-toolchain"


def _configuration_fingerprint(repo_root: Path) -> str:
    """Hash supported Lake/toolchain configuration files."""

    rows = []
    for name in _CONFIGURATION_NAMES:
        path = repo_root / name
        if path.is_file():
            rows.append({"path": name, "sha256": _file_sha256(path)})
    return _stable_digest(rows)


def _file_sha256(path: Path) -> str:
    """Hash a file in bounded chunks."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_digest(value: Any) -> str:
    """Return a deterministic SHA-256 identity for JSON-compatible data."""

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative_or_absolute(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return str(path.resolve())


def _version_control_visible(repo_root: Path, index_path: Path) -> bool | None:
    """Return whether Git would expose generated state, without editing ignores."""

    if not (repo_root / ".git").exists() or not index_path.is_relative_to(repo_root):
        return None
    relative = index_path.relative_to(repo_root).as_posix()
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--", relative],
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.returncode != 0


def _unavailable_status(repo_root: Path, database: Path, reason: str) -> dict[str, Any]:
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "status",
        "status": "unavailable",
        "indexPath": str(database),
        "repository": str(repo_root),
        "reason": reason,
        "freshness": "unavailable",
        "nonclaim": _index_nonclaim(),
    }


def _integer_metadata(metadata: Mapping[str, str], key: str) -> int | None:
    try:
        return int(metadata[key])
    except (KeyError, ValueError):
        return None


def _index_nonclaim() -> str:
    return (
        "The v1 index is navigation evidence. Lexical rows are not Lean-resolved "
        "identities, type matches, proof dependencies, or theorem verdicts."
    )


__all__ = [
    "DEFAULT_INDEX_RELATIVE_PATH",
    "DEFAULT_MAX_INDEX_BYTES",
    "PROOF_SEARCH_RESULT_SCHEMA",
    "SUPPORTED_INDEX_SCOPES",
    "IndexBuildResult",
    "ProofSearchIndexError",
    "build_proof_search_index",
    "capture_repository_snapshot",
    "default_proof_search_index_path",
    "inspect_proof_search_index",
    "query_proof_search_index",
]
