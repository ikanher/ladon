"""Persistent, scope-aware navigation index for interactive Lean proof work.

Version one deliberately indexes project-owned lexical evidence. Its schema has
places for elaborated binders and declaration dependencies, but empty Lean-backed
collections remain explicitly unavailable until a helper supplies them.

The writer is intentionally transactional: snapshot capture, database population,
metadata insertion, and the final replace are separate observable stages.
Query callers use the compatibility result adapter while newer commands consume
the versioned name-search result surface.
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
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.extraction import parse_import_sites, parse_text_declarations
from ladon.lean_layout import LeanSourceMap, discover_lean_source_map, root_for_path
from ladon.lexical_mask import mask_lean_source
from ladon.proof_search_exact_counts import exact_name_counts, match_summary
from ladon.proof_search_name_query import (
    name_casefold,
    query_name_database,
    semantic_name_segments_v1,
)
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
from ladon.proof_search_storage import database_storage_accounting
from ladon.proof_search_v3_projection import project_v3_catalog
from ladon.proofir_catalog import (
    CatalogArtifact,
    ProofIRCatalogError,
    ProofIRConfig,
    catalog_generation_identity,
    discover_catalog_artifacts,
)
from ladon.proofir_link_observations import insert_manifest_link_observations
from ladon.proofir_validation import catalog_diagnostic_code
from ladon.sqlite_publication import (
    PublicationLock,
    PublicationLockBusy,
    acquire_publication_lock,
    durable_replace,
    publication_lock_status,
    release_publication_lock,
)

PROOF_SEARCH_RESULT_SCHEMA = "ladon-proof-search-index-result-v1"
DEFAULT_INDEX_RELATIVE_PATH = Path(".ladon/index/proof-search.sqlite")
DEFAULT_MAX_INDEX_BYTES = 1024 * 1024 * 1024
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

# The following constants define the public safety envelope for one local index.
# Keeping these values beside the writer makes size and scope decisions auditable.


class ProofSearchIndexError(RuntimeError):
    """A v1 index could not be built, opened, or queried safely."""

    def __init__(
        self,
        message: str,
        *,
        exit_class: str = "invocation",
        code: str = "invalid-invocation",
        remediation: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_class = exit_class
        self.code = code
        self.remediation = remediation
        self.details = dict(details or {})


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
    proofir_config: ProofIRConfig
    proofir_artifacts: tuple[CatalogArtifact, ...]


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
    try:
        proofir_config, proofir_artifacts = discover_catalog_artifacts(root)
    except ProofIRCatalogError as exc:
        raise ProofSearchIndexError(str(exc)) from exc
    configuration = _configuration_fingerprint(root, proofir_config, proofir_artifacts)
    source_fingerprint = _stable_digest([source.identity_payload() for source in sources])
    generation = _stable_digest(
        {
            "schema": PROOF_SEARCH_INDEX_SCHEMA,
            "schemaGeneration": PROOF_SEARCH_SCHEMA_GENERATION,
            "helper": PROOF_SEARCH_HELPER_IDENTITY,
            "toolchain": toolchain,
            "configuration": configuration,
            "proofir": catalog_generation_identity(proofir_config, proofir_artifacts),
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
        proofir_config=proofir_config,
        proofir_artifacts=proofir_artifacts,
    )


def build_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    max_index_bytes: int = DEFAULT_MAX_INDEX_BYTES,
    progress: Callable[[Mapping[str, Any]], None] | None = None,
) -> IndexBuildResult:
    """Build and atomically replace one repository's v1 query index."""

    if max_index_bytes < 64 * 1024:
        raise ProofSearchIndexError("maximum index size must be at least 64 KiB")
    started = time.monotonic()
    root = repo_root.resolve()
    destination = _resolved_index_path(root, index_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = _acquire_build_lock(destination)
    try:
        from ladon.proof_search_history_store import refuse_history_replacement

        refuse_history_replacement(destination)
        _build_progress(progress, "discovery")
        snapshot = capture_repository_snapshot(root)
        temporary = _temporary_database_path(destination)
        try:
            counts = _write_database(
                temporary,
                snapshot,
                max_index_bytes=max_index_bytes,
                **({"progress": progress} if progress is not None else {}),
            )
            if temporary.stat().st_size > max_index_bytes:
                raise _index_storage_limit_error(max_index_bytes)
            if capture_repository_snapshot(root).generation_identity != snapshot.generation_identity:
                raise ProofSearchIndexError(
                    "supported repository inputs changed during index build",
                    exit_class="operational", code="source-changed",
                    remediation="Retry after the source tree stops changing.",
                )
            _build_progress(progress, "publication")
            durable_replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    finally:
        release_publication_lock(lock)
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


def update_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    max_history_bytes: int | None = None,
) -> IndexBuildResult:
    """Refresh a compatible lexical generation without changing the public API."""

    from ladon.proof_search_index_update import update_proof_search_index as update

    return update(repo_root, index_path=index_path, max_history_bytes=max_history_bytes)


