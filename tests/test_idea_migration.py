"""Migration must preserve evidence and recover from publication failures."""

import sqlite3

import pytest
from test_proof_search_index import sample_repository

from ladon.idea_history_schema import HISTORY_TABLES
from ladon.idea_migration import migrate_index
from ladon.proof_search_index import (
    build_proof_search_index,
    capture_repository_snapshot,
    inspect_proof_search_index,
)
from ladon.proof_search_schema import EVIDENCE_INDEX_SCHEMA, EVIDENCE_SCHEMA_GENERATION


def legacy_index(tmp_path):
    repo = sample_repository(tmp_path)
    path = build_proof_search_index(repo).index_path
    with sqlite3.connect(path) as db:
        db.execute("DROP VIEW declaration_idea_dates")
        db.execute("DROP VIEW idea_dates")
        for name in HISTORY_TABLES:
            db.execute(f"DROP TABLE {name}")
        for key, value in {
            "indexSchema": EVIDENCE_INDEX_SCHEMA,
            "schemaGeneration": EVIDENCE_SCHEMA_GENERATION,
            "schemaVersion": "6",
        }.items():
            db.execute("UPDATE metadata SET value=? WHERE key=?", (value, key))
        db.execute("PRAGMA user_version=6")
        db.execute(
            "UPDATE declarations SET authority='lean_environment',semantic_status='checked' WHERE name='baseValue'"
        )
    return repo, path


def test_migration_preserves_evidence_and_generation(tmp_path):
    repo, path = legacy_index(tmp_path)
    before = capture_repository_snapshot(repo).generation_identity
    report = migrate_index(repo, index_path=path)
    assert report["metrics"]["accepted"]
    assert report["metrics"]["queryLoss"]["checked"] > 0
    assert capture_repository_snapshot(repo).generation_identity == before
    assert inspect_proof_search_index(repo, index_path=path)["freshness"] == "fresh"
    with sqlite3.connect(path) as db:
        assert (
            db.execute("SELECT authority FROM declarations WHERE name='baseValue'").fetchone()[0]
            == "lean_environment"
        )
        assert db.execute("PRAGMA user_version").fetchone()[0] == 7
    assert migrate_index(repo, index_path=path)["status"] == "already-current"


def test_failure_before_replace_leaves_original(tmp_path, monkeypatch):
    import ladon.idea_migration as migration

    repo, path = legacy_index(tmp_path)
    before = path.read_bytes()
    monkeypatch.setattr(migration, "compare_databases", lambda *a, **k: {"accepted": False})
    with pytest.raises(Exception, match="preservation"):
        migrate_index(repo, index_path=path)
    assert path.read_bytes() == before


def test_failure_after_replace_is_uncertain(tmp_path, monkeypatch):
    import ladon.idea_migration as migration

    repo, path = legacy_index(tmp_path)
    original = migration.durable_replace

    def broken(temp, destination):
        original(temp, destination)
        raise OSError("directory fsync failed")

    monkeypatch.setattr(migration, "durable_replace", broken)
    with pytest.raises(Exception, match="uncertain"):
        migrate_index(repo, index_path=path)


def test_stored_lineage_query_is_identical(tmp_path):
    from test_theorem_lineage_store import sample_plan

    from ladon.theorem_lineage_cli import _identity
    from ladon.theorem_lineage_query import LineageQuery, query_lineage
    from ladon.theorem_lineage_store import ingest_theorem_lineage

    repo, path = legacy_index(tmp_path)
    snapshot = capture_repository_snapshot(repo)
    status = inspect_proof_search_index(repo, index_path=path)
    identity = _identity(repo, snapshot, status)
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        ingest_theorem_lineage(db, sample_plan(), identity)
        before = query_lineage(db, identity, LineageQuery(theorem="Demo.target", boundary="trust"))
        assert before["status"] == "available"
    report = migrate_index(repo, index_path=path)
    assert report["metrics"]["tables"]["lineage_nodes"]["before"]["rows"] == 3
    status = inspect_proof_search_index(repo, index_path=path)
    after_identity = _identity(repo, snapshot, status)
    assert identity == after_identity
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        after = query_lineage(
            db, after_identity, LineageQuery(theorem="Demo.target", boundary="trust")
        )
    before.pop("elapsedSeconds")
    after.pop("elapsedSeconds")
    assert before == after


def test_locked_and_missing_database_have_cli_diagnostics(tmp_path, capsys):
    from ladon.cli import main
    from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock

    repo, path = legacy_index(tmp_path)
    before = path.read_bytes()
    lock = acquire_publication_lock(path)
    try:
        assert main(["proof-search", "index", "migrate", "--repo-root", str(repo)]) != 0
    finally:
        release_publication_lock(lock)
    assert path.read_bytes() == before
    assert "publication" in capsys.readouterr().err
    missing = tmp_path / "missing.sqlite"
    assert (
        main(
            [
                "proof-search",
                "index",
                "migrate",
                "--repo-root",
                str(repo),
                "--index",
                str(missing),
            ]
        )
        != 0
    )
    assert not missing.exists()
    assert "unable to open database" in capsys.readouterr().err
