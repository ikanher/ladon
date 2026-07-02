"""Claim authority route auditing for quoted proof/evidence metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ladon.analysis.proof_surface import (
    combined_surface_rows,
    proof_surface_context,
    proof_surface_route_diagnostics,
    proof_surface_route_row,
    proof_surface_summary,
    proof_surface_witness_diagnostics,
)


CLOSED_STATUSES = {"closed", "lean_closed", "fully_proved"}
CLOSED_AUTHORITIES = {"lean_closed", "lean_proved", "fully_proved"}
PRODUCTION_STATUSES = {"production", "fully_proved", "lean_closed", "closed"}
PRODUCTION_AUTHORITIES = {"production", "fully_proved", "lean_closed", "lean_proved"}
CONDITIONAL_AUTHORITIES = {"conditional_external_evidence"}
IMPORTED_AUTHORITIES = {
    "external_certificate",
    "imported_interval_certified",
    "imported_numeric",
    "interval_certified",
}
WEAK_AUTHORITIES = IMPORTED_AUTHORITIES | {"diagnostic", "smoke", "unchecked"}
KNOWN_AUTHORITIES = (
    CLOSED_AUTHORITIES
    | CONDITIONAL_AUTHORITIES
    | IMPORTED_AUTHORITIES
    | {"diagnostic", "lean_checker", "smoke", "unchecked"}
)
SCOPE_OVERCLAIMS = {
    ("arbitrary_neighbor_event_dp", "sampled_null_event_dp"),
}


@dataclass(frozen=True)
class EvidenceAuthority:
    """Authority label attached to one required evidence route row."""

    name: str
    authorities: tuple[str, ...]


@dataclass(frozen=True)
class TheoremSurfaceRef:
    """A theorem surface referenced by a claim route."""

    surface_id: str
    declaration_name: str = ""
    endpoint_scope: str = ""
    role: str = "primary"


@dataclass(frozen=True)
class ClaimRoute:
    """Normalized route metadata for one quoted external claim."""

    claim_id: str
    status: str = ""
    claimed_status: str = ""
    authority: tuple[str, ...] = ()
    claimed_authority: tuple[str, ...] = ()
    endpoint_scope: str = ""
    primary_theorem_surfaces: tuple[TheoremSurfaceRef, ...] = ()
    supporting_theorem_surfaces: tuple[TheoremSurfaceRef, ...] = ()
    background_theorem_surfaces: tuple[TheoremSurfaceRef, ...] = ()
    required_evidence: tuple[EvidenceAuthority, ...] = ()
    allowed_external_evidence: frozenset[str] = field(default_factory=frozenset)
    nonclaims: tuple[str, ...] = ()
    proof_surface: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_status(self) -> str:
        """Return the strongest status label supplied by the route row."""

        return self.claimed_status or self.status

    @property
    def effective_authorities(self) -> tuple[str, ...]:
        """Return claim-authority labels with legacy authority fallback."""

        return self.claimed_authority or self.authority


def audit_claim_authority(
    claim_rows: Any,
    *,
    joins: list[dict[str, Any]] | None = None,
    surfaces: Any = None,
    proof_surface_witness: dict[str, Any] | None = None,
    proof_surface_joins: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit claim route rows and return diagnostics plus normalized routes."""

    routes = [normalize_claim_route(row) for row in claim_rows if isinstance(row, dict)]
    all_joins = [*(joins or []), *(proof_surface_joins or [])]
    join_by_surface = joins_by_surface_id(all_joins)
    surface_by_id = surfaces_by_id(combined_surface_rows(surfaces, proof_surface_witness))
    proof_surface_ctx = proof_surface_context(proof_surface_witness, proof_surface_joins or [])
    diagnostics: list[dict[str, Any]] = []
    route_rows = []
    for route in routes:
        route_rows.append(route_row(route, join_by_surface, surface_by_id, proof_surface_ctx))
        diagnostics.extend(route_diagnostics(route, join_by_surface, surface_by_id, proof_surface_ctx))
    diagnostics.extend(proof_surface_witness_diagnostics(proof_surface_ctx))
    proof_surface_diagnostic_count = sum(
        1 for row in diagnostics if str(row.get("ruleId", "")).startswith("ladon.proof_surface.")
    )
    return {
        "routes": route_rows,
        "diagnostics": diagnostics,
        "summary": {
            "claimRouteCount": len(routes),
            "diagnosticCount": len(diagnostics),
            "proofSurfaceWitnessPresent": bool(proof_surface_witness),
            "proofSurfaceDiagnosticCount": proof_surface_diagnostic_count,
            "claimAuthorityDiagnosticsDoNotValidateProofTruth": True,
        },
        "proofSurfaceWitness": proof_surface_summary(proof_surface_ctx),
        "trustNote": "Ladon audits claim authority/evidence route alignment; it does not decide theorem truth, proof correctness, or witness adequacy.",
    }


