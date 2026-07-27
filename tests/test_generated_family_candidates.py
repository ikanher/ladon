from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from ladon.analysis.generated_family_candidate_models import (
    CANDIDATE_NONCLAIMS,
)
from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    DECLARATION_STEM_VERSION,
    GROUPING_SUFFIX_WIDTH_VERSION,
    CandidateRatio,
)
from ladon.analysis.generated_family_candidates import (
    analyze_generated_family_candidates,
    declaration_stem_v1,
)
from ladon.extraction import parse_lean_module
from ladon.ir import LeanModule, LeanTextDeclaration


SOURCE_FINGERPRINT = "sha256:portable-source"
SCOPE_FINGERPRINT = "sha256:portable-scope"


def lexical_declaration(
    name: str,
    line: int = 1,
    *,
    candidate_name: str | None = None,
    normalized_block_sha256: str | None = None,
) -> LeanTextDeclaration:
    return LeanTextDeclaration(
        name=name,
        kind="theorem",
        line=line,
        column=9,
        start_offset=line * 10,
        end_offset=line * 10 + len(name),
        identifier=f"lexical:{name}:{line}",
        candidate_name=candidate_name,
        candidate_status=(
            "lexical_candidate"
            if candidate_name is not None
            else "unresolved"
        ),
        normalized_block_sha256=normalized_block_sha256,
        block_normalization_version=(
            "declaration-block-token-v1"
            if normalized_block_sha256 is not None
            else None
        ),
    )


def lean_module(
    name: str,
    *,
    imports: tuple[str, ...] = (),
    declarations: tuple[str, ...] = (),
) -> LeanModule:
    return LeanModule(
        name=name,
        path=f"{name.replace('.', '/')}.lean",
        imports=imports,
        declarations=declarations,
        declaration_evidence=tuple(
            lexical_declaration(declaration, index)
            for index, declaration in enumerate(declarations, start=1)
        ),
    )


def numbered_family(
    parent: str,
    suffixes: tuple[int, ...],
    *,
    import_count: int,
    lexical_count: int,
) -> dict[str, LeanModule]:
    rows: dict[str, LeanModule] = {}
    for index, suffix in enumerate(suffixes):
        name = f"{parent}.Cell{suffix}"
        imports = ("Neutral.Data",) if index < import_count else ()
        declarations = (
            (f"sharedRow{suffix}",)
            if index < lexical_count
            else (f"distinct{chr(65 + index)}",)
        )
        rows[name] = lean_module(
            name,
            imports=imports,
            declarations=declarations,
        )
    return rows


def analyze(
    modules: dict[str, LeanModule],
    **kwargs,
):
    return analyze_generated_family_candidates(
        modules,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        **kwargs,
    )


def partition_by_prefix(result, prefix: str):
    return next(
        partition
        for partition in result.partitions
        if partition.sequence.basename_prefix == prefix
    )


def clauses_by_id(partition) -> dict:
    return {clause.identifier: clause for clause in partition.clauses}


def positive_modules(
    suffixes: tuple[int, ...] = (0, 1, 2, 3, 4),
) -> dict[str, LeanModule]:
    return {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            suffixes,
            import_count=len(suffixes),
            lexical_count=len(suffixes),
        ),
    }


def partition_by_parent(result, parent: str):
    return next(
        partition
        for partition in result.partitions
        if partition.sequence.parent == parent
    )


def feature_by_kind(partition, kind: str):
    return next(
        feature
        for feature in partition.features
        if feature.kind == kind
    )


def assert_boundary_members(candidate) -> None:
    assert [member.identifier for member in candidate.members] == [
        f"Neutral.Rows.Cell{index}" for index in range(5)
    ]
    assert [member.population for member in candidate.members] == [
        "target_owned",
        "target_owned",
        "project_generated",
        "target_owned",
        "target_owned",
    ]


