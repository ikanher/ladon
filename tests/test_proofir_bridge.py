from __future__ import annotations

import copy
import json
from pathlib import Path

from ladon.proofir_bridge import build_bridge_report


FIXTURES = Path(__file__).parent / "fixtures" / "proofir_bridge"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def report_for(proofir_index: dict | None = None, ladon_report: dict | None = None) -> dict:
    return build_bridge_report(
        ladon_report or load_fixture("ladon-report-complex-quadratic.json"),
        proofir_index or load_fixture("proofir-bridge-index-complex-quadratic.json"),
    )


def diagnostic_ids(report: dict) -> list[str]:
    return [row["ruleId"] for row in report["diagnostics"]]


def test_exact_source_hash_declaration_join_produces_high_confidence_card() -> None:
    report = report_for()

    assert report["artifactKind"] == "ladon_proofir_bridge_report"
    assert report["summary"]["joinedSurfaceCount"] == 2
    first_join = report["joins"][0]
    assert first_join["matchKind"] == "exact_source_hash_decl"
    assert first_join["confidence"] == "high"
    assert first_join["declarationConfidence"] == "source_hash"
    assert first_join["warningOnly"] is False
    assert report["reviewerCards"][0]["surfaceCount"] == 2
    assert "proofir.nonclaim_attached_to_root" in diagnostic_ids(report)
    assert "source-hash and source-range joins establish attachment confidence only" in report["trustRules"]


def test_clean_core_declaration_graph_joins_quux_surfaces_by_module_decl() -> None:
    ladon_report = load_fixture("ladon-report-quux-clean-core-complex-quadratic.json")
    proofir_index = load_fixture("proofir-bridge-index-quux-complex-quadratic.json")

    report = report_for(proofir_index, ladon_report)

    assert report["summary"]["declarationCount"] == 8
    assert report["summary"]["joinedSurfaceCount"] == 2
    assert {join["matchKind"] for join in report["joins"]} == {"exact_module_decl"}
    assert {join["confidence"] for join in report["joins"]} == {"medium"}
    assert {join["declarationConfidence"] for join in report["joins"]} == {"derived"}
    assert "proofir.packet_stale_source" not in diagnostic_ids(report)
    assert "proofir.nonclaim_attached_to_root" in diagnostic_ids(report)


def test_quux_surface_bundle_adapts_and_joins_by_source_hash() -> None:
    surface_bundle = load_fixture("proofir-lean-surface-bundle-quux-complex-quadratic.json")

    report = report_for(surface_bundle)

    assert report["summary"]["surfaceCount"] == 1
    assert report["joins"][0]["matchKind"] == "exact_source_hash_decl"
    assert report["joins"][0]["confidence"] == "high"
    claim = report["reviewerCards"][0]["claims"][0]
    assert claim["status"] == "not_replayed_by_extractor"
    assert claim["authority"] == ["lean_kernel_external"]
    assert claim["quotedOnly"] is True
    assert claim["proofTrust"] == "lean_source_marker_extracted"
    assert claim["replayBoundary"]["recommendedCommand"] == "lake env lean Quux/Semantics/ComplexQuadratic.lean"
    assert claim["extractorGuarantee"] == "source_surface_only"


def test_surface_bundle_top_level_source_backfills_surface_source_fields() -> None:
    surface_bundle = load_fixture("proofir-lean-surface-bundle-quux-complex-quadratic.json")
    surface_bundle["surfaces"][0].pop("sourcePath")
    surface_bundle["surfaces"][0].pop("contentHash")

    report = report_for(surface_bundle)

    assert report["joins"][0]["matchKind"] == "exact_source_hash_decl"
    claim = report["reviewerCards"][0]["claims"][0]
    assert claim["sourcePath"] == "Quux/Semantics/ComplexQuadratic.lean"
    assert claim["contentHash"] == "sha256:complex-quadratic-source"


def test_quux_source_hash_alias_produces_source_hash_join_without_mutation() -> None:
    proofir_index = load_fixture("proofir-bridge-index-sourcehash-quux-complex-quadratic.json")
    before = copy.deepcopy(proofir_index)

    report = report_for(proofir_index)

    assert report["joins"][0]["matchKind"] == "exact_source_hash_decl"
    assert report["joins"][0]["confidence"] == "high"
    assert "proofir.packet_stale_source" not in diagnostic_ids(report)
    assert report["reviewerCards"][0]["claims"][0]["authority"] == ["lean_kernel_external"]
    assert proofir_index == before


