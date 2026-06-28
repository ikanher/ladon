from __future__ import annotations

from ladon.analysis.module_dag import summarize_module_dag
from ladon.ir import LeanImport, LeanLexicalMarker, LeanModule


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


def test_module_dag_preserves_import_source_evidence() -> None:
    modules = {
        "A": LeanModule(
            name="A",
            path="A.lean",
            imports=("B",),
            import_sites=(LeanImport(module="B", line=3, text="import B"),),
        ),
        "B": LeanModule(name="B", path="B.lean"),
    }

    summary = summarize_module_dag(modules)

    assert summary["import_sites"] == {
        "A": {
            "B": {
                "sourcePath": "A.lean",
                "line": 3,
                "importText": "import B",
            }
        }
    }


def test_module_dag_dedupes_edges_and_reports_duplicate_import_lines() -> None:
    modules = {
        "A": LeanModule(
            name="A",
            path="A.lean",
            imports=("B", "B"),
            import_sites=(
                LeanImport(module="B", line=1, text="import B"),
                LeanImport(module="B", line=2, text="import B"),
            ),
        ),
        "B": LeanModule(name="B", path="B.lean"),
    }

    summary = summarize_module_dag(modules)

    assert summary["edges"] == {"A": ["B"], "B": []}
    assert summary["edge_count"] == 1
    assert summary["duplicate_import_count"] == 1
    assert summary["duplicate_imports"] == [
        {
            "module": "A",
            "path": "A.lean",
            "target": "B",
            "count": 2,
            "generated": False,
            "generatorFamily": "",
            "lines": [1, 2],
            "importTexts": ["import B", "import B"],
            "suggestedAction": "remove repeated import lines or fix the generator to emit each import once",
        }
    ]


def test_module_dag_reports_generated_metadata_and_handwritten_fan_tables() -> None:
    modules = {
        "A.GeneratedOwner": LeanModule(
            name="A.GeneratedOwner",
            path="A/GeneratedOwner.lean",
            imports=("A.Core",),
            tags=("generated",),
            line_count=5000,
        ),
        "A.Owner": LeanModule(
            name="A.Owner",
            path="A/Owner.lean",
            imports=("A.Core",),
            line_count=3000,
        ),
        "A.Core": LeanModule(name="A.Core", path="A/Core.lean", line_count=10),
    }

    summary = summarize_module_dag(modules)

    assert summary["generated_module_count"] == 1
    assert summary["module_metadata"]["A.GeneratedOwner"]["tags"] == ["generated"]
    assert [row["module"] for row in summary["top_large_modules"][:2]] == [
        "A.GeneratedOwner",
        "A.Owner",
    ]
    assert summary["top_large_handwritten_modules"][0]["module"] == "A.Owner"
    assert "A.GeneratedOwner" not in {
        row["module"] for row in summary["top_handwritten_fan_out"]
    }


def test_module_dag_reports_module_naming_smells_and_generated_families() -> None:
    modules = {
        "A.GeneratedScalarBw2Eps0p5Gamma0p8.Base": LeanModule(
            name="A.GeneratedScalarBw2Eps0p5Gamma0p8.Base",
            path="A/GeneratedScalarBw2Eps0p5Gamma0p8/Base.lean",
            tags=("generated",),
        ),
        "A.GeneratedRouteProductionCandidateWithVeryLongStatusName.Case1DensityPremise.DirectForwardSupportTables": LeanModule(
            name="A.GeneratedRouteProductionCandidateWithVeryLongStatusName.Case1DensityPremise.DirectForwardSupportTables",
            path="A/GeneratedRouteProductionCandidateWithVeryLongStatusName/Case1DensityPremise/DirectForwardSupportTables.lean",
            tags=("generated",),
        ),
        "A.HandwrittenVeryLongSemanticTheoremNameWithTooManyPackedProofCaseTokens": LeanModule(
            name="A.HandwrittenVeryLongSemanticTheoremNameWithTooManyPackedProofCaseTokens",
            path="A/HandwrittenVeryLongSemanticTheoremNameWithTooManyPackedProofCaseTokens.lean",
        ),
    }

    summary = summarize_module_dag(modules)

    assert summary["module_name_smell_count"] == 3
    assert summary["module_name_smell_summary"]["generated_encoded_parameters"] == 1
    assert summary["module_name_smell_summary"]["generated_enumerated_case_segment"] == 1
    assert summary["module_name_smell_summary"]["generated_lifecycle_label"] == 1
    assert summary["module_name_smell_summary"]["long_segment"] == 2
    generated = {
        row["generatorFamily"]: row
        for row in summary["generated_family_summary"]
    }
    assert generated["GeneratedScalarBw2Eps0p5Gamma0p8"]["moduleCount"] == 1
    assert generated["GeneratedRouteProductionCandidateWithVeryLongStatusName"]["reasonSummary"]["generated_lifecycle_label"] == 1


