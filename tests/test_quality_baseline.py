from __future__ import annotations

from ladon.analysis.quality_baseline import (
    calibrate_count,
    summarize_quality_baseline,
)


def test_quality_baseline_summarizes_graph_metric_distributions() -> None:
    module_dag = {
        "edges": {
            "A.Root": ["A.Core", "A.Helper"],
            "A.Helper": ["A.Core"],
            "A.Core": [],
        },
        "root_direct_import_closures": [
            {"reachable_module_count": 3},
            {"reachable_module_count": 1},
        ],
    }
    declaration_graph = {
        "edges": {
            "A.root": ["A.kernel"],
            "A.helper": ["A.kernel"],
            "A.kernel": [],
        },
        "declaration_name_families": [
            {"suffix": "ge_one", "count": 3},
            {"suffix": "le_one", "count": 2},
        ],
        "unresolved_reference_classes": [
            {"classification": "actionable_unknown", "count": 5},
            {"classification": "local_or_field_candidate", "count": 1},
        ],
    }

    baseline = summarize_quality_baseline(module_dag, declaration_graph)
    metrics = baseline["metrics"]

    assert metrics["module_fan_in"]["values"] == [0, 1, 2]
    assert metrics["module_fan_out"]["max"] == 2
    assert metrics["root_import_closure"]["values"] == [1, 3]
    assert metrics["declaration_fan_in"]["values"] == [0, 0, 2]
    assert metrics["declaration_family_size"]["max"] == 3
    assert metrics["unresolved_reference_class_count"]["p90"] == 5


def test_quality_baseline_calibrates_counts_against_metric_values() -> None:
    baseline = {
        "metrics": {
            "module_fan_in": {
                "values": [0, 1, 2, 6],
            }
        }
    }

    calibration = calibrate_count(baseline, "module_fan_in", 6)

    assert calibration == {
        "metric": "module_fan_in",
        "percentile": 100.0,
        "rank_desc": 1,
        "population": 4,
    }
