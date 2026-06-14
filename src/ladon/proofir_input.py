"""Normalize compact ProofIR bridge input shapes."""

from __future__ import annotations

from typing import Any

from ladon.analysis.claim_authority import authority_values


EXPECTED_INDEX_KIND = "proofir_bridge_index"
SURFACE_BUNDLE_KIND = "proof_ir_lean_surface_bundle"


def normalize_proofir_index(proofir_index: Any) -> dict[str, Any] | None:
    """Return a compact bridge index for supported ProofIR input shapes."""

    if not isinstance(proofir_index, dict):
        return None
    kind = proofir_index.get("artifactKind")
    if kind == EXPECTED_INDEX_KIND:
        return normalize_compact_bridge_index(proofir_index)
    if kind == SURFACE_BUNDLE_KIND:
        return normalize_surface_bundle(proofir_index)
    return None


def normalize_compact_bridge_index(proofir_index: dict[str, Any]) -> dict[str, Any]:
    """Normalize current compact bridge-index variants without mutating input."""

    normalized = dict(proofir_index)
    normalized["surfaces"] = normalized_surfaces(proofir_index.get("surfaces", []))
    normalized["claims"] = normalize_claim_rows(proofir_index.get("claims", []))
    normalized["witnessEndpoints"] = copied_dict_rows(proofir_index.get("witnessEndpoints", []))
    normalized["nonclaims"] = copied_dict_rows(proofir_index.get("nonclaims", []))
    normalized["projectionBoundaries"] = copied_dict_rows(proofir_index.get("projectionBoundaries", []))
    return normalized


def normalize_surface_bundle(proofir_index: dict[str, Any]) -> dict[str, Any]:
    """Adapt a Quux Lean surface bundle into the compact bridge-index shape."""

    source = proofir_index.get("source", {})
    source_defaults = dict(source) if isinstance(source, dict) else {}
    surfaces = normalized_bundle_surfaces(proofir_index.get("surfaces", []), source_defaults)
    return {
        "schemaVersion": 1,
        "artifactKind": EXPECTED_INDEX_KIND,
        "sourceArtifactKind": SURFACE_BUNDLE_KIND,
        "source": source_defaults,
        "surfaces": surfaces,
        "claims": [claim_from_surface(surface) for surface in surfaces],
        "witnessEndpoints": [],
        "nonclaims": [],
        "projectionBoundaries": [],
    }


def normalized_bundle_surfaces(rows: Any, source: dict[str, Any]) -> list[dict[str, Any]]:
    """Return bundle surfaces with top-level source fields used as defaults."""

    if not isinstance(rows, list):
        return []
    return [
        normalize_surface_row(bundle_surface_with_source_defaults(surface, source))
        for surface in rows
        if isinstance(surface, dict)
    ]


