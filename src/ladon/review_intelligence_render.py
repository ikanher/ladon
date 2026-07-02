"""Text rendering helpers for Lean review-intelligence sections."""

from __future__ import annotations

from typing import Any


def module_readiness_lines(report: dict[str, Any] | None) -> list[str]:
    """Render Lean module-readiness review rows."""

    if not report:
        return []
    summary = report.get("summary", {})
    witness = report.get("witness", {})
    lines = [
        "Module Readiness",
        f"- rows: {len(report.get('rows', []))}",
        f"- witness: present={witness.get('present', False)} valid={witness.get('valid', False)}",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items())[:8])
    lines.extend(
        (
            f"- {row.get('kind')}: {row.get('module') or row.get('subject')} "
            f"severity={row.get('severity', 'info')}"
        )
        for row in report.get("rows", [])[:5]
    )
    return [*lines, ""]


def import_diet_lines(report: dict[str, Any] | None) -> list[str]:
    """Render optional import-diet witness rows."""

    if not report:
        return []
    summary = report.get("summary", {})
    lines = [
        "Import Diet",
        f"- rows: {len(report.get('rows', []))}",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(
        (
            f"- {row.get('subject')}: {row.get('kind')} "
            f"confidence={row.get('confidence', 'unknown')}"
        )
        for row in report.get("rows", [])[:5]
    )
    return [*lines, ""]


def proof_xray_lines(report: dict[str, Any] | None) -> list[str]:
    """Render optional proof-xray staging rows."""

    if not report:
        return []
    summary = report.get("summary", {})
    lines = [
        "Proof X-Ray",
        f"- rows: {len(report.get('rows', []))}",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(
        (
            f"- {row.get('subject')}: {row.get('kind')} "
            f"authority={row.get('authority', 'unknown')}"
        )
        for row in report.get("rows", [])[:5]
    )
    return [*lines, ""]


def refactoring_prescription_lines(report: dict[str, Any] | None) -> list[str]:
    """Render prioritized refactoring prescription rows."""

    if not report:
        return []
    summary = report.get("summary", {})
    lines = [
        "Refactoring Prescriptions",
        f"- rows: {len(report.get('rows', []))}",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items())[:8])
    lines.extend(
        (
            f"- {row.get('action')}: {row.get('subject')} "
            f"priority={row.get('priority', 0)} confidence={row.get('confidence', 'unknown')}"
        )
        for row in report.get("rows", [])[:8]
    )
    return [*lines, ""]
