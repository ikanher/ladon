from __future__ import annotations

from ladon.analysis.source_patterns import SourceDocument, summarize_source_patterns


def test_source_patterns_report_policy_named_plain_matches() -> None:
    report = summarize_source_patterns(
        [
            SourceDocument(
                module="Pkg.Owner",
                path="Pkg/Owner.lean",
                text="theorem oldSurface : True := by\n  trivial\n",
            )
        ],
        {
            "id": "local-source-audit",
            "patterns": [
                {
                    "id": "stale-owner-term",
                    "pattern": "oldSurface",
                    "kind": "stale_term",
                    "severity": "warning",
                }
            ],
        },
    )

    assert report["policyId"] == "local-source-audit"
    assert report["patternCount"] == 1
    assert report["matchCount"] == 1
    assert report["summary"] == {"stale_term": 1}
    assert report["matches"][0]["path"] == "Pkg/Owner.lean"
    assert report["matches"][0]["line"] == 1
    assert report["findings"][0]["kind"] == "source_pattern.match"


def test_source_patterns_support_regex_case_and_generated_filtering() -> None:
    report = summarize_source_patterns(
        [
            SourceDocument(
                module="Pkg.Generated",
                path="Pkg/Generated.lean",
                text="def generatedMarker : Nat := 1\n",
                tags=("generated",),
            ),
            SourceDocument(
                module="Pkg.Owner",
                path="Pkg/Owner.lean",
                text="def FinalMarker : Nat := 1\n",
            ),
        ],
        {
            "patterns": [
                {
                    "id": "final-marker",
                    "pattern": "finalmarker",
                    "kind": "naming_smell",
                    "caseSensitive": False,
                    "excludeGenerated": True,
                },
                {
                    "id": "generated-marker",
                    "pattern": "generated.*",
                    "kind": "generated_marker",
                    "regex": True,
                    "excludeGenerated": True,
                },
            ],
        },
    )

    assert report["matchCount"] == 1
    assert report["matches"][0]["patternId"] == "final-marker"
    assert report["patternSummary"][1]["matchCount"] == 0


def test_source_patterns_report_zero_match_coverage() -> None:
    report = summarize_source_patterns(
        [SourceDocument(module="Pkg.Owner", path="Pkg/Owner.lean", text="def x := 1\n")],
        {
            "id": "zero-coverage",
            "patterns": [
                {
                    "id": "missing-term",
                    "pattern": "MissingTerm",
                    "kind": "stale_term",
                }
            ],
        },
    )

    assert report["matchCount"] == 0
    assert report["reportedMatchCount"] == 0
    assert report["summary"] == {"stale_term": 0}
    assert report["patternSummary"][0]["matchCount"] == 0


def test_source_patterns_preserve_total_count_when_report_is_capped() -> None:
    report = summarize_source_patterns(
        [
            SourceDocument(
                module="Pkg.Owner",
                path="Pkg/Owner.lean",
                text="DeprecatedLocalTerm\nDeprecatedLocalTerm\nDeprecatedLocalTerm\n",
            )
        ],
        {
            "patterns": [
                {
                    "id": "deprecated-term",
                    "pattern": "DeprecatedLocalTerm",
                    "kind": "stale_term",
                    "maxMatches": 2,
                }
            ],
        },
    )

    assert report["matchCount"] == 3
    assert report["reportedMatchCount"] == 2
    assert report["truncated"] is True
    assert report["patternSummary"][0]["truncated"] is True


def test_source_patterns_emit_diagnostics_for_invalid_rows() -> None:
    report = summarize_source_patterns(
        [SourceDocument(module="Pkg.Owner", path="Pkg/Owner.lean", text="def x := 1\n")],
        {"patterns": [{"id": "bad-regex", "pattern": "[", "regex": True}]},
    )

    assert report["status"] == "policy_diagnostics"
    assert report["diagnostics"][0]["subject"] == "bad-regex"
    assert report["findings"][0]["kind"] == "source_pattern.invalid_policy"