def test_quux_source_anchor_is_low_confidence_warning_not_hash_join() -> None:
    proofir_index = load_fixture("proofir-bridge-index-sourceanchor-quux-complex-quadratic.json")

    report = report_for(proofir_index)

    join = report["joins"][0]
    assert join["matchKind"] == "source_line_anchor_decl"
    assert join["confidence"] == "low"
    assert join["warningOnly"] is True
    assert join["sourceAnchor"]["lineSha256"] == "sha256:root-plus-line"
    assert "declarationContentHash" in join
    assert "proofir.source_anchor_join_warning" in diagnostic_ids(report)
    assert "proofir.packet_stale_source" not in diagnostic_ids(report)


def test_stale_source_hash_emits_diagnostic_but_still_joins_by_range() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["surfaces"][0]["contentHash"] = "sha256:stale"

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "exact_source_range_decl"
    assert "proofir.packet_stale_source" in diagnostic_ids(report)


def test_stale_source_hash_alias_emits_diagnostic_but_still_joins_by_range() -> None:
    index = load_fixture("proofir-bridge-index-sourcehash-quux-complex-quadratic.json")
    index["surfaces"][0]["sourceHash"] = "sha256:stale"

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "exact_source_range_decl"
    assert "proofir.packet_stale_source" in diagnostic_ids(report)


def test_stale_source_hash_emits_diagnostic_on_source_anchor_fallback() -> None:
    index = load_fixture("proofir-bridge-index-sourceanchor-quux-complex-quadratic.json")
    index["surfaces"][0]["sourceHash"] = "sha256:stale"

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "source_line_anchor_decl"
    assert "proofir.packet_stale_source" in diagnostic_ids(report)


def test_stale_source_hash_emits_diagnostic_on_module_decl_fallback() -> None:
    index = load_fixture("proofir-bridge-index-sourcehash-quux-complex-quadratic.json")
    surface = index["surfaces"][0]
    surface["sourceHash"] = "sha256:stale"
    surface.pop("sourceRange")
    surface.pop("sourcePath")

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "exact_module_decl"
    assert "proofir.packet_stale_source" in diagnostic_ids(report)


def test_explicit_declaration_rows_are_preferred_over_derived_rows() -> None:
    ladon_report = {
        "metadata": {"analysis_root_module": "A"},
        "declaration_graph": {
            "declarations": [
                {
                    "declaration": "A.exact",
                    "module": "A",
                    "sourcePath": "A.lean",
                    "contentHash": "sha256:a",
                }
            ],
            "edges": {"A.derived_only": []},
            "top_fan_in": [{"declaration": "A.derived_only"}],
        },
    }
    proofir_index = {
        "artifactKind": "proofir_bridge_index",
        "surfaces": [
            {
                "surfaceId": "surface.a",
                "claimId": "claim.a",
                "module": "A",
                "declarationName": "A.exact",
                "sourcePath": "A.lean",
                "contentHash": "sha256:a",
            }
        ],
    }

    report = build_bridge_report(ladon_report, proofir_index)

    assert report["summary"]["declarationCount"] == 1
    assert report["joins"][0]["matchKind"] == "exact_source_hash_decl"


def test_hash_and_range_joins_outrank_module_only_rows() -> None:
    surface = {
        "surfaceId": "surface.a",
        "claimId": "claim.a",
        "module": "A",
        "declarationName": "A.target",
        "sourcePath": "A.lean",
        "sourceRange": {"startLine": 7, "endLine": 9},
        "contentHash": "sha256:new",
    }
    ladon_report = {
        "declaration_graph": {
            "declarations": [
                {"declaration": "A.target", "module": "A"},
                {
                    "declaration": "A.target",
                    "module": "A",
                    "sourcePath": "A.lean",
                    "sourceRange": {"startLine": 7, "endLine": 9},
                    "contentHash": "sha256:new",
                },
            ]
        }
    }

    hash_report = build_bridge_report(
        ladon_report,
        {"artifactKind": "proofir_bridge_index", "surfaces": [surface]},
    )
    range_surface = {key: value for key, value in surface.items() if key != "contentHash"}
    range_report = build_bridge_report(
        ladon_report,
        {"artifactKind": "proofir_bridge_index", "surfaces": [range_surface]},
    )

    assert hash_report["joins"][0]["matchKind"] == "exact_source_hash_decl"
    assert range_report["joins"][0]["matchKind"] == "exact_source_range_decl"


