"""Lean module-readiness review signals.

These rows summarize module/API boundary pressure from Ladon's existing graph
evidence plus optional Lean-owned witness metadata. They are review-routing
signals, not Lean module-system judgments.
"""

from __future__ import annotations

from typing import Any

from ladon.finding_workflow import canonical_row_evidence


SUPPORTED_WITNESS_KINDS = {"ladon_module_system_witness", "module_system_witness"}
SUPPORTED_SCHEMA_VERSIONS = {1, "1"}


def summarize_module_readiness(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None = None,
    module_system_witness: Any = None,
) -> dict[str, Any]:
    """Return module-readiness rows from graph and optional witness evidence."""

    witness = normalize_module_system_witness(module_system_witness)
    rows = module_readiness_rows(module_dag, declaration_graph, witness)
    diagnostics = witness.get("diagnostics", []) if witness else []
    findings = [
        readiness_finding(row, index)
        for index, row in enumerate(rows[:10])
    ]
    findings.extend(diagnostic_findings(diagnostics))
    return {
        "artifactKind": "ladon_module_readiness_report",
        "schemaVersion": 1,
        "summary": readiness_summary(rows, diagnostics),
        "witness": witness_summary(witness),
        "rows": rows,
        "diagnostics": diagnostics,
        "findings": findings,
        "trustNote": "Module-readiness rows are review-routing evidence only; they are not Lean module-system proof or theorem-truth claims.",
    }


def normalize_module_system_witness(witness: Any) -> dict[str, Any] | None:
    """Normalize optional module-system witness rows."""

    if witness is None:
        return None
    if not isinstance(witness, dict):
        return malformed_witness("module-system witness input must be a JSON object")
    kind = str(witness.get("artifactKind", ""))
    if kind not in SUPPORTED_WITNESS_KINDS:
        return malformed_witness(
            "module-system witness artifactKind is unsupported",
            source=witness,
        )
    if witness.get("schemaVersion") not in SUPPORTED_SCHEMA_VERSIONS:
        return malformed_witness(
            "module-system witness schemaVersion is unsupported; expected 1",
            source=witness,
        )
    rows = [
        normalize_witness_row(row)
        for row in witness.get("modules", witness.get("rows", []))
        if isinstance(row, dict)
    ]
    return {
        "artifactKind": "ladon_module_system_witness",
        "sourceArtifactKind": kind,
        "schemaVersion": 1,
        "valid": True,
        "producer": copied_dict(witness.get("producer")),
        "rows": rows,
        "diagnostics": [],
        "quotedOnly": True,
    }


