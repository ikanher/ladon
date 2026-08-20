from __future__ import annotations

from pathlib import Path
from typing import Any

from ladon.analysis.audit_surface import AuditCommand, extract_audit_surface
from ladon.extraction import (
    parse_lean_module,
    parse_text_declarations,
)
from ladon.ir import LeanTextDeclaration
from ladon.lexical_declarations import (
    DECLARATION_BLOCK_NORMALIZATION_VERSION,
    DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION,
)
from ladon.source_index import build_source_index
from ladon.source_index_models import (
    SOURCE_INDEX_FINGERPRINT_VERSION,
    SOURCE_INDEX_SCHEMA,
    SourceIndex,
    SourceIndexResult,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "declaration_audit_integrity"


def _scope_rows() -> dict[str, LeanTextDeclaration]:
    module = parse_lean_module(FIXTURE_ROOT, FIXTURE_ROOT / "Scope.lean")
    return {row.name: row for row in module.declaration_evidence}


def test_scope_aware_candidate_preserves_primary_context() -> None:
    visible = _scope_rows()["visibleResult"]

    assert visible.namespace_stack == ("Fixture",)
    assert visible.section_stack == ("Parameters",)
    assert visible.modifiers == ("protected",)
    assert visible.privacy == "public"
    assert visible.locality == "global"
    assert visible.candidate_name == "Fixture.visibleResult"
    assert visible.candidate_status == "lexical_candidate"


def test_scope_aware_candidate_has_stable_bounded_evidence() -> None:
    visible = _scope_rows()["visibleResult"]

    assert visible.identifier.startswith("ladon.lexical_declaration.")
    assert visible.normalized_block_sha256 is not None
    assert (
        visible.block_normalization_version == DECLARATION_BLOCK_NORMALIZATION_VERSION
    )
    assert visible.source_range["start"]["offset"] == visible.start_offset


def test_scope_aware_candidates_preserve_visibility_and_nested_context() -> None:
    rows = _scope_rows()

    assert rows["hiddenResult"].privacy == "private"
    assert rows["localResult"].locality == "local"
    qualified = rows["qualifiedResult"]
    assert qualified.namespace_stack == ("Fixture", "Nested")
    assert qualified.section_stack == ("Parameters",)
    assert qualified.candidate_name == "Fixture.Nested.qualifiedResult"


def test_scope_aware_candidates_fail_closed_and_ignore_masked_text() -> None:
    rows = _scope_rows()

    assert rows["mutualLeft"].candidate_status == "unresolved"
    assert rows["mutualRight"].candidate_status == "unresolved"
    assert rows["recovered"].candidate_name == "Fixture.recovered"
    assert "Commented" not in {
        segment for row in rows.values() for segment in row.namespace_stack
    }
    assert "StringOnly" not in rows


def test_unsupported_and_unbalanced_scopes_never_guess_candidate_names() -> None:
    unsupported = parse_lean_module(
        FIXTURE_ROOT,
        FIXTURE_ROOT / "UnsupportedScope.lean",
    )
    assert unsupported.declaration_evidence
    assert {row.candidate_status for row in unsupported.declaration_evidence} == {
        "unresolved"
    }
    assert all(row.candidate_name is None for row in unsupported.declaration_evidence)

    unbalanced = parse_text_declarations(
        "namespace Open\n\ndef retained : Nat := 0\n",
        module="Fixture.Unbalanced",
        source_path="Fixture/Unbalanced.lean",
    )
    assert unbalanced[0].candidate_status == "unresolved"
    assert unbalanced[0].candidate_name is None


def test_normalized_block_hash_removes_only_comment_and_whitespace_trivia() -> None:
    compact = parse_text_declarations(
        "def same:Nat:=1\n",
        module="Fixture.One",
        source_path="Fixture/One.lean",
    )[0]
    formatted = parse_text_declarations(
        "def   same : Nat := 1  -- retained as trivia\n",
        module="Fixture.Two",
        source_path="Fixture/Two.lean",
    )[0]
    changed_literal = parse_text_declarations(
        "def same : Nat := 2\n",
        module="Fixture.Three",
        source_path="Fixture/Three.lean",
    )[0]

    assert compact.normalized_block_sha256 == formatted.normalized_block_sha256
    assert compact.normalized_block_sha256 != changed_literal.normalized_block_sha256
    assert compact.candidate_name == "same"
    assert "theorem equivalence" in compact.nonclaim


def test_declaration_blocks_stop_before_following_top_level_commands() -> None:
    commands = (
        "#check (by exact True.intro : True)\n",
        "open scoped BigOperators\n",
        "example : True := by exact True.intro\n",
        "set_option pp.universes true\n",
        "variable (α : Type)\n",
    )

    for command in commands:
        text = "theorem prior : True := by\n  trivial\n" + command
        prior = parse_text_declarations(text)[0]

        assert prior.block_end_offset == text.index(command)


def test_following_audit_command_does_not_supply_prior_proof_mechanisms(
    tmp_path: Path,
) -> None:
    text = (
        "theorem first : True := by\n  trivial\n#check (by exact True.intro : True)\n"
    )
    path = tmp_path / "Root.lean"
    path.write_text(text, encoding="utf-8")

    module = parse_lean_module(tmp_path, path)

    assert module.declaration_evidence[0].block_end_offset == text.index("#check")
    assert [
        (row.mechanism, row.declaration_candidate) for row in module.proof_mechanisms
    ] == [("trivial", "first")]


def test_multiline_attribute_prefix_belongs_to_following_declaration(
    tmp_path: Path,
) -> None:
    text = (
        "theorem first : True := by\n"
        "  trivial\n"
        "@[simp]\n"
        "theorem second : True := by\n"
        "  trivial\n"
    )
    path = tmp_path / "Root.lean"
    path.write_text(text, encoding="utf-8")

    module = parse_lean_module(tmp_path, path)
    first, second = module.declaration_evidence

    assert first.block_end_offset == text.index("@[simp]")
    assert second.block_start_offset == text.index("@[simp]")
    assert [
        (row.kind, row.mechanism, row.declaration_candidate)
        for row in module.proof_mechanisms
    ] == [
        ("tactic-token", "trivial", "first"),
        ("attribute", "simp", "second"),
        ("tactic-token", "trivial", "second"),
    ]


def test_indented_command_local_option_remains_inside_declaration(
    tmp_path: Path,
) -> None:
    text = (
        "theorem kept : True := by\n"
        "  set_option pp.universes true in\n"
        "    exact True.intro\n"
    )
    path = tmp_path / "Root.lean"
    path.write_text(text, encoding="utf-8")

    module = parse_lean_module(tmp_path, path)

    assert module.declaration_evidence[0].block_end_offset == len(text)
    assert [
        (row.mechanism, row.declaration_candidate) for row in module.proof_mechanisms
    ] == [("exact", "kept")]


def test_unicode_subscript_and_escaped_names_are_lexical_rows() -> None:
    text = (
        "namespace Δ\n"
        "theorem bifrRawTModel_le_eight_on_box₁ : True := by trivial\n"
        "def «comment/-safe-/name» : Nat := 1\n"
        "end Δ\n"
    )

    rows = parse_text_declarations(text)

    assert [row.name for row in rows] == [
        "bifrRawTModel_le_eight_on_box₁",
        "«comment/-safe-/name»",
    ]
    assert [row.candidate_name for row in rows] == [
        "Δ.bifrRawTModel_le_eight_on_box₁",
        "Δ.«comment/-safe-/name»",
    ]
    assert [text[row.start_offset : row.end_offset] for row in rows] == [
        row.name for row in rows
    ]


def test_escaped_identifier_spelling_is_exact_block_evidence() -> None:
    alpha = parse_text_declarations(
        "def «foo/-alpha-/» : Nat := 1\n",
        module="Fixture.Alpha",
        source_path="Fixture/Alpha.lean",
    )[0]
    beta = parse_text_declarations(
        "def «foo/-beta-/» : Nat := 1\n",
        module="Fixture.Beta",
        source_path="Fixture/Beta.lean",
    )[0]

    assert alpha.name == "«foo/-alpha-/»"
    assert beta.name == "«foo/-beta-/»"
    assert alpha.normalized_block_sha256 != beta.normalized_block_sha256
    assert alpha.normalized_source_shape_sha256 == beta.normalized_source_shape_sha256
    assert DECLARATION_BLOCK_NORMALIZATION_VERSION.endswith("-v2")
    assert DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION.endswith("-v2")


def test_source_shape_normalizes_names_and_literals_without_claiming_exactness() -> (
    None
):
    first = parse_text_declarations(
        "def first : Nat := 1\n",
        module="Fixture.One",
        source_path="Fixture/One.lean",
    )[0]
    second = parse_text_declarations(
        "def second : Nat := 2\n",
        module="Fixture.Two",
        source_path="Fixture/Two.lean",
    )[0]
    changed_structure = parse_text_declarations(
        "def third : Nat := Nat.succ 3\n",
        module="Fixture.Three",
        source_path="Fixture/Three.lean",
    )[0]

    assert first.normalized_block_sha256 != second.normalized_block_sha256
    assert first.normalized_source_shape_sha256 == second.normalized_source_shape_sha256
    assert (
        first.normalized_source_shape_sha256
        != changed_structure.normalized_source_shape_sha256
    )
    assert (
        first.source_shape_normalization_version
        == DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION
    )


def _source_index_fixture(
    tmp_path: Path,
) -> tuple[Path, SourceIndexResult, dict[str, Any]]:
    repo = tmp_path / "repo"
    package = repo / "Pkg"
    package.mkdir(parents=True)
    (repo / "Pkg.lean").write_text("import Pkg.Core\n", encoding="utf-8")
    (package / "Core.lean").write_text(
        "namespace Pkg\ndef core : Nat := 1\nend Pkg\n",
        encoding="utf-8",
    )

    result = build_source_index(repo, use_cache=False)
    payload = result.index.to_payload()
    return repo, result, payload


def test_source_index_v3_round_trips_scope_aware_rows(
    tmp_path: Path,
) -> None:
    repo, result, payload = _source_index_fixture(tmp_path)

    assert payload["schema"] == SOURCE_INDEX_SCHEMA
    assert SOURCE_INDEX_SCHEMA.endswith("-v3")
    assert SOURCE_INDEX_FINGERPRINT_VERSION.endswith("-v4")

    decoded = SourceIndex.from_payload(
        repo,
        payload,
        expected_fingerprint=result.index.fingerprint,
    )
    core = decoded.modules["Pkg.Core"].declaration_evidence[0]
    assert core.candidate_name == "Pkg.core"
    assert core.candidate_status == "lexical_candidate"
    assert core.normalized_source_shape_sha256 is not None
    assert (
        core.source_shape_normalization_version
        == DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION
    )


def test_source_index_pre_shape_row_keeps_shape_unavailable(
    tmp_path: Path,
) -> None:
    repo, result, payload = _source_index_fixture(tmp_path)
    core_payload = next(
        entry for entry in payload["entries"] if entry["module"]["name"] == "Pkg.Core"
    )["module"]
    current = core_payload["declarationEvidence"][0]
    core_payload["declarationEvidence"] = [[*current[:18], *current[20:]]]

    row = (
        SourceIndex.from_payload(
            repo,
            payload,
            expected_fingerprint=result.index.fingerprint,
        )
        .modules["Pkg.Core"]
        .declaration_evidence[0]
    )

    assert row.normalized_block_sha256 is not None
    assert row.normalized_source_shape_sha256 is None
    assert row.source_shape_normalization_version is None


def test_source_index_legacy_row_is_scope_unavailable(tmp_path: Path) -> None:
    repo, result, payload = _source_index_fixture(tmp_path)
    core_payload = next(
        entry for entry in payload["entries"] if entry["module"]["name"] == "Pkg.Core"
    )["module"]
    current = core_payload["declarationEvidence"][0]
    core_payload["declarationEvidence"] = [current[:6]]
    legacy = (
        SourceIndex.from_payload(
            repo,
            payload,
            expected_fingerprint=result.index.fingerprint,
        )
        .modules["Pkg.Core"]
        .declaration_evidence[0]
    )
    assert legacy.identifier.startswith("ladon.lexical_declaration.legacy.")
    assert legacy.candidate_status == "scope_unavailable"
    assert legacy.candidate_name is None


def _audit_fixture_commands() -> tuple[AuditCommand, ...]:
    text = (FIXTURE_ROOT / "Audit.lean").read_text(encoding="utf-8")
    surface = extract_audit_surface(
        "Fixture.Audit",
        "Fixture/Audit.lean",
        text,
        declaration_count=1,
    )
    return surface.commands


def test_multiline_bare_audit_subjects_are_source_spanning() -> None:
    check, axioms, _, _ = _audit_fixture_commands()

    assert (check.status, check.subject) == (
        "lexical",
        "Fixture.visibleResult",
    )
    assert check.source_range.start.line == 1
    assert check.source_range.end.line == 2
    assert (axioms.status, axioms.subject) == (
        "lexical",
        "Fixture.Nested.qualifiedResult",
    )
    assert axioms.source_range.start.line == 4
    assert axioms.source_range.end.line == 5


def test_multiline_expression_is_bounded_structured_unparsed() -> None:
    _, _, expression, _ = _audit_fixture_commands()

    assert expression.status == "unparsed"
    assert expression.subject == "(fun x => x)"
    assert expression.source_range.start.line == 7
    assert expression.source_range.end.line == 9
    assert expression.diagnostics[0].code == ("audit.subject_syntax_unsupported")


def test_multiline_string_subject_stays_unparsed_and_unresolved() -> None:
    commands = _audit_fixture_commands()
    string_subject = commands[3]

    assert string_subject.status == "unparsed"
    assert string_subject.subject == ""
    assert string_subject.source_range.start.line == 11
    assert string_subject.source_range.end.line == 12
    assert string_subject.referenced_declaration is None
    assert len(commands) == 4


def test_same_line_non_bare_audit_subject_is_structured_unparsed() -> None:
    row = extract_audit_surface(
        "Fixture.Audit",
        "Fixture/Audit.lean",
        "#check (Nat → Nat)\n",
        declaration_count=0,
    ).commands[0]

    assert row.status == "unparsed"
    assert row.subject == "(Nat → Nat)"
    assert row.diagnostics[0].code == "audit.subject_syntax_unsupported"