def assert_boundary_clauses(candidate) -> None:
    clauses = {row.identifier: row for row in candidate.clauses}
    assert clauses["minimum_member_count"].status == "passed"
    assert (
        clauses["numeric_density"].observed_numerator,
        clauses["numeric_density"].observed_denominator,
    ) == (5, 5)
    assert (
        clauses["common_direct_internal_import"].observed_numerator,
        clauses["common_direct_internal_import"].observed_denominator,
        clauses["common_direct_internal_import"].required_count,
    ) == (4, 5, 4)
    assert (
        clauses["common_lexical_witness"].observed_numerator,
        clauses["common_lexical_witness"].observed_denominator,
        clauses["common_lexical_witness"].required_count,
    ) == (4, 5, 4)
    assert all(row.status == "passed" for row in candidate.clauses)


def assert_boundary_authority(candidate, result) -> None:
    assert candidate.authority.imports == "module_import_graph"
    assert candidate.authority.lexical == "lexical_text"
    assert candidate.authority.conclusion == "ladon_derived_heuristic"
    assert candidate.nonclaims == CANDIDATE_NONCLAIMS
    assert candidate.policy_digest is None
    assert result.candidate_coverage.total_known is True
    assert result.candidate_coverage.total == 1


def test_declaration_stem_v1_has_exact_lexical_boundaries() -> None:
    assert declaration_stem_v1("Ns.rowCell_004'Proof") == (
        "row_Cell_<number>_Proof"
    )
    assert declaration_stem_v1("HTTPServer42") == (
        "HTTP_Server_<number>"
    )
    assert declaration_stem_v1("cell0") == "cell_<number>"
    assert declaration_stem_v1("cell000") == "cell_<number>"
    assert declaration_stem_v1("plain_name") == "plain_name"
    assert declaration_stem_v1("αFoo42") == "α_Foo_<number>"
    assert declaration_stem_v1("βFoo42") == "β_Foo_<number>"
    assert declaration_stem_v1("α₄₂") == "α_<number>"
    assert declaration_stem_v1("'''") is None


def test_explicit_suffix_width_grouping_changes_partition_membership() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **{
            f"Neutral.Rows.Cell{suffix}": lean_module(
                f"Neutral.Rows.Cell{suffix}",
                imports=("Neutral.Data",),
                declarations=(f"sharedRow{suffix}",),
            )
            for suffix in ("1", "2", "01", "02")
        },
    }
    exact = CandidateRatio(1, 1)
    profile = replace(
        BUILTIN_CANDIDATE_PROFILE,
        profile_version="suffix-width-numbered-family-v1",
        grouping_version=GROUPING_SUFFIX_WIDTH_VERSION,
        minimum_members=2,
        minimum_density=exact,
        direct_import_coverage=exact,
        lexical_coverage=exact,
    )

    result = analyze(modules, profile=profile)
    cell_partitions = [
        partition
        for partition in result.partitions
        if partition.sequence.basename_prefix == "Cell"
    ]

    assert len(cell_partitions) == 2
    assert {
        tuple(member.identifier for member in partition.members)
        for partition in cell_partitions
    } == {
        ("Neutral.Rows.Cell01", "Neutral.Rows.Cell02"),
        ("Neutral.Rows.Cell1", "Neutral.Rows.Cell2"),
    }
    assert len(result.candidates) == 2


def test_stems_consume_comment_and_string_safe_declaration_evidence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "Cell0.lean"
    source.write_text(
        (
            '-- theorem fake0 : True := by trivial\n'
            'def message := "theorem fake1 : True"\n'
            "theorem real42 : True := by trivial\n"
        ),
        encoding="utf-8",
    )
    module = parse_lean_module(tmp_path, source)

    assert [row.name for row in module.declaration_evidence] == [
        "message",
        "real42",
    ]
    assert {
        declaration_stem_v1(row.name)
        for row in module.declaration_evidence
    } == {"message", "real_<number>"}