def test_module_dag_separates_facade_and_implementation_fanout() -> None:
    modules = {
        "A.Facade": LeanModule(name="A.Facade", path="A/Facade.lean", imports=("A.Core", "A.Util")),
        "A.Owner": LeanModule(
            name="A.Owner",
            path="A/Owner.lean",
            imports=("A.Core",),
            declarations=("owner",),
        ),
        "A.Core": LeanModule(name="A.Core", path="A/Core.lean"),
        "A.Util": LeanModule(name="A.Util", path="A/Util.lean"),
    }

    summary = summarize_module_dag(modules)

    assert summary["module_metadata"]["A.Facade"]["roles"] == ["facade", "pure_barrel"]
    assert summary["module_metadata"]["A.Facade"]["facadeSubtype"] == "pure_barrel"
    assert summary["top_facade_fan_out"][0]["module"] == "A.Facade"
    assert summary["top_implementation_fan_out"][0]["module"] == "A.Owner"


def test_module_dag_reports_facade_subtypes_and_generated_duplicate_families() -> None:
    modules = {
        "A.GeneratedRoute.All": LeanModule(
            name="A.GeneratedRoute.All",
            path="A/GeneratedRoute/All.lean",
            imports=("A.Core", "A.Core"),
            tags=("generated",),
            import_sites=(
                LeanImport(module="A.Core", line=1, text="import A.Core"),
                LeanImport(module="A.Core", line=2, text="import A.Core"),
            ),
        ),
        "A.Public": LeanModule(
            name="A.Public",
            path="A/Public.lean",
            imports=(
                "A.Public.Child1",
                "A.Public.Child2",
                "A.Public.Child3",
                "A.Public.Child4",
                "A.Public.Child5",
            ),
        ),
        "A.Public.Child1": LeanModule(name="A.Public.Child1", path="A/Public/Child1.lean"),
        "A.Public.Child2": LeanModule(name="A.Public.Child2", path="A/Public/Child2.lean"),
        "A.Public.Child3": LeanModule(name="A.Public.Child3", path="A/Public/Child3.lean"),
        "A.Public.Child4": LeanModule(name="A.Public.Child4", path="A/Public/Child4.lean"),
        "A.Public.Child5": LeanModule(name="A.Public.Child5", path="A/Public/Child5.lean"),
        "A.Mixed": LeanModule(
            name="A.Mixed",
            path="A/Mixed.lean",
            imports=("A.Core", "A.Util", "A.X", "A.Y", "A.Z"),
            declarations=("mixed",),
        ),
        "A.Core": LeanModule(name="A.Core", path="A/Core.lean"),
        "A.Util": LeanModule(name="A.Util", path="A/Util.lean"),
        "A.X": LeanModule(name="A.X", path="A/X.lean"),
        "A.Y": LeanModule(name="A.Y", path="A/Y.lean"),
        "A.Z": LeanModule(name="A.Z", path="A/Z.lean"),
    }

    summary = summarize_module_dag(modules)

    assert summary["facade_subtype_summary"] == {
        "generated_all": 1,
        "mixed_barrel_and_theorems": 1,
        "public_root_facade": 1,
    }
    top_facades = {
        row["module"]: row
        for row in summary["top_facade_like_modules"]
    }
    assert top_facades["A.Mixed"]["subtype"] == "mixed_barrel_and_theorems"
    assert top_facades["A.GeneratedRoute.All"]["subtype"] == "generated_all"
    duplicate = summary["duplicate_imports"][0]
    assert duplicate["generated"] is True
    assert duplicate["generatorFamily"] == "GeneratedRoute"
    assert "fix the generator" in duplicate["suggestedAction"]
    assert summary["duplicate_import_family_summary"][0]["generatorFamily"] == "GeneratedRoute"
    assert summary["duplicate_import_family_summary"][0]["generated"] is True


def test_module_dag_reports_missing_internal_imports_and_lexical_markers() -> None:
    modules = {
        "A.Owner": LeanModule(
            name="A.Owner",
            path="A/Owner.lean",
            imports=("A.Missing", "External.Missing"),
            import_sites=(
                LeanImport(module="A.Missing", line=1, text="import A.Missing"),
                LeanImport(module="External.Missing", line=2, text="import External.Missing"),
            ),
            lexical_markers=(
                LeanLexicalMarker(kind="sorry", line=4, text="  sorry"),
                LeanLexicalMarker(kind="todo", line=1, text="-- TODO"),
            ),
        )
    }

    summary = summarize_module_dag(modules)

    assert summary["missing_internal_import_count"] == 1
    assert summary["missing_internal_imports"][0]["targetModule"] == "A.Missing"
    assert summary["lexical_marker_summary"] == {"sorry": 1, "todo": 1}


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


def test_module_dag_reports_root_direct_import_closure_sizes() -> None:
    modules = {
        "A": LeanModule(name="A", path="A.lean", imports=("B", "C")),
        "B": LeanModule(name="B", path="B.lean", imports=("D",)),
        "C": LeanModule(name="C", path="C.lean"),
        "D": LeanModule(name="D", path="D.lean", imports=("E",)),
        "E": LeanModule(name="E", path="E.lean"),
    }

    summary = summarize_module_dag(modules, chosen_roots=("A",))

    assert summary["root_direct_import_closures"] == [
        {
            "root": "A",
            "direct_import": "B",
            "reachable_module_count": 3,
            "sample_modules": ["B", "D", "E"],
        },
        {
            "root": "A",
            "direct_import": "C",
            "reachable_module_count": 1,
            "sample_modules": ["C"],
        },
    ]