def inspect_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    verify_sources: bool = True,
    changed_limit: int = 5,
) -> dict[str, Any]:
    """Return schema, coverage, and optional live freshness evidence."""

    root = repo_root.resolve()
    database = _resolved_index_path(root, index_path)
    if not database.is_file():
        return _unavailable_status(root, database, "index_missing")
    started = time.monotonic()
    if not 0 <= changed_limit <= 1000:
        raise ProofSearchIndexError("changed listing limit must be between 0 and 1000")
    try:
        with _open_readonly(database) as connection:
            metadata = _metadata(connection)
            from ladon.proof_search_history_schema import require_supported_layout

            _require_query_schema(metadata)
            require_supported_layout(connection, verify_integrity=False)
            counts = _database_counts(connection)
            stored_sources = _stored_sources(connection) if verify_sources else {}
            indexes = schema_lookup_indexes(connection)
            index_columns = schema_index_columns(connection)
            query_surfaces = schema_query_surfaces(connection)
            foreign_keys = schema_foreign_keys(connection)
            from ladon.proof_search_history import history_status
            from ladon.proof_search_history_store import read_history

            retained_history = history_status(database, read_history(connection))
    except (OSError, sqlite3.Error, ValueError, ProofSearchIndexError) as exc:
        return _unavailable_status(root, database, f"index_unreadable: {exc}")
    freshness, current_generation, source_changes = _freshness_details(
        root, metadata, stored_sources, verify_sources=verify_sources,
        changed_limit=changed_limit,
    )
    version_control_visible = _version_control_visible(root, database)
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "status",
        "status": "available",
        "indexPath": str(database),
        "buildLock": _build_lock_status(database),
        "repository": str(root),
        "indexSchema": metadata.get("indexSchema"),
        "schemaVersion": _integer_metadata(metadata, "schemaVersion"),
        "schemaGeneration": metadata.get("schemaGeneration"),
        "generationIdentity": metadata.get("generationIdentity"),
        "helperIdentity": metadata.get("helperIdentity"),
        "currentGenerationIdentity": current_generation,
        "freshness": freshness,
        "history": retained_history,
        "currentEvidenceAssociation": "not-established",
        "sourceChanges": source_changes,
        "generationIdentityMeaning": "stored rows in the queried index",
        "currentGenerationIdentityMeaning": "currently observed supported inputs",
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
        "maxIndexBytes": _integer_metadata(metadata, "maxIndexBytes"),
        "storage": database_storage_accounting(database, _open_readonly),
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
    query_mode: str = "all",
    exclusions: Sequence[str] = (),
    min_matched_segments: int = 1,
    freshness: str = "stored",
) -> dict[str, Any]:
    """Run one deterministic bounded metadata query."""

    _validate_query_options(scope, limit, freshness)
    root = repo_root.resolve()
    database = _resolved_index_path(root, index_path)
    if not database.is_file():
        raise ProofSearchIndexError(f"proof-search index does not exist: {database}")
    started = time.monotonic()
    try:
        with _open_readonly(database) as connection:
            metadata = _metadata(connection)
            _require_query_schema(metadata)
            from ladon.proof_search_history_schema import require_supported_layout

            require_supported_layout(connection, verify_integrity=False)
            stored_sources = _stored_sources(connection) if freshness == "verify" else {}
            rows, truncated, selected_module_count, scope_omissions = query_name_database(
                connection,
                text=text,
                scope=scope,
                roots=tuple(roots),
                limit=limit,
                query_mode=query_mode,
                exclusions=tuple(exclusions),
                min_matched_segments=min_matched_segments,
            )
            qualified_exact, basename_exact = exact_name_counts(
                connection, text=text or "", scope=scope, roots=tuple(roots),
                exclusions=tuple(exclusions),
            )
    except sqlite3.Error as exc:
        raise ProofSearchIndexError(
            "proof-search index is incompatible or unreadable; rebuild it before querying: "
            f"{exc}"
        ) from exc
    except ValueError as exc:
        raise ProofSearchIndexError(str(exc)) from exc
    stored_freshness, current_generation, source_changes = _freshness_details(
        root, metadata, stored_sources, verify_sources=freshness == "verify",
        changed_limit=5, scope=scope, roots=roots,
    )
    summary = match_summary(rows, text, qualified_exact, basename_exact)
    return {
        "schema": PROOF_SEARCH_RESULT_SCHEMA,
        "operation": "query",
        "status": "available",
        "indexPath": str(database),
        "generationIdentity": metadata.get("generationIdentity"),
        "freshness": stored_freshness,
        "sourceChanges": source_changes,
        "matchSummary": summary,
        "queryImpact": source_changes.get("queryImpact", "unknown"),
        "generationIdentityMeaning": "stored rows in the queried index",
        "currentGenerationIdentityMeaning": "currently observed supported inputs",
        "freshnessStatus": ("verified-fresh" if stored_freshness == "fresh" else stored_freshness),
        "currentGenerationIdentity": current_generation,
        "evidenceStatus": metadata.get("evidenceStatus", "unknown"),
        "query": _query_metadata(
            text, scope, roots, limit, query_mode, exclusions, min_matched_segments
        ),
        "scope": {
            "kind": scope,
            "roots": list(roots),
            "includedModules": selected_module_count,
            "omissions": scope_omissions,
        },
        "rows": rows,
        "results": rows,
        "returned": len(rows),
        "truncated": truncated,
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _index_nonclaim(),
    }


