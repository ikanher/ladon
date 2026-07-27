from __future__ import annotations

from ladon.analysis.review_regions import summarize_review_regions
from ladon.coverage import CollectionCoverage, ProducerRegistration, ProducerRegistry
from ladon.coverage import InspectionAction
from ladon.render import render_text


def test_review_regions_group_import_proof_family_and_packet_evidence() -> None:
    module_dag = {
        "root_direct_import_closures": [
            {
                "root": "Mf.Owner",
                "direct_import": "Mf.Big",
                "reachable_module_count": 127,
            }
        ]
    }
    declaration_graph = {
        "declaration_name_families": [{"suffix": "ge_one", "count": 6}],
        "proof_family_similarity_candidates": [{"suffix": "eq_forward"}],
    }
    findings = [
        {"kind": "composite_import_pressure"},
        {"kind": "proof_family_import_pressure"},
    ]
    packet_evidence = [
        {"packet_dir": "/packet", "profile": "review_packet", "profile_status": "complete"}
    ]

    regions = summarize_review_regions(module_dag, declaration_graph, findings, packet_evidence)
    by_kind = {region["kind"]: region for region in regions}

    assert by_kind["import_pressure_region"]["signal_count"] == 2
    assert by_kind["proof_family_region"]["signal_count"] == 3
    assert by_kind["packet_evidence_region"]["signal_count"] == 1


def test_review_regions_label_small_import_closures_as_context() -> None:
    module_dag = {
        "root_direct_import_closures": [
            {
                "root": "Quux.Small",
                "direct_import": "Quux.Small.Helper",
                "reachable_module_count": 2,
            }
        ]
    }

    regions = summarize_review_regions(module_dag, None, [], [])

    assert regions == [
        {
            "kind": "import_context_region",
            "title": "Import-context review region",
            "signal_count": 1,
            "signals": [
                {
                    "kind": "root_import_closure",
                    "subject": "Quux.Small -> Quux.Small.Helper",
                    "count": 2,
                }
            ],
        }
    ]


def test_review_regions_label_broad_import_closures_as_pressure() -> None:
    module_dag = {
        "root_direct_import_closures": [
            {
                "root": "Mf.Owner",
                "direct_import": "Mf.Big",
                "reachable_module_count": 5,
            }
        ]
    }

    regions = summarize_review_regions(module_dag, None, [], [])

    assert regions[0]["kind"] == "import_pressure_region"
    assert regions[0]["title"] == "Import-pressure review region"


def test_text_report_renders_review_regions() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
        },
        "findings": [],
        "review_regions": [
            {
                "kind": "proof_family_region",
                "title": "Proof-family review region",
                "signal_count": 3,
                "signals": [{"kind": "declaration_family", "subject": "ge_one"}],
            }
        ],
    }

    text = render_text(payload)

    assert "Review Regions" in text
    assert "- proof_family_region: Proof-family review region (signals=3)" in text


def test_registered_generated_candidates_become_bounded_review_region() -> None:
    module_dag = generated_candidate_dag(10)

    regions = summarize_review_regions(module_dag, None, [], [])

    assert len(regions) == 1
    candidate_region = regions[0]
    assert {
        "kind": candidate_region["kind"],
        "signalCount": candidate_region["signal_count"],
        "inspectionAction": candidate_region["inspectionAction"],
        "upstreamCoverageRefs": candidate_region["upstreamCoverageRefs"],
    } == {
        "kind": "generated_family_candidate_region",
        "signalCount": 8,
        "inspectionAction": {
            "command": "ladon",
            "arguments": ["inspect", "modules"],
        },
        "upstreamCoverageRefs": ["generated_family.candidates"],
    }
    assert [row["id"] for row in candidate_region["signals"]] == [
        f"candidate-{index:02}.review" for index in range(8)
    ]
    coverage = candidate_region["coverage"]
    assert {
        "visible": coverage["visible"],
        "total": coverage["total"],
        "omitted": coverage["omitted"],
        "completeness": coverage["completeness"],
    } == {
        "visible": 8,
        "total": 10,
        "omitted": 2,
        "completeness": "partial",
    }
    assert candidate_region["coverage"]["causes"][-1][
        "controllingCap"
    ] == 8


def test_registered_regions_are_insertion_order_independent() -> None:
    forward = generated_candidate_dag(3)
    reverse = generated_candidate_dag(3)
    producers = reverse["generated_family_candidates"][
        "producerRegistry"
    ]["producers"]
    reverse["generated_family_candidates"]["producerRegistry"][
        "producers"
    ] = dict(reversed(tuple(producers.items())))

    assert summarize_review_regions(forward, None, [], []) == (
        summarize_review_regions(reverse, None, [], [])
    )


def test_dangling_registered_evidence_fails_closed() -> None:
    module_dag = generated_candidate_dag(2)
    producer = next(
        iter(
            module_dag["generated_family_candidates"][
                "producerRegistry"
            ]["producers"].values()
        )
    )
    producer["evidenceRefs"] = [
        "#/sections/module_dag/generated_family_candidates/candidates/99"
    ]

    assert summarize_review_regions(module_dag, None, [], []) == []


