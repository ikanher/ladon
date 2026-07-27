from __future__ import annotations

import pytest

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    CoverageError,
    CoverageRegistry,
    EvidenceStratumRegistration,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
    derive_coverage,
    legacy_unknown_coverage,
    require_compatible_fingerprints,
)


def complete_collection() -> CollectionCoverage:
    return CollectionCoverage.exact(
        identity="declarations",
        pointer="#/sections/declaration_graph/declarations",
        visible=3,
        total=3,
        population="selected",
        scope="owner:Fixture",
        authority="lexical_text",
        source_fingerprint="sha256:source",
        scope_fingerprint="sha256:scope",
        analysis_fingerprint="sha256:analysis",
    )


def test_exact_and_empty_coverage_are_known_and_complete() -> None:
    nonempty = complete_collection()
    empty = CollectionCoverage.exact(
        identity="audits",
        pointer="#/sections/module_dag/audit_commands",
        visible=0,
        total=0,
        population="selected",
        scope="owner:Fixture",
        authority="lexical_text",
    )

    assert nonempty.total_known is True
    assert nonempty.omitted == 0
    assert nonempty.completeness == "complete"
    assert empty.to_dict()["total"] == 0
    assert empty.to_dict()["observedLowerBound"] == 0


def test_unknown_total_never_invents_total_or_omitted() -> None:
    unknown = CollectionCoverage.unknown(
        identity="declarations",
        pointer="#/sections/declaration_graph/declarations",
        visible=7,
        observed_lower_bound=7,
        completeness="partial",
        population="selected",
        scope="inventory",
        authority="lexical_text",
        causes=(
            CoverageCause(
                kind="extraction",
                identifier="source_index.source_failed",
                detail="one selected source unit was unindexable",
            ),
        ),
    )

    assert unknown.total_known is False
    assert unknown.total is None
    assert unknown.omitted is None
    assert unknown.to_dict()["observedLowerBound"] == 7


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (
            {"visible": 3, "observed_lower_bound": 2, "total": 3, "omitted": 0},
            "observed lower bound",
        ),
        (
            {"visible": 2, "observed_lower_bound": 2, "total": 3, "omitted": 0},
            "total - visible",
        ),
    ],
)
def test_known_coverage_rejects_invalid_arithmetic(
    values: dict[str, int],
    message: str,
) -> None:
    with pytest.raises(CoverageError, match=message):
        CollectionCoverage(
            identity="rows",
            pointer="#/rows",
            total_known=True,
            completeness="partial",
            population="selected",
            scope="owner:Fixture",
            authority="lexical_text",
            causes=(
                CoverageCause(
                    kind="projection",
                    identifier="projection.limit",
                    detail="bounded",
                ),
            ),
            **values,
        )


def test_projection_retains_upstream_total_and_causes() -> None:
    source = complete_collection()
    projected = source.projected(
        identity="declarations.review",
        pointer="#/sections/declaration_graph/declarations",
        visible=1,
        cause=CoverageCause(
            kind="projection",
            identifier="projection.collection_limit",
            detail="review projection retained one row",
            controlling_cap=1,
        ),
    )

    assert projected.total == 3
    assert projected.omitted == 2
    assert projected.completeness == "partial"
    assert projected.causes[-1].kind == "projection"


def test_legacy_missing_coverage_is_explicitly_unknown() -> None:
    row = legacy_unknown_coverage(
        identity="legacy.findings",
        pointer="#/findings",
        visible=2,
        population="selected",
        scope="unknown",
        authority="ladon_derived_heuristic",
    )

    assert row.completeness == "unavailable"
    assert row.total is None
    assert row.causes[0].kind == "compatibility"


def test_registry_round_trip_and_reference_validation() -> None:
    registry = CoverageRegistry().register(complete_collection())
    decoded = CoverageRegistry.from_mapping(registry.to_dict())

    assert decoded.require("declarations") == complete_collection()
    with pytest.raises(CoverageError, match="unknown coverage reference"):
        decoded.require("missing")


