"""Regression contract for lexical scope recovery and index migration."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ladon.cli import main
from ladon.extraction import parse_text_declarations
from ladon.proof_search_index import (
    build_proof_search_index,
    query_proof_search_index,
    update_proof_search_index,
)
from ladon.proof_search_schema import PRIOR_LEXICAL_HELPER_IDENTITY


def declarations(text: str):
    return parse_text_declarations(text, module="Fixture.Scope", source_path="Scope.lean")


def by_name(text: str):
    return {row.name: row for row in declarations(text)}


def test_modifier_prefixed_section_forms_and_compound_scope_closures() -> None:
    rows = by_name(
        "namespace Real\n"
        "noncomputable section\n"
        "theorem inNoncomputable : True := by trivial\n"
        "end\n"
        "end Real\n"
        "@[expose] public section\n"
        "namespace Outer.Inner\n"
        "theorem inDottedNamespace : True := by trivial\n"
        "end Inner\n"
        "end Outer\n"
        "public meta section\n"
        "section IsInducing\nnamespace IsInducing\n"
        "theorem beforeCompoundEnd : True := by trivial\n"
        "end IsInducing.IsInducing\n"
        "section First\nsection Second\n"
        "theorem beforeCompoundSections : True := by trivial\n"
        "end First.Second\n"
    )
    assert rows["inNoncomputable"].candidate_name == "Real.inNoncomputable"
    assert rows["inDottedNamespace"].candidate_name == "Outer.Inner.inDottedNamespace"
    assert rows["beforeCompoundEnd"].candidate_name == "IsInducing.beforeCompoundEnd"
    assert rows["beforeCompoundSections"].candidate_name == "beforeCompoundSections"
    assert all(row.candidate_status == "lexical_candidate" for row in rows.values())


def test_scope_commands_inside_comments_strings_and_multiline_attributes_are_ignored() -> None:
    rows = by_name(
        '/- namespace Fake\nend Fake -/\n'
        'def text : String := "namespace AlsoFake\\nend AlsoFake"\n'
        "namespace Real\n"
        "@[expose\n] public noncomputable section\n"
        "-- namespace Commented\n"
        "theorem retained : True := by trivial\n"
        "end\nend Real\n"
    )
    assert rows["retained"].candidate_name == "Real.retained"
    assert rows["retained"].namespace_stack == ("Real",)


@pytest.mark.parametrize(
    "text",
    [
        "mystery section\ntheorem unknownModifier : True := by trivial\n",
        "namespace A\nnamespace B\ntheorem mismatch : True := by trivial\nend A.C\n",
        "section\ntheorem anonymous : True := by trivial\nend Named\n",
    ],
)
def test_unknown_modifier_and_mismatched_compound_ends_fail_closed(text: str) -> None:
    rows = declarations(text)
    assert rows
    assert all(row.candidate_name is None for row in rows)
    assert all(row.candidate_status == "unresolved" for row in rows)


def test_noncomputable_namespace_is_rejected_without_losing_later_recovery() -> None:
    rows = by_name(
        "noncomputable namespace Bad\n"
        "theorem uncertain : True := by trivial\n"
        "end Bad\n"
        "namespace Good\n"
        "theorem after : True := by trivial\n"
        "end Good\n"
    )
    assert rows["uncertain"].candidate_status == "unresolved"
    assert rows["uncertain"].candidate_name is None
    # An explicit unknown scope opener makes the file state ambiguous thereafter.
    assert rows["after"].candidate_status == "unresolved"
    assert rows["after"].candidate_name is None


def test_eof_open_section_is_kept_only_without_a_scope_mismatch() -> None:
    safe = declarations(
        "section ClosedIciTopology\n"
        "theorem atEof : True := by trivial\n"
    )[0]
    mismatch = declarations(
        "section ClosedIciTopology\n"
        "theorem beforeMismatch : True := by trivial\n"
        "end Wrong\n"
    )[0]
    assert safe.candidate_name == "atEof"
    assert safe.candidate_status == "lexical_candidate"
    assert mismatch.candidate_name is None
    assert mismatch.candidate_status == "unresolved"


def test_null_candidate_basename_row_is_counted_consistently_with_exact_contribution(
    tmp_path: Path,
) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem wanted : True := by trivial\n", encoding="utf-8"
    )
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        db.execute("UPDATE declarations SET candidate_name=NULL WHERE name='wanted'")
        db.execute("UPDATE declarations SET name='wanted' WHERE name='wanted'")
    result = query_proof_search_index(
        tmp_path, text="wanted", freshness="stored", query_mode="phrase"
    )
    exact_rows = [row for row in result["rows"] if row["ranking"]["contribution"] == "exact"]
    assert result["matchSummary"]["basenameExactMatches"] == len(exact_rows)
    assert result["matchSummary"]["exactMatches"] == len(exact_rows)


@pytest.mark.parametrize(
    "prior_identity",
    [
        "lexical-navigation-v5;theorem-lineage-v2;proofir-catalog-v3",
        "lexical-navigation-v4;theorem-lineage-v2;proofir-catalog-v3",
        PRIOR_LEXICAL_HELPER_IDENTITY,
    ],
)
def test_predecessor_identity_update_archives_evidence_and_is_then_noop(
    tmp_path: Path, prior_identity: str
) -> None:
    (tmp_path / "Main.lean").write_text(
        "namespace Real\nnoncomputable section\n"
        "theorem add_one_le_exp : True := by trivial\nend\nend Real\n",
        encoding="utf-8",
    )
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        declaration_id = db.execute("SELECT id FROM declarations").fetchone()[0]
        db.execute("UPDATE metadata SET value=? WHERE key='helperIdentity'", (prior_identity,))
        db.execute(
            "INSERT INTO binders VALUES(?,?,?,?,?,?,?,?)",
            (declaration_id, 0, "h", "explicit", "True", 1, "lean_environment", "True"),
        )
    updated = update_proof_search_index(tmp_path).payload
    assert updated["status"] == "complete"
    assert updated["sourceChanges"] == {"added": 0, "changed": 0, "removed": 0}
    assert updated["lexicalRecoveryModules"] == 1
    assert updated["preservedSnapshots"]
    archive = index.parent / (index.name + ".history") / updated["preservedSnapshots"][0]["path"]
    with sqlite3.connect(archive) as db:
        assert db.execute("SELECT count(*) FROM binders").fetchone()[0] == 1
        assert db.execute(
            "SELECT value FROM metadata WHERE key='helperIdentity'"
        ).fetchone()[0] == prior_identity
    found = query_proof_search_index(
        tmp_path, text="Real.add_one_le_exp", freshness="stored", query_mode="phrase"
    )
    assert found["rows"][0]["candidateName"] == "Real.add_one_le_exp"
    before = index.read_bytes()
    assert update_proof_search_index(tmp_path).payload["status"] == "unchanged"
    assert index.read_bytes() == before


@pytest.mark.parametrize("prefix", ["public", "private", "meta", "noncomputable", "@[expose] public"])
def test_each_supported_section_prefix_keeps_namespace(prefix):
    rows = declarations(f"namespace A\n{prefix} section\ntheorem t : True := trivial\nend\nend A\n")
    assert rows[0].candidate_name == "A.t"


def test_cli_qualified_name_recovers_after_noncomputable_section(tmp_path, capsys):
    (tmp_path / "Main.lean").write_text(
        "namespace Complex\nnoncomputable section\ntheorem first : True := trivial\nend\nend Complex\n"
        "namespace Real\ntheorem add_one_le_exp : True := trivial\nend Real\n"
    )
    build_proof_search_index(tmp_path)
    code = main(["proof-search", "search", "name", "--repo-root", str(tmp_path),
                 "--text", "Real.add_one_le_exp", "--query-mode", "phrase", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["results"][0]["candidateName"] == "Real.add_one_le_exp"
    assert payload["matchSummary"]["qualifiedExactMatches"] == 1


def test_dots_inside_escaped_namespace_components_do_not_close_extra_frames():
    rows = by_name(
        'namespace «A.B».C\ntheorem nested : True := trivial\n'
        'end C\ntheorem outer : True := trivial\nend «A.B»\n'
        'theorem after : True := trivial\n'
    )
    assert rows['nested'].candidate_name == '«A.B».C.nested'
    assert rows['nested'].namespace_stack == ('«A.B»', 'C')
    assert rows['outer'].candidate_name == '«A.B».outer'
    assert rows['after'].candidate_name == 'after'


def test_eof_does_not_promote_unsafe_mutual_frame():
    rows = declarations('namespace A\nmutual\ndef unknown : Nat := 0\n')
    assert rows[0].candidate_name is None
