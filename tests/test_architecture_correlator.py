from __future__ import annotations

from copy import deepcopy

from ladon.analysis.architecture_correlator import (
    architecture_pressure_findings,
    classify_root_scope,
    facade_fanout_findings,
    import_pressure_findings,
    proof_family_import_findings,
    root_scope_findings,
)
from ladon.analysis.architecture_registrations import (
    attach_architecture_producer_registrations,
)
from ladon.analysis.review_regions import summarize_review_regions
from ladon.analysis.structural_joins import (
    STRUCTURAL_JOIN_PLANS,
    build_structural_join,
    deterministic_graph_path,
)
from ladon.pipeline_models import RunContext


def composite_module_dag() -> dict:
    """Return a broad module DAG with genuinely joined architecture signals."""

    closure_members = ["A.Core", *(f"A.Dep{i:02}" for i in range(23))]
    facade_imports = [f"A.Api{i:02}" for i in range(12)]
    inventory = {
        "A.Root",
        "A.Big",
        "A.Public",
        *closure_members,
        *facade_imports,
        *(f"A.Orphan{i:02}" for i in range(3)),
    }
    edges = {module: [] for module in sorted(inventory)}
    edges["A.Root"] = ["A.Big", "A.Public"]
    edges["A.Big"] = closure_members
    edges["A.Public"] = facade_imports
    return {
        "module_count": len(inventory),
        "edge_count": sum(len(targets) for targets in edges.values()),
        "top_fan_in": [
            {"module": "A.Elsewhere", "fan_in": 12},
            {"module": "A.Core", "fan_in": 9},
        ],
        "top_fan_out": [{"module": "A.Root", "fan_out": 11}],
        "top_facade_fan_out": [{"module": "A.Public", "fan_out": 12}],
        "facade_module_count": 8,
        "module_metadata": {
            module: {
                "roles": ["facade"] if module == "A.Public" else [],
            }
            for module in sorted(inventory)
        },
        "chosen_roots": ["A.Root"],
        "root_reachability": {
            "status": "applicable",
            "roots": ["A.Root"],
            "population": "selected_modules",
            "coverageRef": "module_dag.modules",
            "authority": "module_import_graph",
        },
        "source_modules_not_reachable_from_chosen_roots_count": 33,
        "root_direct_import_closures": [
            {
                "root": "A.Root",
                "direct_import": "A.Big",
                "reachable_module_count": 25,
            }
        ],
        "edges": edges,
    }


def composite_declaration_graph() -> dict:
    """Return a declaration family contained by the joined import closure."""

    declarations = [
        {
            "declaration": f"A.Big.proof{i}_ge_one",
            "module": "A.Big",
        }
        for i in range(5)
    ]
    return {
        "declaration_count": len(declarations),
        "declarations": declarations,
        "declaration_name_families": [
            {
                "suffix": "ge_one",
                "count": 5,
                "sample_declarations": [
                    row["declaration"] for row in declarations
                ],
            }
        ],
    }


def composite_findings_by_kind() -> dict:
    """Return composite findings keyed by finding kind."""

    findings = architecture_pressure_findings(
        composite_module_dag(),
        composite_declaration_graph(),
    )
    return {finding["kind"]: finding for finding in findings}


def test_architecture_correlator_emits_expected_joined_findings() -> None:
    by_kind = composite_findings_by_kind()

    assert set(by_kind) == {
        "composite_import_pressure",
        "facade_fanout_pressure",
        "root_scope_pressure",
        "proof_family_import_pressure",
    }


def test_all_composite_kinds_register_structural_join_plans() -> None:
    assert set(STRUCTURAL_JOIN_PLANS) == {
        "composite_import_pressure",
        "facade_fanout_pressure",
        "root_scope_pressure",
        "proof_family_import_pressure",
    }
    relationships = {
        relation
        for plan in STRUCTURAL_JOIN_PLANS.values()
        for relation in plan.relationships
    }
    assert {
        "same_subject",
        "population_membership",
        "closure_membership",
        "deterministic_graph_path",
        "containment",
    } <= relationships


