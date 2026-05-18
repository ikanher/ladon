"""Additive review-region summaries built from Ladon findings."""

from __future__ import annotations

from typing import Any

IMPORT_PRESSURE_THRESHOLD = 5
IMPORT_PRESSURE_FINDINGS = {"root_import_closure_hotspot", "composite_import_pressure"}


def summarize_review_regions(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    findings: list[dict[str, Any]],
    packet_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group related report signals into navigable review regions."""

    regions = [
        import_pressure_region(module_dag, findings),
        proof_family_region(declaration_graph, findings),
        packet_evidence_region(packet_evidence),
    ]
    return [region for region in regions if region is not None]


def import_pressure_region(
    module_dag: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return an import-pressure region when closure/finding signals exist."""

    closures = module_dag.get("root_direct_import_closures", [])[:3]
    signals = [
        closure_signal(row)
        for row in closures
    ]
    pressure_findings = finding_signals(findings, IMPORT_PRESSURE_FINDINGS)
    signals.extend(pressure_findings)
    if is_import_pressure_region(closures, pressure_findings):
        return region("import_pressure_region", "Import-pressure review region", signals)
    return region("import_context_region", "Import-context review region", signals)


def is_import_pressure_region(
    closures: list[dict[str, Any]],
    pressure_findings: list[dict[str, Any]],
) -> bool:
    """Return whether an import region should be labeled as pressure."""

    return bool(pressure_findings) or any(
        int(row.get("reachable_module_count", 0)) >= IMPORT_PRESSURE_THRESHOLD
        for row in closures
    )


def proof_family_region(
    declaration_graph: dict[str, Any] | None,
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a proof-family region when repeated-family signals exist."""

    if declaration_graph is None:
        return None
    signals = [
        {"kind": "declaration_family", "subject": row["suffix"], "count": row["count"]}
        for row in declaration_graph.get("declaration_name_families", [])[:5]
    ]
    signals.extend(
        {
            "kind": "proof_similarity",
            "subject": row["suffix"],
            "score": row.get("similarity_score"),
        }
        for row in declaration_graph.get("proof_family_similarity_candidates", [])[:5]
    )
    signals.extend(finding_signals(findings, {"declaration_family_hotspot", "proof_family_import_pressure"}))
    return region("proof_family_region", "Proof-family review region", signals)


def packet_evidence_region(packet_evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return a packet-evidence region when packet rows exist."""

    signals = [
        {
            "kind": "packet_evidence",
            "subject": row["packet_dir"],
            "status": row.get("status"),
            "profile_status": row.get("profile_status"),
        }
        for row in packet_evidence
    ]
    return region("packet_evidence_region", "Packet-evidence review region", signals)


def closure_signal(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one direct import closure row into a region signal."""

    return {
        "kind": "root_import_closure",
        "subject": f"{row['root']} -> {row['direct_import']}",
        "count": row["reachable_module_count"],
    }


def finding_signals(findings: list[dict[str, Any]], kinds: set[str]) -> list[dict[str, Any]]:
    """Convert selected findings into compact region signals."""

    return [
        {"kind": finding["kind"], "subject": finding.get("subject", "")}
        for finding in findings
        if finding.get("kind") in kinds
    ]


def region(kind: str, title: str, signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build one region row or return none for empty regions."""

    if not signals:
        return None
    return {
        "kind": kind,
        "title": title,
        "signal_count": len(signals),
        "signals": signals,
    }
