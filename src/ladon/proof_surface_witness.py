"""Normalize compact proof-surface witness artifacts.

The witness is quoted route-governance metadata. It records what an external
project verifier says about frozen spec stubs, proof endpoints, no-drift gates,
source pins, and axiom audits. Ladon consumes this shape to route review; it
does not replay Lean proofs or validate theorem truth.
"""

from __future__ import annotations

from typing import Any


PROOF_SURFACE_WITNESS_KIND = "proof_surface_witness"
LEGACY_PROOF_SURFACE_WITNESS_KIND = "ladon_proof_surface_witness"
SUPPORTED_WITNESS_KINDS = {
    PROOF_SURFACE_WITNESS_KIND,
    LEGACY_PROOF_SURFACE_WITNESS_KIND,
}
SUPPORTED_SCHEMA_VERSIONS = {1, "1"}

SPEC_SURFACE_KEYS = {
    "surfaceId",
    "id",
    "claimId",
    "declarationName",
    "module",
    "role",
    "sourcePath",
    "sourceRange",
    "sourceLine",
    "sourceHash",
    "contentHash",
    "endpointScope",
    "scope",
    "proofHolePolicy",
    "nonclaims",
}
ENDPOINT_SURFACE_KEYS = SPEC_SURFACE_KEYS | {
    "authority",
    "proofAuthority",
    "verifier",
    "status",
    "axiomAuditId",
    "requiresNoDriftGate",
    "requiresAxiomAudit",
}
GATE_KEYS = {
    "gateId",
    "surfaceId",
    "id",
    "declarationName",
    "module",
    "specSurfaceId",
    "proofEndpointSurfaceId",
    "endpointSurfaceId",
    "specDeclarationName",
    "endpointDeclarationName",
    "status",
    "verifier",
    "sourcePath",
    "sourceRange",
    "sourceLine",
    "sourceHash",
    "contentHash",
    "nonclaims",
}
AXIOM_AUDIT_KEYS = {
    "auditId",
    "id",
    "surfaceId",
    "proofEndpointSurfaceId",
    "endpointSurfaceId",
    "declarationName",
    "status",
    "allowedAxioms",
    "suspiciousAxioms",
    "unknownAxioms",
    "forbiddenAxioms",
    "command",
    "toolVersion",
    "verifier",
    "nonclaims",
}
SOURCE_PIN_KEYS = {
    "pinId",
    "id",
    "surfaceId",
    "declarationName",
    "sourcePath",
    "sourceRange",
    "sourceLine",
    "contentHash",
    "sourceHash",
    "status",
    "toolVersion",
    "generatedAt",
    "generatedAtUtc",
}


def normalize_proof_surface_witness(witness: Any) -> dict[str, Any] | None:
    """Return a normalized proof-surface witness or malformed witness report."""

    if witness is None:
        return None
    if not isinstance(witness, dict):
        return malformed_witness("proof-surface witness input must be a JSON object")
    kind = str(witness.get("artifactKind", ""))
    if kind not in SUPPORTED_WITNESS_KINDS:
        return malformed_witness(
            f"proof-surface witness artifactKind is unsupported; expected {PROOF_SURFACE_WITNESS_KIND}",
            source=witness,
        )
    schema_version = witness.get("schemaVersion")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return malformed_witness(
            "proof-surface witness schemaVersion is unsupported; expected 1",
            source=witness,
        )

    source_pins = normalize_source_pins(witness.get("sourcePins", []))
    pin_by_surface, pin_by_declaration = source_pin_indexes(source_pins)
    spec_surfaces = normalize_surface_rows(
        witness.get("specSurfaces", []),
        kind="spec_surface",
        default_role="lean_spec_stub",
        known_keys=SPEC_SURFACE_KEYS,
        pin_by_surface=pin_by_surface,
        pin_by_declaration=pin_by_declaration,
    )
    proof_endpoints = normalize_surface_rows(
        witness.get("proofEndpoints", []),
        kind="proof_endpoint",
        default_role="lean_proof_endpoint",
        known_keys=ENDPOINT_SURFACE_KEYS,
        pin_by_surface=pin_by_surface,
        pin_by_declaration=pin_by_declaration,
    )
    gates = normalize_gate_rows(
        witness.get("noDriftGates", []),
        pin_by_surface=pin_by_surface,
        pin_by_declaration=pin_by_declaration,
    )
    axiom_audits = normalize_axiom_audit_rows(witness.get("axiomAudits", []))
    return {
        "artifactKind": PROOF_SURFACE_WITNESS_KIND,
        "sourceArtifactKind": kind,
        "schemaVersion": 1,
        "valid": True,
        "producer": copied_dict(witness.get("producer")),
        "specSurfaces": spec_surfaces,
        "proofEndpoints": proof_endpoints,
        "noDriftGates": gates,
        "axiomAudits": axiom_audits,
        "sourcePins": source_pins,
        "proofHolePolicy": copied_dict(witness.get("proofHolePolicy")),
        "nonclaims": string_list(witness.get("nonclaims")),
        "surfaces": [*spec_surfaces, *proof_endpoints, *gates],
        "diagnostics": [],
        "quotedOnly": True,
        "routeGovernanceOnly": True,
        "quotedMetadata": unknown_fields(
            witness,
            {
                "artifactKind",
                "schemaVersion",
                "producer",
                "specSurfaces",
                "proofEndpoints",
                "noDriftGates",
                "axiomAudits",
                "sourcePins",
                "proofHolePolicy",
                "nonclaims",
            },
        ),
    }


