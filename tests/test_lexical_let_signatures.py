from __future__ import annotations

import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index


def repo_at(root: Path, body: str) -> Path:
    root.mkdir(parents=True)
    (root / "Main.lean").write_text(body, encoding="utf-8")
    return root


def declaration_type(index: Path, name: str) -> str | None:
    with sqlite3.connect(index) as db:
        row = db.execute("SELECT type_text FROM declarations WHERE name=?", (name,)).fetchone()
    return row[0] if row else None


def test_consecutive_and_nested_let_initializers_survive_in_lexical_signature(tmp_path: Path) -> None:
    repo = repo_at(
        tmp_path / "repo",
        """theorem consecutive (x : Nat) : let first := x + 1; let second := first + 1; second > x := by
  omega

theorem nested (x : Nat) : let result := (let inner := x + 1; inner + 1); result > x := by
  omega
""",
    )
    index = build_proof_search_index(repo).index_path
    consecutive = declaration_type(index, "consecutive")
    nested = declaration_type(index, "nested")
    assert consecutive is not None and "first := x + 1" in consecutive
    assert "second := first + 1" in consecutive and "second > x" in consecutive
    assert nested is not None and "inner := x + 1" in nested and "result > x" in nested


def test_binder_default_does_not_cut_off_conclusion(tmp_path: Path) -> None:
    repo = repo_at(
        tmp_path / "repo",
        "theorem withDefault (x : Nat := 0) : TargetSymbol x := by\n  exact trivial\n",
    )
    index = build_proof_search_index(repo).index_path
    signature = declaration_type(index, "withDefault")
    assert signature is not None and "TargetSymbol x" in signature


def test_type_text_contains_final_conclusion_and_never_proof_body(tmp_path: Path) -> None:
    repo = repo_at(
        tmp_path / "repo",
        "theorem conclusionOnly (x : Nat) : FinalConclusionSymbol x := by\n  exact ProofBodyOnlySymbol\n",
    )
    index = build_proof_search_index(repo).index_path
    signature = declaration_type(index, "conclusionOnly")
    assert signature is not None and "FinalConclusionSymbol" in signature
    assert "ProofBodyOnlySymbol" not in signature



def test_let_conclusion_is_searchable_through_cli(tmp_path: Path, capsys) -> None:
    import json

    from ladon.cli import main

    repo = repo_at(tmp_path / "repo", "theorem scoped (x : Nat) : let a := x; FinalMarker a := by\n  exact BodyMarker\n")
    build_proof_search_index(repo)
    assert main(["proof-search", "search", "type-text", "--repo-root", str(repo), "--pattern", "FinalMarker", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [row["candidateName"] for row in payload["results"]] == ["scoped"]


def test_masked_assignments_do_not_change_signature_boundary(tmp_path: Path) -> None:
    repo = repo_at(tmp_path / "repo", 'theorem masked : let text := ":= by"; /- := -/ FinalMarker text := by\n  exact BodyMarker\n')
    signature = declaration_type(build_proof_search_index(repo).index_path, "masked")
    assert signature is not None and "FinalMarker text" in signature
    assert "BodyMarker" not in signature


def test_unbalanced_signature_is_unavailable_with_omission(tmp_path: Path) -> None:
    repo = repo_at(tmp_path / "repo", "theorem uncertain (x : Nat : FinalMarker := by\n  exact BodyMarker\n")
    index = build_proof_search_index(repo).index_path
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT type_status, type_text FROM declarations").fetchone() == ("unavailable", None)
        assert db.execute("SELECT reason FROM omissions WHERE kind='declaration'").fetchall() == [("lexical_signature_unavailable",)]


def test_signature_cap_remains_visible(tmp_path: Path) -> None:
    repo = repo_at(tmp_path / "repo", "theorem bounded : " + "LargeMarker " * 2000 + ":= by\n  exact BodyMarker\n")
    index = build_proof_search_index(repo).index_path
    with sqlite3.connect(index) as db:
        text, size, truncated = db.execute("SELECT type_text, type_text_bytes, type_text_truncated FROM declarations").fetchone()
        assert len(text.encode()) <= 16384 < size
        assert truncated == 1 and "BodyMarker" not in text
        assert db.execute("SELECT reason FROM omissions WHERE kind='declaration'").fetchall() == [("lexical_type_truncated",)]
