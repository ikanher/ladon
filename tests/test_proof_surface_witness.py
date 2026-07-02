from __future__ import annotations

import json
from pathlib import Path

from ladon.proof_surface_witness import normalize_proof_surface_witness
from ladon.proofir_bridge import build_bridge_report
from ladon.proofir_bridge_cli import main as bridge_main


FIXTURES = Path(__file__).parent / "fixtures" / "proof_surface_witness"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def build_fixture_report() -> dict:
    return build_bridge_report(
        load_fixture("ladon-report.json"),
        load_fixture("proofir-index.json"),
        proof_surface_witness=load_fixture("proof-surface-witness.json"),
    )


def diagnostic_ids(report: dict) -> list[str]:
    return [row["ruleId"] for row in report["diagnostics"]]


def diagnostics_by_subject(report: dict) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for diagnostic in report["diagnostics"]:
        rows.setdefault(diagnostic["subject"], []).append(diagnostic["ruleId"])
    return rows


def routes_by_claim(report: dict) -> dict[str, dict]:
    return {
        row["claimId"]: row
        for row in report["routeAudit"]["routes"]
    }


def joins_by_surface(report: dict) -> dict[str, dict]:
    return {
        row["surfaceId"]: row
        for row in report["proofSurfaceJoins"]
    }


def test_normalizes_proof_surface_witness_without_project_name_heuristics() -> None:
    witness = normalize_proof_surface_witness(load_fixture("proof-surface-witness.json"))

    assert witness is not None
    assert witness["valid"] is True
    assert witness["specSurfaces"][0]["proofSurfaceRole"] == "lean_spec_stub"
    assert witness["proofEndpoints"][0]["proofSurfaceRole"] == "lean_proof_endpoint"
    assert witness["specSurfaces"][0]["quotedMetadata"] == {"producerSpecific": "preserved"}
    assert witness["quotedMetadata"] == {"extraTopLevel": {"kept": True}}
    odd_endpoint = {
        row["surfaceId"]: row
        for row in witness["proofEndpoints"]
    }["endpoint.odd"]
    assert odd_endpoint["sourcePath"] == "Odd/Payload.lean"
    assert odd_endpoint["contentHash"] == "sha256:odd-endpoint"


def test_malformed_proof_surface_witness_does_not_fabricate_authority() -> None:
    witness = normalize_proof_surface_witness([])

    assert witness is not None
    assert witness["valid"] is False
    assert witness["surfaces"] == []
    assert witness["diagnostics"][0]["ruleId"] == "ladon.proof_surface.malformed_witness"


def test_bridge_audits_clean_endpoint_and_proof_surface_nonclaims() -> None:
    report = build_fixture_report()
    by_subject = diagnostics_by_subject(report)
    routes = routes_by_claim(report)

    assert report["summary"]["proofSurfaceWitnessPresent"] is True
    assert report["summary"]["proofSurfaceSurfaceCount"] == 12
    assert by_subject["claim.clean"] == ["ladon.proof_surface.clean_endpoint"]
    clean_route = routes["claim.clean"]["proofSurface"]
    assert clean_route["proofEndpoint"]["attachmentConfidence"] == "high"
    assert clean_route["noDriftGates"][0]["status"] == "clean"
    assert clean_route["axiomAudits"][0]["status"] == "clean"
    assert "proof-surface witness rows are not theorem truth" in clean_route["nonclaims"]
    assert "proof-surface witness rows are quoted route-governance evidence only" in report["trustRules"]


def test_bridge_flags_spec_stub_gate_axiom_and_suspicious_axiom_routes() -> None:
    report = build_fixture_report()
    by_subject = diagnostics_by_subject(report)

    assert by_subject["claim.spec_overclaim"] == [
        "ladon.proof_surface.spec_stub_used_as_authority"
    ]
    assert by_subject["claim.missing_gate"] == [
        "ladon.proof_surface.missing_no_drift_gate"
    ]
    assert by_subject["claim.missing_axiom"] == [
        "ladon.proof_surface.missing_axiom_audit"
    ]
    assert "ladon.proof_surface.suspicious_axiom" in by_subject["endpoint.suspicious"]
    assert "Synthetic.Unsafe.assumeFalse" in {
        row.get("axiom", "")
        for row in report["diagnostics"]
        if row["ruleId"] == "ladon.proof_surface.suspicious_axiom"
    }


