"""Refactoring prescriptions derived from Ladon review findings."""

from __future__ import annotations

from typing import Any

from ladon.finding_workflow import canonical_row_evidence


ACTION_MESSAGES = {
    "extract_common_lower_layer": "Extract or clarify a neutral lower layer for shared imports.",
    "move_bridge_to_neutral_namespace": "Move bridge glue to an explicit neutral bridge namespace or policy.",
    "declare_explicit_bridge_policy": "Declare intentional bridge imports explicitly in policy.",
    "split_large_owner": "Split large owner module into smaller reviewable surfaces.",
    "promote_public_facade": "Promote stable API surface to an intentional public facade.",
    "demote_implementation_import": "Demote implementation import pressure behind a facade or lower layer.",
    "clean_generator_output": "Clean repeated generated output at the generator boundary.",
    "move_generated_parameters_to_manifest": "Move generated parameters/cases/status labels to a manifest.",
    "run_import_diet": "Replay Lean/Lake import-diet evidence before changing imports.",
    "add_proof_surface_witness_evidence": "Add proof-surface witness evidence for public claim routes.",
}


def summarize_refactoring_prescriptions(
    *,
    module_dag: dict[str, Any],
    findings: list[dict[str, Any]],
    architecture_policy: dict[str, Any] | None = None,
    import_diet: dict[str, Any] | None = None,
    proof_xray: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return prioritized refactoring prescription rows."""

    rows: list[dict[str, Any]] = []
    rows.extend(architecture_prescriptions(architecture_policy))
    rows.extend(module_smell_prescriptions(module_dag, findings))
    rows.extend(import_diet_prescriptions(import_diet))
    rows.extend(proof_route_prescriptions(findings))
    rows.extend(proof_xray_prescriptions(proof_xray))
    rows = sorted(dedupe(rows), key=lambda row: (-int(row.get("priority", 0)), row["action"], row["subject"]))
    return {
        "artifactKind": "ladon_refactoring_prescription_report",
        "schemaVersion": 1,
        "summary": prescription_summary(rows),
        "rows": rows,
        "findings": [
            prescription_finding(row, index)
            for index, row in enumerate(rows[:20])
        ],
        "trustNote": "Prescriptions are review directions from evidence; Ladon does not rewrite source or prove the refactor is correct.",
    }


def architecture_prescriptions(policy: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return prescriptions from architecture policy rows."""

    if not policy:
        return []
    rows = []
    for row in policy.get("sharedDependencySummary", [])[:20]:
        rows.append(prescription(
            "extract_common_lower_layer",
            row["targetModule"],
            confidence=row.get("confidence", "unknown"),
            priority=int(row.get("confidenceScore", 0)),
            evidence=row,
        ))
    for row in policy.get("findings", []):
        if row.get("kind") != "architecture_policy.direct_forbidden_import":
            continue
        action = "move_bridge_to_neutral_namespace" if row.get("policyContext") == "bridge-ish" else "demote_implementation_import"
        if row.get("policyContext") == "facade-ish":
            action = "promote_public_facade"
        rows.append(prescription(
            action,
            row.get("subject", ""),
            confidence=row.get("triageSeverity", row.get("severity", "unknown")),
            priority=80 if row.get("policyContext") == "core-looking" else 50,
            evidence=row,
        ))
    return rows


def module_smell_prescriptions(module_dag: dict[str, Any], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return prescriptions from module-level smells."""

    rows = []
    for row in module_dag.get("duplicate_import_family_summary", [])[:10]:
        rows.append(prescription(
            "clean_generator_output" if row.get("generated") else "run_import_diet",
            (
                f"{row.get('generatorFamily') or '(non-generated-tag)'} -> "
                f"{row.get('target')}"
            ),
            confidence="medium",
            priority=35,
            evidence=row,
        ))
    for row in module_dag.get("module_name_smells", [])[:20]:
        if row.get("generated"):
            rows.append(prescription(
                "move_generated_parameters_to_manifest",
                row["module"],
                confidence="medium",
                priority=25,
                evidence=row,
            ))
    for finding in findings:
        if finding.get("kind") == "large_target_owned_module":
            rows.append(prescription(
                "split_large_owner",
                finding.get("subject", ""),
                confidence="medium",
                priority=min(70, int(finding.get("count", 0)) // 200),
                evidence=finding,
            ))
    for row in module_dag.get("top_facade_like_modules", [])[:10]:
        if row.get("subtype") == "mixed_barrel_and_theorems":
            rows.append(prescription(
                "promote_public_facade",
                row["module"],
                confidence="low",
                priority=20,
                evidence=row,
            ))
    return rows


def import_diet_prescriptions(import_diet: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return prescriptions from import-diet rows."""

    if not import_diet:
        return []
    return [
        prescription(
            "run_import_diet",
            row.get("subject", ""),
            confidence=row.get("confidence", "unknown"),
            priority=40 + int(row.get("priority", 0)),
            evidence=row,
        )
        for row in import_diet.get("rows", [])
        if row.get("kind") == "redundant_import_candidate"
    ]


def proof_route_prescriptions(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return prescriptions from existing proof-surface route diagnostics."""

    proof_kinds = {
        "ladon.proof_surface.missing_axiom_audit",
        "ladon.proof_surface.missing_no_drift_gate",
        "ladon.proof_surface.spec_stub_used_as_authority",
    }
    return [
        prescription(
            "add_proof_surface_witness_evidence",
            row.get("subject", ""),
            confidence="high",
            priority=85,
            evidence=row,
        )
        for row in findings
        if row.get("ruleId") in proof_kinds or row.get("kind") in proof_kinds
    ]


def proof_xray_prescriptions(proof_xray: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return prescriptions from proof-xray rows."""

    if not proof_xray:
        return []
    return [
        prescription(
            "add_proof_surface_witness_evidence",
            row.get("subject", ""),
            confidence=row.get("confidence", "unknown"),
            priority=45,
            evidence=row,
        )
        for row in proof_xray.get("rows", [])
        if row.get("kind") == "trust_footprint"
    ]


def prescription(action: str, subject: str, *, confidence: str, priority: int, evidence: dict[str, Any]) -> dict[str, Any]:
    """Build one prescription row."""

    return {
        "action": action,
        "subject": subject,
        "message": ACTION_MESSAGES[action],
        "confidence": confidence,
        "priority": int(priority),
        "evidence": evidence,
        "nonclaim": "Review guidance only; Ladon does not change source or prove this refactor is correct.",
    }


def prescription_finding(
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """Return one prescription as a finding."""

    evidence = row.get("evidence")
    inherited = (
        list(evidence.get("evidenceRefs", []))
        if isinstance(evidence, dict)
        and isinstance(evidence.get("evidenceRefs"), list)
        else []
    )
    finding = {
        "kind": f"refactoring_prescription.{row['action']}",
        "severity": "info",
        "subject": row.get("subject", ""),
        "count": int(row.get("priority", 1) or 1),
        "message": row.get("message", ""),
        "refactoringPrescriptionOnly": True,
        "evidenceRefs": [
            *inherited,
            canonical_row_evidence(
                "refactoring_prescriptions",
                "rows",
                index,
                identity={
                    "action": row.get("action"),
                    "subject": row.get("subject", ""),
                },
                authority="refactoring_prescription_analysis",
            ),
        ],
    }
    if isinstance(evidence, dict):
        copy_finding_source_fields(finding, evidence)
    return finding


def copy_finding_source_fields(
    finding: dict[str, Any],
    row: dict[str, Any],
) -> None:
    """Preserve source attachment metadata inherited by a prescription."""

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
        "pathImportSites",
    ):
        if key in row:
            finding[key] = row[key]


def prescription_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count prescriptions by action."""

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["action"]] = counts.get(row["action"], 0) + 1
    return dict(sorted(counts.items()))


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate prescriptions by action and subject."""

    seen = set()
    result = []
    for row in rows:
        key = (row.get("action"), row.get("subject"))
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result