def malformed_witness(reason: str, *, source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a stable malformed witness payload."""

    kind = ""
    version: Any = ""
    if source:
        kind = str(source.get("artifactKind", ""))
        version = source.get("schemaVersion", "")
    return {
        "artifactKind": PROOF_SURFACE_WITNESS_KIND,
        "sourceArtifactKind": kind,
        "schemaVersion": 1,
        "sourceSchemaVersion": version,
        "valid": False,
        "producer": {},
        "specSurfaces": [],
        "proofEndpoints": [],
        "noDriftGates": [],
        "axiomAudits": [],
        "sourcePins": [],
        "proofHolePolicy": {},
        "nonclaims": [],
        "surfaces": [],
        "diagnostics": [
            {
                "ruleId": "ladon.proof_surface.malformed_witness",
                "level": "error",
                "subject": "proof_surface_witness",
                "message": reason,
                "proofSurfaceAuditOnly": True,
            }
        ],
        "quotedOnly": True,
        "routeGovernanceOnly": True,
        "quotedMetadata": {},
    }


def normalize_surface_rows(
    rows: Any,
    *,
    kind: str,
    default_role: str,
    known_keys: set[str],
    pin_by_surface: dict[str, dict[str, Any]],
    pin_by_declaration: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize spec-surface or proof-endpoint rows."""

    if not isinstance(rows, list):
        return []
    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            normalize_surface_row(
                row,
                index=index,
                kind=kind,
                default_role=default_role,
                known_keys=known_keys,
                pin_by_surface=pin_by_surface,
                pin_by_declaration=pin_by_declaration,
            )
        )
    return normalized


