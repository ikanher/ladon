from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    BUILTIN_PROFILE_VERSION,
    CANDIDATE_PROFILE_SCHEMA,
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    GROUPING_SUFFIX_WIDTH_VERSION,
    GROUPING_VERSION,
    CandidateProfile,
    CandidateProfileError,
    CandidateRatio,
    candidate_analysis_fingerprint,
    load_explicit_candidate_profile,
    parse_explicit_candidate_profile,
)


def explicit_profile_payload() -> dict:
    return {
        "schema": CANDIDATE_PROFILE_SCHEMA,
        "profileVersion": "portable-numbered-family-v2",
        "grouping": {"version": GROUPING_VERSION},
        "clauses": {
            "minimumMembers": 3,
            "minimumDensity": {"numerator": 3, "denominator": 4},
            "directInternalImportMemberCoverage": {
                "numerator": 3,
                "denominator": 5,
            },
            "lexicalMemberCoverage": {
                "numerator": 2,
                "denominator": 3,
            },
            "lexicalFeatures": [
                COMMAND_SKELETON_VERSION,
                DECLARATION_STEM_VERSION,
            ],
        },
        "normalizers": {
            "declarationStem": DECLARATION_STEM_VERSION,
            "commandSkeleton": COMMAND_SKELETON_VERSION,
        },
        "representatives": {"limit": 5},
    }


def test_builtin_profile_has_frozen_exact_constants() -> None:
    profile = BUILTIN_CANDIDATE_PROFILE

    assert profile.profile_version == "generic-numbered-family-v1"
    assert profile.minimum_members == 4
    assert profile.minimum_density == CandidateRatio(4, 5)
    assert profile.direct_import_coverage == CandidateRatio(4, 5)
    assert profile.lexical_coverage == CandidateRatio(4, 5)
    assert profile.lexical_features == (
        DECLARATION_STEM_VERSION,
        COMMAND_SKELETON_VERSION,
    )
    assert profile.digest.startswith("sha256:")
    assert len(profile.digest) == 71

    with pytest.raises(
        CandidateProfileError,
        match="frozen built-in constants",
    ):
        CandidateProfile(
            profile_version=BUILTIN_PROFILE_VERSION,
            minimum_members=3,
            minimum_density=CandidateRatio(4, 5),
            direct_import_coverage=CandidateRatio(4, 5),
            lexical_coverage=CandidateRatio(4, 5),
            lexical_features=(
                DECLARATION_STEM_VERSION,
                COMMAND_SKELETON_VERSION,
            ),
            representative_limit=12,
        )


def test_explicit_profile_is_strict_normalized_and_fingerprinted() -> None:
    first = parse_explicit_candidate_profile(explicit_profile_payload())
    reordered = explicit_profile_payload()
    reordered["clauses"] = dict(reversed(list(reordered["clauses"].items())))
    second = parse_explicit_candidate_profile(reordered)

    assert first == second
    assert first.lexical_features == (
        DECLARATION_STEM_VERSION,
        COMMAND_SKELETON_VERSION,
    )
    assert first.digest == second.digest
    assert first.normalized_configuration()["clauses"][
        "directInternalImportMemberCoverage"
    ] == {"numerator": 3, "denominator": 5}

    alternate_grouping = explicit_profile_payload()
    alternate_grouping["grouping"] = {
        "version": GROUPING_SUFFIX_WIDTH_VERSION
    }
    alternate = parse_explicit_candidate_profile(alternate_grouping)
    assert alternate.grouping_version == GROUPING_SUFFIX_WIDTH_VERSION
    assert alternate.digest != first.digest

    baseline = candidate_analysis_fingerprint(
        first,
        source_index_fingerprint="sha256:source-a",
        scope_fingerprint="sha256:scope",
        policy_digest="sha256:policy",
        completeness_fingerprint="sha256:complete-a",
    )
    changed_source = candidate_analysis_fingerprint(
        first,
        source_index_fingerprint="sha256:source-b",
        scope_fingerprint="sha256:scope",
        policy_digest="sha256:policy",
        completeness_fingerprint="sha256:complete-a",
    )
    changed_profile = candidate_analysis_fingerprint(
        parse_explicit_candidate_profile(
            {
                **explicit_profile_payload(),
                "representatives": {"limit": 6},
            }
        ),
        source_index_fingerprint="sha256:source-a",
        scope_fingerprint="sha256:scope",
        policy_digest="sha256:policy",
        completeness_fingerprint="sha256:complete-a",
    )
    changed_internal_inventory = candidate_analysis_fingerprint(
        first,
        source_index_fingerprint="sha256:source-a",
        scope_fingerprint="sha256:scope",
        policy_digest="sha256:policy",
        internal_inventory_fingerprint="sha256:internal-inventory",
        completeness_fingerprint="sha256:complete-a",
    )
    changed_completeness = candidate_analysis_fingerprint(
        first,
        source_index_fingerprint="sha256:source-a",
        scope_fingerprint="sha256:scope",
        policy_digest="sha256:policy",
        completeness_fingerprint="sha256:complete-b",
    )

    assert baseline.startswith("sha256:")
    assert (
        len(
            {
                baseline,
                changed_source,
                changed_profile,
                changed_internal_inventory,
                changed_completeness,
            }
        )
        == 5
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda row: row.pop("profileVersion"),
            "missing=.*profileVersion",
        ),
        (
            lambda row: row.update({"unknown": True}),
            "unknown=.*unknown",
        ),
        (
            lambda row: row["clauses"].update({"confidenceScore": 0.9}),
            "unknown=.*confidenceScore",
        ),
        (
            lambda row: row.update({"profileVersion": BUILTIN_PROFILE_VERSION}),
            "built-in profile identity is reserved",
        ),
        (
            lambda row: row["clauses"].update(
                {"lexicalFeatures": ["exact-source-hash-v1"]}
            ),
            "unsupported lexical feature",
        ),
        (
            lambda row: row["clauses"].update(
                {
                    "minimumDensity": {
                        "numerator": 5,
                        "denominator": 4,
                    }
                }
            ),
            "ratio cannot exceed one",
        ),
        (
            lambda row: row["clauses"].update({"minimumMembers": True}),
            "positive integer",
        ),
        (
            lambda row: row["grouping"].update({"version": "unknown-v1"}),
            "grouping.version is unsupported",
        ),
    ],
)
def test_invalid_or_disguised_profiles_are_rejected(
    mutate,
    message: str,
) -> None:
    payload = explicit_profile_payload()
    mutate(payload)

    with pytest.raises(CandidateProfileError, match=message):
        parse_explicit_candidate_profile(payload)


def test_profile_loader_rejects_duplicate_keys_before_analysis(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        (
            '{"schema":"'
            + CANDIDATE_PROFILE_SCHEMA
            + '","schema":"'
            + CANDIDATE_PROFILE_SCHEMA
            + '"}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(CandidateProfileError, match="duplicate key"):
        load_explicit_candidate_profile(profile_path)


def test_profile_file_round_trip_reports_normalized_digest(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(explicit_profile_payload(), indent=2),
        encoding="utf-8",
    )

    profile = load_explicit_candidate_profile(profile_path)

    assert profile.to_dict()["profileDigest"] == profile.digest
    assert profile.to_dict()["profileVersion"] == ("portable-numbered-family-v2")
