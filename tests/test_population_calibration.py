from __future__ import annotations

import json

import pytest

from ladon.analysis.population_calibration import (
    AmbiguousGeneratedFamilyError,
    GENERATED_FAMILY_POLICY_SCHEMA,
    LEGACY_GENERATED_FAMILY_POLICY_SCHEMA,
    PolicyValidationError,
    PopulationCandidate,
    aggregate_generated_families,
    classify_population,
    classify_populations,
    parse_generated_family_policy,
    summarize_populations,
)


def generated_policy() -> dict:
    return {
        "schema": GENERATED_FAMILY_POLICY_SCHEMA,
        "families": [
            {
                "id": "generated.rows",
                "pathPatterns": ["Pkg/Generated/*.lean"],
                "modulePatterns": ["Pkg.Generated.*"],
                "generator": {"name": "rowgen", "version": "2.1"},
                "manifest": {
                    "identity": "rows-manifest-v3",
                    "path": "generated/rows-manifest.json",
                },
                "source": {"path": ".ladon/generated-policy.json", "line": 4},
            }
        ],
    }


def generated_policy_with_threshold(
    *,
    metric: str = "memberCount",
    at_least: int = 2,
) -> dict:
    payload = generated_policy()
    payload["families"][0]["reviewThreshold"] = {
        "metric": metric,
        "atLeast": at_least,
    }
    return payload


def candidate(
    identifier: str,
    module: str,
    path: str | None,
    **kwargs,
) -> PopulationCandidate:
    return PopulationCandidate(
        identifier=identifier,
        kind=kwargs.pop("kind", "module"),
        module=module,
        source_path=path,
        source_authority=kwargs.pop("source_authority", "lexical_text"),
        **kwargs,
    )


def test_policy_validation_is_versioned_normalized_and_deterministic() -> None:
    first = parse_generated_family_policy(generated_policy())
    reordered_payload = generated_policy()
    reordered_payload["families"][0]["pathPatterns"] = [
        "Pkg/Generated/Z*.lean",
        "Pkg/Generated/*.lean",
    ]
    second_payload = generated_policy()
    second_payload["families"][0]["pathPatterns"] = [
        "Pkg/Generated/*.lean",
        "Pkg/Generated/Z*.lean",
    ]

    second = parse_generated_family_policy(reordered_payload)
    third = parse_generated_family_policy(second_payload)

    assert first.schema == GENERATED_FAMILY_POLICY_SCHEMA
    assert len(first.digest) == 64
    assert second.digest == third.digest
    assert first.families[0].provenance.generator_name == "rowgen"
    assert first.families[0].provenance.manifest_identity == "rows-manifest-v3"


def test_v1_remains_readable_but_thresholds_require_v2() -> None:
    legacy = generated_policy()
    legacy["schema"] = LEGACY_GENERATED_FAMILY_POLICY_SCHEMA

    parsed = parse_generated_family_policy(legacy)

    assert parsed.schema == LEGACY_GENERATED_FAMILY_POLICY_SCHEMA
    legacy["families"][0]["reviewThreshold"] = {
        "metric": "memberCount",
        "atLeast": 2,
    }
    with pytest.raises(PolicyValidationError, match="requires schema"):
        parse_generated_family_policy(legacy)


@pytest.mark.parametrize(
    ("threshold", "message"),
    [
        (
            {"metric": "unknownCount", "atLeast": 2},
            "metric must be one of",
        ),
        (
            {"metric": "memberCount", "atLeast": 0},
            "must be a positive integer",
        ),
        (
            {"metric": "memberCount", "atLeast": True},
            "must be a positive integer",
        ),
    ],
)
def test_review_threshold_validation_is_explicit(
    threshold: dict,
    message: str,
) -> None:
    payload = generated_policy()
    payload["families"][0]["reviewThreshold"] = threshold

    with pytest.raises(PolicyValidationError, match=message):
        parse_generated_family_policy(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"schema": "ladon-generated-family-policy-v9", "families": []},
        {
            "schema": GENERATED_FAMILY_POLICY_SCHEMA,
            "families": [{"id": "bad id", "pathPatterns": ["Pkg/*.lean"]}],
        },
        {
            "schema": GENERATED_FAMILY_POLICY_SCHEMA,
            "families": [{"id": "rows", "pathPatterns": ["/tmp/*.lean"]}],
        },
        {
            "schema": GENERATED_FAMILY_POLICY_SCHEMA,
            "families": [
                {"id": "one", "pathPatterns": ["Pkg/*.lean"]},
                {"id": "two", "pathPatterns": ["Pkg/*.lean"]},
            ],
        },
    ],
)
def test_policy_validation_rejects_unsafe_or_ambiguous_rows(payload: dict) -> None:
    with pytest.raises(PolicyValidationError):
        parse_generated_family_policy(payload)


