"""Proposed task 1.2 public regressions for evidence-preserving index updates."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ladon import cli
from ladon.proof_search_index import build_proof_search_index, update_proof_search_index


def repo_at(root: Path) -> Path:
    root.mkdir()
    (root / "Base.lean").write_text("def baseValue : Nat := 1\n", encoding="utf-8")
    (root / "Main.lean").write_text(
        "import Base\ntheorem bounded : baseValue ≤ 2 := by omega\n", encoding="utf-8"
    )
    return root


def test_supported_mixed_evidence_update_archives_exact_rows_and_refreshes_lexical_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repo_at(tmp_path / "repo")
    database = build_proof_search_index(repo).index_path
    with sqlite3.connect(database) as db:
        generation = db.execute(
            "SELECT value FROM metadata WHERE key='generationIdentity'"
        ).fetchone()[0]
        declaration_id = db.execute(
            "SELECT id FROM declarations WHERE name='bounded'"
        ).fetchone()[0]
        db.execute(
            "UPDATE declarations SET type_status='lean-rendered', authority='lean_environment', "
            "rendered_type='baseValue ≤ 2', semantic_status='complete', "
            "helper_identity='lean-helper-v1', lean_identity='lean-v1' WHERE id=?",
            (declaration_id,),
        )
        db.execute(
            "INSERT INTO binders VALUES (?,?,?,?,?,?,?,?)",
            (declaration_id, 0, "h", "explicit", "baseValue = 1", 1, "lean_environment", "Eq"),
        )
        db.execute(
            "INSERT INTO proofir_generations VALUES (?,?,?,?,?,?)",
            ("proofir-gen", "{}", 1, 24, 0, "configured"),
        )
        db.execute(
            "INSERT INTO proofir_artifacts VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("artifact-1", "proofir-gen", "evidence.json", "sha256:abc", 24,
             "proof-result", "v1", "cataloged", '{"retained":true}', None),
        )
        db.execute(
            "INSERT INTO lineage_closures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("closure-1", "bounded", "Main", "Main.lean", "plan-1", "semantic-fp",
             str(repo), "source-fp", "config-fp", "lean-v1", "helper-v1", generation,
             "schema-v1", "lean_environment", "complete", 1, "[]", 0, 0, "created-1"),
        )
        db.commit()
        archived_rows = {
            "binders": db.execute("SELECT * FROM binders ORDER BY declaration_id,ordinal").fetchall(),
            "proofir_artifacts": db.execute("SELECT * FROM proofir_artifacts ORDER BY artifact_id").fetchall(),
            "proofir_generations": db.execute("SELECT * FROM proofir_generations ORDER BY generation_id").fetchall(),
            "lineage_closures": db.execute("SELECT * FROM lineage_closures ORDER BY closure_id").fetchall(),
        }

    # Same declaration name, changed proposition; the old Lean rendering must not follow it.
    (repo / "Main.lean").write_text(
        "import Base\ntheorem bounded (h : baseValue = 1) : baseValue ≤ 2 := by omega\n",
        encoding="utf-8",
    )
    with monkeypatch.context() as process_guard:
        process_guard.setattr("subprocess.Popen", lambda *args, **kwargs: pytest.fail("update invoked a process"))
        result = update_proof_search_index(repo)

    assert result.payload["status"] == "complete"
    assert result.payload["preservedSnapshots"]
    snapshot = result.payload["preservedSnapshots"][0]
    snapshot_id = snapshot["snapshotId"]
    archive = database.parent / (database.name + ".history") / f"{snapshot_id}.sqlite"
    assert snapshot_id == hashlib.sha256(archive.read_bytes()).hexdigest()
    with sqlite3.connect(archive) as archived:
        assert archived.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        for table, expected in archived_rows.items():
            assert archived.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall() == expected
    with sqlite3.connect(database) as current:
        current_declaration = current.execute(
            "SELECT type_text,type_status,authority,rendered_type,semantic_status,helper_identity,lean_identity "
            "FROM declarations WHERE name='bounded'"
        ).fetchone()
        assert current_declaration[1:3] == ("lexical-signature", "lexical_text")
        assert current_declaration[4:] == ("unavailable", "", "")
        assert current.execute("SELECT COUNT(*) FROM binders").fetchone() == (0,)
        assert current.execute("SELECT COUNT(*) FROM proofir_artifacts").fetchone() == (0,)
        assert current.execute("SELECT value FROM metadata WHERE key='generationIdentity'").fetchone()[0] != generation
    clean = build_proof_search_index(repo, index_path=tmp_path / "clean.sqlite")
    _assert_declarations_equal(database, clean.index_path)


def test_index_history_is_an_explicit_bounded_cli_view(tmp_path: Path, capsys) -> None:
    repo = repo_at(tmp_path / "repo")
    index = build_proof_search_index(repo).index_path
    # New command contract: JSON inventory identifies exact archive digest and reports truncation.
    assert cli.main([
        "proof-search", "index", "history", "--repo-root", str(repo),
        "--index", str(index), "--limit", "1", "--format", "json",
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "ladon-proof-search-index-history-v1"
    assert result["limit"] == 1
    assert isinstance(result["snapshots"], list)
    assert "truncated" in result


def test_semantic_only_override_in_unchanged_module_is_not_inherited(tmp_path: Path) -> None:
    repo = repo_at(tmp_path / "repo")
    database = build_proof_search_index(repo).index_path
    with sqlite3.connect(database) as db:
        declaration_id = db.execute(
            "SELECT id FROM declarations WHERE name='baseValue'"
        ).fetchone()[0]
        db.execute(
            "UPDATE declarations SET type_status='lean-rendered', authority='lean_environment', "
            "rendered_type='Nat from old Lean environment', semantic_status='complete', "
            "helper_identity='old-helper', lean_identity='old-lean' WHERE id=?",
            (declaration_id,),
        )
        db.commit()
    # Change another module so Base is reused by the public updater.
    (repo / "Main.lean").write_text(
        "import Base\ntheorem newlyNamed : baseValue ≤ 2 := by omega\n", encoding="utf-8"
    )
    result = update_proof_search_index(repo)
    assert result.payload["status"] == "complete"
    clean = build_proof_search_index(repo, index_path=tmp_path / "clean.sqlite")
    _assert_declarations_equal(database, clean.index_path)
    with sqlite3.connect(database) as db:
        row = db.execute(
            "SELECT type_status,authority,rendered_type,semantic_status,helper_identity,lean_identity "
            "FROM declarations WHERE name='baseValue'"
        ).fetchone()
    assert row[0:2] == ("lexical-signature", "lexical_text")
    assert row[3:] == ("unavailable", "", "")


def _assert_declarations_equal(updated: Path, clean: Path) -> None:
    with sqlite3.connect(updated) as left, sqlite3.connect(clean) as right:
        left_rows = left.execute("SELECT * FROM declarations ORDER BY id").fetchall()
        right_rows = right.execute("SELECT * FROM declarations ORDER BY id").fetchall()
    assert left_rows == right_rows
