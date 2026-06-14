"""Diagnostics and reviewer cards for ProofIR bridge reports."""

from __future__ import annotations

from typing import Any

from ladon.proofir_input import authority_list, surface_content_hash


def bridge_diagnostics(joins: list[dict[str, Any]], proofir_index: dict[str, Any]) -> list[dict[str, Any]]:
    """Emit conservative bridge diagnostics."""

    diagnostics: list[dict[str, Any]] = []
    joined_surfaces = joined_surface_ids(joins)
    for join in joins:
        diagnostics.extend(join_diagnostics(join))
    diagnostics.extend(stale_source_diagnostics(joins, proofir_index))
    diagnostics.extend(witness_endpoint_diagnostics(proofir_index, joined_surfaces))
    diagnostics.extend(nonclaim_diagnostics(proofir_index, joined_surfaces))
    return diagnostics


def join_diagnostics(join: dict[str, Any]) -> list[dict[str, str]]:
    """Return diagnostics that depend only on one join row."""

    if join["matchKind"] == "unmatched":
        return [
            diagnostic(
                "proofir.unattached_surface",
                "warning",
                join["surfaceId"],
                "ProofIR surface did not join to a Ladon declaration.",
            )
        ]
    if join["matchKind"] == "basename_only":
        return [
            diagnostic(
                "proofir.name_only_join_warning",
                "warning",
                join["surfaceId"],
                "Surface joined by basename only; this is reviewer context, not evidence.",
            )
        ]
    if join["matchKind"] == "source_line_anchor_decl":
        return [
            diagnostic(
                "proofir.source_anchor_join_warning",
                "warning",
                join["surfaceId"],
                "Surface joined by source line anchor only; this is reviewer context, not proof evidence.",
            )
        ]
    return []


