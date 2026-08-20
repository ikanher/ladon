from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index, query_proof_search_index
from ladon.proof_search_name_query import name_casefold, semantic_name_segments_v1


def test_shared_name_normalization_handles_namespace_and_camel_case() -> None:
    assert name_casefold("Project.FixedIndexPathExpression") == (
        "project.fixedindexpathexpression"
    )
    assert semantic_name_segments_v1("Project.FixedIndexPathExpression") == (
        "project fixed index path expression"
    )


def test_exact_casefolded_name_is_monotone_and_source_linked(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem fixedIndexPathExpression : True := True.intro\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    exact = query_proof_search_index(tmp_path, text="fixedIndexPathExpression")
    refined = query_proof_search_index(tmp_path, text="fixedIndex")
    assert [row["candidateName"] for row in exact["rows"]] == [
        "fixedIndexPathExpression"
    ]
    assert {
        row["candidateName"] for row in exact["rows"]
    }.issubset({row["candidateName"] for row in refined["rows"]})


def test_segmented_name_terms_find_camel_case_declaration(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem fixedIndexPathExpression : True := True.intro\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    result = query_proof_search_index(tmp_path, text="index path expression")
    assert result["rows"][0]["candidateName"] == "fixedIndexPathExpression"


def test_results_is_canonical_and_exclusions_are_explicit(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem fixedIndexPathExpression : True := True.intro\n"
        "theorem otherIndexPath : True := True.intro\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    result = query_proof_search_index(
        tmp_path,
        text="index path",
        query_mode="any",
        exclusions=("other",),
    )
    assert result["results"] == result["rows"]
    assert result["query"]["mode"] == "any"
    assert result["query"]["exclude"] == ["other"]
    assert [row["candidateName"] for row in result["results"]] == [
        "fixedIndexPathExpression"
    ]


def test_verified_freshness_reports_status_and_stale_source(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem stableName : True := True.intro\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    fresh = query_proof_search_index(tmp_path, text="stableName", freshness="verify")
    assert fresh["freshnessStatus"] == "verified-fresh"
    (tmp_path / "Main.lean").write_text("theorem changedName : True := True.intro\n", encoding="utf-8")
    stale = query_proof_search_index(tmp_path, text="stableName", freshness="verify")
    assert stale["freshness"] == "stale-source"


def test_name_command_has_v2_schema_and_omits_compat_rows(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem commandName : True := True.intro\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "name", "--repo-root", str(tmp_path), "--text", "commandName", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-name-result-v2"
    assert payload["results"]
    assert "rows" not in payload


def test_file_scope_reports_source_only_root_as_omission(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem indexed : True := True.intro\n", encoding="utf-8")
    (tmp_path / "SourceOnly.lean").write_text("-- source-only\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    result = query_proof_search_index(tmp_path, scope="file", roots=("SourceOnly.lean",))
    assert result["rows"] == []
    assert result["scope"]["omissions"] == [{"kind": "file", "subject": "SourceOnly.lean", "reason": "source_not_indexed"}]


def test_name_access_paths_use_folded_btree_and_fts(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem indexedName : True := True.intro\n", encoding="utf-8")
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        exact_plan = connection.execute("EXPLAIN QUERY PLAN SELECT id FROM declarations INDEXED BY idx_declarations_name_casefold WHERE name_casefold = ?", ("indexedname",)).fetchall()
        fts_plan = connection.execute("EXPLAIN QUERY PLAN SELECT rowid FROM declaration_search WHERE declaration_search MATCH ?", ('"indexed"*',)).fetchall()
    assert any("idx_declarations_name_casefold" in str(row) for row in exact_plan)
    assert any("declaration_search" in str(row) for row in fts_plan)
