"""Predicate, incompleteness, determinism, and projection tests."""

from __future__ import annotations

import random
import subprocess

import pytest

from ladon.analysis.generated_family_candidate_profile import (
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    CandidateProfile,
    CandidateRatio,
)
from ladon.ir import LeanModule
from test_generated_family_candidates import (
    analyze,
    clauses_by_id,
    lean_module,
    numbered_family,
    partition_by_parent,
    partition_by_prefix,
)


def test_target_outside_internal_inventory_remains_external_to_predicate() -> None:
    base = numbered_family(
        "Neutral.Rows",
        (0, 1, 2, 3, 4),
        import_count=5,
        lexical_count=5,
    )
    modules = {
        name: LeanModule(
            **{
                **module.__dict__,
                "imports": ("External.Library",),
            }
        )
        for name, module in base.items()
    }

    result = analyze(
        modules,
        internal_module_names={*modules, "Neutral.Data"},
    )
    partition = partition_by_prefix(result, "Cell")

    assert result.candidates == ()
    import_clause = clauses_by_id(partition)["common_direct_internal_import"]
    assert import_clause.status == "failed"
    assert import_clause.observed_numerator == 0


def test_exact_four_fifths_density_boundary_matches() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 4),
            import_count=4,
            lexical_count=4,
        ),
    }

    candidate = analyze(modules).candidates[0]

    assert candidate.sequence.occupied_suffix_values == (0, 1, 2, 4)
    assert candidate.sequence.inclusive_span == 5
    assert candidate.sequence.gap_count == 1
    assert candidate.sequence.gap_ranges == ((3, 3),)
    density = {row.identifier: row for row in candidate.clauses}["numeric_density"]
    assert (
        density.observed_numerator,
        density.observed_denominator,
        density.status,
    ) == (4, 5, "passed")


def test_each_exact_clause_negative_retains_partition_features() -> None:
    modules = _negative_fixture_modules()
    hashes = _negative_fixture_hashes(modules)

    result = analyze(modules, content_hashes=hashes)

    _assert_negative_candidate_members(result)
    _assert_negative_partition_clauses(result)
    _assert_hash_and_ungrouped_features(result)


def _negative_fixture_modules() -> dict[str, LeanModule]:
    modules = {"Neutral.Data": lean_module("Neutral.Data")}
    specifications = (
        ("Neutral.Rows", (0, 1, 2, 3, 4), 4, 4),
        ("Neutral.Count", (0, 1, 2), 3, 3),
        ("Neutral.Sparse", (0, 1, 2, 5), 4, 4),
        ("Neutral.Imports", (0, 1, 2, 3, 4), 3, 5),
        ("Neutral.Lexical", (0, 1, 2, 3, 4), 5, 3),
        ("Neutral.HashOnly", (0, 1, 2, 3, 4), 5, 0),
    )
    for parent, suffixes, imports, lexical in specifications:
        modules.update(
            numbered_family(
                parent,
                suffixes,
                import_count=imports,
                lexical_count=lexical,
            )
        )
    modules["Neutral.Clones.Alpha"] = lean_module("Neutral.Clones.Alpha")
    modules["Neutral.Clones.Beta"] = lean_module("Neutral.Clones.Beta")
    modules["Neutral.GeneratedThing"] = lean_module("Neutral.GeneratedThing")
    return modules


def _negative_fixture_hashes(
    modules: dict[str, LeanModule],
) -> dict[str, str]:
    return {
        name: "sha256:identical"
        for name in modules
        if name.startswith(("Neutral.HashOnly.", "Neutral.Clones."))
    }


def _assert_negative_candidate_members(result) -> None:
    member_sets = [
        tuple(member.identifier for member in candidate.members)
        for candidate in result.candidates
    ]
    assert member_sets == [tuple(f"Neutral.Rows.Cell{index}" for index in range(5))]


def _assert_negative_partition_clauses(result) -> None:
    count = partition_by_parent(result, "Neutral/Count")
    sparse = partition_by_parent(result, "Neutral/Sparse")
    imports = partition_by_parent(result, "Neutral/Imports")
    lexical = partition_by_parent(result, "Neutral/Lexical")
    assert clauses_by_id(count)["minimum_member_count"].status == "failed"
    assert clauses_by_id(sparse)["numeric_density"].status == "failed"
    assert clauses_by_id(imports)["common_direct_internal_import"].status == "failed"
    assert clauses_by_id(lexical)["common_lexical_witness"].status == "failed"


