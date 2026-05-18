"""OpenSpec backlog and packet-process analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ladon.analysis.openspec_hygiene import summarize_openspec_hygiene


def summarize_openspec_backlog(openspec_root: Path) -> dict[str, Any]:
    """Return operational backlog findings for an OpenSpec root."""

    hygiene = summarize_openspec_hygiene(openspec_root)
    changes_root = openspec_root / "changes"
    change_ids = {
        path.name
        for path in changes_root.iterdir()
        if path.is_dir() and path.joinpath(".openspec.yaml").is_file()
    } if changes_root.is_dir() else set()
    packets = [packet_summary(openspec_root, row, change_ids) for row in hygiene["changes"]]
    findings = [
        finding
        for packet in packets
        for finding in packet["findings"]
    ]
    return {
        "openspec_root": str(openspec_root),
        "change_count": len(packets),
        "finding_count": len(findings),
        "packets": packets,
        "findings": findings,
    }


def packet_summary(
    openspec_root: Path,
    hygiene_row: dict[str, Any],
    change_ids: set[str],
) -> dict[str, Any]:
    """Return one packet summary with operational findings."""

    change_id = hygiene_row["id"]
    change_dir = openspec_root / "changes" / change_id
    automation_path = change_dir / "automation.json"
    automation_commands = read_automation_commands(automation_path)
    child_refs = child_references(change_dir)
    findings = packet_findings(
        change_id,
        hygiene_row,
        automation_path,
        automation_commands,
        child_refs,
        change_ids,
    )
    return {
        "id": change_id,
        "metadata_status": hygiene_row["metadata_status"],
        "inferred_status": hygiene_row["inferred_status"],
        "task_count": hygiene_row["task_count"],
        "checked_task_count": hygiene_row["checked_task_count"],
        "unchecked_task_count": hygiene_row["unchecked_task_count"],
        "has_automation": automation_path.is_file(),
        "automation_command_count": len(automation_commands),
        "has_validation_command": has_validation_command(automation_commands),
        "child_references": child_refs,
        "findings": findings,
    }


def packet_findings(
    change_id: str,
    hygiene_row: dict[str, Any],
    automation_path: Path,
    automation_commands: list[str],
    child_refs: list[str],
    change_ids: set[str],
) -> list[dict[str, Any]]:
    """Return operational findings for one packet."""

    findings: list[dict[str, Any]] = []
    if hygiene_row["drift_kind"]:
        findings.append(make_finding("openspec_status_drift", change_id, hygiene_row["drift_kind"]))
    if not automation_path.is_file():
        findings.append(make_finding("missing_automation", change_id, "missing automation.json"))
    elif not has_validation_command(automation_commands):
        findings.append(make_finding("missing_validation_command", change_id, "automation lacks openspec validate"))
    for child in child_refs:
        if child not in change_ids:
            findings.append(make_finding("stale_child_reference", change_id, child))
    return findings


def make_finding(kind: str, change_id: str, detail: str) -> dict[str, str]:
    """Build one stable backlog finding row."""

    return {
        "kind": kind,
        "change_id": change_id,
        "detail": detail,
    }


def read_automation_commands(automation_path: Path) -> list[str]:
    """Read command strings from automation metadata."""

    if not automation_path.is_file():
        return []
    try:
        payload = json.loads(automation_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return command_strings(payload)


def command_strings(payload: dict[str, Any]) -> list[str]:
    """Return automation commands from flat or phased automation payloads."""

    commands = [item for item in payload.get("commands", []) if isinstance(item, str)]
    phases = payload.get("phases", {})
    if isinstance(phases, dict):
        for phase_commands in phases.values():
            if isinstance(phase_commands, list):
                commands.extend(item for item in phase_commands if isinstance(item, str))
    return [str(command) for command in commands]


def has_validation_command(commands: list[str]) -> bool:
    """Return whether automation includes OpenSpec validation."""

    return any("openspec validate" in command for command in commands)


def child_references(change_dir: Path) -> list[str]:
    """Return child packet IDs referenced by `children/*.md` files."""

    children_dir = change_dir / "children"
    if not children_dir.is_dir():
        return []
    return sorted(path.stem for path in children_dir.glob("*.md"))
