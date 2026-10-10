"""Proposed public history lineage and lifecycle regressions for tasks 3.1/4.1/4.3."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from ladon import cli
from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    capture_repository_snapshot,
    inspect_proof_search_index,
    update_proof_search_index,
)
from ladon.theorem_lineage_store import LineageIdentity, ingest_theorem_lineage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_theorem_lineage_store import sample_plan


def seed_archived_lineage(
    tmp_path: Path, *, stale: bool = False,
    index_name: str = "proof-search.sqlite",
):
    repo = tmp_path / "original-project"
    repo.mkdir()
    (repo / "Base.lean").write_text("def baseValue : Nat := 1\n", encoding="utf-8")
    (repo / "Demo.lean").write_text(
        "namespace Demo\ntheorem target : True := True.intro\nend Demo\n", encoding="utf-8"
    )
    index = tmp_path / index_name
    build_proof_search_index(repo, index_path=index)
    snapshot = capture_repository_snapshot(repo)
    status = inspect_proof_search_index(repo, index_path=index)
    identity = LineageIdentity(
        repository=str(repo.resolve()),
        source_fingerprint=("old-source-observation" if stale else snapshot.source_fingerprint),
        configuration_fingerprint=snapshot.configuration_fingerprint,
        toolchain_identity=snapshot.toolchain_identity,
        base_generation_identity=status["generationIdentity"],
        helper_identity="lexical-navigation-v1;theorem-lineage-v1",
        schema_generation=status["schemaGeneration"],
    )
    with sqlite3.connect(index) as db:
        db.execute("PRAGMA foreign_keys=ON")
        ingest_theorem_lineage(db, sample_plan(), identity)
    (repo / "Demo.lean").write_text(
        "namespace Demo\ntheorem replacement : True := True.intro\nend Demo\n", encoding="utf-8"
    )
    update = update_proof_search_index(repo, index_path=index)
    archive_id = update.payload["preservedSnapshots"][0]["snapshotId"]
    archive = index.parent / (index.name + ".history") / f"{archive_id}.sqlite"
    return repo, index, archive_id, archive, update


def run_history_lineage(repo_root: Path, index: Path, snapshot_id: str, *, refresh="never"):
    return cli.main([
        "theorem", "lineage", "Demo.target", "--repo-root", str(repo_root),
        "--index", str(index), "--history", snapshot_id, "--refresh", refresh,
        "--format", "json",
    ])


def test_exact_historical_lineage_survives_missing_live_project(tmp_path: Path, monkeypatch, capsys) -> None:
    repo, index, snapshot_id, _archive, _update = seed_archived_lineage(tmp_path)
    missing_live_root = repo
    moved_repo = tmp_path / "renamed-original-project"
    repo.rename(moved_repo)
    monkeypatch.setattr(
        "ladon.theorem_lineage_cli.plan_theorem_capsule",
        lambda *args, **kwargs: pytest.fail("historical selection attempted Lean planning"),
    )

    code = run_history_lineage(missing_live_root, index, snapshot_id)

    assert code == 0
    result = json.loads(capsys.readouterr().out)
    _assert_historical_result(result, snapshot_id, missing_live_root)


def test_stale_archived_closure_is_not_repaired_from_its_own_identity(tmp_path: Path, capsys) -> None:
    repo, index, snapshot_id, _archive, _update = seed_archived_lineage(tmp_path, stale=True)
    moved_repo = tmp_path / "renamed-original-project"
    repo.rename(moved_repo)

    code = run_history_lineage(repo, index, snapshot_id)

    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["selectionBasis"] == "historical-snapshot"
    assert result["currentAssociation"] == "not-established"
    assert result["freshness"] == "historical"
    assert result["historicalAssociation"] in {"stale-source", "unavailable"}
    assert result["status"] == "unavailable"


def test_historical_lineage_rejects_mutating_refresh_before_writing(tmp_path: Path, capsys) -> None:
    repo, index, snapshot_id, _archive, _update = seed_archived_lineage(tmp_path)
    before = index.read_bytes()

    code = run_history_lineage(repo, index, snapshot_id, refresh="always")

    assert code != 0
    assert index.read_bytes() == before
    captured = capsys.readouterr()
    assert "cannot" in captured.err.lower() or "reject" in captured.err.lower()


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_registered_archive_damage_blocks_next_update_without_replacing_active(
    tmp_path: Path, damage: str
) -> None:
    repo, index, _snapshot_id, archive, _update = seed_archived_lineage(tmp_path)
    if damage == "missing":
        archive.unlink()
    else:
        archive.write_bytes(b"substituted archive")
    before = index.read_bytes()
    (repo / "Base.lean").write_text("def baseValue : Nat := 2\n", encoding="utf-8")

    with pytest.raises(ProofSearchIndexError):
        update_proof_search_index(repo, index_path=index)

    assert index.read_bytes() == before


def test_build_refuses_to_replace_history_owner_and_prune_protects_it(tmp_path: Path) -> None:
    repo, index, _snapshot_id, _archive, _update = seed_archived_lineage(
        tmp_path, index_name="proof-search.experimental.sqlite"
    )
    before = index.read_bytes()
    with pytest.raises(ProofSearchIndexError):
        build_proof_search_index(repo, index_path=index)
    assert index.read_bytes() == before


def test_prune_protects_history_owning_active_index(tmp_path: Path) -> None:
    repo, index, _snapshot_id, archive, _update = seed_archived_lineage(
        tmp_path, index_name="proof-search.experimental.sqlite"
    )
    from ladon.proof_search_lifecycle import preview_prune

    preview = preview_prune(
        repo, directory=index.parent, selected=(index.name,)
    )
    owned = next(row for row in preview["rows"] if row["name"] == index.name)
    assert owned["classification"] == "protected"
    assert "history" in owned["reason"]
    assert archive.is_file()


def _assert_historical_result(result, snapshot_id, missing_live_root):
    assert result["status"] == "available"
    assert result["theorem"] == "Demo.target"
    assert result["closureId"]
    assert result["selectionBasis"] == "historical-snapshot"
    assert result["currentAssociation"] == "not-established"
    assert result["freshness"] == "historical"
    assert result["historicalAssociation"] == "fresh"
    assert result["snapshotId"] == snapshot_id
    assert result["originalObservation"]["repository"] == str(missing_live_root.resolve())
