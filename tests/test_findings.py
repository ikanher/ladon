from __future__ import annotations

from ladon.analysis.findings import summarize_findings
from ladon.render import render_text


def test_findings_flag_declaration_graph_hotspots() -> None:
    module_dag = {
        "top_fan_in": [],
        "root_direct_import_closures": [
            {
                "root": "A",
                "direct_import": "A.Big",
                "reachable_module_count": 25,
            }
        ],
    }
    declaration_graph = {
        "top_fan_in": [{"declaration": "A.kernel", "fan_in": 6}],
        "top_fan_out": [{"declaration": "A.orchestrator", "fan_out": 7}],
        "declaration_name_families": [{"suffix": "ge_one", "count": 3}],
        "top_unresolved_references": [{"candidate": "State", "count": 8}],
        "top_actionable_unresolved_references": [
            {
                "candidate": "MissingTheorem",
                "classification": "actionable_unknown",
                "count": 8,
            }
        ],
        "declarations_not_reachable_from_chosen_roots_count": 3,
    }

    findings = summarize_findings(module_dag, declaration_graph)

    assert [finding["kind"] for finding in findings] == [
        "root_import_closure_hotspot",
        "declaration_fan_in_hotspot",
        "declaration_fan_out_hotspot",
        "declaration_family_hotspot",
        "unresolved_reference_hotspot",
        "unreachable_declarations",
    ]
    assert findings[0]["subject"] == "A -> A.Big"
    assert findings[1]["subject"] == "A.kernel"
    assert findings[4]["subject"] == "MissingTheorem"
    assert findings[0]["evidenceRefs"][0]["pointer"] == (
        "#/sections/module_dag/root_direct_import_closures/0"
    )
    assert findings[1]["evidenceRefs"][0]["pointer"] == (
        "#/sections/declaration_graph/top_fan_in/0"
    )
    assert findings[4]["evidenceRefs"][0]["pointer"] == (
        "#/sections/declaration_graph/"
        "top_actionable_unresolved_references/0"
    )
    assert findings[5]["evidenceRefs"][0] == {
        "type": "aggregate",
        "section": "declaration_graph",
        "field": "declarations_not_reachable_from_chosen_roots_count",
        "pointer": (
            "#/sections/declaration_graph/"
            "declarations_not_reachable_from_chosen_roots_count"
        ),
        "authority": "declaration_graph",
    }


def test_findings_ignore_below_threshold_rows() -> None:
    declaration_graph = {
        "top_fan_in": [{"declaration": "A.small", "fan_in": 4}],
        "top_fan_out": [{"declaration": "A.small", "fan_out": 4}],
        "top_unresolved_references": [{"candidate": "x", "count": 4}],
        "declarations_not_reachable_from_chosen_roots_count": 0,
    }

    assert summarize_findings({}, declaration_graph) == []


def test_findings_flag_duplicate_imports_and_large_target_owned_modules() -> None:
    module_dag = {
        "top_fan_in": [],
        "top_target_owned_fan_in": [],
        "root_direct_import_closures": [],
        "duplicate_imports": [
            {
                "module": "A.Owner",
                "target": "A.Core",
                "count": 2,
                "lines": [1, 2],
            }
        ],
        "module_name_smells": [
            {
                "module": "A.GeneratedScalarBw2Eps0p5Gamma0p8.Base",
                "reasonKinds": ["generated_encoded_parameters", "long_segment"],
                "suggestedAction": "move generated parameters into a manifest",
            }
        ],
        "top_target_owned_large_modules": [
            {
                "module": "A.Owner",
                "lineCount": 3000,
                "population": "target_owned",
            }
        ],
    }

    findings = summarize_findings(module_dag, None)

    assert [finding["kind"] for finding in findings] == [
        "duplicate_import_target",
        "module_name_smell",
        "large_target_owned_module",
    ]
    assert "lines 1, 2" in findings[0]["message"]
    assert "generated_encoded_parameters" in findings[1]["message"]
    assert findings[2]["count"] == 3000