def _validate_query_options(scope: str, limit: int, freshness: str) -> None:
    if scope not in SUPPORTED_INDEX_SCOPES:
        expected = ", ".join(sorted(SUPPORTED_INDEX_SCOPES))
        raise ProofSearchIndexError(f"unsupported scope {scope!r}; expected {expected}")
    if limit < 1 or limit > 1000:
        raise ProofSearchIndexError("query limit must be between 1 and 1000")
    if freshness not in {"stored", "verify"}:
        raise ProofSearchIndexError("freshness must be stored or verify")


def _query_metadata(
    text: str | None,
    scope: str,
    roots: Sequence[str],
    limit: int,
    mode: str,
    exclusions: Sequence[str],
    minimum: int,
) -> dict[str, Any]:
    terms = semantic_name_segments_v1(text).split() if text else []
    return {
        "text": text,
        "scope": scope,
        "roots": list(roots),
        "limit": limit,
        "mode": mode,
        "exclude": list(exclusions),
        "minMatchedSegments": minimum,
        "rankingPolicy": "generic-token-downweight-v1",
        "queryTerms": terms,
        "downweightedTerms": [
            term
            for term in terms
            if term in {"bound", "path", "le", "eq", "of", "has", "map", "mem"}
        ],
    }


def _write_database(
    path: Path,
    snapshot: RepositorySnapshot,
    *,
    max_index_bytes: int,
    progress: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, int]:
    """Populate a constrained fresh database and return collection counts."""

    try:
        return _write_database_connection(path, snapshot, max_index_bytes, progress)
    except sqlite3.Error as exc:
        if getattr(exc, "sqlite_errorcode", None) == sqlite3.SQLITE_FULL or (
            "database or disk is full" in str(exc).lower()
        ):
            raise _index_storage_limit_error(max_index_bytes) from exc
        raise ProofSearchIndexError(f"SQLite index build failed: {exc}") from exc


def _index_storage_limit_error(max_index_bytes: int) -> ProofSearchIndexError:
    max_index_mib = round(max_index_bytes / (1024 * 1024), 2)
    return ProofSearchIndexError(
        "proof-search index reached its configured limit of "
        f"{max_index_bytes} bytes ({max_index_mib} MiB)",
        exit_class="operational",
        code="index-storage-limit",
        remediation=(
            "Confirm available disk space, then rerun with a larger "
            "--max-index-mib value; the existing published index is unchanged."
        ),
        details={"maxIndexBytes": max_index_bytes, "maxIndexMiB": max_index_mib},
    )