def route_diagnostics(
    route: ClaimRoute,
    join_by_surface: dict[str, dict[str, Any]],
    surface_by_id: dict[str, dict[str, Any]],
    proof_surface_ctx: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return diagnostics for one normalized claim route."""

    proof_surface_ctx = proof_surface_ctx or {}
    diagnostics: list[dict[str, Any]] = []
    if lacks_route_metadata(route):
        diagnostics.append(
            route_diagnostic(
                "ladon.claim.missing_route_context",
                "info",
                route.claim_id,
                "Claim has quoted status but no route authority metadata; Ladon will not infer full closure.",
            )
        )
    diagnostics.extend(unknown_authority_diagnostics(route))
    diagnostics.extend(closed_with_imported_evidence(route))
    diagnostics.extend(authority_mismatch(route))
    diagnostics.extend(endpoint_scope_overclaim(route, surface_by_id))
    diagnostics.extend(missing_primary_theorem_surface(route, join_by_surface))
    diagnostics.extend(proof_surface_route_diagnostics(route, proof_surface_ctx))
    return diagnostics


def lacks_route_metadata(route: ClaimRoute) -> bool:
    """Return whether a claim has status but no explicit route metadata."""

    return (
        bool(route.status)
        and not route.claimed_status
        and not route.claimed_authority
        and not route.endpoint_scope
        and not route.primary_theorem_surfaces
        and not route.required_evidence
    )


def unknown_authority_diagnostics(route: ClaimRoute) -> list[dict[str, Any]]:
    """Return diagnostics for preserved-but-unknown authority labels."""

    rows = []
    for label in route.effective_authorities:
        if label and label not in KNOWN_AUTHORITIES:
            rows.append(
                route_diagnostic(
                    "ladon.evidence.unknown_authority",
                    "warning",
                    route.claim_id,
                    f"Unknown claim authority {label!r} is preserved and not treated as Lean-closed.",
                    authority=label,
                )
            )
    for evidence in route.required_evidence:
        for label in evidence.authorities:
            if label and label not in KNOWN_AUTHORITIES:
                rows.append(
                    route_diagnostic(
                        "ladon.evidence.unknown_authority",
                        "warning",
                        route.claim_id,
                        f"Unknown evidence authority {label!r} on {evidence.name} is preserved and not treated as Lean-closed.",
                        evidenceName=evidence.name,
                        authority=label,
                    )
                )
    return rows


def closed_with_imported_evidence(route: ClaimRoute) -> list[dict[str, Any]]:
    """Return diagnostics for closed claims that still require imported evidence."""

    if not route_claims_closed(route):
        return []
    rows = []
    for evidence in route.required_evidence:
        imported = [label for label in evidence.authorities if label in IMPORTED_AUTHORITIES]
        for label in imported:
            rows.append(
                route_diagnostic(
                    "ladon.claim.closed_with_imported_evidence",
                    "warning",
                    route.claim_id,
                    f"Claim advertises closed authority, but required evidence {evidence.name} uses {label}; this is an authority/evidence route mismatch, not a proof invalidation.",
                    evidenceName=evidence.name,
                    authority=label,
                )
            )
    return rows


def authority_mismatch(route: ClaimRoute) -> list[dict[str, Any]]:
    """Return diagnostics for production/fully-proved claims with weak evidence."""

    if not route_claims_production_or_fully_proved(route):
        return []
    rows = []
    for evidence in route.required_evidence:
        if route_is_honestly_conditional(route) and evidence_allowed(route, evidence):
            continue
        weak = [label for label in evidence.authorities if label in WEAK_AUTHORITIES]
        for label in weak:
            rows.append(
                route_diagnostic(
                    "ladon.evidence.authority_mismatch",
                    "warning",
                    route.claim_id,
                    f"Claim advertises production or fully proved authority, but evidence {evidence.name} uses {label}; this is an authority/evidence route mismatch, not a proof invalidation.",
                    evidenceName=evidence.name,
                    authority=label,
                )
            )
    return rows


def endpoint_scope_overclaim(
    route: ClaimRoute,
    surface_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return endpoint-scope overclaim diagnostics."""

    claimed = route.endpoint_scope
    if not claimed:
        return []
    rows = []
    for surface_ref in route.primary_theorem_surfaces:
        observed = observed_surface_scope(surface_ref, surface_by_id)
        if not observed or observed == claimed:
            continue
        if (claimed, observed) in SCOPE_OVERCLAIMS:
            rows.append(
                route_diagnostic(
                    "ladon.claim.endpoint_scope_overclaim",
                    "warning",
                    route.claim_id,
                    f"Claim advertises endpoint scope {claimed}, but primary theorem surface {surface_ref.surface_id} records {observed}; this is a claim/evidence route mismatch, not a proof invalidation.",
                    claimedScope=claimed,
                    observedScope=observed,
                    surfaceId=surface_ref.surface_id,
                )
            )
        else:
            rows.append(
                route_diagnostic(
                    "ladon.claim.endpoint_scope_mismatch",
                    "info",
                    route.claim_id,
                    f"Claim endpoint scope {claimed} differs from observed primary theorem scope {observed}; no configured strength relation was applied.",
                    claimedScope=claimed,
                    observedScope=observed,
                    surfaceId=surface_ref.surface_id,
                )
            )
    return rows


def missing_primary_theorem_surface(
    route: ClaimRoute,
    join_by_surface: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return diagnostics for claims without attached primary theorem support."""

    if not route_is_public_claim(route):
        return []
    if not route.primary_theorem_surfaces:
        return [
            route_diagnostic(
                "ladon.claim.missing_primary_theorem_surface",
                "warning",
                route.claim_id,
                "Public claim has no primary theorem surface; Ladon cannot attach the advertised route to a primary Lean declaration.",
            )
        ]
    joined = [
        join_by_surface.get(surface.surface_id, {})
        for surface in route.primary_theorem_surfaces
        if surface.surface_id
    ]
    if any(str(join.get("matchKind", "")) not in {"", "unmatched"} for join in joined):
        return []
    return [
        route_diagnostic(
            "ladon.claim.missing_primary_theorem_surface",
            "warning",
            route.claim_id,
            "Public claim has primary theorem surface references, but none join to a Ladon declaration.",
        )
    ]


def route_row(
    route: ClaimRoute,
    join_by_surface: dict[str, dict[str, Any]],
    surface_by_id: dict[str, dict[str, Any]],
    proof_surface_ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a reviewer-facing route row with attachment separate from authority."""

    proof_surface_ctx = proof_surface_ctx or {}
    primary = [surface_ref_row(surface, join_by_surface, surface_by_id) for surface in route.primary_theorem_surfaces]
    return {
        "claimId": route.claim_id,
        "status": route.status,
        "claimedStatus": route.claimed_status,
        "authority": list(route.authority),
        "claimedAuthority": list(route.claimed_authority),
        "endpointScope": route.endpoint_scope,
        "primaryTheoremSurfaces": primary,
        "supportingTheoremSurfaceCount": len(route.supporting_theorem_surfaces),
        "backgroundTheoremSurfaceCount": len(route.background_theorem_surfaces),
        "requiredEvidenceAuthorities": {
            evidence.name: list(evidence.authorities)
            for evidence in route.required_evidence
        },
        "allowedExternalEvidence": sorted(route.allowed_external_evidence),
        "nonclaims": list(route.nonclaims),
        "proofSurface": proof_surface_route_row(route, proof_surface_ctx),
        "quotedOnly": True,
        "routeGovernanceOnly": True,
    }


def surface_ref_row(
    surface_ref: TheoremSurfaceRef,
    join_by_surface: dict[str, dict[str, Any]],
    surface_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return one primary theorem surface with attachment confidence."""

    join = join_by_surface.get(surface_ref.surface_id, {})
    return {
        "surfaceId": surface_ref.surface_id,
        "declarationName": surface_ref.declaration_name or str(surface_by_id.get(surface_ref.surface_id, {}).get("declarationName", "")),
        "endpointScope": observed_surface_scope(surface_ref, surface_by_id),
        "matchKind": str(join.get("matchKind", "")),
        "attachmentConfidence": str(join.get("confidence", "")),
        "warningOnly": join.get("warningOnly") is True,
    }


def normalize_claim_route(row: dict[str, Any]) -> ClaimRoute:
    """Normalize one external claim row into route-audit fields."""

    return ClaimRoute(
        claim_id=str(row.get("claimId", "")),
        status=str(row.get("status", "")),
        claimed_status=str(row.get("claimedStatus", "")),
        authority=tuple(authority_values(row.get("authority"))),
        claimed_authority=tuple(authority_values(row.get("claimedAuthority"))),
        endpoint_scope=str(row.get("endpointScope", "")),
        primary_theorem_surfaces=tuple(surface_refs(row.get("primaryTheoremSurfaces"), "primary")),
        supporting_theorem_surfaces=tuple(surface_refs(row.get("supportingTheoremSurfaces"), "supporting")),
        background_theorem_surfaces=tuple(surface_refs(row.get("backgroundTheoremSurfaces"), "background")),
        required_evidence=tuple(evidence_authorities(row.get("requiredEvidenceAuthorities"))),
        allowed_external_evidence=frozenset(string_values(row.get("allowedExternalEvidence"))),
        nonclaims=tuple(string_values(row.get("nonclaims"))),
        proof_surface=normalize_proof_surface_route(row),
    )


def normalize_proof_surface_route(row: dict[str, Any]) -> dict[str, Any]:
    """Return proof-surface route metadata from a compact claim row."""

    proof_surface = row.get("proofSurface")
    normalized = dict(proof_surface) if isinstance(proof_surface, dict) else {}
    for key in (
        "specSurfaceId",
        "proofEndpointSurfaceId",
        "endpointSurfaceId",
        "requiresNoDriftGate",
        "requireNoDriftGate",
        "requiresAxiomAudit",
        "requireAxiomAudit",
    ):
        if key in row and key not in normalized:
            normalized[key] = row[key]
    return normalized


def surface_refs(value: Any, role: str) -> list[TheoremSurfaceRef]:
    """Return normalized theorem surface references."""

    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if isinstance(item, str):
            refs.append(TheoremSurfaceRef(surface_id=item, role=role))
        elif isinstance(item, dict):
            refs.append(
                TheoremSurfaceRef(
                    surface_id=str(item.get("surfaceId") or item.get("id") or ""),
                    declaration_name=str(item.get("declarationName", "")),
                    endpoint_scope=str(item.get("endpointScope") or item.get("scope") or ""),
                    role=str(item.get("role", role)),
                )
            )
    return refs


def evidence_authorities(value: Any) -> list[EvidenceAuthority]:
    """Return normalized required evidence authority rows."""

    if not isinstance(value, dict):
        return []
    return [
        EvidenceAuthority(str(name), tuple(authority_values(authorities)))
        for name, authorities in sorted(value.items())
    ]


def authority_values(value: Any) -> list[str]:
    """Return authority values as strings without dropping unknown labels."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, dict):
        return [str(item) for item in value.values() if str(item)]
    return []


def string_values(value: Any) -> list[str]:
    """Return string values from compact route fields."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, dict):
        values = []
        for key, item in value.items():
            if isinstance(item, str):
                values.append(item)
            elif item:
                values.append(str(key))
        return values
    return []


def joins_by_surface_id(joins: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return join rows keyed by surface id."""

    return {
        str(join.get("surfaceId", "")): join
        for join in joins
        if isinstance(join, dict) and join.get("surfaceId")
    }


def surfaces_by_id(surfaces: Any) -> dict[str, dict[str, Any]]:
    """Return surface rows keyed by surface id."""

    if not isinstance(surfaces, list):
        return {}
    return {
        str(surface.get("surfaceId", "")): surface
        for surface in surfaces
        if isinstance(surface, dict) and surface.get("surfaceId")
    }


def observed_surface_scope(
    surface_ref: TheoremSurfaceRef,
    surface_by_id: dict[str, dict[str, Any]],
) -> str:
    """Return observed endpoint scope from a ref or attached surface row."""

    if surface_ref.endpoint_scope:
        return surface_ref.endpoint_scope
    surface = surface_by_id.get(surface_ref.surface_id, {})
    scope = surface.get("endpointScope") or surface.get("scope")
    if isinstance(scope, list):
        return ",".join(str(item) for item in scope)
    return str(scope or "")


def route_claims_closed(route: ClaimRoute) -> bool:
    """Return whether a route advertises closed authority."""

    return (
        route.effective_status in CLOSED_STATUSES
        or any(label in CLOSED_AUTHORITIES for label in route.effective_authorities)
    )


def route_claims_production_or_fully_proved(route: ClaimRoute) -> bool:
    """Return whether a route advertises production or fully proved status."""

    return (
        route.effective_status in PRODUCTION_STATUSES
        or any(label in PRODUCTION_AUTHORITIES for label in route.effective_authorities)
    )


def route_is_public_claim(route: ClaimRoute) -> bool:
    """Return whether the route is public enough to require a primary theorem."""

    return bool(
        route.endpoint_scope
        or route.claimed_status
        or route.claimed_authority
        or route.required_evidence
    )


def route_is_honestly_conditional(route: ClaimRoute) -> bool:
    """Return whether route metadata already labels conditional external evidence."""

    return (
        route.effective_status in CONDITIONAL_AUTHORITIES
        or any(label in CONDITIONAL_AUTHORITIES for label in route.effective_authorities)
        or bool(route.allowed_external_evidence)
    )


def evidence_allowed(route: ClaimRoute, evidence: EvidenceAuthority) -> bool:
    """Return whether external evidence was explicitly allowed by route metadata."""

    return evidence.name in route.allowed_external_evidence


def route_diagnostic(rule_id: str, level: str, subject: str, message: str, **extra: Any) -> dict[str, Any]:
    """Build one route-audit diagnostic row."""

    row: dict[str, Any] = {
        "ruleId": rule_id,
        "level": level,
        "subject": subject,
        "message": message,
        "authorityAuditOnly": True,
    }
    row.update({key: value for key, value in extra.items() if value not in {"", None}})
    return row
