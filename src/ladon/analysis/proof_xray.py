"""Optional proof x-ray staging analysis.

Proof x-ray rows are quoted proof-shape evidence. They are absent-safe and
authority-labeled so parser candidates are never promoted to elaborated proof
dependencies.
"""

from __future__ import annotations

from typing import Any

from ladon.finding_workflow import canonical_row_evidence


SUPPORTED_KINDS = {"ladon_proof_xray", "proof_xray"}
SUPPORTED_SCHEMA_VERSIONS = {1, "1"}
VALID_AUTHORITIES = {"parser_observed", "lean_elaborated", "external_tool_quoted", "unknown"}


def summarize_proof_xray(witness: Any) -> dict[str, Any]:
    """Return optional proof x-ray report rows."""

    normalized = normalize_proof_xray(witness)
    rows = proof_xray_rows(normalized)
    diagnostics = normalized.get("diagnostics", [])
    findings = [
        proof_xray_finding(row, index)
        for index, row in enumerate(rows)
    ]
    findings.extend(diagnostic_findings(diagnostics))
    return {
        "artifactKind": "ladon_proof_xray_report",
        "schemaVersion": 1,
        "summary": proof_xray_summary(rows, diagnostics),
        "witness": witness_summary(normalized),
        "rows": rows,
        "diagnostics": diagnostics,
        "findings": findings,
        "trustNote": "Proof x-ray rows are proof-shape review evidence only; they do not validate theorem truth or proof correctness.",
    }


def normalize_proof_xray(witness: Any) -> dict[str, Any]:
    """Normalize optional proof x-ray witness data."""

    if not isinstance(witness, dict):
        return malformed_witness("proof-xray input must be a JSON object")
    kind = str(witness.get("artifactKind", ""))
    if kind not in SUPPORTED_KINDS:
        return malformed_witness("proof-xray artifactKind is unsupported", source=witness)
    if witness.get("schemaVersion") not in SUPPORTED_SCHEMA_VERSIONS:
        return malformed_witness("proof-xray schemaVersion is unsupported; expected 1", source=witness)
    rows = [
        normalize_row(row)
        for row in witness.get("rows", witness.get("proofs", []))
        if isinstance(row, dict)
    ]
    return {
        "artifactKind": "ladon_proof_xray",
        "sourceArtifactKind": kind,
        "schemaVersion": 1,
        "valid": True,
        "producer": copied_dict(witness.get("producer")),
        "rows": rows,
        "diagnostics": weak_row_diagnostics(rows),
        "quotedOnly": True,
    }