def test_declaration_registration_accepts_serialized_source_index_identity() -> None:
    coverage = CollectionCoverage.exact(
        identity="declaration_integrity.co_reachable_collisions",
        pointer=(
            "#/sections/module_dag/declaration_integrity/"
            "producerRegistrations/producers"
        ),
        visible=1,
        total=1,
        population="selected_context_collision_registrations",
        scope="selected_module_graph",
        authority="lexical_text_and_module_import_graph",
    )
    producer = ProducerRegistration(
        identity="collision-1.co_reachable",
        kind="co_reachable_declaration_collision_candidate",
        evidence_refs=(
            (
                "#/sections/module_dag/declaration_integrity/"
                "collisionCandidates/0"
            ),
            "source-index:declaration:decl:a",
        ),
        coverage_ref=coverage.identity,
        authority="lexical_text_and_module_import_graph",
        nonclaims=("Lexical and graph evidence only.",),
        action=InspectionAction(
            noun="declarations",
            filters=(("integrityGroup", "collision-1"),),
        ),
    )
    registry = ProducerRegistry().register_producer(producer)
    module_dag = {
        "declaration_integrity": {
            "collisionCandidates": [
                {
                    "id": "collision-1",
                    "representativeMembers": [
                        {
                            "canonicalRef": (
                                "source-index:declaration:decl:a"
                            )
                        }
                    ],
                }
            ],
            "producerRegistrations": registry.to_dict(),
            "coverage": {coverage.identity: coverage.to_dict()},
        },
        "declaration_coreachable_coverage": coverage.to_dict(),
    }

    regions = summarize_review_regions(module_dag, None, [], [])

    assert regions[0]["kind"] == "declaration_collision_region"
    assert regions[0]["signals"][0]["evidenceRefs"][-1] == (
        "source-index:declaration:decl:a"
    )
    assert regions[0]["inspectionAction"]["arguments"] == [
        "inspect",
        "declarations",
    ]


def test_explicit_architecture_registry_becomes_integrity_region() -> None:
    coverage = CollectionCoverage.exact(
        identity="architecture.joined_evidence",
        pointer="#/sections/module_dag/architecture/evidence",
        visible=1,
        total=1,
        population="structurally_joined_architecture_evidence",
        scope="selected_module_graph",
        authority="ladon_derived_structural_join",
    )
    producer = ProducerRegistration(
        identity="architecture:import-pressure",
        kind="composite_import_pressure",
        evidence_refs=(
            "#/sections/module_dag/architecture/evidence/0",
        ),
        coverage_ref=coverage.identity,
        authority="ladon_derived_structural_join",
        nonclaims=("Structural graph evidence is not a Lean defect.",),
        action=InspectionAction(
            noun="modules",
            filters=(("module", "Fixture.Root"),),
        ),
    )
    module_dag = {
        "architecture": {
            "evidence": [{"id": producer.identity}],
            "producerRegistrations": (
                ProducerRegistry()
                .register_producer(producer)
                .to_dict()
            ),
            "coverage": coverage.to_dict(),
        }
    }

    regions = summarize_review_regions(module_dag, None, [], [])

    assert regions[0]["kind"] == "architecture_integrity_region"
    assert regions[0]["signals"][0]["id"] == producer.identity
    assert regions[0]["authority"] == (
        "ladon_derived_structural_join"
    )


def generated_candidate_dag(count: int) -> dict:
    """Return one canonical generated-candidate registry fixture."""

    candidates = [
        {"id": f"candidate-{index:02}"}
        for index in range(count)
    ]
    coverage = CollectionCoverage.exact(
        identity="generated_family.candidates",
        pointer=(
            "#/sections/module_dag/generated_family_candidates/candidates"
        ),
        visible=count,
        total=count,
        population="generated_family_candidates",
        scope="selected_module_inventory",
        authority="ladon_derived_heuristic",
    )
    registry = ProducerRegistry()
    for index in range(count):
        registry = registry.register_producer(
            ProducerRegistration(
                identity=f"candidate-{index:02}.review",
                kind="generated_family_candidate",
                evidence_refs=(
                    (
                        "#/sections/module_dag/"
                        "generated_family_candidates/candidates/"
                        f"{index}"
                    ),
                ),
                coverage_ref=coverage.identity,
                authority="ladon_derived_heuristic",
                nonclaims=("Candidate evidence is not a defect claim.",),
                action=InspectionAction(
                    noun="modules",
                    filters=(
                        ("module", f"Fixture.Cell{index}"),
                    ),
                ),
            )
        )
    return {
        "generated_family_candidate_coverage": coverage.to_dict(),
        "generated_family_candidates": {
            "candidates": candidates,
            "producerRegistry": registry.to_dict(),
        },
    }