def stale_source_diagnostics(
    joins: list[dict[str, Any]],
    proofir_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return diagnostics for source hash drift."""

    surfaces = surfaces_by_id(proofir_index)
    return [
        diagnostic(
            "proofir.packet_stale_source",
            "warning",
            join["surfaceId"],
            "ProofIR surface hash does not match Ladon declaration source hash.",
        )
        for join in joins
        if stale_source_drift(join, surfaces.get(join["surfaceId"], {}))
    ]


def stale_source_drift(join: dict[str, Any], surface: dict[str, Any]) -> bool:
    """Return whether a joined row carries stale source hash evidence."""

    return (
        stale_source_hash_comparable(join)
        and bool(surface_content_hash(surface))
        and bool(join.get("declarationContentHash"))
        and surface_content_hash(surface) != join.get("declarationContentHash")
    )


def stale_source_hash_comparable(join: dict[str, Any]) -> bool:
    """Return whether a joined row has enough identity to compare source hashes."""

    return join.get("matchKind") in {
        "exact_source_range_decl",
        "source_line_anchor_decl",
        "exact_module_decl",
    }


def witness_endpoint_diagnostics(
    proofir_index: dict[str, Any],
    joined_surfaces: set[str],
) -> list[dict[str, Any]]:
    """Return diagnostics for witness endpoints without declaration support."""

    diagnostics: list[dict[str, Any]] = []
    for endpoint in proofir_index.get("witnessEndpoints", []):
        if not isinstance(endpoint, dict):
            continue
        refs = set(str(ref) for ref in endpoint.get("surfaceIds", []))
        if refs and not refs.intersection(joined_surfaces):
            diagnostics.append(
                diagnostic(
                    "proofir.witness_endpoint_without_declaration_join",
                    "warning",
                    str(endpoint.get("endpointId", "")),
                    "Witness endpoint has no joined declaration surface under this Ladon root.",
                )
            )
    return diagnostics


def nonclaim_diagnostics(
    proofir_index: dict[str, Any],
    joined_surfaces: set[str],
) -> list[dict[str, Any]]:
    """Return diagnostics for nonclaims attached to joined root surfaces."""

    diagnostics: list[dict[str, Any]] = []
    for nonclaim in proofir_index.get("nonclaims", []):
        if not isinstance(nonclaim, dict):
            continue
        refs = set(str(ref) for ref in nonclaim.get("surfaceIds", []))
        if refs.intersection(joined_surfaces):
            diagnostics.append(
                diagnostic(
                    "proofir.nonclaim_attached_to_root",
                    "info",
                    str(nonclaim.get("nonclaimId", "")),
                    "A forbidden interpretation is attached to a declaration under this root.",
                )
            )
    return diagnostics


def reviewer_cards(
    ladon_report: dict[str, Any],
    proofir_index: dict[str, Any],
    joins: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    route_audit: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build compact reviewer cards."""

    joined = [join for join in joins if join["matchKind"] != "unmatched"]
    if not joined:
        return []
    return [
        {
            "root": ladon_report.get("metadata", {}).get("analysis_root_module"),
            "surfaceCount": len(joined),
            "claims": joined_claims(proofir_index, joined),
            "witnessEndpoints": joined_witness_endpoints(proofir_index, joined),
            "nonclaims": joined_nonclaims(proofir_index, joined),
            "diagnostics": [row["ruleId"] for row in diagnostics],
            "routeAudit": route_audit_card(route_audit),
            "trustNote": "Ladon structural context only; ProofIR statuses are quoted, not promoted.",
        }
    ]


def route_audit_card(route_audit: dict[str, Any] | None) -> dict[str, Any]:
    """Return compact route-audit metadata for one reviewer card."""

    if not route_audit:
        return {
            "claimRouteCount": 0,
            "diagnosticCount": 0,
            "routes": [],
            "trustNote": "no claim authority route audit supplied",
        }
    summary = route_audit.get("summary", {})
    return {
        "claimRouteCount": int(summary.get("claimRouteCount", 0)),
        "diagnosticCount": int(summary.get("diagnosticCount", 0)),
        "routes": route_audit.get("routes", []),
        "trustNote": str(route_audit.get("trustNote", "")),
    }


def joined_claims(proofir_index: dict[str, Any], joins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return claims attached to joined surfaces."""

    claim_ids = {join["claimId"] for join in joins}
    return [
        joined_claim_row(claim)
        for claim in proofir_index.get("claims", [])
        if isinstance(claim, dict) and claim.get("claimId") in claim_ids
    ]


def joined_claim_row(claim: dict[str, Any]) -> dict[str, Any]:
    """Return a reviewer-facing claim row with quoted metadata preserved."""

    row: dict[str, Any] = {
        "claimId": str(claim.get("claimId", "")),
        "status": str(claim.get("status", "")),
        "authority": authority_list(claim.get("authority")),
        "scope": str(claim.get("scope", "")),
        "quotedOnly": True,
    }
    copy_route_claim_metadata(row, claim)
    copy_optional_claim_metadata(row, claim)
    return row


def copy_route_claim_metadata(target: dict[str, Any], claim: dict[str, Any]) -> None:
    """Copy quoted route-authority metadata into one claim row."""

    for key in ("claimedStatus", "endpointScope"):
        if claim.get(key):
            target[key] = str(claim[key])
    for key in (
        "claimedAuthority",
        "primaryTheoremSurfaces",
        "supportingTheoremSurfaces",
        "backgroundTheoremSurfaces",
        "allowedExternalEvidence",
        "nonclaims",
    ):
        if isinstance(claim.get(key), list) and claim[key]:
            target[key] = list(claim[key])
    if isinstance(claim.get("requiredEvidenceAuthorities"), dict) and claim["requiredEvidenceAuthorities"]:
        target["requiredEvidenceAuthorities"] = {
            str(name): list(authority_list(authority))
            for name, authority in claim["requiredEvidenceAuthorities"].items()
        }


def copy_optional_claim_metadata(target: dict[str, Any], claim: dict[str, Any]) -> None:
    """Copy optional quoted surface metadata into one claim row."""

    for key in ("proofTrust", "extractorGuarantee", "sourcePath", "contentHash"):
        if claim.get(key):
            target[key] = str(claim[key])
    for key in ("replayBoundary", "sourceRange"):
        if isinstance(claim.get(key), dict) and claim[key]:
            target[key] = dict(claim[key])


def joined_witness_endpoints(proofir_index: dict[str, Any], joins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return witness endpoints attached to joined surfaces."""

    surface_ids = {join["surfaceId"] for join in joins}
    rows = []
    for endpoint in proofir_index.get("witnessEndpoints", []):
        if not isinstance(endpoint, dict):
            continue
        refs = set(str(ref) for ref in endpoint.get("surfaceIds", []))
        if refs.intersection(surface_ids):
            rows.append(
                {
                    "endpointId": str(endpoint.get("endpointId", "")),
                    "status": str(endpoint.get("status", "")),
                    "authority": authority_list(endpoint.get("authority")),
                    "scope": str(endpoint.get("scope", "")),
                }
            )
    return rows


def joined_nonclaims(proofir_index: dict[str, Any], joins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return nonclaims attached to joined surfaces."""

    surface_ids = {join["surfaceId"] for join in joins}
    rows = []
    for nonclaim in proofir_index.get("nonclaims", []):
        if not isinstance(nonclaim, dict):
            continue
        refs = set(str(ref) for ref in nonclaim.get("surfaceIds", []))
        if refs.intersection(surface_ids):
            rows.append(
                {
                    "nonclaimId": str(nonclaim.get("nonclaimId", "")),
                    "statement": str(nonclaim.get("statement", "")),
                }
            )
    return rows


def surfaces_by_id(proofir_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return ProofIR surfaces keyed by id."""

    return {
        str(surface.get("surfaceId")): surface
        for surface in proofir_index.get("surfaces", [])
        if isinstance(surface, dict)
    }


def joined_surface_ids(joins: list[dict[str, Any]]) -> set[str]:
    """Return surface ids that joined by any non-empty match kind."""

    return {join["surfaceId"] for join in joins if join["matchKind"] != "unmatched"}


def diagnostic(rule_id: str, level: str, subject: str, message: str) -> dict[str, str]:
    """Build one bridge diagnostic."""

    return {
        "ruleId": rule_id,
        "level": level,
        "subject": subject,
        "message": message,
    }
