from __future__ import annotations

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.inspection_models import ArtifactIdentity, InspectionDataset
from ladon.inspection_query import inspect_dataset
from ladon.inspection_render import render_inspection_text


def artifact() -> ArtifactIdentity:
    return ArtifactIdentity(
        kind="source-index",
        schema="ladon-source-index-v3",
        fingerprint="sha256:artifact",
        source_fingerprint="sha256:source",
    )


def test_unknown_empty_collection_does_not_claim_omission_or_exhaustion() -> None:
    coverage = CollectionCoverage.unknown(
        identity="source_index.audit_commands",
        pointer="#/entries",
        visible=0,
        observed_lower_bound=0,
        population="audit_commands",
        scope="source_index",
        authority="lexical_text",
        completeness="partial",
        causes=(
            CoverageCause(
                kind="compatibility",
                identifier="source_index.audit_commands_unavailable",
                detail="Legacy artifact does not carry audit command rows.",
            ),
        ),
        source_fingerprint="sha256:source",
    )
    page = inspect_dataset(
        InspectionDataset(
            noun="audits",
            artifact=artifact(),
            coverage=coverage.to_dict(),
            rows=(),
            unavailable_reason="audit evidence is unavailable",
        )
    )

    payload = page.to_dict()

    assert payload["coverage"]["matchingTotalKnown"] is False
    assert payload["coverage"]["matchingTotal"] is None
    assert payload["coverage"]["omitted"] is None
    assert payload["coverage"]["pageExhaustsMatches"] is False
    assert "0 observed matching" in render_inspection_text(page)


def test_complete_empty_collection_reports_exact_exhaustion() -> None:
    coverage = CollectionCoverage.exact(
        identity="source_index.audit_commands",
        pointer="#/entries",
        visible=0,
        total=0,
        population="audit_commands",
        scope="source_index",
        authority="lexical_text",
        source_fingerprint="sha256:source",
    )
    page = inspect_dataset(
        InspectionDataset(
            noun="audits",
            artifact=artifact(),
            coverage=coverage.to_dict(),
            rows=(),
        )
    ).to_dict()

    assert page["coverage"]["matchingTotalKnown"] is True
    assert page["coverage"]["matchingTotal"] == 0
    assert page["coverage"]["omitted"] == 0
    assert page["coverage"]["pageExhaustsMatches"] is True