def test_four_population_classification_and_authority_precedence() -> None:
    policy = parse_generated_family_policy(generated_policy())
    rows = [
        candidate("authored", "Pkg.Owner", "Pkg/Owner.lean"),
        candidate("imported", "Dep.Theorem", "vendor/Dep/Theorem.lean"),
        candidate(
            "compiler",
            "Pkg.Owner",
            "Pkg/Owner.lean",
            kind="declaration",
            compiler_generated=True,
            compiler_authority="lean_environment",
            toolchain="Lean 4.30.0",
        ),
        candidate("generated", "Pkg.Generated.Row1", "Pkg/Generated/Row1.lean"),
    ]

    classified = classify_populations(
        rows,
        target_source_roots=["Pkg"],
        policy=policy,
    )
    by_id = {row.identifier: row for row in classified}

    assert {
        "populations": {
            identifier: row.population for identifier, row in by_id.items()
        },
        "compilerAuthority": by_id["compiler"].classification_authority,
        "compilerSourceAuthority": by_id["compiler"].source_authority,
        "generatedFamily": by_id["generated"].family_id,
        "generatedMatchCount": len(by_id["generated"].matched_rules),
        "generatedPolicyDigest": by_id["generated"].policy_digest,
    } == {
        "populations": {
            "authored": "target_owned",
            "compiler": "compiler_generated",
            "generated": "project_generated",
            "imported": "imported",
        },
        "compilerAuthority": "lean_environment",
        "compilerSourceAuthority": "lexical_text",
        "generatedFamily": "generated.rows",
        "generatedMatchCount": 2,
        "generatedPolicyDigest": policy.digest,
    }


def test_compiler_evidence_wins_inside_a_configured_generated_source() -> None:
    policy = parse_generated_family_policy(generated_policy())
    row = candidate(
        "synthetic",
        "Pkg.Generated.Row1",
        "Pkg/Generated/Row1.lean",
        kind="declaration",
        compiler_generated=True,
        compiler_authority="lean_environment",
        toolchain="Lean 4.30.0",
    )

    result = classify_population(
        row,
        target_source_roots=["Pkg"],
        policy=policy,
    )

    assert result.population == "compiler_generated"
    assert result.family_id is None
    assert result.matched_rules
    assert result.family_provenance is not None


def test_generated_looking_authored_name_is_not_heuristically_promoted() -> None:
    policy = parse_generated_family_policy(generated_policy())
    result = classify_population(
        candidate(
            "authored-generated-name",
            "Pkg.Handwritten.GeneratedIdea",
            "Pkg/Handwritten/GeneratedIdea.lean",
        ),
        target_source_roots=["Pkg"],
        policy=policy,
    )

    assert result.population == "target_owned"
    assert result.family_id is None
    assert result.matched_rules == ()


def test_contradictory_or_incomplete_evidence_remains_unclassified() -> None:
    policy = parse_generated_family_policy(generated_policy())
    missing_source = classify_population(
        candidate("missing", "Pkg.Unknown", None),
        target_source_roots=["Pkg"],
        policy=policy,
    )
    missing_compiler_provenance = classify_population(
        candidate(
            "compiler",
            "Pkg.Owner",
            "Pkg/Owner.lean",
            kind="declaration",
            compiler_generated=True,
        ),
        target_source_roots=["Pkg"],
        policy=policy,
    )

    assert missing_source.population == "unclassified"
    assert (
        missing_source.diagnostics[0].code
        == "population.ownership_unavailable"
    )
    assert missing_compiler_provenance.population == "unclassified"
    assert (
        missing_compiler_provenance.diagnostics[0].code
        == "population.compiler_provenance_incomplete"
    )


def test_concrete_cross_family_overlap_is_rejected_before_metrics() -> None:
    policy = parse_generated_family_policy(
        {
            "schema": GENERATED_FAMILY_POLICY_SCHEMA,
            "families": [
                {"id": "broad", "pathPatterns": ["Pkg/Generated/*.lean"]},
                {"id": "named", "modulePatterns": ["Pkg.Generated.Row*"]},
            ],
        }
    )
    row = candidate(
        "ambiguous",
        "Pkg.Generated.Row1",
        "Pkg/Generated/Row1.lean",
    )

    with pytest.raises(AmbiguousGeneratedFamilyError) as error:
        classify_population(
            row,
            target_source_roots=["Pkg"],
            policy=policy,
        )

    assert error.value.family_ids == ("broad", "named")
    assert len(error.value.matches) == 2