def normalize_surface_row(
    row: dict[str, Any],
    *,
    index: int,
    kind: str,
    default_role: str,
    known_keys: set[str],
    pin_by_surface: dict[str, dict[str, Any]],
    pin_by_declaration: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Normalize one spec-surface or proof-endpoint row."""

    declaration, surface_id = surface_identity(row, index, kind)
    normalized = base_surface_row(row, declaration, surface_id, kind, default_role, known_keys)
    add_optional_surface_fields(normalized, row)
    apply_source_pin(normalized, pin_by_surface.get(surface_id) or pin_by_declaration.get(declaration))
    return compact_dict(normalized)


def surface_identity(row: dict[str, Any], index: int, kind: str) -> tuple[str, str]:
    """Return declaration and surface id for a witness surface."""

    declaration = str(row.get("declarationName", ""))
    surface_id = str(row.get("surfaceId") or row.get("id") or f"{kind}.{index}")
    return declaration, surface_id


def base_surface_row(
    row: dict[str, Any],
    declaration: str,
    surface_id: str,
    kind: str,
    default_role: str,
    known_keys: set[str],
) -> dict[str, Any]:
    """Return common normalized fields for a spec or endpoint surface."""

    role = str(row.get("role") or default_role)
    return {
        "surfaceId": surface_id,
        "claimId": str(row.get("claimId", "")),
        "declarationName": declaration,
        "module": str(row.get("module") or module_name(declaration)),
        "role": role,
        "proofSurfaceRole": role,
        "surfaceKind": kind,
        "endpointScope": surface_scope(row),
        "sourcePath": str(row.get("sourcePath", "")),
        "sourceRange": copied_dict(row.get("sourceRange")),
        "sourceLine": row.get("sourceLine"),
        "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
        "nonclaims": string_list(row.get("nonclaims")),
        "quotedMetadata": unknown_fields(row, known_keys),
        "quotedOnly": True,
        "routeGovernanceOnly": True,
    }


def add_optional_surface_fields(normalized: dict[str, Any], row: dict[str, Any]) -> None:
    """Copy optional endpoint/spec metadata into a normalized surface."""

    if "proofHolePolicy" in row:
        normalized["proofHolePolicy"] = copied_dict(row.get("proofHolePolicy"))
    add_optional_keys(normalized, row, ("authority", "proofAuthority", "verifier", "status", "axiomAuditId"))
    add_optional_bool(normalized, row, "requiresNoDriftGate")
    add_optional_bool(normalized, row, "requiresAxiomAudit")


def add_optional_keys(normalized: dict[str, Any], row: dict[str, Any], keys: tuple[str, ...]) -> None:
    """Copy optional quoted keys when present."""

    for key in keys:
        if key in row:
            normalized[key] = copied_value(row[key])


def add_optional_bool(normalized: dict[str, Any], row: dict[str, Any], key: str) -> None:
    """Copy optional boolean flags when present."""

    if key in row:
        normalized[key] = bool(row[key])


def normalize_gate_rows(
    rows: Any,
    *,
    pin_by_surface: dict[str, dict[str, Any]],
    pin_by_declaration: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize no-drift gate rows."""

    if not isinstance(rows, list):
        return []
    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            normalize_gate_row(
                row,
                index=index,
                pin_by_surface=pin_by_surface,
                pin_by_declaration=pin_by_declaration,
            )
        )
    return normalized


