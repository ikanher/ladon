from __future__ import annotations

import json
from pathlib import Path

from ladon.analysis.claim_authority import audit_claim_authority
from ladon.analysis.conditional_signature import conditional_signature_diagnostics


FIXTURES = Path(__file__).parent / "fixtures" / "claim_authority"


def load_routes() -> dict:
    return json.loads((FIXTURES / "routes.json").read_text(encoding="utf-8"))


def diagnostic_ids(report: dict) -> list[str]:
    return [row["ruleId"] for row in report["diagnostics"]]


def diagnostics_by_subject(report: dict) -> dict[str, list[str]]:
    by_subject: dict[str, list[str]] = {}
    for row in report["diagnostics"]:
        by_subject.setdefault(row["subject"], []).append(row["ruleId"])
    return by_subject


def test_route_audit_catches_closed_claim_with_imported_evidence() -> None:
    fixture = load_routes()

    report = audit_claim_authority(
        [fixture["claims"][0]],
        joins=fixture["joins"],
        surfaces=fixture["surfaces"],
    )

    assert "ladon.claim.closed_with_imported_evidence" in diagnostic_ids(report)
    diagnostic = report["diagnostics"][0]
    assert diagnostic["evidenceName"] == "finiteWindow"
    assert diagnostic["authority"] == "imported_interval_certified"
    assert "not a proof invalidation" in diagnostic["message"]


def test_route_audit_catches_endpoint_scope_overclaim() -> None:
    fixture = load_routes()

    report = audit_claim_authority(
        [fixture["claims"][1]],
        joins=fixture["joins"],
        surfaces=fixture["surfaces"],
    )

    assert "ladon.claim.endpoint_scope_overclaim" in diagnostic_ids(report)
    diagnostic = report["diagnostics"][0]
    assert diagnostic["claimedScope"] == "arbitrary_neighbor_event_dp"
    assert diagnostic["observedScope"] == "sampled_null_event_dp"


def test_route_audit_catches_all_lean_scalar_replay_overclaim() -> None:
    fixture = load_routes()

    report = audit_claim_authority(
        [fixture["claims"][2]],
        joins=fixture["joins"],
        surfaces=fixture["surfaces"],
    )

    assert "ladon.evidence.authority_mismatch" in diagnostic_ids(report)
    assert report["diagnostics"][0]["evidenceName"] == "scalarRows"


def test_route_audit_accepts_scoped_and_honestly_imported_routes() -> None:
    fixture = load_routes()

    report = audit_claim_authority(
        [fixture["claims"][3], fixture["claims"][4]],
        joins=fixture["joins"],
        surfaces=fixture["surfaces"],
    )

    by_subject = diagnostics_by_subject(report)
    assert "ladon.claim.endpoint_scope_overclaim" not in by_subject.get("claim.sampled_null.scoped", [])
    assert "ladon.claim.closed_with_imported_evidence" not in by_subject.get("claim.imported.honest", [])


def test_allowed_external_evidence_does_not_mask_closed_claim_overclaim() -> None:
    fixture = load_routes()
    claim = dict(fixture["claims"][0])
    claim["allowedExternalEvidence"] = ["finiteWindow"]

    report = audit_claim_authority([claim], joins=fixture["joins"], surfaces=fixture["surfaces"])

    assert "ladon.claim.closed_with_imported_evidence" in diagnostic_ids(report)


def test_route_audit_keeps_source_attachment_separate_from_authority() -> None:
    fixture = load_routes()

    report = audit_claim_authority(
        [fixture["claims"][0]],
        joins=fixture["joins"],
        surfaces=fixture["surfaces"],
    )

    route = report["routes"][0]
    primary = route["primaryTheoremSurfaces"][0]
    assert primary["attachmentConfidence"] == "high"
    assert primary["matchKind"] == "exact_source_hash_decl"
    assert route["claimedAuthority"] == ["lean_proved"]
    assert route["requiredEvidenceAuthorities"]["finiteWindow"] == ["imported_interval_certified"]


def test_route_audit_reports_missing_primary_theorem_surface() -> None:
    fixture = load_routes()
    claim = dict(fixture["claims"][0])
    claim["primaryTheoremSurfaces"] = []

    report = audit_claim_authority([claim], joins=fixture["joins"], surfaces=fixture["surfaces"])

    assert "ladon.claim.missing_primary_theorem_surface" in diagnostic_ids(report)


def test_route_audit_records_weak_primary_theorem_attachment() -> None:
    fixture = load_routes()
    claim = dict(fixture["claims"][3])
    claim["primaryTheoremSurfaces"] = ["surface.basename_only"]

    report = audit_claim_authority([claim], joins=fixture["joins"], surfaces=fixture["surfaces"])

    primary = report["routes"][0]["primaryTheoremSurfaces"][0]
    assert primary["attachmentConfidence"] == "low"
    assert primary["warningOnly"] is True


def test_final_sounding_conditional_signature_is_warning_only() -> None:
    declarations = [
        {
            "declaration": "BMinSep.CountBucket.closed_eventDP",
            "signature": (FIXTURES / "RouteSurface.lean").read_text(encoding="utf-8"),
        }
    ]

    diagnostics = conditional_signature_diagnostics(declarations)

    assert diagnostics == [
        {
            "ruleId": "ladon.theorem.final_name_conditional_statement",
            "level": "warning",
            "subject": "BMinSep.CountBucket.closed_eventDP",
            "message": "Final-sounding theorem name exposes conditional premise token EvidenceAt; this is a review hint, not proof that the theorem, witness, or claim is invalid.",
            "authorityAuditOnly": True,
            "token": "EvidenceAt",
        }
    ]


def test_conditional_signature_is_lowered_when_route_is_honestly_conditional() -> None:
    declarations = [
        {
            "declaration": "BMinSep.CountBucket.closed_eventDP",
            "signature": "theorem closed_eventDP (hForwardCDF : EvidenceAt) : True",
        }
    ]
    claims = [
        {
            "claimId": "claim.imported.honest",
            "claimedAuthority": "conditional_external_evidence",
            "primaryTheoremSurfaces": [
                {
                    "surfaceId": "surface.closed",
                    "declarationName": "BMinSep.CountBucket.closed_eventDP",
                }
            ],
        }
    ]

    diagnostics = conditional_signature_diagnostics(declarations, claims)

    assert diagnostics[0]["level"] == "info"
    assert diagnostics[0]["ruleId"] == "ladon.theorem.final_name_conditional_statement"


def test_conditional_signature_lowering_is_declaration_linked() -> None:
    declarations = [
        {
            "declaration": "BMinSep.CountBucket.closed_eventDP",
            "signature": "theorem closed_eventDP (hForwardCDF : EvidenceAt) : True",
        },
        {
            "declaration": "BMinSep.Other.production_eventDP",
            "signature": "theorem production_eventDP (falsePkg : Package) : True",
        },
    ]
    claims = [
        {
            "claimId": "claim.imported.honest",
            "claimedAuthority": "conditional_external_evidence",
            "primaryTheoremSurfaces": [
                {
                    "surfaceId": "surface.closed",
                    "declarationName": "BMinSep.CountBucket.closed_eventDP",
                }
            ],
        }
    ]

    diagnostics = conditional_signature_diagnostics(declarations, claims)
    by_subject = {row["subject"]: row for row in diagnostics}

    assert by_subject["BMinSep.CountBucket.closed_eventDP"]["level"] == "info"
    assert by_subject["BMinSep.Other.production_eventDP"]["level"] == "warning"
