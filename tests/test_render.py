from __future__ import annotations

from ladon.render import render_text


def test_text_report_groups_module_dag_details() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 3,
            "edge_count": 2,
            "acyclic": True,
            "topological_layer_count": 2,
            "facade_module_count": 1,
            "top_fan_in": [{"module": "A.Core", "fan_in": 2}],
            "top_fan_out": [{"module": "A.Root", "fan_out": 2}],
            "facade_modules": ["A.Facade"],
            "source_modules_not_reachable_from_chosen_roots": ["A.Orphan"],
            "source_modules_not_reachable_from_chosen_roots_count": 1,
            "root_direct_import_closures": [
                {
                    "root": "A.Root",
                    "direct_import": "A.Core",
                    "reachable_module_count": 4,
                }
            ],
        },
        "findings": [],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Top Module Fan-In\n- A.Core: 2" in text
    assert "Top Module Fan-Out\n- A.Root: 2" in text
    assert "Root Direct Import Closures\n- A.Root -> A.Core: 4" in text
    assert "Facade Modules\n- A.Facade" in text
    assert "Modules Not Reachable From Chosen Roots\n- count: 1\n- A.Orphan" in text


def test_text_report_renders_unresolved_reference_classifications() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
            "top_fan_in": [],
            "top_fan_out": [],
        },
        "findings": [],
        "declaration_graph": {
            "declaration_count": 1,
            "edge_count": 0,
            "unresolved_reference_count": 2,
            "declaration_name_families": [
                {
                    "suffix": "ge_one",
                    "count": 3,
                    "sample_declarations": ["A.x_ge_one", "A.y_ge_one"],
                }
            ],
            "unresolved_reference_classes": [
                {"classification": "local_or_field_candidate", "count": 9},
                {"classification": "actionable_unknown", "count": 2},
            ],
            "top_unresolved_references": [
                {
                    "candidate": "count",
                    "classification": "local_or_field_candidate",
                    "count": 9,
                }
            ],
            "top_actionable_unresolved_references": [
                {
                    "candidate": "MissingTheorem",
                    "classification": "actionable_unknown",
                    "count": 2,
                }
            ],
        },
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Top Unresolved References\n- count: 9 (local_or_field_candidate)" in text
    assert "Declaration Name Families\n- ge_one: 3" in text
    assert "Unresolved Reference Classes\n- local_or_field_candidate: 9" in text
    assert "Top Actionable Unresolved References\n- MissingTheorem: 2" in text