def _assert_hash_and_ungrouped_features(result) -> None:
    hash_only = partition_by_parent(result, "Neutral/HashOnly")
    assert clauses_by_id(hash_only)["common_lexical_witness"].status == "failed"
    assert {feature.kind for feature in hash_only.features} >= {
        "exact_source_hash",
        "direct_internal_import",
    }
    assert {member.identifier for member in result.ungrouped_members} >= {
        "Neutral.Clones.Alpha",
        "Neutral.Clones.Beta",
        "Neutral.GeneratedThing",
    }
    serialized = {row["id"]: row for row in result.to_dict()["ungroupedMembers"]}
    assert serialized["Neutral.Clones.Alpha"] == {
        "id": "Neutral.Clones.Alpha",
        "module": "Neutral.Clones.Alpha",
        "path": "Neutral/Clones/Alpha.lean",
        "population": "unclassified",
        "status": "not_partitioned",
        "reason": "final_segment_has_no_decimal_suffix",
    }


@pytest.mark.parametrize(
    "incomplete_keyword",
    [
        "incomplete_structural_modules",
        "incomplete_import_modules",
        "incomplete_lexical_modules",
    ],
)
def test_required_unknown_evidence_is_unavailable_not_false(
    incomplete_keyword: str,
) -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3, 4),
            import_count=5,
            lexical_count=5,
        ),
    }
    kwargs = {incomplete_keyword: {"Neutral.Rows.Cell4"}}

    result = analyze(modules, **kwargs)
    partition = partition_by_prefix(result, "Cell")
    clauses = clauses_by_id(partition)

    assert result.candidates == ()
    assert partition.evaluation_status == "unavailable"
    assert clauses["required_evidence_complete"].status == "unavailable"
    affected_clause = {
        "incomplete_structural_modules": "numeric_density",
        "incomplete_import_modules": "common_direct_internal_import",
        "incomplete_lexical_modules": "common_lexical_witness",
    }[incomplete_keyword]
    assert clauses[affected_clause].status == "unavailable"
    assert result.candidate_coverage.total_known is False
    assert result.candidate_coverage.total is None
    assert result.candidate_coverage.omitted is None


def test_unknown_evidence_dominates_observed_clause_failure() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2),
            import_count=3,
            lexical_count=3,
        ),
    }

    complete_result = analyze(modules)
    result = analyze(
        modules,
        incomplete_lexical_modules={"Neutral.Rows.Cell2"},
    )
    complete_partition = partition_by_prefix(complete_result, "Cell")
    partition = partition_by_prefix(result, "Cell")

    assert complete_partition.evaluation_status == "non_match"
    assert partition.evaluation_status == "unavailable"
    assert complete_result.analysis_fingerprint != result.analysis_fingerprint
    assert clauses_by_id(partition)["minimum_member_count"].status == "failed"
    assert clauses_by_id(partition)["common_lexical_witness"].status == "unavailable"


def test_command_skeleton_is_a_separate_supported_lexical_witness() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3, 4),
            import_count=5,
            lexical_count=0,
        ),
    }
    skeletons = {
        f"Neutral.Rows.Cell{index}": ("theorem IDENT : TYPE := by TACTIC",)
        for index in range(4)
    }

    result = analyze(modules, command_skeletons=skeletons)
    partition = partition_by_prefix(result, "Cell")
    selected = next(
        feature
        for feature in partition.features
        if feature.identifier == partition.selected_lexical_feature_id
    )

    assert len(result.candidates) == 1
    assert selected.kind == "command_skeleton"
    assert selected.version == COMMAND_SKELETON_VERSION
    assert selected.member_count == 4
    assert all(
        feature.version != DECLARATION_STEM_VERSION or feature.member_count < 4
        for feature in partition.features
    )


