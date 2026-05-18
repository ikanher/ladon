from __future__ import annotations

from ladon.analysis.review_regions import summarize_review_regions
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