def test_candidate_names_and_block_hashes_remain_distinct_features() -> None:
    modules = candidate_name_block_modules()

    result = analyze(modules)
    partition = partition_by_prefix(result, "Cell")
    selected = next(
        feature
        for feature in partition.features
        if feature.identifier == partition.selected_lexical_feature_id
    )
    block_feature = feature_by_kind(
        partition,
        "normalized_declaration_block_hash",
    )

    assert len(result.candidates) == 1
    assert (
        selected.version,
        selected.value,
        selected.member_count,
    ) == (DECLARATION_STEM_VERSION, "shared_<number>", 4)
    assert (
        block_feature.member_count,
        block_feature.authority,
    ) == (5, "lexical_declaration_block_hash")


def candidate_name_block_modules() -> dict[str, LeanModule]:
    modules = {"Neutral.Data": lean_module("Neutral.Data")}
    for index in range(5):
        name = f"Neutral.Rows.Cell{index}"
        declaration = lexical_declaration(
            f"written{chr(65 + index)}",
            candidate_name=(
                f"Scope.shared{index}" if index < 4 else None
            ),
            normalized_block_sha256="sha256:shared-block",
        )
        modules[name] = LeanModule(
            name=name,
            path=f"{name.replace('.', '/')}.lean",
            imports=("Neutral.Data",),
            declarations=(declaration.name,),
            declaration_evidence=(declaration,),
        )
    return modules


def test_normalized_block_hash_alone_cannot_qualify() -> None:
    modules = {"Neutral.Data": lean_module("Neutral.Data")}
    for index in range(5):
        name = f"Neutral.Shape.Cell{index}"
        declaration = lexical_declaration(
            f"distinct{chr(65 + index)}",
            normalized_block_sha256="sha256:shared-shape",
        )
        modules[name] = LeanModule(
            name=name,
            path=f"{name.replace('.', '/')}.lean",
            imports=("Neutral.Data",),
            declarations=(declaration.name,),
            declaration_evidence=(declaration,),
        )

    result = analyze(modules)
    partition = partition_by_parent(result, "Neutral/Shape")

    assert result.candidates == ()
    assert clauses_by_id(partition)[
        "common_lexical_witness"
    ].status == "failed"
    assert any(
        feature.kind == "normalized_declaration_block_hash"
        and feature.member_count == 5
        for feature in partition.features
    )


def test_exact_five_member_four_fifths_boundary_matches() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3, 4),
            import_count=4,
            lexical_count=4,
        ),
    }
    populations = {
        name: (
            "project_generated"
            if name.endswith("Cell2")
            else "target_owned"
        )
        for name in modules
    }

    result = analyze(modules, populations=populations)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert_boundary_members(candidate)
    assert_boundary_clauses(candidate)
    assert_boundary_authority(candidate, result)


def test_full_internal_inventory_is_separate_from_candidate_eligibility() -> None:
    modules = numbered_family(
        "Neutral.Rows",
        (0, 1, 2, 3, 4),
        import_count=5,
        lexical_count=5,
    )

    selected_only = analyze(modules)
    full_inventory = analyze(
        modules,
        internal_module_names={*modules, "Neutral.Data"},
    )

    assert selected_only.candidates == ()
    assert len(full_inventory.candidates) == 1
    assert [
        member.identifier for member in full_inventory.candidates[0].members
    ] == [f"Neutral.Rows.Cell{index}" for index in range(5)]
    assert all(
        "Neutral.Data" in member.direct_internal_imports
        for member in full_inventory.candidates[0].members
    )
    assert full_inventory.internal_inventory_fingerprint is not None
    assert (
        selected_only.analysis_fingerprint
        != full_inventory.analysis_fingerprint
    )


def test_explicit_internal_inventory_rejects_missing_candidate_identity() -> None:
    modules = numbered_family(
        "Neutral.Rows",
        (0, 1, 2, 3),
        import_count=4,
        lexical_count=4,
    )

    with pytest.raises(ValueError, match="omits candidate modules"):
        analyze(
            modules,
            internal_module_names={
                "Neutral.Data",
                "Neutral.Rows.Cell0",
            },
        )
