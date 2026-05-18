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
    assert report["reviewerCards"][0]["surfaceCount"] == 2
    assert "proofir.nonclaim_attached_to_root" in diagnostic_ids(report)


def test_clean_core_declaration_graph_joins_quux_surfaces_by_module_decl() -> None:
    ladon_report = load_fixture("ladon-report-quux-clean-core-complex-quadratic.json")
    proofir_index = load_fixture("proofir-bridge-index-quux-complex-quadratic.json")

    report = report_for(proofir_index, ladon_report)

    assert report["summary"]["declarationCount"] == 8
    assert report["summary"]["joinedSurfaceCount"] == 2
    assert {join["matchKind"] for join in report["joins"]} == {"exact_module_decl"}
    assert {join["confidence"] for join in report["joins"]} == {"medium"}
    assert "proofir.packet_stale_source" not in diagnostic_ids(report)
    assert "proofir.nonclaim_attached_to_root" in diagnostic_ids(report)


def test_stale_source_hash_emits_diagnostic_but_still_joins_by_range() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["surfaces"][0]["contentHash"] = "sha256:stale"

    report = report_for(index)

    assert report["joins"][0]["matchKind"] == "exact_source_range_decl"
    assert "proofir.packet_stale_source" in diagnostic_ids(report)


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
    assert "proofir.name_only_join_warning" in diagnostic_ids(report)


def test_bridge_quotes_proofir_status_without_promotion() -> None:
    index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    index["claims"][0]["status"] = "conditional"

    report = report_for(index)

    claim_rows = report["reviewerCards"][0]["claims"]
    by_claim = {row["claimId"]: row for row in claim_rows}
    assert by_claim["claim.complex.root_plus_supplied_sqrt"]["status"] == "conditional"
    assert all(row.get("status") != "established_by_ladon" for row in claim_rows)


def test_no_proofir_index_leaves_empty_optional_report() -> None:
    report = build_bridge_report(load_fixture("ladon-report-complex-quadratic.json"), None)

    assert report["summary"]["proofirIndexPresent"] is False
    assert report["joins"] == []
    assert report["diagnostics"] == []


def test_malformed_index_reports_error_diagnostic() -> None:
    report = build_bridge_report(load_fixture("ladon-report-complex-quadratic.json"), {"artifactKind": "wrong"})

    assert report["summary"]["proofirIndexPresent"] is True
    assert diagnostic_ids(report) == ["proofir.malformed_bridge_index"]


def test_build_bridge_report_does_not_mutate_inputs() -> None:
    ladon_report = load_fixture("ladon-report-complex-quadratic.json")
    proofir_index = load_fixture("proofir-bridge-index-complex-quadratic.json")
    before = copy.deepcopy(proofir_index)

    build_bridge_report(ladon_report, proofir_index)

    assert proofir_index == before