def bundle_surface_with_source_defaults(surface: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Copy top-level bundle source fields into a surface when absent."""

    normalized = dict(surface)
    if not normalized.get("sourcePath") and source.get("sourcePath"):
        normalized["sourcePath"] = source["sourcePath"]
    if not normalized.get("contentHash") and source.get("contentHash"):
        normalized["contentHash"] = source["contentHash"]
    return normalized


def normalized_surfaces(rows: Any) -> list[dict[str, Any]]:
    """Return normalized surface rows."""

    if not isinstance(rows, list):
        return []
    return [normalize_surface_row(surface) for surface in rows if isinstance(surface, dict)]


def copied_dict_rows(rows: Any) -> list[dict[str, Any]]:
    """Return shallow copies of dictionary rows."""

    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def normalize_surface_row(surface: dict[str, Any]) -> dict[str, Any]:
    """Normalize one ProofIR surface row to compact bridge fields."""

    normalized = dict(surface)
    normalize_source_anchor(normalized)
    if "contentHash" not in normalized and normalized.get("sourceHash"):
        normalized["contentHash"] = normalized["sourceHash"]
    if "module" not in normalized and normalized.get("declarationName"):
        normalized["module"] = module_name(str(normalized["declarationName"]))
    return normalized


def normalize_source_anchor(surface: dict[str, Any]) -> None:
    """Copy nested source-anchor metadata into normalized surface keys."""

    anchor = surface.get("sourceAnchor")
    if not isinstance(anchor, dict):
        return
    surface["sourceAnchor"] = dict(anchor)
    if not surface.get("declarationName"):
        surface["declarationName"] = str(anchor.get("declarationName", ""))
    if not surface.get("sourcePath"):
        surface["sourcePath"] = source_anchor_path(anchor)
    if surface.get("sourceLine") is None and anchor.get("startLine") is not None:
        surface["sourceLine"] = anchor.get("startLine")


def source_anchor_path(anchor: dict[str, Any]) -> str:
    """Return the strongest source path from a nested source anchor."""

    return str(anchor.get("repositoryPath") or anchor.get("sourcePath") or anchor.get("packetPath") or "")


def normalize_claim_rows(rows: Any) -> list[dict[str, Any]]:
    """Normalize claim rows while accepting string or list authority fields."""

    if not isinstance(rows, list):
        return []
    return [normalize_claim_row(row) for row in rows if isinstance(row, dict)]


def normalize_claim_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return one claim row with list-valued authority."""

    normalized = dict(row)
    normalized["authority"] = authority_list(normalized.get("authority"))
    if "claimedAuthority" in normalized:
        normalized["claimedAuthority"] = authority_values(normalized.get("claimedAuthority"))
    if "requiredEvidenceAuthorities" in normalized:
        normalized["requiredEvidenceAuthorities"] = normalized_evidence_authority_map(
            normalized.get("requiredEvidenceAuthorities")
        )
    if "allowedExternalEvidence" in normalized:
        normalized["allowedExternalEvidence"] = string_list(normalized.get("allowedExternalEvidence"))
    if "nonclaims" in normalized:
        normalized["nonclaims"] = string_list(normalized.get("nonclaims"))
    for key in (
        "primaryTheoremSurfaces",
        "supportingTheoremSurfaces",
        "backgroundTheoremSurfaces",
    ):
        if key in normalized:
            normalized[key] = normalized_surface_refs(normalized.get(key))
    return normalized


def normalized_evidence_authority_map(value: Any) -> dict[str, list[str]]:
    """Return evidence authorities keyed by evidence name."""

    if not isinstance(value, dict):
        return {}
    return {
        str(name): authority_values(authority)
        for name, authority in sorted(value.items())
    }


def string_list(value: Any) -> list[str]:
    """Return compact route string fields as lists."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, dict):
        return [str(key) for key, item in value.items() if item]
    return []


def normalized_surface_refs(value: Any) -> list[Any]:
    """Return route theorem surface references without mutating nested rows."""

    if not isinstance(value, list):
        return []
    rows: list[Any] = []
    for item in value:
        if isinstance(item, dict):
            rows.append(dict(item))
        elif isinstance(item, str):
            rows.append(item)
    return rows


def claim_from_surface(surface: dict[str, Any]) -> dict[str, Any]:
    """Build a quoted claim row from a normalized surface bundle row."""

    claim_id = str(surface.get("claimId") or surface.get("surfaceId", ""))
    row = {
        "claimId": claim_id,
        "status": surface_status(surface),
        "authority": authority_list(surface.get("authority")),
        "scope": surface_scope(surface),
        "proofTrust": str(surface.get("proofTrust", "")),
        "replayBoundary": surface.get("replayBoundary", {}),
        "extractorGuarantee": str(surface.get("extractorGuarantee", "")),
        "sourcePath": str(surface.get("sourcePath", "")),
        "sourceRange": surface.get("sourceRange", {}),
        "contentHash": surface_content_hash(surface),
    }
    for key in (
        "claimedStatus",
        "claimedAuthority",
        "endpointScope",
        "primaryTheoremSurfaces",
        "supportingTheoremSurfaces",
        "backgroundTheoremSurfaces",
        "requiredEvidenceAuthorities",
        "allowedExternalEvidence",
        "nonclaims",
    ):
        if key in surface:
            row[key] = surface[key]
    return normalize_claim_row(row)


def surface_status(surface: dict[str, Any]) -> str:
    """Return the quoted status for an adapted surface."""

    replay = surface.get("replayBoundary")
    if isinstance(replay, dict) and replay.get("status"):
        return str(replay["status"])
    return str(surface.get("status", ""))


def surface_scope(surface: dict[str, Any]) -> str:
    """Return a compact scope label for an adapted surface."""

    scope = surface.get("scope")
    if isinstance(scope, list):
        return ",".join(str(item) for item in scope)
    if scope:
        return str(scope)
    return str(surface.get("sourceKind", ""))


def surface_content_hash(surface: dict[str, Any]) -> str:
    """Return a normalized surface content hash."""

    return str(surface.get("contentHash") or surface.get("sourceHash") or "")


def authority_list(value: Any) -> list[str]:
    """Return authority metadata as a list of strings."""

    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def module_name(declaration: str) -> str:
    """Return the module portion of a fully qualified declaration name."""

    return declaration.rsplit(".", 1)[0] if "." in declaration else ""