def normalize_gate_row(
    row: dict[str, Any],
    *,
    index: int,
    pin_by_surface: dict[str, dict[str, Any]],
    pin_by_declaration: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Normalize one no-drift gate row."""

    declaration = str(row.get("declarationName", ""))
    gate_id = str(row.get("gateId") or row.get("surfaceId") or row.get("id") or f"gate.{index}")
    gate = base_gate_row(row, declaration, gate_id)
    apply_source_pin(gate, pin_by_surface.get(gate["surfaceId"]) or pin_by_declaration.get(declaration))
    return compact_dict(gate)


def base_gate_row(row: dict[str, Any], declaration: str, gate_id: str) -> dict[str, Any]:
    """Return common normalized fields for one no-drift gate."""

    endpoint_id = str(row.get("proofEndpointSurfaceId") or row.get("endpointSurfaceId") or "")
    return {
        "gateId": gate_id,
        "surfaceId": str(row.get("surfaceId") or gate_id),
        "declarationName": declaration,
        "module": str(row.get("module") or module_name(declaration)),
        "role": "lean_no_drift_gate",
        "proofSurfaceRole": "lean_no_drift_gate",
        "surfaceKind": "no_drift_gate",
        "specSurfaceId": str(row.get("specSurfaceId", "")),
        "proofEndpointSurfaceId": endpoint_id,
        "endpointSurfaceId": endpoint_id,
        "specDeclarationName": str(row.get("specDeclarationName", "")),
        "endpointDeclarationName": str(row.get("endpointDeclarationName", "")),
        "status": str(row.get("status", "")),
        "verifier": copied_value(row.get("verifier")),
        "sourcePath": str(row.get("sourcePath", "")),
        "sourceRange": copied_dict(row.get("sourceRange")),
        "sourceLine": row.get("sourceLine"),
        "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
        "nonclaims": string_list(row.get("nonclaims")),
        "quotedMetadata": unknown_fields(row, GATE_KEYS),
        "quotedOnly": True,
        "routeGovernanceOnly": True,
    }


def normalize_axiom_audit_rows(rows: Any) -> list[dict[str, Any]]:
    """Normalize quoted axiom audit rows."""

    if not isinstance(rows, list):
        return []
    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        endpoint_id = str(row.get("proofEndpointSurfaceId") or row.get("endpointSurfaceId") or row.get("surfaceId", ""))
        audit = {
            "auditId": str(row.get("auditId") or row.get("id") or f"axiom_audit.{index}"),
            "surfaceId": str(row.get("surfaceId") or endpoint_id),
            "proofEndpointSurfaceId": endpoint_id,
            "endpointSurfaceId": endpoint_id,
            "declarationName": str(row.get("declarationName", "")),
            "status": str(row.get("status", "")),
            "allowedAxioms": string_list(row.get("allowedAxioms")),
            "suspiciousAxioms": string_list(row.get("suspiciousAxioms")),
            "unknownAxioms": string_list(row.get("unknownAxioms")),
            "forbiddenAxioms": string_list(row.get("forbiddenAxioms")),
            "command": str(row.get("command", "")),
            "toolVersion": str(row.get("toolVersion", "")),
            "verifier": copied_value(row.get("verifier")),
            "nonclaims": string_list(row.get("nonclaims")),
            "quotedMetadata": unknown_fields(row, AXIOM_AUDIT_KEYS),
            "quotedOnly": True,
            "routeGovernanceOnly": True,
        }
        normalized.append(compact_dict(audit))
    return normalized


def normalize_source_pins(rows: Any) -> list[dict[str, Any]]:
    """Normalize source pin rows."""

    if not isinstance(rows, list):
        return []
    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        pin = {
            "pinId": str(row.get("pinId") or row.get("id") or f"source_pin.{index}"),
            "surfaceId": str(row.get("surfaceId", "")),
            "declarationName": str(row.get("declarationName", "")),
            "sourcePath": str(row.get("sourcePath", "")),
            "sourceRange": copied_dict(row.get("sourceRange")),
            "sourceLine": row.get("sourceLine"),
            "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
            "status": str(row.get("status", "")),
            "toolVersion": str(row.get("toolVersion", "")),
            "generatedAt": str(row.get("generatedAt") or row.get("generatedAtUtc") or ""),
            "quotedMetadata": unknown_fields(row, SOURCE_PIN_KEYS),
            "quotedOnly": True,
            "routeGovernanceOnly": True,
        }
        normalized.append(compact_dict(pin))
    return normalized


def source_pin_indexes(
    pins: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return source pins keyed by surface id and declaration name."""

    by_surface = {
        str(pin.get("surfaceId", "")): pin
        for pin in pins
        if pin.get("surfaceId")
    }
    by_declaration = {
        str(pin.get("declarationName", "")): pin
        for pin in pins
        if pin.get("declarationName")
    }
    return by_surface, by_declaration


def apply_source_pin(row: dict[str, Any], pin: dict[str, Any] | None) -> None:
    """Apply source-pin defaults to one witness surface row."""

    if not pin:
        return
    for key in ("sourcePath", "sourceRange", "sourceLine", "contentHash"):
        if not row.get(key) and pin.get(key):
            row[key] = copied_value(pin[key])
    row["sourcePin"] = dict(pin)
    if pin.get("status"):
        row["sourcePinStatus"] = str(pin["status"])


def surface_scope(row: dict[str, Any]) -> str:
    """Return compact endpoint scope from a witness surface row."""

    scope = row.get("endpointScope") or row.get("scope") or ""
    if isinstance(scope, list):
        return ",".join(str(item) for item in scope)
    return str(scope)


def unknown_fields(row: dict[str, Any], known_keys: set[str]) -> dict[str, Any]:
    """Return fields outside the normalized schema as quoted metadata."""

    return {
        str(key): copied_value(value)
        for key, value in row.items()
        if key not in known_keys
    }


def copied_dict(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy for JSON-like fields."""

    return dict(value) if isinstance(value, dict) else {}


def copied_value(value: Any) -> Any:
    """Return a shallow copy of JSON-like values."""

    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return list(value)
    return value


def string_list(value: Any) -> list[str]:
    """Return compact witness string fields as lists."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, dict):
        return [str(key) for key, item in value.items() if item]
    return []


def compact_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Drop empty normalized values while preserving boolean false."""

    return {
        key: value
        for key, value in row.items()
        if not empty_value(value)
    }


def empty_value(value: Any) -> bool:
    """Return whether a normalized JSON value is semantically absent."""

    return value is None or value == "" or value == [] or value == () or value == {}


def module_name(declaration: str) -> str:
    """Return the module portion of a fully qualified declaration name."""

    return declaration.rsplit(".", 1)[0] if "." in declaration else ""
