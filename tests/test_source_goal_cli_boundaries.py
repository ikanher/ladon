"""New source routes keep reports separate from inputs and parsing separate from Lean."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.proof_search_cli import proof_search_main


def _arguments(repo: Path):
    return [
        "goal", "capture", "--repo-root", str(repo), "--source", "Owner.lean",
        "--module", "Owner", "--line", "2", "--column", "6",
        "--lean-path", "/absent/lean", "--lake-path", "/absent/lake", "--format", "json",
    ]


@pytest.mark.parametrize("name", ["Owner.lean", "lean-toolchain", "report.json"])
def test_source_capture_rejects_output_in_target_before_execution(tmp_path, capsys, name):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Owner.lean").write_text("example : True := by\n  skip\n")
    (repo / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    before = {p.name: p.read_bytes() for p in repo.iterdir()}
    code = proof_search_main([*_arguments(repo), "--output", str(repo / name)])
    streams = capsys.readouterr()
    assert code == 2
    assert streams.out == ""
    assert json.loads(streams.err)["diagnostic"]["code"] == "source-report-destination"
    assert {p.name: p.read_bytes() for p in repo.iterdir()} == before


@pytest.mark.parametrize("ordinal", [-1, 2])
def test_unknown_diagnostic_selection_does_not_guess_a_record(ordinal):
    from ladon.compiler_goal_query import parse_compiler_goal_query

    text = "Owner.lean:3:28: error: Type mismatch\n  True\nhas type\n  Prop\nbut is expected to have type\n  Nat\n"
    if ordinal < 0:
        with pytest.raises(ValueError):
            parse_compiler_goal_query(text, diagnostic_ordinal=ordinal)
    else:
        query = parse_compiler_goal_query(text, diagnostic_ordinal=ordinal)
        assert query["status"] == "unsupported"
        assert query["selected"] is None


def test_text_parser_does_not_append_another_error_to_expected_type():
    from ladon.compiler_goal_query import parse_compiler_goal_query

    text = (
        "Owner.lean:3:28: error: Type mismatch\n  True\nhas type\n  Prop\n"
        "but is expected to have type\n  Nat\n"
        "Owner.lean:4:0: error: unknown identifier 'next'\n"
    )
    query = parse_compiler_goal_query(text)
    assert query["status"] == "parsed"
    assert query["selected"]["expectedType"] == "Nat"


def test_diagnostic_unindented_claim_is_not_an_expected_type():
    from ladon.compiler_goal_query import parse_compiler_goal_query

    query = parse_compiler_goal_query(
        "Owner.lean:3:28: error: Type mismatch\n  True\nhas type\n  Prop\n"
        "but is expected to have type\nThe theorem is true\n"
    )
    assert query["status"] == "unsupported"
    assert query["selected"] is None
