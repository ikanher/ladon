from __future__ import annotations

from ladon.analysis.module_dag import summarize_module_dag
from ladon.ir import LeanModule


def test_module_dag_summarizes_acyclic_import_layers_and_roots() -> None:
    modules = {
        "A": LeanModule(name="A", path="A.lean", imports=("B", "C"), declarations=()),
        "B": LeanModule(name="B", path="B.lean", imports=("D",), declarations=("b",)),
        "C": LeanModule(name="C", path="C.lean", imports=("D",), declarations=("c",)),
        "D": LeanModule(name="D", path="D.lean", imports=(), declarations=("d",)),
        "E": LeanModule(name="E", path="E.lean", imports=(), declarations=("e",)),
    }

    summary = summarize_module_dag(modules, chosen_roots=("A",))

    assert summary["module_count"] == 5
    assert summary["edge_count"] == 4
    assert summary["acyclic"] is True
    assert summary["max_rank"] == 2
    assert summary["topological_layer_count"] == 3
    assert summary["layer_widths"] == [
        {"rank": 0, "width": 2, "sample_modules": ["A", "E"]},
        {"rank": 1, "width": 2, "sample_modules": ["B", "C"]},
        {"rank": 2, "width": 1, "sample_modules": ["D"]},
    ]
    assert summary["root_like_modules"] == ["A", "E"]
    assert summary["facade_modules"] == ["A"]
    assert summary["source_modules_not_reachable_from_chosen_roots"] == ["E"]


def test_module_dag_reports_cycles_without_claiming_layers() -> None:
    modules = {
        "A": LeanModule(name="A", path="A.lean", imports=("B",), declarations=("a",)),
        "B": LeanModule(name="B", path="B.lean", imports=("A",), declarations=("b",)),
        "C": LeanModule(name="C", path="C.lean", imports=(), declarations=("c",)),
    }

    summary = summarize_module_dag(modules)

    assert summary["acyclic"] is False
    assert summary["cyclic_component_count"] == 1
    assert summary["largest_cyclic_component_size"] == 2
    assert summary["top_cyclic_components"] == [
        {"size": 2, "sample_modules": ["A", "B"]}
    ]
    assert summary["topological_layer_count"] == 0
    assert summary["max_rank"] == 0
