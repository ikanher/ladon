"""OpenSpec packet status hygiene analysis."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


CHECKBOX_RE = re.compile(r"^\s*-\s+\[(?P<mark>[ xX])\]")
STATUS_RE = re.compile(r"^(?P<prefix>\s*status:\s*)(?P<status>\S+)(?P<suffix>.*)$")


def summarize_openspec_hygiene(openspec_root: Path) -> dict[str, Any]:
    """Return status/task drift summary for an OpenSpec root."""

    changes_root = openspec_root / "changes"
    rows = [
        inspect_change(change_dir)
        for change_dir in sorted(changes_root.iterdir())
        if change_dir.is_dir() and change_dir.joinpath(".openspec.yaml").is_file()
    ] if changes_root.is_dir() else []
    drift_rows = [row for row in rows if row["drift_kind"]]
    return {
        "openspec_root": str(openspec_root),
        "change_count": len(rows),
        "drift_count": len(drift_rows),
        "completed_active_drift_count": sum(
            1 for row in drift_rows if row["drift_kind"] == "completed_tasks_marked_active"
        ),
        "changes": rows,
        "drifts": drift_rows,
    }


def inspect_change(change_dir: Path) -> dict[str, Any]:
    """Inspect one OpenSpec change directory."""

    metadata_path = change_dir / ".openspec.yaml"
    tasks_path = change_dir / "tasks.md"
    metadata_status = read_metadata_status(metadata_path)
    task_summary = read_task_summary(tasks_path)
    inferred_status = inferred_change_status(task_summary)
    drift_kind = status_drift_kind(metadata_status, inferred_status)
    return {
        "id": change_dir.name,
        "metadata_path": str(metadata_path),
        "tasks_path": str(tasks_path),
        "metadata_status": metadata_status,
        "inferred_status": inferred_status,
        "drift_kind": drift_kind,
        **task_summary,
    }


def read_metadata_status(metadata_path: Path) -> str | None:
    """Read the simple `status:` value from an OpenSpec metadata file."""

    if not metadata_path.is_file():
        return None
    for line in metadata_path.read_text(encoding="utf-8").splitlines():
        match = STATUS_RE.match(line)
        if match:
            return match.group("status")
    return None


def read_task_summary(tasks_path: Path) -> dict[str, Any]:
    """Count checked and unchecked task-list items."""

    if not tasks_path.is_file():
        return {
            "task_file_exists": False,
            "task_count": 0,
            "checked_task_count": 0,
            "unchecked_task_count": 0,
        }
    checked = 0
    unchecked = 0
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        if match.group("mark").lower() == "x":
            checked += 1
        else:
            unchecked += 1
    return {
        "task_file_exists": True,
        "task_count": checked + unchecked,
        "checked_task_count": checked,
        "unchecked_task_count": unchecked,
    }


def inferred_change_status(task_summary: dict[str, Any]) -> str:
    """Infer status from checklist evidence only."""

    if not task_summary["task_file_exists"] or task_summary["task_count"] == 0:
        return "unknown"
    if task_summary["unchecked_task_count"] == 0:
        return "completed"
    return "active"


def status_drift_kind(metadata_status: str | None, inferred_status: str) -> str | None:
    """Return a narrow drift label for contradictory status evidence."""

    if metadata_status == "active" and inferred_status == "completed":
        return "completed_tasks_marked_active"
    if metadata_status == "completed" and inferred_status == "active":
        return "open_tasks_marked_completed"
    return None


def normalize_completed_active_statuses(openspec_root: Path) -> list[str]:
    """Rewrite completed-active drift metadata statuses to `completed`."""

    summary = summarize_openspec_hygiene(openspec_root)
    changed: list[str] = []
    for row in summary["drifts"]:
        if row["drift_kind"] != "completed_tasks_marked_active":
            continue
        replace_metadata_status(Path(row["metadata_path"]), "completed")
        changed.append(row["id"])
    return changed


def replace_metadata_status(metadata_path: Path, new_status: str) -> None:
    """Replace only the status line in an OpenSpec metadata file."""

    lines = metadata_path.read_text(encoding="utf-8").splitlines(keepends=True)
    rewritten: list[str] = []
    replaced = False
    for line in lines:
        match = STATUS_RE.match(line.rstrip("\n"))
        if match and not replaced:
            newline = "\n" if line.endswith("\n") else ""
            rewritten.append(f"{match.group('prefix')}{new_status}{match.group('suffix')}{newline}")
            replaced = True
        else:
            rewritten.append(line)
    if not replaced:
        raise ValueError(f"missing status line in {metadata_path}")
    metadata_path.write_text("".join(rewritten), encoding="utf-8")
