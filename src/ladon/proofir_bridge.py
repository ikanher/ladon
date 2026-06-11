"""Optional bridge between Ladon reports and compact ProofIR indexes."""

from __future__ import annotations

from typing import Any

from ladon.proofir_input import authority_list, normalize_proofir_index, surface_content_hash


def build_bridge_report(
    ladon_report: dict[str, Any],
    proofir_index: dict[str, Any] | None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join one Ladon report with one compact ProofIR bridge index."""

    del policy
    declarations = declaration_rows(ladon_report)
    if proofir_index is None:
        return empty_report(ladon_report)
    normalized_index = normalize_proofir_index(proofir_index)
    if normalized_index is None:
        return malformed_report(ladon_report)

    joins = join_surfaces(declarations, normalized_index.get("surfaces", []))
    diagnostics = bridge_diagnostics(joins, normalized_index)
    cards = reviewer_cards(ladon_report, normalized_index, joins, diagnostics)
    return {
        "schemaVersion": 1,
        "artifactKind": "ladon_proofir_bridge_report",
        "summary": {
            "proofirIndexPresent": True,
            "declarationCount": len(declarations),
            "surfaceCount": len(normalized_index.get("surfaces", [])),
            "joinedSurfaceCount": joined_count(joins),
            "unmatchedSurfaceCount": unmatched_count(joins),
            "diagnosticCount": len(diagnostics),
        },
        "joins": joins,
        "diagnostics": diagnostics,
        "reviewerCards": cards,
        "trustRules": [
            "bridge diagnostics do not establish theorem truth",
            "bridge diagnostics do not promote ProofIR status",
            "Ladon declaration edges are structural context, not proof dependencies",
            "source-hash and source-range joins establish attachment confidence only",
            "name-only joins are warning-only",
        ],
    }


def empty_report(ladon_report: dict[str, Any]) -> dict[str, Any]:
    """Return a valid bridge report when no ProofIR index was supplied."""

    return {
        "schemaVersion": 1,
        "artifactKind": "ladon_proofir_bridge_report",
        "summary": {
            "proofirIndexPresent": False,
            "declarationCount": len(declaration_rows(ladon_report)),
            "surfaceCount": 0,
            "joinedSurfaceCount": 0,
            "unmatchedSurfaceCount": 0,
            "diagnosticCount": 0,
        },
        "joins": [],
        "diagnostics": [],
        "reviewerCards": [],
        "trustRules": [
            "no ProofIR index supplied; normal Ladon report remains unchanged",
        ],
    }


def malformed_report(ladon_report: dict[str, Any]) -> dict[str, Any]:
    """Return a warning report for malformed optional ProofIR input."""

    row = diagnostic(
        "proofir.malformed_bridge_index",
        "error",
        "proofir_index",
        "ProofIR bridge index is missing artifactKind=proofir_bridge_index.",
    )
    return {
        "schemaVersion": 1,
        "artifactKind": "ladon_proofir_bridge_report",
        "summary": {
            "proofirIndexPresent": True,
            "declarationCount": len(declaration_rows(ladon_report)),
            "surfaceCount": 0,
            "joinedSurfaceCount": 0,
            "unmatchedSurfaceCount": 0,
            "diagnosticCount": 1,
        },
        "joins": [],
        "diagnostics": [row],
        "reviewerCards": [],
        "trustRules": [
            "malformed optional ProofIR input cannot support bridge diagnostics",
        ],
    }


def declaration_rows(ladon_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized declaration rows from a Ladon report."""

    graph = ladon_report.get("declaration_graph", {})
    if not isinstance(graph, dict):
        return []
    rows = graph.get("declarations", [])
    if isinstance(rows, list) and rows:
        return [explicit_declaration_row(row) for row in rows if isinstance(row, dict)]
    return derived_declaration_rows(ladon_report)


def explicit_declaration_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one explicit declaration row without mutating the report."""

    normalized = dict(row)
    if "sourcePath" not in normalized and normalized.get("path"):
        normalized["sourcePath"] = normalized["path"]
    normalized.setdefault("confidence", explicit_row_confidence(normalized))
    return normalized


def explicit_row_confidence(row: dict[str, Any]) -> str:
    """Return a conservative declaration-row confidence label."""

    if row.get("sourcePath") and row.get("contentHash"):
        return "source_hash"
    if row.get("sourcePath") and row.get("sourceRange"):
        return "source_range"
    if row.get("declaration") and row.get("module"):
        return "module_decl"
    return "none"


def derived_declaration_rows(ladon_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive declaration rows from clean-core declaration graph summaries."""

    graph = ladon_report.get("declaration_graph", {})
    if not isinstance(graph, dict):
        return []
    metadata = ladon_report.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    root_module = str(metadata.get("analysis_root_module", ""))
    root_path = relative_analysis_root(metadata)
    rows = []
    for name in declaration_names_from_graph(graph):
        module = module_name(name)
        row = {
            "declaration": name,
            "module": module,
            "nameResolutionMethod": "graph_summary_derived",
            "confidence": "derived",
        }
        if root_path and module == root_module:
            row["sourcePath"] = root_path
        rows.append(row)
    return rows


def relative_analysis_root(metadata: dict[str, Any]) -> str:
    """Return the analysis root path relative to the repo root when available."""

    root = str(metadata.get("analysis_root", ""))
    repo_root = str(metadata.get("repo_root", ""))
    if not root:
        return ""
    if repo_root and root.startswith(f"{repo_root}/"):
        return root[len(repo_root) + 1 :]
    return root


def declaration_names_from_graph(graph: dict[str, Any]) -> list[str]:
    """Collect declaration names from clean-core graph fields."""

    names: set[str] = set()
    edges = graph.get("edges", {})
    if isinstance(edges, dict):
        names.update(str(name) for name in edges if name)
    roots = graph.get("chosen_roots", [])
    if isinstance(roots, list):
        names.update(str(name) for name in roots if isinstance(name, str) and name)
    names.update(declarations_from_rank_rows(graph.get("top_fan_in", [])))
    names.update(declarations_from_rank_rows(graph.get("top_fan_out", [])))
    return sorted(names)


def declarations_from_rank_rows(rows: Any) -> set[str]:
    """Return declaration names from top fan-in/fan-out rank rows."""

    declarations = set()
    if not isinstance(rows, list):
        return declarations
    for row in rows:
        if isinstance(row, dict) and row.get("declaration"):
            declarations.add(str(row["declaration"]))
    return declarations


def module_name(declaration: str) -> str:
    """Return the module portion of a fully qualified declaration name."""

    return declaration.rsplit(".", 1)[0] if "." in declaration else ""


def join_surfaces(declarations: list[dict[str, Any]], surfaces: Any) -> list[dict[str, Any]]:
    """Join ProofIR surface rows to Ladon declarations."""

    if not isinstance(surfaces, list):
        return []
    return [join_surface(declarations, surface) for surface in surfaces if isinstance(surface, dict)]


def join_surface(declarations: list[dict[str, Any]], surface: dict[str, Any]) -> dict[str, Any]:
    """Join one ProofIR surface to the best available declaration row."""

    for match_kind, confidence, matcher in join_matchers():
        row = first_matching_join(declarations, surface, match_kind, confidence, matcher)
        if row:
            return row
    return unmatched_surface_row(surface)


def join_matchers() -> tuple[tuple[str, str, Any], ...]:
    """Return matchers in strongest-to-weakest attachment order."""

    return (
        ("exact_source_hash_decl", "high", exact_source_hash_decl),
        ("exact_source_range_decl", "medium", exact_source_range_decl),
        ("source_line_anchor_decl", "low", source_line_anchor_decl),
        ("exact_module_decl", "medium", exact_module_decl),
        ("basename_only", "low", basename_match),
    )


def first_matching_join(
    declarations: list[dict[str, Any]],
    surface: dict[str, Any],
    match_kind: str,
    confidence: str,
    matcher: Any,
) -> dict[str, Any] | None:
    """Return the first join row accepted by one matcher."""

    for declaration in declarations:
        if matcher(surface, declaration):
            return join_row(surface, declaration, match_kind, confidence)
    return None


def unmatched_surface_row(surface: dict[str, Any]) -> dict[str, Any]:
    """Return the stable unmatched surface row."""

    return {
        "surfaceId": str(surface.get("surfaceId", "")),
        "claimId": str(surface.get("claimId", "")),
        "declarationName": str(surface.get("declarationName", "")),
        "matchKind": "unmatched",
        "confidence": "none",
    }


def exact_source_hash_decl(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for exact source path, hash, and declaration match."""

    return (
        same_decl(surface, declaration)
        and same_source_path(surface, declaration)
        and bool(surface_content_hash(surface))
        and surface_content_hash(surface) == declaration.get("contentHash")
    )


def exact_source_range_decl(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for exact source path, source range, and declaration match."""

    return (
        same_decl(surface, declaration)
        and same_source_path(surface, declaration)
        and same_source_range(surface.get("sourceRange"), declaration.get("sourceRange"))
    )


def exact_module_decl(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for exact module and declaration match."""

    return (
        same_decl(surface, declaration)
        and bool(surface.get("module"))
        and surface.get("module") == declaration.get("module")
    )


def source_line_anchor_decl(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for conservative declaration/path/start-line anchor matches."""

    source_line = surface.get("sourceLine")
    source_range = declaration.get("sourceRange")
    return (
        same_decl(surface, declaration)
        and same_source_path(surface, declaration)
        and source_line is not None
        and isinstance(source_range, dict)
        and source_line == source_range.get("startLine")
    )


def basename_match(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for basename-only declaration matches."""

    wanted = str(surface.get("declarationName", ""))
    actual = str(declaration.get("declaration", ""))
    return bool(wanted) and wanted == actual.rsplit(".", 1)[-1]


def same_decl(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for exact declaration-name match."""

    return bool(surface.get("declarationName")) and surface.get("declarationName") == declaration.get("declaration")


def same_source_path(surface: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """Return true for exact source-path match."""

    return bool(surface.get("sourcePath")) and surface.get("sourcePath") == declaration_source_path(declaration)


def declaration_source_path(declaration: dict[str, Any]) -> str:
    """Return the declaration source path from current or legacy row fields."""

    return str(declaration.get("sourcePath") or declaration.get("path") or "")


def same_source_range(surface_range: Any, declaration_range: Any) -> bool:
    """Return true for exact or compatible line-only source ranges."""

    if surface_range == declaration_range and surface_range is not None:
        return True
    if not isinstance(surface_range, dict) or not isinstance(declaration_range, dict):
        return False
    start_line = surface_range.get("startLine")
    end_line = surface_range.get("endLine")
    return (
        start_line is not None
        and end_line is not None
        and start_line == declaration_range.get("startLine")
        and end_line == declaration_range.get("endLine")
    )


def join_row(
    surface: dict[str, Any],
    declaration: dict[str, Any],
    match_kind: str,
    confidence: str,
) -> dict[str, Any]:
    """Build one bridge join row."""

    row = {
        "surfaceId": str(surface.get("surfaceId", "")),
        "claimId": str(surface.get("claimId", "")),
        "declarationName": str(declaration.get("declaration", "")),
        "module": str(declaration.get("module", "")),
        "matchKind": match_kind,
        "confidence": confidence,
        "declarationConfidence": str(declaration.get("confidence", "")),
        "warningOnly": match_kind in {"basename_only", "source_line_anchor_decl"},
    }
    if surface.get("sourceAnchor"):
        row["sourceAnchor"] = dict(surface["sourceAnchor"])
    if declaration.get("contentHash"):
        row["declarationContentHash"] = str(declaration["contentHash"])
    return row


def bridge_diagnostics(joins: list[dict[str, Any]], proofir_index: dict[str, Any]) -> list[dict[str, Any]]:
    """Emit conservative bridge diagnostics."""

    diagnostics: list[dict[str, Any]] = []
    joined_surfaces = joined_surface_ids(joins)
    for join in joins:
        if join["matchKind"] == "unmatched":
            diagnostics.append(
                diagnostic(
                    "proofir.unattached_surface",
                    "warning",
                    join["surfaceId"],
                    "ProofIR surface did not join to a Ladon declaration.",
                )
            )
        if join["matchKind"] == "basename_only":
            diagnostics.append(
                diagnostic(
                    "proofir.name_only_join_warning",
                    "warning",
                    join["surfaceId"],
                    "Surface joined by basename only; this is reviewer context, not evidence.",
                )
            )
        if join["matchKind"] == "source_line_anchor_decl":
            diagnostics.append(
                diagnostic(
                    "proofir.source_anchor_join_warning",
                    "warning",
                    join["surfaceId"],
                    "Surface joined by source line anchor only; this is reviewer context, not proof evidence.",
                )
            )

    diagnostics.extend(stale_source_diagnostics(joins, proofir_index))
    diagnostics.extend(witness_endpoint_diagnostics(proofir_index, joined_surfaces))
    diagnostics.extend(nonclaim_diagnostics(proofir_index, joined_surfaces))
    return diagnostics


def stale_source_diagnostics(
    joins: list[dict[str, Any]],
    proofir_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return diagnostics for source hash drift."""

    surfaces = surfaces_by_id(proofir_index)
    diagnostics: list[dict[str, Any]] = []
    for join in joins:
        surface = surfaces.get(join["surfaceId"], {})
        if (
            join["matchKind"] == "exact_source_range_decl"
            and surface_content_hash(surface)
            and join.get("declarationContentHash")
        ):
            diagnostics.append(
                diagnostic(
                    "proofir.packet_stale_source",
                    "warning",
                    join["surfaceId"],
                    "ProofIR surface hash does not match Ladon declaration source hash.",
                )
            )
    return diagnostics


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
) -> list[dict[str, Any]]:
    """Build compact reviewer cards."""

    if not joins:
        return []
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
            "trustNote": "Ladon structural context only; ProofIR statuses are quoted, not promoted.",
        }
    ]


def joined_claims(proofir_index: dict[str, Any], joins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return claims attached to joined surfaces."""

    claim_ids = {join["claimId"] for join in joins}
    rows = []
    for claim in proofir_index.get("claims", []):
        if isinstance(claim, dict) and claim.get("claimId") in claim_ids:
            rows.append(
                {
                    "claimId": str(claim.get("claimId", "")),
                    "status": str(claim.get("status", "")),
                    "authority": authority_list(claim.get("authority")),
                    "scope": str(claim.get("scope", "")),
                }
            )
    return rows


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


def joined_count(joins: list[dict[str, Any]]) -> int:
    """Count joined surfaces."""

    return len(joined_surface_ids(joins))


def unmatched_count(joins: list[dict[str, Any]]) -> int:
    """Count unmatched surfaces."""

    return sum(1 for join in joins if join["matchKind"] == "unmatched")


def diagnostic(rule_id: str, level: str, subject: str, message: str) -> dict[str, str]:
    """Build one bridge diagnostic."""

    return {
        "ruleId": rule_id,
        "level": level,
        "subject": subject,
        "message": message,
    }