def malformed_witness(reason: str, *, source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return malformed proof-xray witness payload."""

    return {
        "artifactKind": "ladon_proof_xray",
        "sourceArtifactKind": str(source.get("artifactKind", "")) if source else "",
        "schemaVersion": 1,
        "sourceSchemaVersion": source.get("schemaVersion", "") if source else "",
        "valid": False,
        "producer": {},
        "rows": [],
        "diagnostics": [
            {
                "kind": "proof_xray.malformed_witness",
                "severity": "warning",
                "subject": "proof_xray",
                "message": reason,
                "proofXrayOnly": True,
            }
        ],
        "quotedOnly": True,
    }


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one proof x-ray row."""

    authority = str(row.get("authority") or row.get("authorityLabel") or "unknown")
    if authority not in VALID_AUTHORITIES:
        authority = "unknown"
    return compact({
        "rowId": str(row.get("rowId") or row.get("id") or ""),
        "declarationName": str(row.get("declarationName", "")),
        "module": str(row.get("module", "")),
        "kind": str(row.get("kind") or row.get("rowKind") or "proof_shape"),
        "authority": authority,
        "backend": str(row.get("backend", "")),
        "toolVersion": str(row.get("toolVersion", "")),
        "command": str(row.get("command", "")),
        "sourcePath": str(row.get("sourcePath", "")),
        "sourceRange": copied_dict(row.get("sourceRange")),
        "selectionRange": copied_dict(row.get("selectionRange")),
        "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
        "confidence": str(row.get("confidence", "unknown")),
        "tacticSkeleton": string_list(row.get("tacticSkeleton")),
        "automationHotspots": string_list(row.get("automationHotspots")),
        "dependencies": string_list(row.get("dependencies")),
        "axioms": string_list(row.get("axioms")),
        "sorries": string_list(row.get("sorries")),
        "unsafeDeclarations": string_list(row.get("unsafeDeclarations")),
        "nonclaims": string_list(row.get("nonclaims")),
        "quotedOnly": True,
    })


def weak_row_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return diagnostics for rows lacking mandatory authority metadata."""

    diagnostics = []
    for row in rows:
        missing = [
            key
            for key in ("authority", "backend", "toolVersion", "confidence")
            if not row.get(key) or row.get(key) == "unknown"
        ]
        if missing:
            diagnostics.append({
                "kind": "proof_xray.weak_authority_metadata",
                "severity": "warning",
                "subject": row_subject(row),
                "message": "Proof x-ray row lacks complete backend/version/confidence authority metadata.",
                "missing": missing,
                "proofXrayOnly": True,
            })
    return diagnostics


def proof_xray_rows(witness: dict[str, Any]) -> list[dict[str, Any]]:
    """Classify proof-shape review pressure rows."""

    if not witness.get("valid"):
        return []
    rows = []
    for row in witness.get("rows", []):
        if row.get("automationHotspots") or len(row.get("tacticSkeleton", [])) >= 5:
            rows.append(classified_row("automation_hotspot", row, "Proof-shape row suggests automation or tactic-skeleton review pressure."))
        if row.get("dependencies"):
            rows.append(classified_row("dependency_context", row, "Proof-shape row quotes dependency-like context with an explicit authority label."))
        if row.get("axioms") or row.get("sorries") or row.get("unsafeDeclarations"):
            rows.append(classified_row("trust_footprint", row, "Proof-shape row quotes axiom, sorry, or unsafe footprint metadata."))
    return rows


def classified_row(kind: str, row: dict[str, Any], message: str) -> dict[str, Any]:
    """Return one classified proof x-ray row."""

    return compact({
        "kind": kind,
        "severity": "info" if row.get("authority") == "lean_elaborated" else "warning",
        "subject": row_subject(row),
        "declarationName": row.get("declarationName"),
        "module": row.get("module"),
        "authority": row.get("authority", "unknown"),
        "backend": row.get("backend"),
        "toolVersion": row.get("toolVersion"),
        "confidence": row.get("confidence"),
        "message": message,
        "evidence": row,
        "nonclaim": "Proof-shape review evidence only; not theorem-truth validation.",
    })


def row_subject(row: dict[str, Any]) -> str:
    """Return row subject."""

    return str(row.get("declarationName") or row.get("module") or row.get("rowId") or "proof_xray")


def proof_xray_finding(
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """Convert classified proof-xray row to a finding."""

    finding = {
        "kind": f"proof_xray.{row['kind']}",
        "severity": row.get("severity", "info"),
        "subject": row.get("subject", ""),
        "count": 1,
        "message": row.get("message", ""),
        "proofXrayOnly": True,
        "evidenceRefs": [
            canonical_row_evidence(
                "proof_xray",
                "rows",
                index,
                identity={
                    "kind": row.get("kind"),
                    "subject": row.get("subject", ""),
                },
                authority=str(row.get("authority", "external_tool_quoted")),
            )
        ],
    }
    evidence = row.get("evidence")
    if isinstance(evidence, dict):
        copy_finding_source_fields(finding, evidence)
    return finding


def diagnostic_findings(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return diagnostics as findings."""

    return [
        {
            "kind": row.get("kind", "proof_xray.diagnostic"),
            "severity": row.get("severity", "warning"),
            "subject": row.get("subject", "proof_xray"),
            "count": 1,
            "message": row.get("message", ""),
            "proofXrayOnly": True,
            "evidenceRefs": [
                canonical_row_evidence(
                    "proof_xray",
                    "diagnostics",
                    index,
                    identity={
                        "kind": row.get("kind", "proof_xray.diagnostic"),
                        "subject": row.get("subject", "proof_xray"),
                    },
                    authority="external_tool_quoted",
                )
            ],
        }
        for index, row in enumerate(diagnostics)
    ]


def copy_finding_source_fields(
    finding: dict[str, Any],
    row: dict[str, Any],
) -> None:
    """Preserve source attachment metadata supplied by a proof-xray row."""

    for key in (
        "sourcePath",
        "sourceRange",
        "selectionRange",
        "contentHash",
        "sourceHash",
        "confidence",
        "authority",
        "line",
        "column",
        "endLine",
        "endColumn",
    ):
        if key in row:
            finding[key] = row[key]


def proof_xray_summary(rows: list[dict[str, Any]], diagnostics: list[dict[str, Any]]) -> dict[str, int]:
    """Count rows by kind."""

    counts: dict[str, int] = {}
    for row in [*rows, *diagnostics]:
        counts[str(row.get("kind", "unknown"))] = counts.get(str(row.get("kind", "unknown")), 0) + 1
    return dict(sorted(counts.items()))


def witness_summary(witness: dict[str, Any]) -> dict[str, Any]:
    """Return compact witness state."""

    return {
        "present": True,
        "valid": witness.get("valid") is True,
        "rowCount": len(witness.get("rows", [])),
        "diagnosticCount": len(witness.get("diagnostics", [])),
        "quotedOnly": True,
    }


def copied_dict(value: Any) -> dict[str, Any]:
    """Return copied dict."""

    return dict(value) if isinstance(value, dict) else {}


def string_list(value: Any) -> list[str]:
    """Return string list."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def compact(row: dict[str, Any]) -> dict[str, Any]:
    """Drop empty values while preserving booleans."""

    return {key: value for key, value in row.items() if not empty(value)}


def empty(value: Any) -> bool:
    """Return whether a JSON-like value should be omitted."""

    return value is None or value == "" or value == [] or value == {}