def test_discovery_order_and_zero_padding_have_stable_predicate_evidence() -> None:
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3, 4),
            import_count=5,
            lexical_count=5,
        ),
    }
    items = list(modules.items())
    random.Random(42).shuffle(items)

    first = analyze(modules)
    second = analyze(dict(items))

    assert first.to_dict() == second.to_dict()

    padded = {
        name.replace("Cell0", "Cell000"): LeanModule(
            **{
                **module.__dict__,
                "name": module.name.replace("Cell0", "Cell000"),
                "path": module.path.replace("Cell0", "Cell000"),
            }
        )
        for name, module in modules.items()
    }
    padded_result = analyze(padded)
    first_sequence = first.candidates[0].sequence
    padded_sequence = padded_result.candidates[0].sequence

    assert first_sequence.suffix_values == padded_sequence.suffix_values
    assert first_sequence.inclusive_span == padded_sequence.inclusive_span
    assert first_sequence.gap_count == padded_sequence.gap_count
    assert [row.status for row in first.candidates[0].clauses] == [
        row.status for row in padded_result.candidates[0].clauses
    ]


def test_representatives_are_bounded_with_exact_known_coverage() -> None:
    profile = CandidateProfile(
        profile_version="bounded-numbered-family-v2",
        minimum_members=4,
        minimum_density=CandidateRatio(4, 5),
        direct_import_coverage=CandidateRatio(4, 5),
        lexical_coverage=CandidateRatio(4, 5),
        lexical_features=(DECLARATION_STEM_VERSION,),
        representative_limit=2,
    )
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3, 4),
            import_count=5,
            lexical_count=5,
        ),
    }

    candidate = analyze(modules, profile=profile).candidates[0]

    assert tuple(
        representative.member_id for representative in candidate.representatives
    ) == (
        "Neutral.Rows.Cell0",
        "Neutral.Rows.Cell1",
    )
    coverage = candidate.representative_coverage
    assert coverage.visible == 2
    assert coverage.total_known is True
    assert coverage.total == 5
    assert coverage.omitted == 3
    assert coverage.completeness == "partial"
    assert coverage.causes[0].controlling_cap == 2
    assert len(candidate.members) == 5


def test_feature_keys_are_bounded_without_losing_the_strongest_witness() -> None:
    profile = CandidateProfile(
        profile_version="bounded-feature-keys-v1",
        minimum_members=4,
        minimum_density=CandidateRatio(4, 5),
        direct_import_coverage=CandidateRatio(4, 5),
        lexical_coverage=CandidateRatio(4, 5),
        lexical_features=(DECLARATION_STEM_VERSION,),
        representative_limit=2,
    )
    partition = partition_by_prefix(
        analyze(_bounded_feature_modules(), profile=profile),
        "Cell",
    )

    _assert_bounded_selected_feature(partition)
    _assert_bounded_feature_coverage(partition)


def _bounded_feature_modules() -> dict[str, LeanModule]:
    unique_names = tuple(
        f"unique{chr(ord('A') + index)}"
        for index in range(20)
    )
    modules = {"Neutral.Data": lean_module("Neutral.Data")}
    for index, unique_name in enumerate(unique_names):
        name = f"Neutral.Rows.Cell{index}"
        modules[name] = lean_module(
            name,
            imports=("Neutral.Data",),
            declarations=(f"sharedRow{index}", unique_name),
        )
    return modules


def _assert_bounded_selected_feature(partition) -> None:
    selected = next(
        feature
        for feature in partition.features
        if feature.identifier == partition.selected_lexical_feature_id
    )

    assert selected.value == "shared_Row_<number>"
    assert selected.member_count == 20
    assert len(
        [
            feature
            for feature in partition.features
            if feature.version == DECLARATION_STEM_VERSION
        ]
    ) == 12


def _assert_bounded_feature_coverage(partition) -> None:
    coverage = partition.feature_coverage
    assert coverage.population == "observed_aggregate_feature_keys"
    assert coverage.visible == 13
    assert coverage.total_known is True
    assert coverage.total == 22
    assert coverage.observed_lower_bound == 22
    assert coverage.omitted == 9
    assert coverage.causes[0].identifier == "candidate.feature_key_limit"
    assert coverage.causes[0].controlling_cap == 12


def test_core_detector_never_starts_a_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("candidate analysis attempted a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    modules = {
        "Neutral.Data": lean_module("Neutral.Data"),
        **numbered_family(
            "Neutral.Rows",
            (0, 1, 2, 3),
            import_count=4,
            lexical_count=4,
        ),
    }

    assert len(analyze(modules).candidates) == 1
