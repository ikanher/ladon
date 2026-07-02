"""Proof-surface witness route auditing.

This module consumes normalized witness rows and claim-route objects. It emits
review-routing diagnostics about authority attachment, no-drift gates, axiom
audits, and proof-hole quarantine. It does not replay Lean or decide theorem
truth.
"""

from __future__ import annotations

from typing import Any


PROOF_SURFACE_CLEAN_GATE_STATUSES = {"clean", "ok", "passed", "rfl", "success", "verified"}
PROOF_SURFACE_CLEAN_AXIOM_STATUSES = {"clean", "ok", "passed", "verified"}
PROOF_SURFACE_STRONG_MATCHES = {"exact_source_hash_decl", "exact_source_range_decl"}


def combined_surface_rows(
    surfaces: Any,
    proof_surface_witness: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return ProofIR and proof-surface witness surfaces in one lookup list."""

    rows = list(surfaces) if isinstance(surfaces, list) else []
    if isinstance(proof_surface_witness, dict):
        rows.extend(dict_rows(proof_surface_witness.get("surfaces", [])))
    return rows


def proof_surface_context(
    witness: dict[str, Any] | None,
    joins: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build lookup maps for proof-surface route auditing."""

    if not isinstance(witness, dict):
        return empty_context()
    surfaces = dict_rows(witness.get("surfaces", []))
    return {
        "present": True,
        "valid": witness.get("valid") is True,
        "diagnostics": dict_rows(witness.get("diagnostics", [])),
        "surfaces": rows_by_key(surfaces, "surfaceId"),
        "surfacesByDeclaration": rows_by_key(surfaces, "declarationName"),
        "joins": rows_by_key(joins, "surfaceId"),
        "gates": dict_rows(witness.get("noDriftGates", [])),
        "axiomAudits": dict_rows(witness.get("axiomAudits", [])),
        "proofHolePolicy": policy_dict(witness.get("proofHolePolicy")),
        "nonclaims": list(witness.get("nonclaims", [])),
    }


def empty_context() -> dict[str, Any]:
    """Return a stable context when no witness is supplied."""

    return {
        "present": False,
        "valid": False,
        "diagnostics": [],
        "surfaces": {},
        "surfacesByDeclaration": {},
        "joins": {},
        "gates": [],
        "axiomAudits": [],
        "proofHolePolicy": {},
        "nonclaims": [],
    }


def dict_rows(rows: Any) -> list[dict[str, Any]]:
    """Return dictionary rows from a JSON-like list."""

    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def rows_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Return rows keyed by a non-empty string field."""

    return {
        str(row.get(key, "")): row
        for row in rows
        if row.get(key)
    }


def policy_dict(policy: Any) -> dict[str, Any]:
    """Return proof-hole policy as a dictionary."""

    return policy if isinstance(policy, dict) else {}


def proof_surface_summary(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return compact proof-surface witness summary metadata."""

    return {
        "present": ctx.get("present") is True,
        "valid": ctx.get("valid") is True,
        "surfaceCount": len(ctx.get("surfaces", {})),
        "gateCount": len(ctx.get("gates", [])),
        "axiomAuditCount": len(ctx.get("axiomAudits", [])),
        "nonclaims": list(ctx.get("nonclaims", [])),
        "quotedOnly": True,
        "routeGovernanceOnly": True,
    }


def proof_surface_witness_diagnostics(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return witness-wide proof-surface diagnostics and classifications."""

    if not ctx.get("present"):
        return []
    diagnostics = [row for row in ctx.get("diagnostics", []) if isinstance(row, dict)]
    diagnostics.extend(suspicious_axiom_diagnostics(ctx))
    diagnostics.extend(frozen_spec_hub_diagnostics(ctx))
    diagnostics.extend(proof_hole_quarantine_diagnostics(ctx))
    return diagnostics


def proof_surface_route_diagnostics(route: Any, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return proof-surface route diagnostics for one claim."""

    if not ctx.get("valid"):
        return []
    endpoint = route_proof_endpoint(route, ctx)
    spec = route_spec_surface(route, ctx)
    rows = spec_stub_authority_diagnostics(route, ctx)
    rows.extend(missing_gate_diagnostics(route, spec, endpoint, ctx))
    rows.extend(missing_axiom_diagnostics(route, endpoint, ctx))
    rows.extend(clean_endpoint_diagnostics(route, spec, endpoint, ctx))
    return rows


def missing_gate_diagnostics(
    route: Any,
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return missing no-drift gate diagnostics for one route."""

    if not proof_surface_requires_gate(route, endpoint):
        return []
    if clean_gate_for_route(spec, endpoint, ctx):
        return []
    return [
        proof_surface_diagnostic(
            "ladon.proof_surface.missing_no_drift_gate",
            "warning",
            route.claim_id,
            "Claim requires spec-to-proof drift protection, but no clean no-drift gate links the spec surface and proof endpoint.",
            specSurfaceId=str(spec.get("surfaceId", "")),
            proofEndpointSurfaceId=str(endpoint.get("surfaceId", "")),
        )
    ]


def missing_axiom_diagnostics(
    route: Any,
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return missing axiom audit diagnostics for one route."""

    if not proof_surface_requires_axiom_audit(route, endpoint):
        return []
    if clean_axiom_audit_for_endpoint(endpoint, ctx):
        return []
    return [
        proof_surface_diagnostic(
            "ladon.proof_surface.missing_axiom_audit",
            "warning",
            route.claim_id,
            "Claim requires an axiom footprint, but no accepted clean axiom audit row is attached to the proof endpoint.",
            proofEndpointSurfaceId=str(endpoint.get("surfaceId", "")),
        )
    ]


def clean_endpoint_diagnostics(
    route: Any,
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return clean endpoint classification for one route."""

    if not clean_endpoint_route(route, spec, endpoint, ctx):
        return []
    return [
        proof_surface_diagnostic(
            "ladon.proof_surface.clean_endpoint",
            "info",
            route.claim_id,
            "Proof endpoint has acceptable attachment and quoted route evidence for required gates and axiom audits; this is route-governance evidence, not theorem-truth validation.",
            proofEndpointSurfaceId=str(endpoint.get("surfaceId", "")),
        )
    ]


def spec_stub_authority_diagnostics(route: Any, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return diagnostics for claims using frozen spec stubs as authority."""

    rows = []
    for surface_ref in route.primary_theorem_surfaces:
        surface = proof_surface_for_ref(surface_ref, ctx)
        if str(surface.get("proofSurfaceRole", "")) != "lean_spec_stub":
            continue
        rows.append(
            proof_surface_diagnostic(
                "ladon.proof_surface.spec_stub_used_as_authority",
                "warning",
                route.claim_id,
                "Public claim cites a frozen spec stub as proof authority; cite a proof endpoint and no-drift evidence instead.",
                surfaceId=surface_ref.surface_id,
                declarationName=str(surface.get("declarationName", "")),
            )
        )
    return rows


def suspicious_axiom_diagnostics(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return diagnostics for suspicious or unknown quoted axiom footprints."""

    rows = []
    for audit in ctx.get("axiomAudits", []):
        for axiom_class, axioms in suspicious_axiom_groups(audit):
            for axiom in axioms:
                rows.append(suspicious_axiom_diagnostic(audit, axiom_class, str(axiom)))
    return rows


def suspicious_axiom_groups(audit: dict[str, Any]) -> tuple[tuple[str, list[Any]], ...]:
    """Return suspicious axiom fields with stable labels."""

    return (
        ("suspicious", list(audit.get("suspiciousAxioms", []))),
        ("unknown", list(audit.get("unknownAxioms", []))),
        ("forbidden", list(audit.get("forbiddenAxioms", []))),
    )


def suspicious_axiom_diagnostic(
    audit: dict[str, Any],
    axiom_class: str,
    axiom: str,
) -> dict[str, Any]:
    """Return one suspicious axiom diagnostic row."""

    return proof_surface_diagnostic(
        "ladon.proof_surface.suspicious_axiom",
        "warning",
        str(audit_subject(audit)),
        f"Axiom audit quotes {axiom_class} axiom {axiom}; this is route-governance evidence, not proof invalidation.",
        axiom=axiom,
        axiomClass=axiom_class,
        auditId=str(audit.get("auditId", "")),
        auditStatus=str(audit.get("status", "")),
    )


def audit_subject(audit: dict[str, Any]) -> str:
    """Return the stable subject for one axiom audit."""

    return audit.get("proofEndpointSurfaceId") or audit.get("surfaceId") or audit.get("auditId", "")


def frozen_spec_hub_diagnostics(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return classifications for intentionally quarantined frozen spec hubs."""

    rows = []
    for hub in hub_rows(ctx):
        subject = str(hub.get("module", "")) if isinstance(hub, dict) else str(hub)
        if subject:
            rows.append(frozen_spec_hub_diagnostic(subject))
    return rows


def hub_rows(ctx: dict[str, Any]) -> list[Any]:
    """Return configured frozen spec hub rows."""

    hubs = ctx.get("proofHolePolicy", {}).get("frozenSpecHubs", [])
    return hubs if isinstance(hubs, list) else []


def frozen_spec_hub_diagnostic(subject: str) -> dict[str, Any]:
    """Return one frozen spec hub classification row."""

    return proof_surface_diagnostic(
        "ladon.proof_surface.frozen_spec_hub",
        "info",
        subject,
        "Module is classified as a frozen spec hub with quarantined proof holes; it is not proof authority.",
    )


def proof_hole_quarantine_diagnostics(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return diagnostics for proof holes outside allowed witness quarantine."""

    return [
        proof_hole_quarantine_diagnostic(violation, index)
        for index, violation in enumerate(proof_hole_violations(ctx), start=1)
    ]


def proof_hole_violations(ctx: dict[str, Any]) -> list[Any]:
    """Return proof-hole policy violations from all supported fields."""

    policy = ctx.get("proofHolePolicy", {})
    violations = []
    for key in ("violations", "escapedProofHoles", "unquarantinedProofHoles"):
        value = policy.get(key, []) if isinstance(policy, dict) else []
        if isinstance(value, list):
            violations.extend(value)
    return violations


def proof_hole_quarantine_diagnostic(violation: Any, index: int) -> dict[str, Any]:
    """Return one escaped proof-hole diagnostic."""

    return proof_surface_diagnostic(
        "ladon.proof_surface.proof_hole_outside_quarantine",
        "warning",
        proof_hole_violation_subject(violation, index),
        "Proof-hole marker appears outside the witness quarantine policy; this is route-governance evidence, not proof invalidation.",
    )


def proof_hole_violation_subject(violation: Any, index: int) -> str:
    """Return a stable subject for one proof-hole policy violation."""

    if isinstance(violation, dict):
        return str(
            violation.get("declarationName")
            or violation.get("sourcePath")
            or violation.get("surfaceId")
            or f"proof_hole_violation.{index}"
        )
    return str(violation or f"proof_hole_violation.{index}")


def proof_surface_route_row(route: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Return reviewer-facing proof-surface route metadata for one claim."""

    if not ctx.get("present"):
        return {}
    spec = route_spec_surface(route, ctx)
    endpoint = route_proof_endpoint(route, ctx)
    gates = gates_for_route(spec, endpoint, ctx)
    audits = axiom_audits_for_endpoint(endpoint, ctx)
    return compact_route_dict(
        {
            "specSurface": proof_surface_row_summary(spec, ctx),
            "proofEndpoint": proof_surface_row_summary(endpoint, ctx),
            "noDriftGates": [proof_surface_gate_summary(gate, ctx) for gate in gates],
            "axiomAudits": [axiom_audit_summary(audit) for audit in audits],
            "requiresNoDriftGate": proof_surface_requires_gate(route, endpoint),
            "requiresAxiomAudit": proof_surface_requires_axiom_audit(route, endpoint),
            "nonclaims": proof_surface_nonclaims(route, spec, endpoint, ctx),
            "quotedOnly": True,
            "routeGovernanceOnly": True,
        }
    )


def proof_surface_row_summary(surface: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Return compact surface metadata for route output."""

    if not surface:
        return {}
    surface_id = str(surface.get("surfaceId", ""))
    join = ctx.get("joins", {}).get(surface_id, {})
    return compact_route_dict(
        {
            "surfaceId": surface_id,
            "declarationName": str(surface.get("declarationName", "")),
            "role": str(surface.get("proofSurfaceRole") or surface.get("role", "")),
            "surfaceKind": str(surface.get("surfaceKind", "")),
            "endpointScope": str(surface.get("endpointScope", "")),
            "matchKind": str(join.get("matchKind", "")),
            "attachmentConfidence": str(join.get("confidence", "")),
            "warningOnly": join.get("warningOnly") is True,
            "staleSource": proof_surface_join_stale(surface_id, ctx),
            "status": str(surface.get("status", "")),
            "verifier": surface.get("verifier", {}),
            "sourcePath": str(surface.get("sourcePath", "")),
            "contentHash": str(surface.get("contentHash", "")),
            "nonclaims": list(surface.get("nonclaims", [])),
        }
    )


def proof_surface_gate_summary(gate: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Return compact no-drift gate metadata for route output."""

    summary = proof_surface_row_summary(gate, ctx)
    summary.update(gate_identity_summary(gate))
    return summary


def gate_identity_summary(gate: dict[str, Any]) -> dict[str, Any]:
    """Return identity fields for one no-drift gate."""

    return compact_route_dict(
        {
            "gateId": str(gate.get("gateId", "")),
            "status": str(gate.get("status", "")),
            "specSurfaceId": str(gate.get("specSurfaceId", "")),
            "proofEndpointSurfaceId": str(gate.get("proofEndpointSurfaceId", "")),
        }
    )


def axiom_audit_summary(audit: dict[str, Any]) -> dict[str, Any]:
    """Return compact axiom audit metadata for route output."""

    return compact_route_dict(
        {
            "auditId": str(audit.get("auditId", "")),
            "proofEndpointSurfaceId": str(audit.get("proofEndpointSurfaceId", "")),
            "declarationName": str(audit.get("declarationName", "")),
            "status": str(audit.get("status", "")),
            "allowedAxioms": list(audit.get("allowedAxioms", [])),
            "suspiciousAxioms": list(audit.get("suspiciousAxioms", [])),
            "unknownAxioms": list(audit.get("unknownAxioms", [])),
            "forbiddenAxioms": list(audit.get("forbiddenAxioms", [])),
            "command": str(audit.get("command", "")),
            "toolVersion": str(audit.get("toolVersion", "")),
        }
    )


def proof_surface_nonclaims(
    route: Any,
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> list[str]:
    """Return combined proof-surface nonclaims for reviewer output."""

    values: list[str] = []
    values.extend(route.nonclaims)
    values.extend(ctx.get("nonclaims", []))
    values.extend(spec.get("nonclaims", []))
    values.extend(endpoint.get("nonclaims", []))
    return sorted(set(str(value) for value in values if str(value)))


def route_spec_surface(route: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Return the spec surface referenced by a claim route, if any."""

    spec_id = str(route.proof_surface.get("specSurfaceId", ""))
    if spec_id:
        return ctx.get("surfaces", {}).get(spec_id, {})
    return first_primary_surface_with_role(route, ctx, "lean_spec_stub")


def route_proof_endpoint(route: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Return the proof endpoint referenced by a claim route, if any."""

    endpoint_id = str(
        route.proof_surface.get("proofEndpointSurfaceId")
        or route.proof_surface.get("endpointSurfaceId")
        or ""
    )
    if endpoint_id:
        return ctx.get("surfaces", {}).get(endpoint_id, {})
    return first_primary_surface_with_role(route, ctx, "lean_proof_endpoint")


def first_primary_surface_with_role(route: Any, ctx: dict[str, Any], role: str) -> dict[str, Any]:
    """Return the first primary surface with a proof-surface role."""

    for surface_ref in route.primary_theorem_surfaces:
        surface = proof_surface_for_ref(surface_ref, ctx)
        if str(surface.get("proofSurfaceRole", "")) == role:
            return surface
    return {}


def proof_surface_for_ref(surface_ref: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Return a witness surface by id or declaration name."""

    if surface_ref.surface_id and surface_ref.surface_id in ctx.get("surfaces", {}):
        return ctx["surfaces"][surface_ref.surface_id]
    if surface_ref.declaration_name:
        return ctx.get("surfacesByDeclaration", {}).get(surface_ref.declaration_name, {})
    return {}


def proof_surface_requires_gate(route: Any, endpoint: dict[str, Any]) -> bool:
    """Return whether a route requires no-drift gate evidence."""

    return bool(
        route.proof_surface.get("requiresNoDriftGate")
        or route.proof_surface.get("requireNoDriftGate")
        or endpoint.get("requiresNoDriftGate")
    )


def proof_surface_requires_axiom_audit(route: Any, endpoint: dict[str, Any]) -> bool:
    """Return whether a route requires axiom audit evidence."""

    return bool(
        route.proof_surface.get("requiresAxiomAudit")
        or route.proof_surface.get("requireAxiomAudit")
        or endpoint.get("requiresAxiomAudit")
    )


def clean_gate_for_route(
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> bool:
    """Return whether a clean no-drift gate links the route surfaces."""

    return any(clean_gate(gate, ctx) for gate in gates_for_route(spec, endpoint, ctx))


def gates_for_route(
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return no-drift gates linking the route spec and endpoint."""

    if not spec and not endpoint:
        return []
    return [
        gate
        for gate in ctx.get("gates", [])
        if gate_links_route(gate, spec, endpoint)
    ]


def gate_links_route(
    gate: dict[str, Any],
    spec: dict[str, Any],
    endpoint: dict[str, Any],
) -> bool:
    """Return whether a no-drift gate links the supplied route surfaces."""

    return gate_spec_matches(gate, spec) and gate_endpoint_matches(gate, endpoint)


def gate_spec_matches(gate: dict[str, Any], spec: dict[str, Any]) -> bool:
    """Return whether a gate matches a spec surface."""

    if not spec:
        return True
    return (
        str(gate.get("specSurfaceId", "")) == str(spec.get("surfaceId", ""))
        or str(gate.get("specDeclarationName", "")) == str(spec.get("declarationName", ""))
    )


def gate_endpoint_matches(gate: dict[str, Any], endpoint: dict[str, Any]) -> bool:
    """Return whether a gate matches a proof endpoint."""

    if not endpoint:
        return True
    endpoint_id = str(endpoint.get("surfaceId", ""))
    endpoint_decl = str(endpoint.get("declarationName", ""))
    return (
        str(gate.get("proofEndpointSurfaceId", "")) == endpoint_id
        or str(gate.get("endpointSurfaceId", "")) == endpoint_id
        or str(gate.get("endpointDeclarationName", "")) == endpoint_decl
    )


def clean_gate(gate: dict[str, Any], ctx: dict[str, Any]) -> bool:
    """Return whether a no-drift gate has clean status and accepted attachment."""

    status = str(gate.get("status", ""))
    return status in PROOF_SURFACE_CLEAN_GATE_STATUSES and proof_surface_attachment_accepted(
        str(gate.get("surfaceId", "")),
        ctx,
    )


def clean_axiom_audit_for_endpoint(endpoint: dict[str, Any], ctx: dict[str, Any]) -> bool:
    """Return whether an endpoint has a clean accepted axiom audit."""

    return any(clean_axiom_audit(audit) for audit in axiom_audits_for_endpoint(endpoint, ctx))


def axiom_audits_for_endpoint(endpoint: dict[str, Any], ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Return axiom audits attached to an endpoint."""

    if not endpoint:
        return []
    return [
        audit
        for audit in ctx.get("axiomAudits", [])
        if axiom_audit_matches_endpoint(audit, endpoint)
    ]


def axiom_audit_matches_endpoint(audit: dict[str, Any], endpoint: dict[str, Any]) -> bool:
    """Return whether one axiom audit belongs to an endpoint."""

    endpoint_id = str(endpoint.get("surfaceId", ""))
    endpoint_decl = str(endpoint.get("declarationName", ""))
    audit_endpoint = str(
        audit.get("proofEndpointSurfaceId")
        or audit.get("endpointSurfaceId")
        or audit.get("surfaceId", "")
    )
    return audit_endpoint == endpoint_id or str(audit.get("declarationName", "")) == endpoint_decl


def clean_axiom_audit(audit: dict[str, Any]) -> bool:
    """Return whether a quoted axiom audit is clean."""

    return (
        str(audit.get("status", "")) in PROOF_SURFACE_CLEAN_AXIOM_STATUSES
        and not audit.get("suspiciousAxioms")
        and not audit.get("unknownAxioms")
        and not audit.get("forbiddenAxioms")
    )


def clean_endpoint_route(
    route: Any,
    spec: dict[str, Any],
    endpoint: dict[str, Any],
    ctx: dict[str, Any],
) -> bool:
    """Return whether a route satisfies clean endpoint classification."""

    if not clean_endpoint_surface(endpoint, ctx):
        return False
    if proof_surface_requires_gate(route, endpoint) and not clean_gate_for_route(spec, endpoint, ctx):
        return False
    if proof_surface_requires_axiom_audit(route, endpoint) and not clean_axiom_audit_for_endpoint(endpoint, ctx):
        return False
    return True


def clean_endpoint_surface(endpoint: dict[str, Any], ctx: dict[str, Any]) -> bool:
    """Return whether an endpoint is a strongly attached proof endpoint."""

    return (
        bool(endpoint)
        and str(endpoint.get("proofSurfaceRole", "")) == "lean_proof_endpoint"
        and proof_surface_attachment_accepted(str(endpoint.get("surfaceId", "")), ctx)
    )


def proof_surface_attachment_accepted(surface_id: str, ctx: dict[str, Any]) -> bool:
    """Return whether a witness surface has strong enough attachment."""

    join = ctx.get("joins", {}).get(surface_id, {})
    return (
        str(join.get("matchKind", "")) in PROOF_SURFACE_STRONG_MATCHES
        and join.get("warningOnly") is not True
        and not proof_surface_join_stale(surface_id, ctx)
    )


def proof_surface_join_stale(surface_id: str, ctx: dict[str, Any]) -> bool:
    """Return whether a proof-surface join has stale source hash context."""

    join = ctx.get("joins", {}).get(surface_id, {})
    surface = ctx.get("surfaces", {}).get(surface_id, {})
    surface_hash = str(surface.get("contentHash", ""))
    declaration_hash = str(join.get("declarationContentHash", ""))
    return bool(surface_hash and declaration_hash and surface_hash != declaration_hash)


def compact_route_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Drop empty route-output fields while preserving false booleans."""

    return {
        key: value
        for key, value in row.items()
        if not route_value_empty(value)
    }


def route_value_empty(value: Any) -> bool:
    """Return whether a route-output value is empty."""

    return value is None or value == "" or value == [] or value == {} or value == ()


def proof_surface_diagnostic(
    rule_id: str,
    level: str,
    subject: str,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    """Build one proof-surface route-audit diagnostic row."""

    row: dict[str, Any] = {
        "ruleId": rule_id,
        "level": level,
        "subject": subject,
        "message": message,
        "authorityAuditOnly": True,
        "proofSurfaceAuditOnly": True,
    }
    row.update({key: value for key, value in extra.items() if value not in {"", None}})
    return row
