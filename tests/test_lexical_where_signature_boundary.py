"""Source signatures stop before a same-line structure-style proof body."""

from __future__ import annotations

import sqlite3

from ladon.proof_search_index import (
    build_proof_search_index,
    inspect_proof_search_index,
    update_proof_search_index,
)

SOURCE = (
    "theorem measure_preserving (f : Nat → Nat) : True where\n"
    "  measurable := by trivial\n"
    "  map_eq := by trivial\n"
)


def test_same_line_where_does_not_enter_indexed_type(tmp_path):
    (tmp_path / "Main.lean").write_text(SOURCE, encoding="utf-8")
    index = build_proof_search_index(tmp_path).index_path

    with sqlite3.connect(index) as db:
        type_text, status = db.execute(
            "SELECT type_text, type_status FROM declarations WHERE name = ?",
            ("measure_preserving",),
        ).fetchone()

    assert type_text == "(f : Nat → Nat) : True"
    assert status == "lexical-signature"


def test_prior_where_signature_is_recovered_without_source_edit(tmp_path):
    (tmp_path / "Main.lean").write_text(SOURCE, encoding="utf-8")
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        db.execute(
            "UPDATE metadata SET value=? WHERE key='helperIdentity'",
            ("lexical-navigation-v4;theorem-lineage-v2;proofir-catalog-v3",),
        )
        db.execute(
            "UPDATE declarations SET type_text=?, rendered_type=?, conclusion_text=?",
            ("(f : Nat → Nat) : True where measurable",) * 3,
        )
        db.execute("INSERT INTO declaration_search(declaration_search) VALUES('rebuild')")

    assert inspect_proof_search_index(tmp_path)["freshness"] == "stale-configuration"
    result = update_proof_search_index(tmp_path).payload
    assert result["status"] == "complete"
    assert result["lexicalRecoveryModules"] == 1
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT type_text FROM declarations").fetchone()[0] == (
            "(f : Nat → Nat) : True"
        )
