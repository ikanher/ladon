"""Optional Lean/Lake import-diet witness analysis."""

from __future__ import annotations

from typing import Any

from ladon.finding_workflow import canonical_row_evidence

SUPPORTED_KINDS = {"ladon_import_diet_witness", "import_diet_witness"}
SUPPORTED_SCHEMA_VERSIONS = {1, "1"}


def summarize_import_diet(module_dag: dict[str, Any], witness: Any) -> dict[str, Any]:
    """Return import-diet report rows from optional witness evidence."""

    normalized = normalize_import_diet_witness(witness)
    rows = import_diet_rows(module_dag, normalized)
    diagnostics = normalized.get("diagnostics", [])
    findings = [
        import_diet_finding(row, index)
        for index, row in enumerate(rows)
    ]
    findings.extend(diagnostic_findings(diagnostics))
    return {
        "artifactKind": "ladon_import_diet_report",
        "schemaVersion": 1,
        "summary": import_diet_summary(rows, diagnostics),
        "witness": witness_summary(normalized),
        "rows": rows,
        "diagnostics": diagnostics,
        "findings": findings,
        "trustNote": "Import-diet rows quote Lean/Lake-owned build evidence; Ladon does not prove an import can be removed without replaying the named command.",
    }


def normalize_import_diet_witness(witness: Any) -> dict[str, Any]:
    """Normalize an import-diet witness or return a malformed report."""

    if not isinstance(witness, dict):
        return malformed_witness("import-diet witness input must be a JSON object")
    kind = str(witness.get("artifactKind", ""))
    if kind not in SUPPORTED_KINDS:
        return malformed_witness("import-diet witness artifactKind is unsupported", source=witness)
    if witness.get("schemaVersion") not in SUPPORTED_SCHEMA_VERSIONS:
        return malformed_witness("import-diet witness schemaVersion is unsupported; expected 1", source=witness)
    rows = [
        normalize_witness_row(row)
        for row in witness.get("modules", witness.get("rows", []))
        if isinstance(row, dict)
    ]
    return {
        "artifactKind": "ladon_import_diet_witness",
        "sourceArtifactKind": kind,
        "schemaVersion": 1,
        "valid": True,
        "producer": copied_dict(witness.get("producer")),
        "rows": rows,
        "diagnostics": [],
        "quotedOnly": True,
    }