def test_import_pressure_selects_joined_candidate_not_global_maximum() -> None:
    finding = import_pressure_findings(composite_module_dag())[0]

    assert finding["subject"] == "A.Root -> A.Big"
    assert [row["subject"] for row in finding["component_signals"]] == [
        "A.Root -> A.Big",
        "A.Core",
    ]
    assert finding["join"]["kind"] == "root_import_closure_membership"
    graph_witness = next(
        row
        for row in finding["join"]["witnessRefs"]
        if row["type"] == "deterministic-graph-path"
    )
    assert graph_witness["path"] == ["A.Big", "A.Core"]
    assert "count" not in finding


def test_component_measures_keep_units_populations_and_denominators() -> None:
    by_kind = composite_findings_by_kind()
    signals = by_kind["composite_import_pressure"]["component_signals"]

    assert signals[0]["measure"] == {
        "unit": "module",
        "population": "root_direct_import_closure",
        "scope": "A.Root -> A.Big",
        "denominator": {
            "status": "known",
            "value": composite_module_dag()["module_count"],
            "unit": "module",
            "population": "selected_module_inventory",
        },
        "aggregation": "distinct_modules",
    }
    assert signals[1]["measure"]["unit"] == "import_edge"
    assert (
        signals[1]["measure"]["population"]
        == "selected_module_import_graph"
    )
    assert signals[1]["measure"]["denominator"]["status"] == "known"


def test_homogeneous_headlines_do_not_sum_component_values() -> None:
    by_kind = composite_findings_by_kind()

    root = by_kind["root_scope_pressure"]
    assert root["count"] == 33
    assert root["count"] != sum(
        signal["value"] for signal in root["component_signals"]
    )
    assert root["headlineMeasure"]["aggregation"] == "distinct_modules"

    proof = by_kind["proof_family_import_pressure"]
    assert proof["count"] == 5
    assert proof["count"] != sum(
        signal["value"] for signal in proof["component_signals"]
    )
    assert (
        proof["headlineMeasure"]["aggregation"]
        == "distinct_declarations"
    )


def test_composites_preserve_authority_coverage_and_nonclaims() -> None:
    for finding in composite_findings_by_kind().values():
        assert finding["authority"] == "ladon_derived_structural_join"
        assert finding["componentAuthorities"]
        assert finding["join"]["componentRefs"] == finding["evidenceRefs"]
        assert finding["coverage"]["claimKind"] == "positive_witness"
        assert finding["coverage"]["exhaustive"] is False
        assert "Lean elaboration" in finding["nonclaims"][0]
        assert finding["stable_key"] == (
            f"{finding['kind']}:{finding['subject']}"
        )


def test_joined_architecture_findings_register_one_bounded_region() -> None:
    dag = composite_module_dag()
    declarations = composite_declaration_graph()
    findings = architecture_pressure_findings(dag, declarations)
    attach_architecture_producer_registrations(
        RunContext(repo_root="."),
        dag,
        findings,
        declarations,
    )

    regions = summarize_review_regions(dag, declarations, findings, [])
    architecture = next(
        row
        for row in regions
        if row["kind"] == "architecture_integrity_region"
    )

    _assert_architecture_region(architecture)
    _assert_registered_architecture_producers(dag)


def _assert_architecture_region(architecture: dict) -> None:
    assert architecture["signal_count"] == 4
    assert architecture["upstreamCoverageRefs"] == [
        "module_dag.architecture_joined_evidence"
    ]
    assert architecture["inspectionAction"]["arguments"][:2] == [
        "inspect",
        "modules",
    ]
    assert {
        signal["kind"] for signal in architecture["signals"]
    } == {
        "composite_import_pressure",
        "facade_fanout_pressure",
        "root_scope_pressure",
        "proof_family_import_pressure",
    }


def _assert_registered_architecture_producers(dag: dict) -> None:
    producers = dag["architectureProducerRegistrations"]["producers"]
    for producer in producers.values():
        assert producer["evidenceRefs"][0].startswith("#/sections/findings/")
        assert producer["evidenceRefs"][1].endswith("/join")
        assert any(
            "/join/witnessRefs/" in reference
            for reference in producer["evidenceRefs"]
        )


