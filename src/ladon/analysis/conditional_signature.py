"""Warning-only heuristics for final-sounding conditional theorem signatures."""

from __future__ import annotations

from typing import Any

from ladon.analysis.claim_authority import normalize_claim_route, route_diagnostic, route_is_honestly_conditional


FINAL_NAME_MARKERS = (
    "final",
    "production",
    "maintained",
    "closed",
    "theorem",
    "eventdp",
    "event_dp",
)
HIGH_RISK_PREMISE_TOKENS = (
    "EvidenceAt",
    "Certificate",
    "Package",
    "falsePkg",
    "hForwardCDF",
    "hReverseCDF",
    "hcountMassEvidence",
    "haggregateEvidence",
    "imported",
)


def conditional_signature_diagnostics(
    declarations: Any,
    claim_rows: Any = None,
) -> list[dict[str, Any]]:
    """Return warning-only diagnostics for final-sounding conditional signatures."""

    if not isinstance(declarations, list):
        return []
    conditional_declarations = honestly_conditional_declarations(claim_rows)
    return [
        diagnostic
        for declaration in declarations
        if isinstance(declaration, dict)
        for diagnostic in [conditional_signature_diagnostic(declaration, conditional_declarations)]
        if diagnostic
    ]


def honestly_conditional_declarations(claim_rows: Any) -> set[str]:
    """Return declarations covered by honestly conditional route rows."""

    claims = [normalize_claim_route(row) for row in claim_rows or [] if isinstance(row, dict)]
    declarations: set[str] = set()
    for route in claims:
        if route_is_honestly_conditional(route):
            declarations.update(surface.declaration_name for surface in route.primary_theorem_surfaces)
    return {declaration for declaration in declarations if declaration}


def conditional_signature_diagnostic(
    declaration: dict[str, Any],
    conditional_declarations: set[str],
) -> dict[str, Any] | None:
    """Return a diagnostic for one declaration when the heuristic matches."""

    name = declaration_name(declaration)
    signature = declaration_signature(declaration)
    token = high_risk_token(signature)
    if not final_sounding_name(name) or not token:
        return None
    level = "info" if name in conditional_declarations else "warning"
    return route_diagnostic(
        "ladon.theorem.final_name_conditional_statement",
        level,
        name,
        f"Final-sounding theorem name exposes conditional premise token {token}; this is a review hint, not proof that the theorem, witness, or claim is invalid.",
        token=token,
    )


def final_sounding_name(name: str) -> bool:
    """Return whether a theorem name sounds like a final endpoint."""

    lower = name.lower()
    return any(marker in lower for marker in FINAL_NAME_MARKERS)


def high_risk_token(signature: str) -> str:
    """Return the first high-risk conditional premise token in a signature."""

    for token in HIGH_RISK_PREMISE_TOKENS:
        if token in signature:
            return token
    if " row " in f" {signature.lower()} ":
        return "row"
    return ""


def declaration_name(declaration: dict[str, Any]) -> str:
    """Return a declaration name from common row shapes."""

    return str(declaration.get("declaration") or declaration.get("declarationName") or declaration.get("name") or "")


def declaration_signature(declaration: dict[str, Any]) -> str:
    """Return a declaration signature/type text from common row shapes."""

    return str(declaration.get("signature") or declaration.get("type") or declaration.get("theoremType") or "")
