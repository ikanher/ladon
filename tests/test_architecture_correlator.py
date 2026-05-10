from __future__ import annotations

from ladon.analysis.architecture_correlator import (
    architecture_pressure_findings,
    classify_root_scope,
)


def test_architecture_correlator_emits_composite_findings_with_components() -> None:
    module_dag = {
        "module_count": 40,
        "top_fan_in": [{"module": "A.Core", "fan_in": 9}],
        "top_fan_out": [{"module": "A.Root", "fan_out": 11}],
        "facade_module_count": 8,
        "chosen_roots": ["A.Root"],
        "source_modules_not_reachable_from_chosen_roots_count": 33,
        "root_direct_import_closures": [
            {
                "root": "A.Root",
                "direct_import": "A.Big",
                "reachable_module_count": 25,
            }
        ],
    }
    declaration_graph = {
        "declaration_name_families": [{"suffix": "ge_one", "count": 5}],
    }

    findings = architecture_pressure_findings(module_dag, declaration_graph)
    by_kind = {finding["kind"]: finding for finding in findings}

    assert "composite_import_pressure" in by_kind
    assert "facade_fanout_pressure" in by_kind
    assert "root_scope_pressure" in by_kind
    assert "proof_family_import_pressure" in by_kind
    assert by_kind["composite_import_pressure"]["component_signals"] == [
        {"metric": "root_import_closure", "subject": "A.Root -> A.Big", "value": 25},
        {"metric": "module_fan_in", "subject": "A.Core", "value": 9},
    ]
    assert by_kind["root_scope_pressure"]["root_scope"]["classification"] == "narrow_owner_broad_import"
    assert by_kind["root_scope_pressure"]["component_signals"]
    assert "architecture pressure" in by_kind["facade_fanout_pressure"]["message"]


def test_architecture_correlator_requires_correlated_signals() -> None:
    module_dag = {
        "module_count": 40,
        "top_fan_in": [{"module": "A.Core", "fan_in": 9}],
        "top_fan_out": [{"module": "A.Root", "fan_out": 11}],
        "facade_module_count": 0,
        "source_modules_not_reachable_from_chosen_roots_count": 0,
        "root_direct_import_closures": [],
    }

    findings = architecture_pressure_findings(module_dag, None)

    assert findings == []


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

    assert classify_root_scope(module_dag)["classification"] == "public_root_narrow_inventory"


def test_root_scope_classifies_deep_owner_without_broad_import() -> None:
    module_dag = {
        "module_count": 370,
        "chosen_roots": ["Quux.Semantics.Propagation"],
        "source_modules_not_reachable_from_chosen_roots_count": 369,
        "root_direct_import_closures": [],
    }

    assert classify_root_scope(module_dag)["classification"] == "narrow_owner"