def test_architecture_registration_suppresses_dangling_nested_witness() -> None:
    dag = composite_module_dag()
    declarations = composite_declaration_graph()
    finding = deepcopy(import_pressure_findings(dag)[0])
    path_witness = next(
        witness
        for witness in finding["join"]["witnessRefs"]
        if witness["type"] == "deterministic-graph-path"
    )
    path_witness["edgeRefs"][0]["pointer"] = (
        "#/sections/module_dag/edges/does-not-exist/0"
    )

    attach_architecture_producer_registrations(
        RunContext(repo_root="."),
        dag,
        [finding],
        declarations,
    )

    assert dag["architectureProducerRegistrations"]["producers"] == {}
    assert dag["architecture_joined_coverage"]["total"] == 0
    assert not any(
        row["kind"] == "architecture_integrity_region"
        for row in summarize_review_regions(
            dag,
            declarations,
            [finding],
            [],
        )
    )


def test_disconnected_global_hotspots_do_not_form_import_composite() -> None:
    module_dag = composite_module_dag()
    module_dag["top_fan_in"] = [
        {"module": "A.Orphan00", "fan_in": 30},
    ]

    assert import_pressure_findings(module_dag) == []


def test_partial_declaration_rows_do_not_form_proof_family_composite() -> None:
    declaration_graph = composite_declaration_graph()
    declaration_graph["declarations"] = declaration_graph["declarations"][:2]

    assert (
        proof_family_import_findings(
            composite_module_dag(),
            declaration_graph,
        )
        == []
    )


def test_facade_membership_must_resolve_in_canonical_metadata() -> None:
    module_dag = composite_module_dag()
    module_dag["module_metadata"]["A.Public"]["roles"] = []

    assert facade_fanout_findings(module_dag) == []


def test_not_applicable_root_views_suppress_every_root_composite() -> None:
    module_dag = composite_module_dag()
    module_dag["root_reachability"] = {
        **module_dag["root_reachability"],
        "status": "not_applicable",
        "roots": [],
    }

    assert import_pressure_findings(module_dag) == []
    assert root_scope_findings(module_dag) == []
    assert (
        proof_family_import_findings(
            module_dag,
            composite_declaration_graph(),
        )
        == []
    )
    assert facade_fanout_findings(module_dag)


def test_dangling_join_pointer_fails_closed() -> None:
    reference = {
        "type": "aggregate",
        "section": "module_dag",
        "field": "missing",
        "pointer": "#/sections/module_dag/missing",
        "authority": "module_import_graph",
    }

    assert (
        build_structural_join(
            "root_scope_pressure",
            canonical_sections={"module_dag": {"module_count": 1}},
            component_metrics=("module_count", "unreachable_modules"),
            component_refs=(reference, reference),
            witness_refs=(
                {
                    "type": "population-subset",
                    "pointer": "#/sections/module_dag/module_count",
                },
            ),
            population="modules",
            scope="inventory",
            authority="module_import_graph",
            coverage_refs=("module_dag.modules",),
        )
        is None
    )


def test_deterministic_graph_path_uses_lexicographic_shortest_witness() -> None:
    edges = {
        "A": ["C", "B"],
        "B": ["D"],
        "C": ["D"],
        "D": [],
    }

    assert deterministic_graph_path(edges, "A", "D") == ("A", "B", "D")


def test_join_output_is_deterministic_under_ranked_row_reordering() -> None:
    first = composite_module_dag()
    second = deepcopy(first)
    second["top_fan_in"] = list(reversed(second["top_fan_in"]))

    first_finding = import_pressure_findings(first)[0]
    second_finding = import_pressure_findings(second)[0]

    assert first_finding["subject"] == second_finding["subject"]
    assert (
        first_finding["component_signals"]
        == second_finding["component_signals"]
    )


def test_root_scope_classifies_public_roots_separately() -> None:
    module_dag = {
        "module_count": 530,
        "chosen_roots": ["Mf"],
        "source_modules_not_reachable_from_chosen_roots_count": 517,
        "root_direct_import_closures": [
            {
                "root": "Mf",
                "direct_import": "Mf.Basic",
                "reachable_module_count": 12,
            }
        ],
    }

    assert (
        classify_root_scope(module_dag)["classification"]
        == "public_root_narrow_inventory"
    )


def test_root_scope_classifies_deep_owner_without_broad_import() -> None:
    module_dag = {
        "module_count": 370,
        "chosen_roots": ["Quux.Semantics.Propagation"],
        "source_modules_not_reachable_from_chosen_roots_count": 369,
        "root_direct_import_closures": [],
    }

    assert classify_root_scope(module_dag)["classification"] == "narrow_owner"