def malformed_witness(reason: str, *, source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a malformed import-diet witness payload."""

    return {
        "artifactKind": "ladon_import_diet_witness",
        "sourceArtifactKind": str(source.get("artifactKind", "")) if source else "",
        "schemaVersion": 1,
        "sourceSchemaVersion": source.get("schemaVersion", "") if source else "",
        "valid": False,
        "producer": {},
        "rows": [],
        "diagnostics": [
            {
                "kind": "import_diet.malformed_witness",
                "severity": "warning",
                "subject": "import_diet_witness",
                "message": reason,
                "importDietOnly": True,
            }
        ],
        "quotedOnly": True,
    }


def normalize_witness_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one import-diet witness row."""

    return compact({
        "module": str(row.get("module", "")),
        "sourcePath": str(row.get("sourcePath", "")),
        "originalImports": string_list(row.get("originalImports")),
        "minimizedImports": string_list(row.get("minimizedImports")),
        "removedImports": string_list(row.get("removedImports")),
        "toolName": str(row.get("toolName") or row.get("backend") or ""),
        "toolVersion": str(row.get("toolVersion", "")),
        "command": str(row.get("command", "")),
        "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
        "currentContentHash": str(row.get("currentContentHash", "")),
        "confidence": str(row.get("confidence", "unknown")),
        "status": str(row.get("status", "")),
        "quotedOnly": True,
    })


def import_diet_rows(module_dag: dict[str, Any], witness: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare fresh witness rows to observed import sites."""

    if not witness.get("valid"):
        return []
    rows = []
    edges = module_dag.get("edges", {})
    import_sites = module_dag.get("import_sites", {})
    metadata = module_dag.get("module_metadata", {})
    rank_by_module = review_rank_by_module(module_dag)
    for row in witness.get("rows", []):
        module = row.get("module", "")
        if module not in edges:
            rows.append(stale_row(row, "module is absent from current Ladon module inventory"))
            continue
        if witness_row_stale(row, metadata.get(module, {})):
            rows.append(stale_row(row, "witness source hash does not match current module evidence"))
            continue
        observed = set(edges.get(module, []))
        minimized = set(row.get("minimizedImports", []))
        removed = set(row.get("removedImports", [])) or (observed - minimized)
        for target in sorted(observed & removed):
            site = import_sites.get(module, {}).get(target, {})
            rows.append(compact({
                "kind": "redundant_import_candidate",
                "severity": "info",
                "module": module,
                "targetModule": target,
                "subject": f"{module} -> {target}",
                "sourcePath": site.get("sourcePath") or row.get("sourcePath"),
                "line": site.get("line"),
                "importText": site.get("importText"),
                "toolName": row.get("toolName"),
                "toolVersion": row.get("toolVersion"),
                "command": row.get("command"),
                "contentHash": row.get("contentHash"),
                "confidence": row.get("confidence", "unknown"),
                "priority": rank_by_module.get(module, 0),
                "nonclaim": "Quoted import-minimization evidence only; replay the named Lean/Lake command before removing imports.",
            }))
    return sorted(rows, key=lambda item: (-int(item.get("priority", 0)), item.get("subject", "")))


def witness_row_stale(row: dict[str, Any], metadata: dict[str, Any]) -> bool:
    """Return whether row-level hash metadata says the witness is stale."""

    current_hash = str(row.get("currentContentHash") or metadata.get("contentHash", ""))
    witness_hash = str(row.get("contentHash", ""))
    return bool(current_hash and witness_hash and current_hash != witness_hash)


def stale_row(row: dict[str, Any], reason: str) -> dict[str, Any]:
    """Return a stale import-diet diagnostic row."""

    return compact({
        "kind": "stale_import_diet_witness",
        "severity": "warning",
        "module": row.get("module", ""),
        "subject": row.get("module", "import_diet_witness"),
        "message": reason,
        "toolName": row.get("toolName"),
        "command": row.get("command"),
        "sourcePath": row.get("sourcePath"),
        "contentHash": row.get("contentHash"),
        "confidence": "low",
        "nonclaim": "Stale import-diet evidence does not classify imports as removable.",
    })


def review_rank_by_module(module_dag: dict[str, Any]) -> dict[str, int]:
    """Return impact rank from available fan and facade rows."""

    ranks: dict[str, int] = {}
    for field, metric in (
        ("top_fan_in", "fan_in"),
        ("top_fan_out", "fan_out"),
        ("top_target_owned_fan_in", "fan_in"),
        ("top_facade_fan_out", "fan_out"),
    ):
        for row in module_dag.get(field, []):
            ranks[str(row.get("module", ""))] = max(
                ranks.get(str(row.get("module", "")), 0),
                int(row.get(metric, 0)),
            )
    for row in module_dag.get("root_direct_import_closures", []):
        ranks[str(row.get("root", ""))] = max(
            ranks.get(str(row.get("root", "")), 0),
            int(row.get("reachable_module_count", 0)),
        )
    return ranks


def import_diet_finding(
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """Convert an import-diet row to a finding."""

    finding = {
        "kind": f"import_diet.{row['kind']}",
        "severity": row.get("severity", "info"),
        "subject": row.get("subject", ""),
        "count": int(row.get("priority", 1) or 1),
        "message": row.get("message")
        or f"{row.get('targetModule')} is a quoted redundant-import candidate for {row.get('module')}.",
        "importDietOnly": True,
        "authority": "external_tool_quoted",
        "evidenceRefs": [
            canonical_row_evidence(
                "import_diet",
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
    copy_finding_source_fields(finding, row)
    return finding


def diagnostic_findings(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return diagnostic rows as findings."""

    return [
        {
            "kind": row.get("kind", "import_diet.diagnostic"),
            "severity": row.get("severity", "warning"),
            "subject": row.get("subject", "import_diet_witness"),
            "count": 1,
            "message": row.get("message", ""),
            "importDietOnly": True,
            "evidenceRefs": [
                canonical_row_evidence(
                    "import_diet",
                    "diagnostics",
                    index,
                    identity={
                        "kind": row.get("kind", "import_diet.diagnostic"),
                        "subject": row.get("subject", "import_diet_witness"),
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
    """Preserve source attachment metadata supplied by an import-diet row."""

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


def import_diet_summary(rows: list[dict[str, Any]], diagnostics: list[dict[str, Any]]) -> dict[str, int]:
    """Count import-diet rows by kind."""

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
    """Return a shallow dictionary copy from JSON-like input."""

    return dict(value) if isinstance(value, dict) else {}


def string_list(value: Any) -> list[str]:
    """Return string list from JSON-like input."""

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
