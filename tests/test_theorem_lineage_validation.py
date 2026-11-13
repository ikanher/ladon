"""Live lineage validation must be cheap without weakening evidence identity."""
import json
import sqlite3
from dataclasses import replace
from types import SimpleNamespace

import pytest
from test_proof_search_index import sample_repository
from test_theorem_lineage_store import sample_plan

import ladon.proof_search_index as index_api
import ladon.theorem_lineage_cli as cli
from ladon.theorem_cli import build_theorem_parser
from ladon.theorem_lineage_store import ingest_theorem_lineage


@pytest.fixture
def stored(tmp_path):
    repo = sample_repository(tmp_path)
    built = index_api.build_proof_search_index(repo)
    snapshot = index_api.capture_repository_snapshot(repo)
    with sqlite3.connect(built.index_path) as connection:
        identity = cli._identity(repo, snapshot, index_api._metadata(connection))
        ingest_theorem_lineage(connection, sample_plan(), identity)
        connection.execute("PRAGMA journal_mode=WAL")
    args = build_theorem_parser().parse_args(["lineage", "Demo.target", "--refresh", "never"])
    args.repo_root = str(repo)
    args.output = str(tmp_path / "result.json")
    return repo, built.index_path, snapshot, args


def run(args):
    code = cli.run_lineage_command(args)
    return code, json.loads(open(args.output).read())


def forbid(*_args, **_kwargs):
    pytest.fail("stored lookup called comprehensive diagnostics or source capture")


def test_absent_closure_needs_no_source_capture(stored, monkeypatch):
    _repo, _index, _snapshot, args = stored
    args.theorem = "Demo.absent"
    monkeypatch.setattr(cli, "capture_repository_snapshot", forbid)
    code, result = run(args)
    assert code != 0
    assert result["reason"] == "not_ingested"
    assert result["refresh"]["performed"] is False


def test_present_closure_skips_diagnostics_and_captures_twice(stored, monkeypatch):
    _repo, _index, snapshot, args = stored
    calls = []
    monkeypatch.setattr(index_api, "_database_counts", forbid)
    monkeypatch.setattr(index_api, "database_storage_accounting", forbid)
    def capture(_repo):
        calls.append(True)
        return snapshot
    monkeypatch.setattr(cli, "capture_repository_snapshot", capture)
    code, result = run(args)
    assert code == 0
    assert result["authority"] == "lean_environment"
    assert result["freshness"] == "fresh"
    assert len(calls) == 2


def test_unstable_validation_cannot_be_replaced_by_a_third_snapshot(stored, monkeypatch):
    _repo, _index, snapshot, args = stored
    observations = iter([snapshot, replace(snapshot, generation_identity="changed"), snapshot])
    monkeypatch.setattr(cli, "capture_repository_snapshot", lambda _: next(observations))
    code, result = run(args)
    assert code != 0
    assert result["reason"] == "unstable-source"


@pytest.mark.parametrize("field,reason", [
    ("source_fingerprint", "stale-source"),
    ("configuration_fingerprint", "stale-configuration"),
    ("toolchain_identity", "stale-toolchain"),
])
def test_stale_identity_fails_closed(stored, monkeypatch, field, reason):
    _repo, _index, snapshot, args = stored
    changed = replace(snapshot, **{field: "changed"}, generation_identity="changed")
    monkeypatch.setattr(cli, "capture_repository_snapshot", lambda _: changed)
    code, result = run(args)
    assert code != 0
    assert result["reason"] == reason


def test_concurrent_publication_does_not_mix_read_generations(stored, monkeypatch):
    _repo, index, snapshot, args = stored
    calls = []
    def capture(_repo):
        calls.append(True)
        if len(calls) == 2:
            with sqlite3.connect(index) as writer:
                writer.execute("UPDATE metadata SET value='new' WHERE key='generationIdentity'")
                writer.execute("UPDATE lineage_closures SET active=0")
        return snapshot
    monkeypatch.setattr(cli, "capture_repository_snapshot", capture)
    code, result = run(args)
    assert code == 0
    assert result["status"] == "available"
    code, result = run(args)
    assert code != 0
    assert result["reason"] == "not_ingested"


def test_refresh_missing_can_ingest_after_read_preflight(stored, monkeypatch):
    _repo, index, _snapshot, args = stored
    with sqlite3.connect(index) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("DELETE FROM lineage_closures")
    args.refresh = "missing"
    monkeypatch.setattr(cli, "plan_theorem_capsule", lambda *_a, **_kw: SimpleNamespace(payload=sample_plan()))
    code, result = run(args)
    assert code == 0
    assert result["refresh"]["performed"] is True


@pytest.mark.parametrize("damage", ["missing", "corrupt", "schema", "layout"])
def test_invalid_index_never_becomes_an_empty_database(stored, damage):
    _repo, index, _snapshot, args = stored
    if damage == "missing":
        index.unlink()
    elif damage == "corrupt":
        index.write_bytes(b"not sqlite")
    else:
        with sqlite3.connect(index) as connection:
            if damage == "schema":
                connection.execute("UPDATE metadata SET value='unsupported' WHERE key='schemaGeneration'")
            else:
                connection.execute("DROP TABLE lineage_nodes")
    with pytest.raises((RuntimeError, index_api.ProofSearchIndexError)):
        run(args)
    if damage == "missing":
        assert not index.exists()


@pytest.mark.parametrize("policy", ["always", "stale"])
def test_refresh_preserves_policy_and_rechecks_source(stored, monkeypatch, policy):
    repo, index, _snapshot, args = stored
    args.refresh = policy
    if policy == "stale":
        with sqlite3.connect(index) as connection:
            connection.execute("UPDATE lineage_closures SET source_fingerprint='old'")
    def plan(*_args, **_kwargs):
        (repo / "lean-toolchain").write_text("changed during planning")
        return SimpleNamespace(payload=sample_plan())
    monkeypatch.setattr(cli, "plan_theorem_capsule", plan)
    code, result = run(args)
    assert code != 0
    assert result["reason"] == "unstable-source"
    with sqlite3.connect(index) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lineage_closures").fetchone()[0] == 1


def test_refresh_rejects_index_generation_change_during_planning(stored, monkeypatch):
    _repo, index, _snapshot, args = stored
    args.refresh = "always"
    def plan(*_args, **_kwargs):
        with sqlite3.connect(index) as writer:
            writer.execute("UPDATE metadata SET value='new' WHERE key='generationIdentity'")
        return SimpleNamespace(payload=sample_plan())
    monkeypatch.setattr(cli, "plan_theorem_capsule", plan)
    code, result = run(args)
    assert code != 0
    assert result["reason"] == "stale-identity"


@pytest.mark.parametrize("view", ["summary", "closure", "graph", "routes", "spines", "tree", "bottlenecks"])
def test_all_stored_views_remain_read_only(stored, monkeypatch, view):
    _repo, index, _snapshot, args = stored
    args.view = view
    before = index.read_bytes()
    monkeypatch.setattr(cli, "plan_theorem_capsule", forbid)
    code, result = run(args)
    assert code == 0
    assert result["authority"] == "lean_environment"
    assert result["refresh"]["performed"] is False
    assert index.read_bytes() == before
