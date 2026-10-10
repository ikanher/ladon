"""Request-scoped incremental refresh of a compatible lexical index."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from ladon.proof_search_history_schema import (
    clear_retained_projection,
    require_supported_layout,
    semantic_modules,
    supported_index_schema,
)
from ladon.proof_search_history_store import (
    archive_base,
    create_history_catalog,
    enforce_history_budget,
    history_directory,
    read_history,
    validate_history,
)
from ladon.proof_search_index import (
    PROOF_SEARCH_RESULT_SCHEMA,
    IndexBuildResult,
    ProofSearchIndexError,
    _acquire_build_lock,
    _database_counts,
    _index_nonclaim,
    _index_storage_limit_error,
    _insert_coverage,
    _insert_layout_omissions,
    _insert_metadata,
    _insert_module_semantic_states,
    _insert_proofir_catalog,
    _insert_source,
    _insert_source_roots,
    _insert_symbol_rows,
    _integer_metadata,
    _metadata,
    _open_readonly,
    _resolved_index_path,
    _stored_sources,
    _temporary_database_path,
    _validate_database,
    capture_repository_snapshot,
)
from ladon.proof_search_retained import first_retained_evidence_table
from ladon.proof_search_schema import PRIOR_LEXICAL_HELPER_IDENTITY, PROOF_SEARCH_HELPER_IDENTITY
from ladon.sqlite_publication import durable_replace, release_publication_lock


def update_proof_search_index(
    repo_root: Path,
    *,
    index_path: Path | None = None,
    max_history_bytes: int | None = None,
) -> IndexBuildResult:
    """Reuse unchanged lexical modules in an owned, atomically published copy."""

    started = time.monotonic()
    root = repo_root.resolve()
    destination = _resolved_index_path(root, index_path)
    if not destination.is_file():
        raise _full_build_required("index is missing")
    lock = _acquire_build_lock(destination)
    try:
        snapshot = capture_repository_snapshot(root)
        with _open_readonly(destination) as old:
            metadata = _metadata(old)
            _require_compatible_base(metadata, snapshot, root)
            base_generation = metadata.get("generationIdentity")
            old_sources = _stored_sources(old)
            changed, removed = _source_delta(snapshot, old_sources)
            extractor_changed = metadata.get("helperIdentity") != PROOF_SEARCH_HELPER_IDENTITY
            history = read_history(old)
            validate_history(destination, history)
            enforce_history_budget(history_directory(destination), max_history_bytes)
            if not _needs_publication(changed, removed, extractor_changed):
                _ensure_source_stable(root, snapshot)
                return IndexBuildResult({
                    "schema": PROOF_SEARCH_RESULT_SCHEMA, "operation": "update",
                    "status": "unchanged", "indexPath": str(destination),
                    "baseGenerationIdentity": base_generation,
                    "generationIdentity": base_generation,
                    "reusedModules": len(snapshot.sources), "extractedModules": 0,
                    "sourceChanges": {"added": 0, "changed": 0, "removed": 0},
                    "databaseBytes": destination.stat().st_size,
                    "elapsedSeconds": round(time.monotonic() - started, 6),
                })
            require_supported_layout(old)
            retained = first_retained_evidence_table(old)
            preserved = []
            if retained is not None:
                entry = archive_base(old, history_directory(destination), max_history_bytes)
                entry["path"] = Path(entry["path"]).name
                preserved.append(entry)
                history = [row for row in history if row["snapshotId"] != entry["snapshotId"]] + preserved
            recovery_modules = _recovery_modules(old, snapshot, removed, extractor_changed)
            max_index_bytes = _integer_metadata(metadata, "maxIndexBytes")
            if not max_index_bytes:
                raise _full_build_required("base index has no stored size policy")
            counts, temporary_bytes = _publish_copy(
                root, destination, old, snapshot, changed | recovery_modules, removed,
                max_index_bytes, history,
            )
        return IndexBuildResult({
            "schema": PROOF_SEARCH_RESULT_SCHEMA, "operation": "update",
            "status": "complete", "indexPath": str(destination),
            "baseGenerationIdentity": base_generation,
            "generationIdentity": snapshot.generation_identity, "freshness": "fresh",
            "reusedModules": len(snapshot.sources) - len(changed | recovery_modules),
            "extractedModules": len(changed | recovery_modules), "removedModules": len(removed),
            "lexicalRecoveryModules": len(recovery_modules - changed - removed),
            "preservedSnapshots": preserved,
            "historyBytes": sum(row["bytes"] for row in history),
            "currentEvidenceAssociation": "not-established",
            "sourceChanges": {
                "added": len(changed - old_sources.keys()),
                "changed": len(changed & old_sources.keys()),
                "removed": len(removed),
            },
            "counts": counts, "databaseBytes": destination.stat().st_size,
            "temporaryDatabaseBytes": temporary_bytes,
            "maxIndexBytes": max_index_bytes,
            "elapsedSeconds": round(time.monotonic() - started, 6),
            "nonclaim": _index_nonclaim(),
        })
    except sqlite3.Error as exc:
        raise _full_build_required(f"base index is incompatible or unreadable: {exc}") from exc
    finally:
        release_publication_lock(lock)


def _needs_publication(changed, removed, extractor_changed):
    return bool(changed or removed or extractor_changed)


def _recovery_modules(old, snapshot, removed, extractor_changed):
    modules = semantic_modules(old) - removed
    if extractor_changed:
        modules |= {source.module for source in snapshot.sources}
    return modules


def _source_delta(snapshot, old_sources):
    current_sources = {
        source.module: (
            source.relative_path, source.sha256, source.package,
            source.generated, source.source_bytes,
        ) for source in snapshot.sources
    }
    changed = {name for name in current_sources if current_sources[name] != old_sources.get(name)}
    removed = old_sources.keys() - current_sources.keys()
    return changed, removed


def _ensure_source_stable(root: Path, snapshot) -> None:
    observed = capture_repository_snapshot(root)
    if observed.generation_identity != snapshot.generation_identity:
        from ladon.proof_search_freshness import _changed_sources

        changes = _changed_sources(
            _source_identity_rows(observed), _source_identity_rows(snapshot),
        )
        raise ProofSearchIndexError(
            "supported repository inputs changed during index update",
            exit_class="operational", code="source-changed",
            remediation="Retry after concurrent edits settle.",
            details={"sourceChanges": {kind: rows[:20] for kind, rows in changes.items()},
                     "truncated": {kind: len(rows) > 20 for kind, rows in changes.items()}},
        )


def _source_identity_rows(snapshot):
    return {source.module: (source.relative_path, source.sha256, source.package,
                            source.generated, source.source_bytes) for source in snapshot.sources}


def _publish_copy(root, destination, old, snapshot, changed, removed, max_index_bytes, history):
    temporary = _temporary_database_path(destination)
    try:
        counts = _populate_updated_copy(
            temporary, old, snapshot, changed, removed, max_index_bytes, history
        )
        if temporary.stat().st_size > max_index_bytes:
            raise _index_storage_limit_error(max_index_bytes)
        temporary_bytes = temporary.stat().st_size
        _ensure_source_stable(root, snapshot)
        durable_replace(temporary, destination)
        return counts, temporary_bytes
    except OSError as error:
        uncertain = not temporary.exists()
        raise ProofSearchIndexError(
            f"index publication {'durability is uncertain' if uncertain else 'failed'}: {error}",
            exit_class="operational",
            code="publication-uncertain" if uncertain else "publication-failed",
            remediation="Inspect the active generation and retained history before retrying.",
        ) from error
    except sqlite3.Error as exc:
        if "database or disk is full" in str(exc).lower():
            raise _index_storage_limit_error(max_index_bytes) from exc
        raise ProofSearchIndexError(f"SQLite index update failed: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _populate_updated_copy(temporary, old, snapshot, changed, removed, max_index_bytes, history):
    with sqlite3.connect(temporary) as copy:
        old.backup(copy)
    with sqlite3.connect(temporary) as copy:
        copy.execute("PRAGMA foreign_keys = ON")
        copy.execute("PRAGMA synchronous = FULL")
        clear_retained_projection(copy)
        create_history_catalog(copy, history)
        page_size = int(copy.execute("PRAGMA page_size").fetchone()[0])
        copy.execute(f"PRAGMA max_page_count = {max(1, max_index_bytes // page_size)}")
        # FTS5's external-content index has no deletion triggers.
        # Rebuild it after the affected declaration rows change.
        for module in sorted(changed | removed):
            copy.execute(
                "DELETE FROM omissions WHERE kind='declaration' AND subject IN "
                "(SELECT id FROM declarations WHERE module=?)", (module,),
            )
            copy.execute("DELETE FROM modules WHERE name=?", (module,))
        copy.execute("DELETE FROM symbols")
        for source in snapshot.sources:
            if source.module in changed:
                _insert_source(copy, source)
        copy.execute("INSERT INTO declaration_search(declaration_search) VALUES('rebuild')")
        _insert_symbol_rows(copy)
        copy.execute("DELETE FROM module_semantic_state")
        declaration_count = int(copy.execute("SELECT COUNT(*) FROM declarations").fetchone()[0])
        import_count = int(copy.execute("SELECT COUNT(*) FROM module_imports").fetchone()[0])
        structure_count = int(copy.execute("SELECT COUNT(*) FROM structures").fetchone()[0])
        _insert_module_semantic_states(copy, snapshot, declaration_count, import_count)
        copy.execute("DELETE FROM omissions WHERE kind='module'")
        copy.execute("DELETE FROM omissions WHERE kind='declaration' AND subject NOT IN (SELECT id FROM declarations)")
        _insert_layout_omissions(copy, snapshot.layout)
        copy.execute("DELETE FROM evidence_coverage")
        _insert_coverage(
            copy, modules=len(snapshot.sources), declarations=declaration_count,
            imports=import_count, structures=structure_count,
        )
        copy.execute("DELETE FROM source_roots")
        _insert_source_roots(copy, snapshot)
        copy.execute("DELETE FROM proofir_generations")
        _insert_proofir_catalog(copy, snapshot)
        copy.execute("DELETE FROM metadata")
        _insert_metadata(copy, snapshot, max_index_bytes=max_index_bytes)
        copy.execute("PRAGMA user_version = 6")
        copy.execute("PRAGMA optimize")
        copy.commit()
        _validate_database(copy)
        counts = _database_counts(copy)
    return counts


def _require_compatible_base(metadata, snapshot, root: Path) -> None:
    if not supported_index_schema(metadata):
        raise _full_build_required("base index schema is incompatible")
    if metadata.get("repository") != str(root):
        raise _full_build_required("index belongs to another repository")
    if metadata.get("helperIdentity") not in {
        PROOF_SEARCH_HELPER_IDENTITY, PRIOR_LEXICAL_HELPER_IDENTITY,
    }:
        raise _full_build_required("base extractor identity is not supported")
    if metadata.get("toolchainIdentity") != snapshot.toolchain_identity or (
        metadata.get("configurationFingerprint") != snapshot.configuration_fingerprint
    ) or metadata.get("layoutStatus") != snapshot.layout.status:
        raise _full_build_required("toolchain, configuration or source layout changed")


def _full_build_required(reason: str) -> ProofSearchIndexError:
    return ProofSearchIndexError(
        f"incremental update needs an explicit full build: {reason}",
        exit_class="operational", code="full-build-required",
        remediation="Preserve the old index; build with the intended --repo-root and a new --index path.",
    )
