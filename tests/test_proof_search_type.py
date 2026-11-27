from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def test_type_search_returns_lexical_shortlist_and_diagnostics(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem first : Nat := 1\ntheorem second : Nat := 2\n", encoding="utf-8"
    )
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--limit", "1", "--diagnostic-limit", "1", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-type-text-result-v2"
    assert payload["results"][0]["authority"] == "lexical_shortlist"
    assert "Nat" in payload["results"][0]["typeText"]
    assert payload["freshness"] == "stored"
    assert payload["matched"] >= payload["returned"] == 1
    assert payload["matchedExact"] is True
    assert payload["diagnostics"]


def test_retired_type_alias_fails_before_index_access(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "proof-search", "search", "type", "--repo-root", str(tmp_path),
            "--pattern", "Nat", "--format", "json",
        ]
    )
    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["exitClass"] == "invocation"
    assert diagnostic["migration"] == "use 'search type-text'"


def test_warm_sqlite_shortlist_has_bounded_latency(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        query_type_shortlist(connection, TypeSearchRequest("Nat"))
        started = time.perf_counter()
        for _ in range(10):
            query_type_shortlist(connection, TypeSearchRequest("Nat"))
    assert (time.perf_counter() - started) < 1.0


def test_type_text_verify_includes_index_generation_evidence(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--freshness", "verify", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["freshnessEvidence"]["generationIdentity"]


def test_type_text_module_scope_reports_population_evidence(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--scope", "module", "--root", "Main", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["coverage"]["scope"]["kind"] == "module"
    assert payload["coverage"]["scope"]["modules"] == 1


def test_type_text_reports_field_contributions_and_bounded_omissions(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem first : Nat := 1\ntheorem second : Nat := 2\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    status = main(
        [
            "proof-search",
            "search",
            "type-text",
            "--repo-root",
            str(tmp_path),
            "--pattern",
            "Nat",
            "--limit",
            "1",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    row = payload["results"][0]
    assert row["fieldContributions"]["typeText"]
    assert row["typeTextBytes"] >= 0
    assert payload["coverage"]["fieldContributionCounts"]["typeText"] == 1
    assert payload["coverage"]["shortlistMatchedLowerBound"] >= 2
    assert payload["coverage"]["populationComplete"] is False
    assert payload["omissions"][0]["kind"] == "result-cap"


def test_type_text_matching_is_literal_and_case_consistent(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    for pattern, expected in (("nat", 1), ("%", 0), ("_", 0)):
        status = main(
            [
                "proof-search", "search", "type-text", "--repo-root", str(tmp_path),
                "--pattern", pattern, "--format", "json",
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert status == 0
        assert len(payload["results"]) == expected
        if expected:
            assert payload["results"][0]["fieldContributions"]["typeText"] is True


def test_fragment_tokenizer_preserves_identifiers_primes_quotes_and_operators() -> None:
    from ladon.proof_search_fragments import contains_fragment, tokenize_lean_text

    assert tokenize_lean_text("‖y - a‖ ^ 2") == tokenize_lean_text("‖y-a‖^2")
    assert contains_fragment("ab", "ab")
    assert not contains_fragment("a b", "ab")
    assert contains_fragment('term "a b" + x', '"a b"')
    assert tokenize_lean_text("x' := y") != tokenize_lean_text("x := y")
    assert tokenize_lean_text(":=") != tokenize_lean_text(": =")
    assert tokenize_lean_text("Nat→∃! n") == tokenize_lean_text("Nat → ∃! n")
    assert tokenize_lean_text("∃!") != tokenize_lean_text("∃ !")


def test_tokenizer_preserves_content_and_numeric_boundaries():
    from ladon.proof_search_fragments import contains_fragment, tokenize_lean_text

    assert contains_fragment("x, y", ",")
    assert not contains_fragment("12", "2")
    assert contains_fragment("f ' ' x", "' '")
    assert tokenize_lean_text("«foo bar»") == ("«foo bar»",)
    assert not contains_fragment("«foo bar»", "«foobar»")
    assert not contains_fragment("Nat", "nat")


def test_normalized_fragment_search_conjoins_and_deduplicates_fragments(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem gauss : ‖y - a‖ ^ 2 + s * c / (s + c) = 0 := by sorry\n"
        "theorem split : Measure.pi μ := by sorry\n",
        encoding="utf-8",
    )
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        request = TypeSearchRequest(None, fragments=("‖y-a‖^2", "s*c/(s+c)", "s * c / (s + c)"))
        payload = query_type_shortlist(connection, request)
    assert [row["candidateName"] for row in payload["results"]] == ["gauss"]
    assert payload["results"][0]["fragmentMatches"] == ["‖y-a‖^2", "s*c/(s+c)"]


def test_normalized_fragment_search_ranks_real_conclusions_before_limit(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem Alpha : Nat := 0\ntheorem Zed : Nat := 0\n", encoding="utf-8"
    )
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE declarations SET authority='lean_environment', type_status='lean-rendered', rendered_type='Nat', conclusion_text='Nat' WHERE candidate_name='Zed'")
        connection.execute("UPDATE declarations SET authority='lean_environment', type_status='lean-rendered', rendered_type='Nat', conclusion_text='Other' WHERE candidate_name='Alpha'")
        connection.commit()
        connection.row_factory = sqlite3.Row
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        payload = query_type_shortlist(connection, TypeSearchRequest(None, fragments=("Nat",), limit=1))
    assert payload["results"][0]["candidateName"] == "Zed"
    assert payload["results"][0]["conclusionAvailable"] is True
    assert payload["results"][0]["conclusionMatchCount"] == 1


def test_fragment_ranking_counts_every_conclusion_fragment_before_limit(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem Alpha : Nat := 0\ntheorem Zed : Nat := 0\n", encoding="utf-8"
    )
    database = build_proof_search_index(tmp_path).index_path
    first = "‖y - a‖ ^ 2"
    second = "s * c / (s + c)"
    both = f"{first} + {second}"
    with sqlite3.connect(database) as connection:
        for name, conclusion in (("Alpha", first), ("Zed", both)):
            connection.execute(
                "UPDATE declarations SET authority='lean_environment',type_status='lean-rendered',type_text=?,rendered_type=?,conclusion_text=? WHERE candidate_name=?",
                (both, both, conclusion, name),
            )
        connection.commit()
        connection.row_factory = sqlite3.Row
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        payload = query_type_shortlist(connection, TypeSearchRequest(None, fragments=("‖y-a‖^2", "s*c/(s+c)"), limit=1))
    assert payload["results"][0]["candidateName"] == "Zed"
    assert payload["results"][0]["conclusionMatchCount"] == 2


def test_normalized_signature_fallback_and_literal_contract_remain_distinct(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--fragment", "Nat", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-type-fragment-result-v1"
    row = payload["results"][0]
    assert row["conclusionAvailable"] is False
    assert row["conclusionMatchCount"] == 0
    assert row["fragmentEvidence"][0]["fields"] == ["typeText"]
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "nat", "--format", "json"])
    literal = json.loads(capsys.readouterr().out)
    assert status == 0
    assert literal["schema"] == "ladon-proof-search-type-text-result-v2"


def test_normalized_result_validates_against_its_versioned_schema(tmp_path: Path, capsys) -> None:
    from jsonschema import Draft202012Validator

    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--fragment", "Nat", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    schema_path = Path(__file__).parents[1] / "src/ladon/schemas/ladon-proof-search-type-fragment-result-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def test_normalized_scope_filters_and_portable_field_shapes(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem product : Nat := 0\ntheorem tail : Nat := 0\ntheorem other : Nat := 0\n",
        encoding="utf-8",
    )
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE declarations SET module='Measure.Product', package='mathlib', type_text='AEMeasurable ∂(Measure.pi μ) = ∏ i', rendered_type='AEMeasurable ∂(Measure.pi μ) = ∏ i', conclusion_text='AEMeasurable ∂(Measure.pi μ) = ∏ i' WHERE candidate_name='product'")
        connection.execute("UPDATE declarations SET module='Series.Tail', namespace='Series', package='mathlib', type_text=?, rendered_type=?, conclusion_text=? WHERE candidate_name='tail'", ("dy k x = ∑' else 0",) * 3)
        connection.execute("UPDATE declarations SET module='Other', package='other', type_text='AEMeasurable dy k x =', rendered_type='AEMeasurable dy k x =', conclusion_text='AEMeasurable dy k x =' WHERE candidate_name='other'")
        connection.commit()
        connection.row_factory = sqlite3.Row
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        product = query_type_shortlist(connection, TypeSearchRequest(None, fragments=("AEMeasurable", "∂(Measure.pi μ) = ∏ i"), package="mathlib", module="Measure.Product"))
        tail = query_type_shortlist(connection, TypeSearchRequest(None, fragments=("dy k x =", "∑'", "else 0"), package="mathlib", namespace="Series"))
        omitted = query_type_shortlist(connection, TypeSearchRequest(None, fragments=("AEMeasurable", "dy k x ="), package="mathlib"))
    assert [item["candidateName"] for item in product["results"]] == ["product"]
    assert [item["candidateName"] for item in tail["results"]] == ["tail"]
    assert omitted["results"] == []


def test_fragment_cli_rejects_empty_and_mixed_queries(tmp_path: Path, capsys) -> None:
    for query in (("--fragment", "  "), ("--pattern", "Nat", "--fragment", "Nat")):
        status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), *query, "--format", "json"])
        captured = capsys.readouterr()
        assert status != 0
        assert captured.out == ""


def test_fragment_negative_result_reports_scoped_signature_omissions(tmp_path):
    from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist

    (tmp_path / "Main.lean").write_text("theorem longName : " + "Nat → " * 4000 + "True := by trivial\n")
    (tmp_path / "Other.lean").write_text("axiom short : True\n")
    path = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(path) as connection:
        def search_module(module):
            request = TypeSearchRequest(fragments=("False",), module=module)
            return query_type_shortlist(connection, request)
        partial, complete = search_module("Main"), search_module("Other")
    assert partial["results"] == []
    assert partial["matchedExact"] and not partial["truncated"]
    assert partial["coverage"]["populationComplete"] is False
    assert partial["coverage"]["indexedTypeOmissions"] == {"lexical_type_truncated": 1}
    assert complete["coverage"]["indexedTypeOmissions"] == {}


def test_fragments_can_come_from_different_eligible_fields_of_one_declaration(tmp_path):
    from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist

    (tmp_path / "Main.lean").write_text("axiom key : Nat\n")
    path = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE declarations SET authority='lean_environment',type_status='lean-rendered',"
                           "type_text='NotationOnly',rendered_type='RenderedOnly',conclusion_text='RenderedOnly'")
        result = query_type_shortlist(connection, TypeSearchRequest(fragments=("NotationOnly", "RenderedOnly")))
    row = result["results"][0]
    assert [item["fields"] for item in row["fragmentEvidence"]] == [["typeText"], ["renderedType", "conclusionText"]]
    assert row["conclusionMatchCount"] == 1