def _write_database_connection(
    path: Path,
    snapshot: RepositorySnapshot,
    max_index_bytes: int,
    progress: Callable[[Mapping[str, Any]], None] | None = None,
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
        for ordinal, source in enumerate(snapshot.sources, 1):
            module_counts = _insert_source(connection, source)
            declaration_count += module_counts[0]
            import_count += module_counts[1]
            structure_count += module_counts[2]
            type_truncation_count += module_counts[3]
            if ordinal % max(1, len(snapshot.sources) // 20) == 0 or ordinal == len(snapshot.sources):
                _build_progress(progress, "extraction", processedModules=ordinal,
                                totalModules=len(snapshot.sources))
        _insert_module_semantic_states(connection, snapshot, declaration_count, import_count)
        _insert_layout_omissions(connection, snapshot.layout)
        _insert_symbol_rows(connection)
        proofir_counts = _insert_proofir_catalog(connection, snapshot)
        _insert_coverage(
            connection,
            modules=len(snapshot.sources),
            declarations=declaration_count,
            imports=import_count,
            structures=structure_count,
        )
        # Tiny fixture databases deliberately retain SQLite's index-first plan;
        # optimize larger populations where statistics can improve joins.
        if declaration_count + import_count + structure_count > 100:
            connection.execute("PRAGMA optimize")
        connection.commit()
        _build_progress(progress, "validation")
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
        "proofirArtifacts": proofir_counts["artifacts"],
        "proofirRelations": proofir_counts["relations"],
        "proofirDiagnostics": proofir_counts["diagnostics"],
        "proofirV3Artifacts": proofir_counts["v3Artifacts"],
    }


def _insert_proofir_catalog(
    connection: sqlite3.Connection,
    snapshot: RepositorySnapshot,
) -> dict[str, int]:
    """Insert one configured ProofIR catalog generation."""

    generation_id = snapshot.generation_identity
    config_json = json.dumps(
        snapshot.proofir_config.identity_payload(),
        sort_keys=True,
        separators=(",", ":"),
    )
    connection.execute(
        """
        INSERT INTO proofir_generations(
            generation_id, config_json, artifact_count, total_bytes, active, status
        ) VALUES (?, ?, ?, ?, 1, ?)
        """,
        (
            generation_id,
            config_json,
            len(snapshot.proofir_artifacts),
            sum(artifact.byte_size for artifact in snapshot.proofir_artifacts),
            "configured" if snapshot.proofir_config.configured else "not-configured",
        ),
    )
    artifact_ids: dict[str, str] = {}
    content_ids: dict[str, str | None] = {}
    file_digests: dict[str, str] = {}
    for artifact in snapshot.proofir_artifacts:
        artifact_id = _insert_catalog_artifact(connection, generation_id, artifact)
        artifact_ids[artifact.relative_path] = artifact_id
        content_ids[artifact.relative_path] = (
            str(artifact.content_artifact_id) if artifact.content_artifact_id is not None else None
        )
        file_digests[artifact.relative_path] = str(artifact.file_digest)
        _insert_catalog_diagnostic(connection, generation_id, artifact, artifact_id)
    relation_count = _insert_catalog_relations(
        connection,
        generation_id,
        snapshot.proofir_config.relationships,
        artifact_ids,
        content_ids,
        file_digests,
    )
    v3_count = project_v3_catalog(connection, snapshot)
    return {
        "artifacts": len(snapshot.proofir_artifacts),
        "relations": relation_count,
        "diagnostics": int(
            sum(
                artifact.state != "cataloged" or bool(artifact.diagnostic)
                for artifact in snapshot.proofir_artifacts
            )
        ),
        "v3Artifacts": v3_count,
    }


def _insert_catalog_artifact(
    connection: sqlite3.Connection, generation_id: str, artifact: CatalogArtifact
) -> str:
    artifact_id = _stable_digest({"generation": generation_id, **artifact.identity_payload()})
    connection.execute(
        "INSERT INTO proofir_artifacts(artifact_id,generation_id,path,sha256,byte_size,artifact_kind,schema_version,state,metadata_json,diagnostic) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            artifact_id,
            generation_id,
            artifact.relative_path,
            artifact.sha256,
            artifact.byte_size,
            artifact.artifact_kind,
            artifact.schema_version,
            artifact.state,
            artifact.metadata_json,
            artifact.diagnostic,
        ),
    )
    return artifact_id