def malformed_witness(reason: str, *, source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a malformed module-system witness payload."""

    return {
        "artifactKind": "ladon_module_system_witness",
        "sourceArtifactKind": str(source.get("artifactKind", "")) if source else "",
        "schemaVersion": 1,
        "sourceSchemaVersion": source.get("schemaVersion", "") if source else "",
        "valid": False,
        "producer": {},
        "rows": [],
        "diagnostics": [
            {
                "kind": "module_readiness.malformed_witness",
                "severity": "warning",
                "subject": "module_system_witness",
                "message": reason,
                "moduleReadinessOnly": True,
            }
        ],
        "quotedOnly": True,
    }


def normalize_witness_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one quoted module-system witness row."""

    return compact({
        "module": str(row.get("module", "")),
        "sourcePath": str(row.get("sourcePath", "")),
        "status": str(row.get("status", "")),
        "visibility": str(row.get("visibility", "")),
        "publicImports": string_list(row.get("publicImports")),
        "privateImports": string_list(row.get("privateImports")),
        "exposedDeclarations": string_list(row.get("exposedDeclarations")),
        "backend": str(row.get("backend") or row.get("toolName") or ""),
        "toolVersion": str(row.get("toolVersion", "")),
        "command": str(row.get("command", "")),
        "contentHash": str(row.get("contentHash") or row.get("sourceHash") or ""),
        "confidence": str(row.get("confidence", "unknown")),
        "authority": "external_tool_quoted",
        "quotedOnly": True,
    })


def module_readiness_rows(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    witness: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build module-readiness rows from available evidence."""

    rows: list[dict[str, Any]] = []
    rows.extend(facade_rows(module_dag))
    rows.extend(implementation_pressure_rows(module_dag))
    rows.extend(generated_aggregation_rows(module_dag))
    rows.extend(namespace_drift_rows(module_dag, declaration_graph))
    rows.extend(witness_rows(witness))
    return sorted(rows, key=row_sort_key)


def facade_rows(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Return readiness rows for public facade/API pressure."""

    rows = []
    for row in module_dag.get("top_facade_like_modules", [])[:10]:
        subtype = str(row.get("subtype", ""))
        if subtype == "generated_all":
            continue
        rows.append(readiness_row(
            "public_facade_pressure",
            row["module"],
            "info",
            "Facade-like module has broad public import surface; review API boundary and implementation exposure.",
            sourcePath=row.get("path"),
            fanOut=row.get("fan_out"),
            facadeSubtype=subtype,
            evidence={"declarationCount": row.get("declarationCount"), "tags": row.get("tags", [])},
        ))
    return rows


def implementation_pressure_rows(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Return readiness rows for implementation modules acting like API."""

    rows = []
    for row in module_dag.get("top_handwritten_fan_in", [])[:8]:
        fan_in = int(row.get("fan_in", 0))
        if fan_in < 5:
            continue
        rows.append(readiness_row(
            "implementation_public_pressure",
            row["module"],
            "info",
            "Handwritten implementation module has high fan-in; review whether a public facade or common layer should own this surface.",
            sourcePath=row.get("path"),
            fanIn=fan_in,
            sampleImporters=row.get("sample_importers", []),
        ))
    return rows


def generated_aggregation_rows(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Return readiness rows for generated aggregation modules."""

    return [
        readiness_row(
            "generated_public_aggregation",
            row["module"],
            "info",
            "Generated aggregation module is public API pressure; review generator boundary rather than treating it as ordinary implementation coupling.",
            sourcePath=row.get("path"),
            fanOut=row.get("fan_out"),
            facadeSubtype=row.get("subtype"),
        )
        for row in module_dag.get("top_facade_like_modules", [])[:10]
        if row.get("subtype") == "generated_all"
    ]


def namespace_drift_rows(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return namespace/module drift rows when declaration evidence exists."""

    if not declaration_graph:
        return []
    metadata = module_dag.get("module_metadata", {})
    by_module: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for declaration in declaration_graph.get("declarations", []):
        name = str(declaration.get("declaration", ""))
        module = str(declaration.get("module", ""))
        namespace = name.rsplit(".", 1)[0] if "." in name else ""
        if not module or not namespace or namespace_compatible(module, namespace):
            continue
        by_module.setdefault(module, {}).setdefault(namespace, []).append(declaration)
    return [
        namespace_drift_row(module, namespaces, metadata)
        for module, namespaces in sorted(by_module.items())
    ][:20]


def namespace_compatible(module: str, namespace: str) -> bool:
    """Accept module, child, and conventional parent namespace layouts."""

    return (
        namespace == module
        or namespace.startswith(f"{module}.")
        or module.startswith(f"{namespace}.")
    )


def namespace_drift_row(
    module: str,
    namespaces: dict[str, list[dict[str, Any]]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build one aggregated unrelated-namespace diagnostic per module."""

    ranked = sorted(
        namespaces.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    namespace, declarations = ranked[0]
    samples = sorted(
        str(row.get("declaration", ""))
        for rows in namespaces.values()
        for row in rows
    )
    source_path = next(
        (
            row.get("sourcePath")
            for row in declarations
            if row.get("sourcePath")
        ),
        metadata.get(module, {}).get("path"),
    )
    return readiness_row(
        "namespace_module_drift",
        module,
        "info",
        "Dominant declaration namespace is unrelated to the module path; "
        "review source organization without treating this as a Lean "
        "correctness failure.",
        namespace=namespace,
        unrelatedNamespaceCounts={
            name: len(rows)
            for name, rows in ranked
        },
        declarationCount=sum(len(rows) for rows in namespaces.values()),
        sampleDeclarations=samples[:8],
        sourcePath=source_path,
        authority="source_declaration_inventory",
    )


def witness_rows(witness: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return rows quoted from optional module-system witnesses."""

    if not witness or not witness.get("valid"):
        return []
    return [
        readiness_row(
            "module_system_witness",
            row["module"],
            "info" if complete_witness_row(row) else "warning",
            "Lean module-system witness row is quoted as module boundary evidence.",
            **{key: value for key, value in row.items() if key != "module"},
        )
        for row in witness.get("rows", [])
        if row.get("module")
    ]


def complete_witness_row(row: dict[str, Any]) -> bool:
    """Return whether witness metadata is strong enough for high confidence."""

    return all(row.get(key) for key in ("backend", "toolVersion", "command", "contentHash"))


def readiness_row(kind: str, module: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    """Build one module-readiness row."""

    row = {
        "kind": kind,
        "severity": severity,
        "module": module,
        "subject": module,
        "message": message,
        "nonclaim": "Review-routing evidence only; not a Lean module-system proof or theorem-truth claim.",
    }
    row.update({key: value for key, value in extra.items() if not empty(value)})
    return row


def readiness_finding(
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """Convert one readiness row into a report finding."""

    finding = {
        "kind": f"module_readiness.{row['kind']}",
        "severity": row.get("severity", "info"),
        "subject": row.get("subject", row.get("module", "")),
        "count": int(row.get("fanIn") or row.get("fanOut") or 1),
        "message": row.get("message", ""),
        "moduleReadinessOnly": True,
        "evidenceRefs": [
            canonical_row_evidence(
                "module_readiness",
                "rows",
                index,
                identity={
                    "kind": row.get("kind"),
                    "subject": row.get("subject", row.get("module", "")),
                },
                authority=str(row.get("authority", "module_readiness_analysis")),
            )
        ],
    }
    copy_finding_source_fields(finding, row)
    return finding


def diagnostic_findings(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return malformed witness diagnostics as findings."""

    return [
        {
            "kind": row.get("kind", "module_readiness.diagnostic"),
            "severity": row.get("severity", "warning"),
            "subject": row.get("subject", "module_system_witness"),
            "count": 1,
            "message": row.get("message", ""),
            "moduleReadinessOnly": True,
            "evidenceRefs": [
                canonical_row_evidence(
                    "module_readiness",
                    "diagnostics",
                    index,
                    identity={
                        "kind": row.get("kind", "module_readiness.diagnostic"),
                        "subject": row.get("subject", "module_system_witness"),
                    },
                    authority="module_readiness_analysis",
                )
            ],
        }
        for index, row in enumerate(diagnostics)
    ]


def copy_finding_source_fields(
    finding: dict[str, Any],
    row: dict[str, Any],
) -> None:
    """Preserve source attachment metadata supplied by a readiness row."""

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


def readiness_summary(rows: list[dict[str, Any]], diagnostics: list[dict[str, Any]]) -> dict[str, int]:
    """Count readiness rows by kind."""

    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["kind"])] = counts.get(str(row["kind"]), 0) + 1
    for row in diagnostics:
        counts[str(row.get("kind", "diagnostic"))] = counts.get(str(row.get("kind", "diagnostic")), 0) + 1
    return dict(sorted(counts.items()))


def witness_summary(witness: dict[str, Any] | None) -> dict[str, Any]:
    """Return compact witness state."""

    if witness is None:
        return {"present": False, "valid": False}
    return {
        "present": True,
        "valid": witness.get("valid") is True,
        "rowCount": len(witness.get("rows", [])),
        "diagnosticCount": len(witness.get("diagnostics", [])),
        "quotedOnly": True,
    }


def row_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    """Sort rows by broad review priority."""

    priority = {
        "namespace_module_drift": 0,
        "implementation_public_pressure": 1,
        "public_facade_pressure": 2,
        "generated_public_aggregation": 3,
        "module_system_witness": 4,
    }
    return (priority.get(str(row.get("kind", "")), 99), str(row.get("module", "")), str(row.get("subject", "")))


def copied_dict(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy from JSON-like input."""

    return dict(value) if isinstance(value, dict) else {}


def string_list(value: Any) -> list[str]:
    """Return a list of strings from JSON-like input."""

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
