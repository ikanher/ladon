from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    inspect_proof_search_index,
    update_proof_search_index,
)

PRIOR_HELPER = "lexical-navigation-v3;theorem-lineage-v2;proofir-catalog-v3"


def prior_index(tmp_path: Path, *, retained: bool = False):
    (tmp_path / "Main.lean").write_text("theorem cached (x : Nat) : let a := x; FinalMarker a := by trivial\n")
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        db.execute("UPDATE metadata SET value=? WHERE key='helperIdentity'", (PRIOR_HELPER,))
        db.execute("UPDATE declarations SET type_text='(x : Nat) : let a', rendered_type='(x : Nat) : let a', conclusion_text='(x : Nat) : let a'")
        db.execute("INSERT INTO declaration_search(declaration_search) VALUES('rebuild')")
        if retained:
            identifier = db.execute("SELECT id FROM declarations").fetchone()[0]
            db.execute("INSERT INTO binders VALUES(?,?,?,?,?,?,?,?)", (identifier, 0, "h", "explicit", "True", 1, "lean_environment", "True"))
    return index


def test_prior_extractor_is_stale_and_recovers_without_source_edit(tmp_path: Path) -> None:
    index = prior_index(tmp_path)
    assert inspect_proof_search_index(tmp_path)["freshness"] == "stale-configuration"
    result = update_proof_search_index(tmp_path).payload
    assert result["status"] == "complete"
    assert result["sourceChanges"] == {"added": 0, "changed": 0, "removed": 0}
    assert result["lexicalRecoveryModules"] == result["extractedModules"] == 1
    assert inspect_proof_search_index(tmp_path)["freshness"] == "fresh"
    with sqlite3.connect(index) as db:
        assert "FinalMarker a" in db.execute("SELECT type_text FROM declarations").fetchone()[0]
    before = index.read_bytes()
    assert update_proof_search_index(tmp_path).payload["status"] == "unchanged"
    assert index.read_bytes() == before


def test_extractor_recovery_archives_retained_rows_before_replacement(tmp_path: Path) -> None:
    index = prior_index(tmp_path, retained=True)
    with sqlite3.connect(index) as db:
        expected = db.execute("SELECT * FROM binders").fetchall()
    result = update_proof_search_index(tmp_path).payload
    assert result["status"] == "complete"
    assert len(result["preservedSnapshots"]) == 1
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT * FROM binders").fetchall() == []
    archive = index.parent / (index.name + ".history") / result["preservedSnapshots"][0]["path"]
    with sqlite3.connect(archive) as db:
        assert db.execute("SELECT * FROM binders").fetchall() == expected
        assert db.execute("SELECT value FROM metadata WHERE key='helperIdentity'").fetchone()[0] == PRIOR_HELPER


def test_unknown_helper_is_rejected_without_changing_index(tmp_path: Path) -> None:
    index = prior_index(tmp_path)
    with sqlite3.connect(index) as db:
        db.execute("UPDATE metadata SET value='unknown-extractor' WHERE key='helperIdentity'")
    before = index.read_bytes()
    with pytest.raises(ProofSearchIndexError) as raised:
        update_proof_search_index(tmp_path)
    assert raised.value.code == "full-build-required"
    assert index.read_bytes() == before
    assert not (index.parent / (index.name + ".history")).exists()