def _insert_catalog_diagnostic(
    connection: sqlite3.Connection, generation_id: str, artifact: CatalogArtifact, artifact_id: str
) -> None:
    if artifact.state == "cataloged" and not artifact.diagnostic:
        return
    reason = artifact.state if artifact.state != "cataloged" else "truncated"
    try:
        structured = json.loads(artifact.diagnostic or "null")
    except json.JSONDecodeError:
        structured = None
    pointer = structured.get("pointer", "/") if isinstance(structured, dict) else "/"
    details = {
        "artifactKind": artifact.artifact_kind,
        "diagnostic": artifact.diagnostic,
        "stage": artifact.validation_stage,
        "code": catalog_diagnostic_code(artifact.state, artifact.diagnostic),
        "pointer": pointer,
        "sourceRecordRetained": True,
        "semanticRowsProjected": False,
        "retained": artifact.state != "malformed",
    }
    connection.execute(
        "INSERT INTO proofir_diagnostics(diagnostic_id,generation_id,artifact_id,kind,subject,reason,details_json) VALUES(?,?,?,?,?,?,?)",
        (
            _stable_digest({"artifact": artifact_id, "reason": reason}),
            generation_id,
            artifact_id,
            "proofir_catalog",
            artifact.relative_path,
            reason,
            json.dumps(details, sort_keys=True, separators=(",", ":")),
        ),
    )


def _insert_catalog_relations(
    connection: sqlite3.Connection,
    generation_id: str,
    relationships: tuple[tuple[str, str, str, str], ...],
    artifact_ids: dict[str, str],
    content_ids: dict[str, str | None],
    file_digests: dict[str, str],
) -> int:
    try:
        return insert_manifest_link_observations(
            connection,
            generation_id,
            relationships,
            artifact_ids,
            content_ids,
            file_digests,
        )
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error


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


def _insert_module_semantic_states(
    connection: sqlite3.Connection,
    snapshot: RepositorySnapshot,
    declaration_count: int,
    import_count: int,
) -> None:
    """Record conservative lexical state for every discovered source module."""

    for source in snapshot.sources:
        connection.execute(
            "INSERT INTO module_semantic_state VALUES (?, ?, '', ?, '', ?, ?, 'lexical', 'semantic extraction not requested', ?, ?)",
            (
                source.module,
                source.sha256,
                snapshot.source_fingerprint,
                PROOF_SEARCH_HELPER_IDENTITY,
                snapshot.toolchain_identity,
                declaration_count,
                import_count,
            ),
        )


def _insert_symbol_rows(connection: sqlite3.Connection) -> None:
    """Materialize unique declaration names as the reverse-query frontier."""

    connection.execute(
        "INSERT OR IGNORE INTO symbols(name,declaration_id,kind,ownership) "
        "SELECT COALESCE(candidate_name,name), id, kind, 'project' FROM declarations"
    )


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
        structure, truncated = _insert_one_declaration(
            connection, source, text, masked, declaration
        )
        structures += int(structure)
        truncations += int(truncated)
    return structures, truncations


