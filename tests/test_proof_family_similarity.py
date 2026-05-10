from __future__ import annotations

from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.proof_family_similarity import proof_family_similarity_candidates
from ladon.ir import LeanDeclaration
from ladon.render import render_text


def test_proof_family_similarity_detects_high_overlap_family() -> None:
    declarations = {
        "A.left_ge_one": LeanDeclaration(
            name="A.left_ge_one",
            module="A",
            kind="theorem",
            references=("A.kernel", "MissingLemma", "localValue"),
        ),
        "A.right_ge_one": LeanDeclaration(
            name="A.right_ge_one",
            module="A",
            kind="theorem",
            references=("A.kernel", "MissingLemma", "otherLocal"),
        ),
        "A.kernel": LeanDeclaration(name="A.kernel", module="A", kind="def"),
    }
    graph = summarize_declaration_graph(declarations)

    candidates = graph["proof_family_similarity_candidates"]

    assert candidates[0]["suffix"] == "ge_one"
    assert candidates[0]["best_pair"] == ["A.left_ge_one", "A.right_ge_one"]
    assert candidates[0]["max_reference_overlap"] == 1.0
    assert candidates[0]["max_unresolved_profile_overlap"] == 1.0
    assert candidates[0]["shared_kind"] is True


def test_proof_family_similarity_ignores_low_overlap_family() -> None:
    declarations = {
        "A.left_ge_one": LeanDeclaration(
            name="A.left_ge_one",
            module="A",
            references=("A.leftKernel", "MissingLemma"),
        ),
        "A.right_ge_one": LeanDeclaration(
            name="A.right_ge_one",
            module="A",
            references=("A.rightKernel", "x"),
        ),
        "A.leftKernel": LeanDeclaration(name="A.leftKernel", module="A"),
        "A.rightKernel": LeanDeclaration(name="A.rightKernel", module="A"),
    }
    edges = {
        "A.left_ge_one": ["A.leftKernel"],
        "A.right_ge_one": ["A.rightKernel"],
        "A.leftKernel": [],
        "A.rightKernel": [],
    }
    unresolved_profiles = {
        "A.left_ge_one": {"actionable_unknown": 1},
        "A.right_ge_one": {"local_or_field_candidate": 1},
    }

    assert proof_family_similarity_candidates(declarations, edges, unresolved_profiles) == []


def test_text_report_renders_proof_family_similarity_candidates() -> None:
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
            "declaration_count": 2,
            "edge_count": 0,
            "unresolved_reference_count": 0,
            "proof_family_similarity_candidates": [
                {
                    "suffix": "ge_one",
                    "count": 2,
                    "best_pair": ["A.left_ge_one", "A.right_ge_one"],
                    "similarity_score": 1.0,
                    "max_reference_overlap": 1.0,
                    "max_unresolved_profile_overlap": 0.0,
                    "fan_out_delta": 0,
                    "shared_kind": True,
                }
            ],
        },
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Proof Family Similarity Candidates" in text
    assert "similar proof-family candidate" in text