def test_findings_do_not_penalize_long_handwritten_semantic_names() -> None:
    findings = summarize_findings(
        {
            "module_name_smells": [
                {
                    "module": "Domain.CenteredTightnessExactJensenHybridCommand",
                    "generated": False,
                    "reasonKinds": ["long_module_name", "long_segment"],
                }
            ]
        },
        None,
    )

    assert findings == []


def test_findings_cap_each_hotspot_family() -> None:
    declaration_graph = {
        "top_fan_in": [],
        "top_fan_out": [],
        "top_actionable_unresolved_references": [
            {"candidate": f"missing{i}", "count": 9}
            for i in range(5)
        ],
        "declarations_not_reachable_from_chosen_roots_count": 0,
    }

    findings = summarize_findings({}, declaration_graph)

    assert len(findings) == 3
    assert findings[-1]["subject"] == "missing2"


def test_findings_use_actionable_unresolved_rows_when_available() -> None:
    declaration_graph = {
        "top_fan_in": [],
        "top_fan_out": [],
        "top_unresolved_references": [{"candidate": "count", "count": 20}],
        "top_actionable_unresolved_references": [
            {"candidate": "MissingTheorem", "count": 7}
        ],
        "declarations_not_reachable_from_chosen_roots_count": 0,
    }

    findings = summarize_findings({}, declaration_graph)

    assert [finding["subject"] for finding in findings] == ["MissingTheorem"]


def duplicate_fan_findings() -> tuple[list[dict], dict]:
    """Return promoted findings plus unchanged raw fan tables."""

    importers = [
        "A.Owner1",
        "A.Owner2",
        "A.Owner3",
        "A.Owner4",
        "A.Owner5",
    ]
    module_dag = {
        "top_fan_in": [
            {
                "module": "A.Core",
                "fan_in": 5,
                "sample_importers": importers,
                "population": "all_importers_to_all_targets",
                "authority": "module_import_graph",
            }
        ],
        "top_target_owned_fan_in": [
            {
                "module": "A.Core",
                "fan_in": 5,
                "sample_importers": importers,
                "population": (
                    "target_owned_importers_to_target_owned_targets"
                ),
                "authority": (
                    "module_import_graph_and_population_policy"
                ),
            }
        ],
    }

    return summarize_findings(module_dag, None), module_dag


def test_equivalent_fan_promotions_are_promoted_once() -> None:
    findings, module_dag = duplicate_fan_findings()

    assert len(findings) == 1
    assert findings[0]["kind"] == "target_owned_module_fan_in_hotspot"
    assert findings[0]["promotion_population"] == (
        "target_owned_importers_to_target_owned_targets"
    )
    assert len(module_dag["top_fan_in"]) == 1
    assert len(module_dag["top_target_owned_fan_in"]) == 1


def test_fan_promotion_exposes_stable_threshold_and_authority_metadata() -> None:
    finding = duplicate_fan_findings()[0][0]

    assert finding["promotion_threshold"] == 5
    assert finding["authority"] == (
        "module_import_graph_and_population_policy"
    )
    assert finding["metric"] == "module_fan_in"
    assert finding["stable_key"].startswith("module_fan_in:A.Core:5:")
    assert finding["id"].startswith("ladon.finding.")


def test_text_report_renders_findings_before_declaration_graph() -> None:
    payload = {
        "metadata": {
            "repo_root": "/repo",
            "analysis_root_module": "A",
        },
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
        },
        "findings": [
            {
                "kind": "unresolved_reference_hotspot",
                "severity": "info",
                "subject": "State",
                "count": 8,
                "message": "State appears as an unresolved reference candidate 8 times.",
            }
        ],
        "declaration_graph": {
            "declaration_count": 1,
            "edge_count": 0,
            "unresolved_reference_count": 8,
        },
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert text.index("Findings") < text.index("Declaration Graph")
    assert "- [info] unresolved_reference_hotspot State: " in text