def test_population_summary_names_denominator_and_every_exclusion() -> None:
    policy = parse_generated_family_policy(generated_policy())
    classified = classify_populations(
        [
            candidate("authored", "Pkg.Owner", "Pkg/Owner.lean"),
            candidate("imported", "Dep.Owner", "vendor/Dep/Owner.lean"),
            candidate("generated", "Pkg.Generated.Row1", "Pkg/Generated/Row1.lean"),
        ],
        target_source_roots=["Pkg"],
        policy=policy,
    )

    target_summary = summarize_populations(classified)
    compiler_summary = summarize_populations(
        classified,
        selected_population="compiler_generated",
    )

    assert target_summary.numerator == 1
    assert target_summary.denominator == 3
    assert target_summary.counts["project_generated"] == 1
    assert target_summary.exclusions["imported"] == 1
    assert compiler_summary.numerator == 0
    assert compiler_summary.denominator == 3


def test_generated_family_aggregate_is_bounded_and_keeps_raw_members() -> None:
    policy = parse_generated_family_policy(generated_policy_with_threshold())
    rows = [
        candidate(
            "row-2",
            "Pkg.Generated.Row2",
            "Pkg/Generated/Row2.lean",
            source_size_bytes=200,
            declaration_count=4,
            imports=("Pkg.Generated.Row1", "Pkg.Core"),
        ),
        candidate(
            "row-1",
            "Pkg.Generated.Row1",
            "Pkg/Generated/Row1.lean",
            source_size_bytes=100,
            declaration_count=3,
            imports=("Pkg.Core",),
        ),
    ]
    classified = classify_populations(
        rows,
        target_source_roots=["Pkg"],
        policy=policy,
    )

    first = aggregate_generated_families(
        rows,
        classified,
        representative_limit=1,
    )[0]
    second = aggregate_generated_families(
        list(reversed(rows)),
        list(reversed(classified)),
        representative_limit=1,
    )[0]

    assert {
        "memberCount": first.member_count,
        "sourceSizeBytes": first.source_size_bytes,
        "declarationCount": first.declaration_count,
        "internalImports": first.internal_import_targets,
        "externalImports": first.external_import_targets,
        "internalImportCount": first.internal_import_count,
        "externalImportCount": first.external_import_count,
        "representatives": first.representative_member_ids,
        "representativeOmitted": first.representative_omitted_count,
        "rawMembers": first.raw_member_ids,
        "reviewThreshold": first.review_threshold.to_dict(),
        "reviewMetricValue": first.review_metric_value,
        "reviewThresholdCrossed": first.review_threshold_crossed,
        "nonclaim": "does not establish a generator defect" in first.nonclaim,
    } == {
        "memberCount": 2,
        "sourceSizeBytes": 300,
        "declarationCount": 7,
        "internalImports": ("Pkg.Generated.Row1",),
        "externalImports": ("Pkg.Core",),
        "internalImportCount": 1,
        "externalImportCount": 2,
        "representatives": ("row-1",),
        "representativeOmitted": 1,
        "rawMembers": ("row-1", "row-2"),
        "reviewThreshold": {"metric": "memberCount", "atLeast": 2},
        "reviewMetricValue": 2,
        "reviewThresholdCrossed": True,
        "nonclaim": True,
    }
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(),
        sort_keys=True,
    )


def test_family_aggregate_identity_survives_unrelated_policy_changes() -> None:
    first_policy = parse_generated_family_policy(generated_policy())
    expanded_payload = generated_policy()
    expanded_payload["families"].append(
        {"id": "generated.other", "pathPatterns": ["Other/*.lean"]}
    )
    expanded_policy = parse_generated_family_policy(expanded_payload)
    rows = [
        candidate(
            "row-1",
            "Pkg.Generated.Row1",
            "Pkg/Generated/Row1.lean",
        )
    ]

    first_classification = classify_populations(
        rows,
        target_source_roots=["Pkg"],
        policy=first_policy,
    )
    expanded_classification = classify_populations(
        rows,
        target_source_roots=["Pkg"],
        policy=expanded_policy,
    )
    first = aggregate_generated_families(rows, first_classification)[0]
    expanded = aggregate_generated_families(rows, expanded_classification)[0]

    assert first.identifier == expanded.identifier
    assert first.policy_digest != expanded.policy_digest