def test_missing_declaration_emits_unattached_surface() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["surfaces"][0]["declarationName"] = "Quux.Semantics.ComplexQuadratic.missing"

    report = report_for(index)

    assert "proofir.unattached_surface" in diagnostic_ids(report)
    assert report["summary"]["unmatchedSurfaceCount"] == 1


def test_witness_endpoint_without_joined_surface_warns() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["witnessEndpoints"][0]["surfaceIds"] = ["surface.missing"]

    report = report_for(index)

    assert "proofir.witness_endpoint_without_declaration_join" in diagnostic_ids(report)


def test_name_only_join_is_low_confidence_warning() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    surface = index["surfaces"][0]
    surface.pop("module")
    surface.pop("sourcePath")
    surface.pop("sourceRange")
    surface.pop("contentHash")
    surface["declarationName"] = "root_plus_is_root"

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "basename_only"
    assert report["joins"][0]["confidence"] == "low"
    assert report["joins"][0]["warningOnly"] is True
    assert "proofir.name_only_join_warning" in diagnostic_ids(report)


def test_bridge_quotes_proofir_status_without_promotion() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["claims"][0]["status"] = "conditional"

    report = report_for(index)

    claim_rows = report["reviewerCards"][0]["claims"]
    by_claim = {row["claimId"]: row for row in claim_rows}
    assert by_claim["claim.complex.root_plus_supplied_sqrt"]["status"] == "conditional"
    assert all(row.get("status") != "established_by_ladon" for row in claim_rows)


def test_bridge_preserves_route_authority_metadata_and_emits_audit_diagnostic() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["claims"][0].update(
        {
            "claimedStatus": "lean_closed",
            "claimedAuthority": "lean_proved",
            "endpointScope": "sampled_null_event_dp",
            "primaryTheoremSurfaces": [index["surfaces"][0]["surfaceId"]],
            "requiredEvidenceAuthorities": {"finiteWindow": "imported_interval_certified"},
            "allowedExternalEvidence": [],
            "nonclaims": ["not arbitrary_neighbor_event_dp"],
        }
    )

    report = report_for(index)

    assert "ladon.claim.closed_with_imported_evidence" in diagnostic_ids(report)
    claim = report["reviewerCards"][0]["claims"][0]
    assert claim["claimedAuthority"] == ["lean_proved"]
    assert claim["requiredEvidenceAuthorities"] == {
        "finiteWindow": ["imported_interval_certified"]
    }
    route = report["routeAudit"]["routes"][0]
    assert route["primaryTheoremSurfaces"][0]["attachmentConfidence"] == "high"
    assert "claim authority diagnostics audit evidence-route alignment only" in report["trustRules"]


def test_bridge_preserves_unknown_authority_without_upgrading() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["claims"][0].update(
        {
            "claimedAuthority": "project_local_magic",
            "primaryTheoremSurfaces": [index["surfaces"][0]["surfaceId"]],
        }
    )

    report = report_for(index)

    assert "ladon.evidence.unknown_authority" in diagnostic_ids(report)
    claim = report["reviewerCards"][0]["claims"][0]
    assert claim["claimedAuthority"] == ["project_local_magic"]


def test_no_proofir_index_leaves_empty_optional_report() -> None:
    report = build_bridge_report(load_fixture("ladon-report-complex-quadratic.json"), None)

    assert report["summary"]["proofirIndexPresent"] is False
    assert report["joins"] == []
    assert report["diagnostics"] == []


def test_malformed_index_reports_error_diagnostic() -> None:
    report = build_bridge_report(load_fixture("ladon-report-complex-quadratic.json"), {"artifactKind": "wrong"})

    assert report["summary"]["proofirIndexPresent"] is True
    assert diagnostic_ids(report) == ["proofir.malformed_bridge_index"]
    assert "proofir_bridge_index" in report["diagnostics"][0]["message"]
    assert "proof_ir_lean_surface_bundle" in report["diagnostics"][0]["message"]


def test_non_object_proofir_payload_reports_malformed_diagnostic() -> None:
    report = build_bridge_report(load_fixture("ladon-report-complex-quadratic.json"), [])

    assert report["summary"]["proofirIndexPresent"] is True
    assert report["joins"] == []
    assert diagnostic_ids(report) == ["proofir.malformed_bridge_index"]


def test_build_bridge_report_does_not_mutate_inputs() -> None:
    ladon_report = load_fixture("ladon-report-complex-quadratic.json")
    proofir_index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    before = copy.deepcopy(proofir_index)

    build_bridge_report(ladon_report, proofir_index)

    assert proofir_index == before
