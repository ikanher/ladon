"""Evidence-preserving historical schema migration and catalogue publication."""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

from ladon.idea_history import catalogue_summary, ingest_catalogue
from ladon.idea_history_schema import create_history_schema
from ladon.migration_metrics import compare_databases
from ladon.proof_search_history_schema import require_supported_layout, supported_index_schema
from ladon.proof_search_index import (
    ProofSearchIndexError,
    _metadata,
    default_proof_search_index_path,
)
from ladon.proof_search_schema import (
    EVIDENCE_INDEX_SCHEMA,
    PROOF_SEARCH_INDEX_SCHEMA,
    PROOF_SEARCH_INDEX_SCHEMA_VERSION,
    PROOF_SEARCH_SCHEMA_GENERATION,
)
from ladon.sqlite_publication import (
    acquire_publication_lock,
    durable_replace,
    release_publication_lock,
)

OBSERVATIONS = {
    "declaration_names": "SELECT id,name,module,authority,semantic_status FROM declarations ORDER BY id LIMIT 1000",
    "type_text": "SELECT id,type_text,rendered_type,type_status FROM declarations ORDER BY id LIMIT 1000",
    "dependency_endpoints": "SELECT * FROM declaration_dependencies ORDER BY source,target,kind LIMIT 1000",
    "lineage_identity": "SELECT * FROM lineage_closures ORDER BY closure_id LIMIT 1000",
    "lineage_nodes": "SELECT * FROM lineage_nodes ORDER BY closure_id,name LIMIT 1000",
}


def _read(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def _path(repo, index_path):
    return Path(index_path or default_proof_search_index_path(Path(repo))).resolve()


def _require_owner(db, repo):
    metadata = _metadata(db)
    if metadata.get("repository") != str(Path(repo).resolve()):
        raise ProofSearchIndexError("index belongs to another repository")
    if not supported_index_schema(metadata):
        raise ProofSearchIndexError("unsupported index schema; preserve it and build to a new path")
    require_supported_layout(db)
    return metadata


def _temporary(destination):
    descriptor, filename = tempfile.mkstemp(
        prefix=destination.name + ".ideas-", suffix=".sqlite", dir=destination.parent
    )
    os.close(descriptor)
    return Path(filename)


def _reject_wal(path):
    # Replacing the main file while another process owns a WAL is unsafe.
    # Other Ladon publishers use DELETE journaling and the same publication lock.
    if Path(str(path) + "-wal").exists():
        raise ProofSearchIndexError(
            "active WAL sidecar: close writers and checkpoint before migration"
        )


def migrate_index(repo, *, index_path=None):
    """Migrate v6 to v7 without a source scan, Lean invocation or semantic refresh."""
    path = _path(repo, index_path)
    started = time.monotonic()
    lock = acquire_publication_lock(path)
    temporary = None
    backup = None
    try:
        _reject_wal(path)
        with _read(path) as source:
            metadata = _require_owner(source, repo)
            if metadata["indexSchema"] == PROOF_SEARCH_INDEX_SCHEMA:
                return {"status": "already-current", "indexPath": str(path)}
            if metadata["indexSchema"] != EVIDENCE_INDEX_SCHEMA:
                raise ProofSearchIndexError(
                    "historical migration requires v6; older snapshots remain readable"
                )
            # Unique recovery snapshot: never overwrite an earlier baseline.
            backup = _temporary(path)
            with sqlite3.connect(backup) as saved:
                source.backup(saved)
        with backup.open("rb") as stream:
            os.fsync(stream.fileno())
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        temporary = _temporary(path)
        shutil.copyfile(backup, temporary)
        changes = {
            "indexSchema": PROOF_SEARCH_INDEX_SCHEMA,
            "schemaVersion": str(PROOF_SEARCH_INDEX_SCHEMA_VERSION),
            "schemaGeneration": PROOF_SEARCH_SCHEMA_GENERATION,
        }
        with sqlite3.connect(temporary) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            create_history_schema(db)
            db.executemany(
                "UPDATE metadata SET value=? WHERE key=?", [(v, k) for k, v in changes.items()]
            )
            db.execute(f"PRAGMA user_version={PROOF_SEARCH_INDEX_SCHEMA_VERSION}")
            db.commit()
            require_supported_layout(db)
        metrics = compare_databases(
            backup, temporary, expected_metadata=changes, queries=OBSERVATIONS
        )
        if not metrics["accepted"]:
            raise ProofSearchIndexError(
                f"migration preservation gate failed; recovery snapshot: {backup}"
            )
        _publish(temporary, path, backup)
        return {
            "status": "migrated",
            "indexPath": str(path),
            "backupPath": str(backup),
            "metrics": metrics,
            "elapsedSeconds": time.monotonic() - started,
            "historicalCoverage": {
                "selectedIdeas": 0,
                "note": "Migration does not invent historical attributions.",
            },
        }
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        release_publication_lock(lock)


def _publish(temporary, path, backup=None):
    try:
        durable_replace(temporary, path)
    except OSError as error:
        if not temporary.exists():
            raise ProofSearchIndexError(
                f"publication durability uncertain; inspect destination and recovery snapshot {backup}"
            ) from error
        raise


def sync_ideas(repo, *, index_path=None):
    path = _path(repo, index_path)
    lock = acquire_publication_lock(path)
    temporary = None
    try:
        _reject_wal(path)
        temporary = _temporary(path)
        with _read(path) as source:
            metadata = _require_owner(source, repo)
            if metadata["indexSchema"] != PROOF_SEARCH_INDEX_SCHEMA:
                raise ProofSearchIndexError("run index migrate before ideas-sync")
            with sqlite3.connect(temporary) as target:
                source.backup(target)
        with sqlite3.connect(temporary) as db:
            db.execute("PRAGMA foreign_keys=ON")
            try:
                ingest_catalogue(db, repo)
            except ValueError as error:
                raise ProofSearchIndexError(str(error)) from error
            db.commit()
            require_supported_layout(db)
            result = catalogue_summary(db)
        _publish(temporary, path)
        return {"status": "synchronized", "indexPath": str(path), "historical": result}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        release_publication_lock(lock)


def read_ideas(repo, *, index_path=None, limit=1000):
    from ladon.idea_history import catalogue_digest, load_catalogue

    path = _path(repo, index_path)
    with _read(path) as db:
        _require_owner(db, repo)
        result = catalogue_summary(db, limit=limit)
    try:
        data = load_catalogue(repo)
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error
    stored = result.get("input")
    result["inputStatus"] = (
        ("missing-retained" if stored else "unassessed")
        if data is None
        else ("current" if stored and stored[0] == catalogue_digest(data) else "changed")
    )
    return result