def test_registry_decoder_rejects_malformed_rows_and_boolean_coercion() -> None:
    with pytest.raises(CoverageError, match="rows must be objects"):
        CoverageRegistry.from_mapping(
            {
                "schema": "ladon-collection-coverage-v1",
                "collections": {"declarations": []},
            }
        )
    row = complete_collection().to_dict()
    row["totalKnown"] = "true"
    with pytest.raises(CoverageError, match="totalKnown must be a boolean"):
        CollectionCoverage.from_mapping(row)


def test_incompatible_fingerprints_fail_closed() -> None:
    left = complete_collection()
    right = CollectionCoverage.exact(
        identity="modules",
        pointer="#/sections/module_dag/modules",
        visible=1,
        total=1,
        population="selected",
        scope="owner:Fixture",
        authority="module_import_graph",
        source_fingerprint="sha256:other",
    )

    with pytest.raises(CoverageError, match="source fingerprint"):
        require_compatible_fingerprints((left, right))


def test_generic_producer_registration_uses_ordinary_inspection() -> None:
    row = ProducerRegistration(
        identity="candidate:neutral",
        kind="generated_family_candidate",
        evidence_refs=("module:Neutral.Rows.Cell0",),
        coverage_ref="generated_family_candidates",
        authority="ladon_derived_heuristic",
        nonclaims=("Advisory source regularity is not provenance.",),
        action=InspectionAction(
            noun="modules",
            filters=(("candidate", "candidate:neutral"),),
        ),
    ).to_dict()

    assert row["inspectionAction"]["arguments"][:2] == ["inspect", "modules"]
    assert row["inspectionAction"]["command"] == "ladon"


def test_derived_coverage_suppresses_exhaustive_partial_claims() -> None:
    registry = CoverageRegistry().register(
        CollectionCoverage.unknown(
            identity="declarations",
            pointer="#/sections/declaration_graph/declarations",
            visible=3,
            observed_lower_bound=3,
            completeness="partial",
            population="lexical_declarations",
            scope="inventory",
            authority="lexical",
            causes=(
                CoverageCause(
                    kind="extraction",
                    identifier="source.failed",
                    detail="one source was unreadable",
                ),
            ),
        )
    )

    exhaustive = derive_coverage(
        registry,
        ("declarations",),
        claim_kind="exhaustive",
    )
    witness = derive_coverage(
        registry,
        ("declarations",),
        claim_kind="positive_witness",
    )

    assert exhaustive.status == "unavailable"
    assert exhaustive.exhaustive is False
    assert witness.status == "subset"
    assert witness.exhaustive is False


def test_derived_coverage_is_exhaustive_only_for_complete_inputs() -> None:
    registry = CoverageRegistry().register(
        CollectionCoverage.exact(
            identity="findings",
            pointer="#/sections/findings",
            visible=0,
            total=0,
            population="promoted_findings",
            scope="selected",
            authority="ladon-derived",
        )
    )

    derived = derive_coverage(
        registry,
        ("findings",),
        claim_kind="absence",
    )

    assert derived.status == "available"
    assert derived.exhaustive is True
    assert derived.nonclaims == ()


def test_producer_registry_rejects_conflicting_rows() -> None:
    action = InspectionAction(noun="modules")
    producer = ProducerRegistration(
        identity="producer.modules",
        kind="module",
        evidence_refs=("#/sections/module_dag/module_metadata",),
        coverage_ref="module_dag.modules",
        authority="lexical",
        nonclaims=("Module rows are not Lean elaboration evidence.",),
        action=action,
    )
    stratum = EvidenceStratumRegistration(
        identity="stratum.modules.target_owned",
        evidence_kind="module",
        severity="info",
        status="observed",
        population="target_owned",
        role="module",
        coverage_ref="module_dag.modules",
        authority="lexical",
    )
    registry = (
        ProducerRegistry()
        .register_producer(producer)
        .register_stratum(stratum)
    )

    assert list(registry.to_dict()["producers"]) == ["producer.modules"]
    assert list(registry.to_dict()["strata"]) == [
        "stratum.modules.target_owned"
    ]
    with pytest.raises(CoverageError, match="producer identity already"):
        registry.register_producer(
            ProducerRegistration(
                identity=producer.identity,
                kind="other",
                evidence_refs=producer.evidence_refs,
                coverage_ref=producer.coverage_ref,
                authority=producer.authority,
                nonclaims=producer.nonclaims,
                action=producer.action,
            )
        )