def test_stale_and_weak_witness_attachments_do_not_clear_clean_endpoint() -> None:
    report = build_fixture_report()
    by_subject = diagnostics_by_subject(report)
    routes = routes_by_claim(report)
    joins = joins_by_surface(report)

    assert "ladon.proof_surface.clean_endpoint" not in by_subject.get("claim.stale", [])
    assert "ladon.proof_surface.clean_endpoint" not in by_subject.get("claim.weak", [])
    assert joins["endpoint.stale"]["matchKind"] == "exact_source_range_decl"
    assert routes["claim.stale"]["proofSurface"]["proofEndpoint"]["staleSource"] is True
    assert joins["endpoint.weak"]["matchKind"] == "basename_only"
    assert routes["claim.weak"]["proofSurface"]["proofEndpoint"]["warningOnly"] is True


def test_role_metadata_not_pipeline_math_names_drives_clean_endpoint_classification() -> None:
    report = build_fixture_report()
    by_subject = diagnostics_by_subject(report)
    routes = routes_by_claim(report)

    assert by_subject["claim.odd_clean"] == ["ladon.proof_surface.clean_endpoint"]
    proof_surface = routes["claim.odd_clean"]["proofSurface"]
    assert proof_surface["specSurface"]["declarationName"] == "Odd.Payload.carried_spec"
    assert proof_surface["proofEndpoint"]["declarationName"] == "Odd.Payload.carried_endpoint"
    assert proof_surface["noDriftGates"][0]["declarationName"] == "Odd.Payload.carried_gate"


def test_witness_wide_frozen_hub_and_escaped_proof_hole_are_reported() -> None:
    report = build_fixture_report()
    by_subject = diagnostics_by_subject(report)

    assert by_subject["Synthetic.SpecHub"] == [
        "ladon.proof_surface.frozen_spec_hub"
    ]
    assert by_subject["Synthetic.ProofCore.escaped_hole"] == [
        "ladon.proof_surface.proof_hole_outside_quarantine"
    ]


def test_embedded_proof_surface_witness_is_accepted() -> None:
    index = load_fixture("proofir-index.json")
    index["proofSurfaceWitness"] = load_fixture("proof-surface-witness.json")

    report = build_bridge_report(load_fixture("ladon-report.json"), index)

    assert "ladon.proof_surface.clean_endpoint" in diagnostic_ids(report)
    assert report["summary"]["proofSurfaceWitnessPresent"] is True


def test_bridge_cli_accepts_optional_proof_surface_witness(tmp_path: Path) -> None:
    output = tmp_path / "bridge-report.json"

    status = bridge_main(
        [
            "--ladon-report",
            str(FIXTURES / "ladon-report.json"),
            "--proofir-index",
            str(FIXTURES / "proofir-index.json"),
            "--proof-surface-witness",
            str(FIXTURES / "proof-surface-witness.json"),
            "--out",
            str(output),
        ]
    )

    assert status == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert "ladon.proof_surface.clean_endpoint" in diagnostic_ids(report)


def test_malformed_witness_is_reported_through_bridge() -> None:
    report = build_bridge_report(
        load_fixture("ladon-report.json"),
        load_fixture("proofir-index.json"),
        proof_surface_witness={"artifactKind": "wrong", "schemaVersion": 1},
    )

    ids = diagnostic_ids(report)
    assert "ladon.proof_surface.malformed_witness" in ids
    assert "ladon.proof_surface.clean_endpoint" not in ids
    assert report["summary"]["proofSurfaceSurfaceCount"] == 0
