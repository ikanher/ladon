from __future__ import annotations

import json
from pathlib import Path

from ladon.atlas import atlas_reviewer_cards, build_report_atlas, render_atlas_markdown, render_reviewer_cards_markdown


def test_build_report_atlas_creates_review_surface_nodes(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    atlas = build_report_atlas(tmp_path)

    nodes = {node["id"]: node for node in atlas["nodes"]}

    assert atlas["summary"]["reports"] == 1
    assert nodes["report:quux/owner.json"]["kind"] == "report"
    assert nodes["module:quux:Quux.Semantics.Propagation"]["kind"] == "module"
    assert nodes["declaration:quux:Quux.Semantics.PropagationAlgebra"]["kind"] == "declaration"
    assert nodes["declaration:quux:Quux.Semantics.PropagationAlgebra"]["data"][
        "evidence_confidence"
    ] == "parser_source_range"
    assert nodes["declaration:quux:Quux.Semantics.PropagationAlgebra"]["data"][
        "has_content_hash"
    ] is True
    assert nodes["finding:quux/owner.json:0"]["kind"] == "finding"
    assert nodes["region:quux/owner.json:import_context_region"]["kind"] == "review_region"


def test_build_report_atlas_links_reports_to_review_surface(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    atlas = build_report_atlas(tmp_path)
    edges = {(edge["source"], edge["kind"], edge["target"]) for edge in atlas["edges"]}

    assert (
        "report:quux/owner.json",
        "analyzes_root",
        "module:quux:Quux.Semantics.Propagation",
    ) in edges
    assert (
        "report:quux/owner.json",
        "has_review_region",
        "region:quux/owner.json:import_context_region",
    ) in edges


def test_build_report_atlas_is_deterministic(tmp_path: Path) -> None:
    write_report(tmp_path / "b" / "two.json", sample_report(root="B.Root"))
    write_report(tmp_path / "a" / "one.json", sample_report(root="A.Root"))

    first = build_report_atlas(tmp_path)
    second = build_report_atlas(tmp_path)

    assert first == second
    assert [node["id"] for node in first["nodes"]] == sorted(node["id"] for node in first["nodes"])


def test_build_report_atlas_ignores_auxiliary_json(tmp_path: Path) -> None:
    write_report(tmp_path / ".lean-cache" / "cache.json", {"modules": []})
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    atlas = build_report_atlas(tmp_path)

    assert atlas["summary"]["reports"] == 1
    assert [node["id"] for node in atlas["nodes"] if node["kind"] == "report"] == [
        "report:quux/owner.json"
    ]


def test_render_atlas_markdown_includes_counts_and_reports(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    markdown = render_atlas_markdown(build_report_atlas(tmp_path))

    assert "# Ladon Report Atlas" in markdown
    assert "- reports: 1" in markdown
    assert "| `quux/owner.json` | Quux.Semantics.Propagation | 1 | 1 |" in markdown


def test_atlas_reviewer_cards_include_routing_fields(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    cards = atlas_reviewer_cards(build_report_atlas(tmp_path))

    assert cards == [
        {
            "report": "quux/owner.json",
            "root": "Quux.Semantics.Propagation",
            "extraction_backend": "unknown",
            "top_findings": ["declaration_fan_in_hotspot: Quux.Semantics.PropagationAlgebra"],
            "review_regions": ["Import-context review region"],
            "declaration_evidence": {
                "rows": 1,
                "source_ranges": 1,
                "content_hashes": 1,
                "confidence_counts": {"parser_source_range": 1},
            },
            "packet_evidence": {
                "rows": 1,
                "incomplete": 1,
                "missing": 0,
                "partial": 1,
                "stale": 0,
            },
            "bridge_diagnostics": {
                "diagnostic_count": 0,
                "diagnostic_counts": {},
                "low_confidence_join_count": 0,
                "unmatched_join_count": 0,
                "route_audit_claim_count": 0,
                "route_audit_diagnostic_count": 0,
                "trust_rules": [],
            },
            "strongest_evidence": [
                "finding: declaration_fan_in_hotspot: Quux.Semantics.PropagationAlgebra"
            ],
            "known_non_claims": ["not recorded in atlas"],
            "source_report_json": "quux/owner.json",
            "source_report_text": "quux/owner.txt",
        }
    ]


def test_atlas_reviewer_cards_include_optional_bridge_data(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    cards = atlas_reviewer_cards(build_report_atlas(tmp_path), [sample_bridge_report()])

    assert cards[0]["bridge_diagnostics"] == {
        "diagnostic_count": 2,
        "diagnostic_counts": {
            "proofir.name_only_join_warning": 1,
            "proofir.packet_stale_source": 1,
        },
        "low_confidence_join_count": 1,
        "unmatched_join_count": 0,
        "route_audit_claim_count": 1,
        "route_audit_diagnostic_count": 1,
        "trust_rules": ["name-only joins are warning-only"],
    }


def test_render_reviewer_cards_markdown_is_compact(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "owner.json", sample_report())

    markdown = render_reviewer_cards_markdown(build_report_atlas(tmp_path))

    assert "# Ladon Atlas Reviewer Cards" in markdown
    assert "## `quux/owner.json`" in markdown
    assert "- declaration evidence: rows=1 ranges=1 hashes=1 confidence(parser_source_range=1)" in markdown
    assert "- packet evidence: rows=1 incomplete=1 missing=0 stale=0" in markdown
    assert "- bridge diagnostics: diagnostics=0 low_confidence_joins=0 unmatched=0" in markdown
    assert "- strongest evidence:" in markdown
    assert "not recorded in atlas" in markdown
    assert "no bridge report supplied" in markdown


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def sample_report(root: str = "Quux.Semantics.Propagation") -> dict:
    return {
        "metadata": {
            "analysis_root_module": root,
            "repo_root": "/repo/quux",
        },
        "module_dag": {
            "module_count": 10,
            "edge_count": 12,
            "top_fan_in": [{"module": root, "fan_in": 3}],
            "top_fan_out": [{"module": "Quux.Problems", "fan_out": 4}],
            "root_direct_import_closures": [
                {
                    "root": root,
                    "direct_import": "Quux.Semantics.Core",
                    "reachable_module_count": 2,
                }
            ],
        },
        "declaration_graph": {
            "declaration_count": 2,
            "edge_count": 1,
            "declarations": [
                {
                    "declaration": "Quux.Semantics.PropagationAlgebra",
                    "module": root,
                    "sourcePath": "Quux/Semantics/Propagation.lean",
                    "sourceRange": {"startLine": 12, "endLine": 20},
                    "contentHash": "sha256:propagation",
                    "confidence": "parser_source_range",
                }
            ],
            "top_fan_in": [
                {"declaration": "Quux.Semantics.PropagationAlgebra", "fan_in": 8}
            ],
            "top_fan_out": [
                {"declaration": "Quux.Semantics.OrderedPropagationGraph.propagate", "fan_out": 3}
            ],
        },
        "findings": [
            {
                "kind": "declaration_fan_in_hotspot",
                "subject": "Quux.Semantics.PropagationAlgebra",
                "count": 8,
            }
        ],
        "packet_evidence": [
            {
                "packet_dir": "/packets/review",
                "status": "partial",
                "profile": "review_packet",
                "profile_status": "partial",
                "score": 1,
                "max_score": 3,
            }
        ],
        "review_regions": [
            {
                "kind": "import_context_region",
                "title": "Import-context review region",
                "signal_count": 1,
                "signals": [
                    {
                        "kind": "root_import_closure",
                        "subject": f"{root} -> Quux.Semantics.Core",
                        "count": 2,
                    }
                ],
            }
        ],
    }


def sample_bridge_report(root: str = "Quux.Semantics.Propagation") -> dict:
    return {
        "reviewerCards": [{"root": root}],
        "joins": [
            {
                "surfaceId": "surface.name_only",
                "declarationName": "target",
                "matchKind": "basename_only",
                "confidence": "low",
                "warningOnly": True,
            }
        ],
        "diagnostics": [
            {
                "ruleId": "proofir.name_only_join_warning",
                "level": "warning",
                "subject": "surface.name_only",
            },
            {
                "ruleId": "proofir.packet_stale_source",
                "level": "warning",
                "subject": "surface.name_only",
            },
        ],
        "routeAudit": {
            "summary": {"claimRouteCount": 1, "diagnosticCount": 1},
            "routes": [],
        },
        "trustRules": ["name-only joins are warning-only"],
    }