def _insert_one_declaration(
    connection: sqlite3.Connection,
    source: IndexedSource,
    text: str,
    masked: str,
    declaration: Any,
) -> tuple[bool, bool]:
    candidate = declaration.candidate_name
    type_text, type_bytes, type_truncated = _lexical_type_text(text, masked, declaration)
    structure_name = candidate if declaration.kind in {"structure", "class"} else None
    connection.execute(
        """
        INSERT INTO declarations(
            id, name, candidate_name, name_casefold, name_segments, namespace, kind, module, package,
            path, line, column_number, start_offset, end_offset,
            block_sha256, type_text, type_text_bytes, type_text_truncated,
            type_status, authority, privacy, locality, structure_name,
            doc_text, rendered_type, conclusion_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            declaration.identifier,
            declaration.name,
            candidate,
            name_casefold(candidate or declaration.name),
            semantic_name_segments_v1(candidate or declaration.name),
            ".".join(declaration.namespace_stack),
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
            "",
            type_text or "",
            type_text or "",
        ),
    )
    if type_truncated:
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
    _insert_search_row(connection, declaration.identifier, candidate or declaration.name, type_text)
    if structure_name is not None:
        connection.execute(
            "INSERT INTO structures VALUES (?, ?, ?, 'lexical_text')",
            (declaration.identifier, structure_name, source.module),
        )
    return structure_name is not None, type_truncated


def _insert_search_row(
    connection: sqlite3.Connection,
    declaration_id: str,
    name: str,
    type_text: str | None,
) -> None:
    """Insert one compact FTS row linked to the declaration's private rowid."""

    connection.execute(
        """
        INSERT INTO declaration_search(
            rowid, candidate_name, name_segments, namespace, module, package,
            doc_text, rendered_type, conclusion_text, type_text
        )
        SELECT rowid, ?, name_segments, namespace, module, package,
            doc_text, rendered_type, conclusion_text, type_text
        FROM declarations WHERE id = ?
        """,
        (name, declaration_id),
    )


def _lexical_type_text(
    text: str,
    masked: str,
    declaration: Any,
) -> tuple[str | None, int, bool]:
    """Return a bounded lexical signature without claiming elaboration."""

    finish = declaration.block_end_offset or declaration.end_offset
    raw_tail = text[declaration.end_offset : finish]
    masked_tail = masked[declaration.end_offset : finish]
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
        "proofirConfigured": str(snapshot.proofir_config.configured).lower(),
        "proofirArtifactCount": str(len(snapshot.proofir_artifacts)),
        "proofirGenerationId": snapshot.generation_identity,
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
    storage = database_storage_accounting(destination, _open_readonly)
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
        "storage": storage,
        "limits": {
            "maxIndexBytes": max_index_bytes,
            "maxLexicalTypeBytes": _MAX_LEXICAL_TYPE_BYTES,
            "maxQueryRows": 1000,
        },
        "build": {"mode": "lexical", "publication": "atomic"},
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
    return _freshness_from_snapshot(capture_repository_snapshot(repo_root), metadata)


def _stored_sources(connection: sqlite3.Connection) -> dict[str, tuple[str, str, str, bool, int]]:
    return {
        str(row[0]): (str(row[1]), str(row[2]), str(row[3]), bool(row[4]), int(row[5]))
        for row in connection.execute(
            "SELECT name,path,source_sha256,package,generated,source_bytes FROM modules"
        )
    }


def _freshness_details(
    repo_root: Path,
    metadata: Mapping[str, str],
    stored_sources: Mapping[str, tuple[str, str, str, bool, int]],
    *,
    verify_sources: bool,
    changed_limit: int,
    scope: str | None = None,
    roots: Sequence[str] = (),
) -> tuple[str, str | None, dict[str, Any]]:
    from ladon.proof_search_freshness import _freshness_details as details

    return details(
        repo_root, metadata, stored_sources, verify_sources=verify_sources,
        changed_limit=changed_limit, scope=scope, roots=roots,
        capture=capture_repository_snapshot,
    )


def _freshness_from_snapshot(
    snapshot: RepositorySnapshot, metadata: Mapping[str, str]
) -> tuple[str, str]:
    from ladon.proof_search_freshness import _freshness_from_snapshot as compare

    return compare(snapshot, metadata)


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
        "proofir_generations",
        "proofir_artifacts",
        "proofir_relations",
        "proofir_diagnostics",
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


def _require_query_schema(metadata: Mapping[str, str]) -> None:
    """Reject stale query layouts before any schema-specific SQL executes."""

    from ladon.proof_search_history_schema import supported_index_schema

    if not supported_index_schema(metadata):
        raise ProofSearchIndexError(
            "proof-search index schema is incompatible; rebuild it before querying"
        )


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
        prefix=f".{destination.name}.{os.getpid()}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    return Path(raw_path)


def _acquire_build_lock(destination: Path) -> PublicationLock:
    """Acquire the shared ownership-safe SQLite publication lock."""

    try:
        return acquire_publication_lock(destination)
    except PublicationLockBusy as error:
        raise ProofSearchIndexError(str(error)) from error


def _build_lock_status(destination: Path) -> dict[str, Any]:
    """Describe shared kernel lock ownership without trusting stale PID text."""

    return publication_lock_status(destination)


def _toolchain_identity(repo_root: Path) -> str:
    """Return exact pinned toolchain text or an explicit absence label."""

    path = repo_root / "lean-toolchain"
    if not path.is_file():
        return "unavailable:no-lean-toolchain"
    return path.read_text(encoding="utf-8").strip() or "unavailable:empty-lean-toolchain"


def _configuration_fingerprint(
    repo_root: Path,
    proofir_config: Any | None = None,
    proofir_artifacts: tuple[CatalogArtifact, ...] = (),
) -> str:
    """Hash supported Lake/toolchain and configured ProofIR inputs."""

    rows = []
    for name in _CONFIGURATION_NAMES:
        path = repo_root / name
        if path.is_file():
            rows.append({"path": name, "sha256": _file_sha256(path)})
    if proofir_config is not None:
        rows.append(
            {
                "path": ".ladon/proofir.json",
                "proofir": catalog_generation_identity(proofir_config, proofir_artifacts),
            }
        )
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


def _build_progress(progress, phase: str, **counts: int) -> None:
    if progress is not None:
        progress({"phase": phase, "status": "running", **counts})
