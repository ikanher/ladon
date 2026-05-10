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


def test_findings_ignore_below_threshold_rows() -> None:
    declaration_graph = {
        "top_fan_in": [{"declaration": "A.small", "fan_in": 4}],
        "top_fan_out": [{"declaration": "A.small", "fan_out": 4}],
        "top_unresolved_references": [{"candidate": "x", "count": 4}],
        "declarations_not_reachable_from_chosen_roots_count": 0,
    }

    assert summarize_findings({}, declaration_graph) == []


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
