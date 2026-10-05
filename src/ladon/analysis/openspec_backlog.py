"""OpenSpec backlog and packet-process analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ladon.analysis.authority_freeze import inspect_authority_freeze
from ladon.analysis.openspec_hygiene import summarize_openspec_hygiene

DELTA_HEADER_RE = re.compile(
    r"^## (?:ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$",
    re.MULTILINE,
)
RECONCILIATION_LEDGER = Path("reconciliation/legacy-state-ledger.json")
CHANGE_ID_RE = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
DATED_ARCHIVE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")


def summarize_openspec_backlog(openspec_root: Path) -> dict[str, Any]:
    """Return operational backlog findings for an OpenSpec root."""

    hygiene = summarize_openspec_hygiene(openspec_root)
    freeze = inspect_authority_freeze(openspec_root)
    changes_root = openspec_root / "changes"
    active_change_ids = {
        path.name
        for path in changes_root.iterdir()
        if path.is_dir() and path.joinpath(".openspec.yaml").is_file()
    } if changes_root.is_dir() else set()
    referenced_change_ids = active_change_ids | archived_change_ids(changes_root / "archive")
    referenced_change_ids.update(freeze["localChildPlans"])
    packets = [
        packet_summary(openspec_root, row, referenced_change_ids)
        for row in hygiene["changes"]
    ]
    findings = [
        finding
        for packet in packets
        for finding in packet["findings"]
    ]
    findings.extend(reconciliation_ledger_findings(openspec_root, hygiene["changes"]))
    findings.extend(freeze["findings"])
    return {
        "openspec_root": str(openspec_root),
        "change_count": len(packets),
        "finding_count": len(findings),
        "packets": packets,
        "findings": findings,
        "expansion_freeze": freeze,
    }


def packet_summary(
    openspec_root: Path,
    hygiene_row: dict[str, Any],
    referenced_change_ids: set[str],
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
        change_dir,
        automation_path,
        automation_commands,
        child_refs,
        referenced_change_ids,
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
        "has_delta_spec": has_delta_spec(change_dir),
        "child_references": child_refs,
        "findings": findings,
    }


def packet_findings(
    change_id: str,
    hygiene_row: dict[str, Any],
    change_dir: Path,
    automation_path: Path,
    automation_commands: list[str],
    child_refs: list[str],
    referenced_change_ids: set[str],
) -> list[dict[str, Any]]:
    """Return operational findings for one packet."""

    findings: list[dict[str, Any]] = []
    if hygiene_row["drift_kind"]:
        findings.append(make_finding("openspec_status_drift", change_id, hygiene_row["drift_kind"]))
    if hygiene_row["inferred_status"] == "completed" and not has_delta_spec(change_dir):
        findings.append(
            make_finding(
                "invalid_completed_packet",
                change_id,
                "completed packet has no OpenSpec delta requirements",
            )
        )
    if not automation_path.is_file():
        findings.append(make_finding("missing_automation", change_id, "missing automation.json"))
    elif not has_validation_command(automation_commands):
        findings.append(make_finding("missing_validation_command", change_id, "automation lacks openspec validate"))
    for child in child_refs:
        if child not in referenced_change_ids:
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


def archived_change_ids(archive_root: Path) -> set[str]:
    """Return packet IDs represented by dated archive directories."""

    if not archive_root.is_dir():
        return set()
    change_ids: set[str] = set()
    for metadata_path in archive_root.glob("*/.openspec.yaml"):
        match = CHANGE_ID_RE.search(metadata_path.read_text(encoding="utf-8"))
        if match:
            change_ids.add(match.group(1))
            continue
        dated_match = DATED_ARCHIVE_RE.fullmatch(metadata_path.parent.name)
        if dated_match:
            change_ids.add(dated_match.group(1))
    return change_ids


def has_delta_spec(change_dir: Path) -> bool:
    """Return whether a packet contains at least one delta-requirements header."""

    specs_dir = change_dir / "specs"
    return specs_dir.is_dir() and any(
        DELTA_HEADER_RE.search(path.read_text(encoding="utf-8"))
        for path in specs_dir.glob("*/spec.md")
    )


def reconciliation_ledger_findings(
    openspec_root: Path,
    hygiene_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return coverage, ownership, and archive findings from the tracked ledger."""

    ledger_path = openspec_root / RECONCILIATION_LEDGER
    if not ledger_path.is_file():
        return []
    try:
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [ledger_finding("invalid_reconciliation_ledger", f"invalid JSON: {exc.msg}")]
    if not isinstance(payload, dict):
        return [ledger_finding("invalid_reconciliation_ledger", "ledger root must be an object")]
    findings = ledger_shape_findings(payload, openspec_root)
    changes = {str(row["id"]): row for row in hygiene_rows}
    findings.extend(ledger_packet_findings(payload.get("packets"), changes))
    findings.extend(ledger_archive_findings(payload.get("archiveBatches")))
    return findings


def ledger_shape_findings(
    payload: dict[str, Any],
    openspec_root: Path,
) -> list[dict[str, str]]:
    """Return top-level ledger structure findings."""

    findings: list[dict[str, str]] = []
    if payload.get("schemaVersion") != 1:
        findings.append(ledger_finding("invalid_reconciliation_ledger", "schemaVersion must be 1"))
    dependency_ref = payload.get("dependencyLedgerRef")
    project_root = openspec_root.parent
    if not isinstance(dependency_ref, str) or not project_root.joinpath(dependency_ref).is_file():
        findings.append(
            ledger_finding(
                "invalid_reconciliation_ledger",
                "dependencyLedgerRef must name an existing alpha dependency ledger",
            )
        )
    for key in ("baseline", "packets", "archiveBatches", "selfArchiveHandoff"):
        if key not in payload:
            findings.append(ledger_finding("invalid_reconciliation_ledger", f"missing {key}"))
    return findings


def ledger_packet_findings(
    packet_rows: Any,
    changes: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    """Return packet-level coverage and ownership findings."""

    if not isinstance(packet_rows, list):
        return [ledger_finding("invalid_reconciliation_ledger", "packets must be a list")]
    findings: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in packet_rows:
        if not isinstance(row, dict):
            findings.append(ledger_finding("invalid_reconciliation_ledger", "packet row must be an object"))
            continue
        change_id = str(row.get("id") or "")
        if not change_id or change_id in seen:
            findings.append(
                ledger_finding("invalid_reconciliation_ledger", f"missing or duplicate packet id: {change_id!r}")
            )
            continue
        seen.add(change_id)
        findings.extend(packet_coverage_findings(row, changes.get(change_id)))
    return findings


def packet_coverage_findings(
    row: dict[str, Any],
    hygiene_row: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Return coverage findings for one ledger packet."""

    change_id = str(row["id"])
    evidence = row.get("requirementEvidence")
    if not isinstance(evidence, list) or not evidence:
        return [ledger_finding("unowned_requirement", f"{change_id}: no requirement evidence")]
    findings = requirement_evidence_findings(row, evidence)
    findings.extend(packet_state_findings(row, hygiene_row))
    return findings


def requirement_evidence_findings(
    packet: dict[str, Any],
    evidence_rows: list[Any],
) -> list[dict[str, str]]:
    """Return the flattened findings for a packet's requirement evidence."""

    disposition = str(packet.get("disposition") or "")
    allowed = {"covered"} if disposition == "complete" else {"covered", "transferred", "retained"}
    findings: list[dict[str, str]] = []
    for evidence in evidence_rows:
        findings.extend(packet_evidence_findings(packet, evidence, allowed))
    return findings


def packet_state_findings(
    packet: dict[str, Any],
    hygiene_row: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Return findings derived from a packet's overall reconciliation state."""

    change_id = str(packet["id"])
    disposition = str(packet.get("disposition") or "")
    findings: list[dict[str, str]] = []
    if disposition == "blocked":
        findings.append(ledger_finding("reconciliation_blocker", f"{change_id}: blocked disposition"))
    if (
        disposition == "complete"
        and hygiene_row is not None
        and int(hygiene_row.get("unchecked_task_count", 0)) > 0
    ):
        findings.append(
            ledger_finding(
                "verified_shipped_unchecked_tasks",
                f"{change_id}: {hygiene_row['unchecked_task_count']} unchecked tasks",
            )
        )
    return findings


def packet_evidence_findings(
    packet: dict[str, Any],
    evidence: Any,
    allowed_outcomes: set[str],
) -> list[dict[str, str]]:
    """Return ownership and coverage findings for one requirement-evidence row."""

    change_id = str(packet["id"])
    if not isinstance(evidence, dict):
        return [ledger_finding("invalid_reconciliation_ledger", f"{change_id}: invalid evidence row")]
    disposition = str(packet.get("disposition") or "")
    requirement = str(evidence.get("requirement") or "(unnamed)")
    outcome = str(evidence.get("outcome") or "")
    findings: list[dict[str, str]] = []
    completion = completion_outcome_finding(
        change_id,
        disposition,
        requirement,
        outcome,
        allowed_outcomes,
    )
    if completion:
        findings.append(completion)
    ownership = residual_ownership_finding(packet, requirement, outcome)
    if ownership:
        findings.append(ownership)
    proof = completion_evidence_finding(change_id, disposition, requirement, evidence)
    if proof:
        findings.append(proof)
    return findings


def completion_outcome_finding(
    change_id: str,
    disposition: str,
    requirement: str,
    outcome: str,
    allowed_outcomes: set[str],
) -> dict[str, str] | None:
    """Return a finding when a completed disposition has an unsupported outcome."""

    completed = disposition in {"complete", "superseded-with-residuals"}
    if not completed or outcome in allowed_outcomes:
        return None
    return ledger_finding(
        "uncovered_completion",
        f"{change_id}: {requirement} has outcome {outcome or '(missing)'}",
    )


def residual_ownership_finding(
    packet: dict[str, Any],
    requirement: str,
    outcome: str,
) -> dict[str, str] | None:
    """Return a finding when residual work lacks an explicit owner."""

    residual = outcome in {"transferred", "retained", "blocked"}
    if not residual or packet.get("residualOwner"):
        return None
    return ledger_finding(
        "unowned_requirement",
        f"{packet['id']}: {requirement} has no residual owner",
    )


def completion_evidence_finding(
    change_id: str,
    disposition: str,
    requirement: str,
    evidence: dict[str, Any],
) -> dict[str, str] | None:
    """Return a finding when complete work lacks source, test, or gate evidence."""

    if disposition != "complete" or complete_evidence(evidence):
        return None
    return ledger_finding(
        "uncovered_completion",
        f"{change_id}: {requirement} lacks source, test, or gate evidence",
    )


def complete_evidence(item: dict[str, Any]) -> bool:
    """Return whether a completed requirement has source, test, and gate evidence."""

    return all(
        isinstance(item.get(key), list) and bool(item[key])
        for key in ("source", "tests", "gates")
    )


def ledger_archive_findings(batch_rows: Any) -> list[dict[str, str]]:
    """Return archive-sequence findings, excluding the final self-archive handoff."""

    if not isinstance(batch_rows, list):
        return [ledger_finding("invalid_reconciliation_ledger", "archiveBatches must be a list")]
    findings: list[dict[str, str]] = []
    sequences = [row.get("sequence") for row in batch_rows if isinstance(row, dict)]
    if sequences != list(range(1, len(sequences) + 1)):
        findings.append(ledger_finding("invalid_reconciliation_ledger", "archive sequences must be contiguous"))
    for row in batch_rows[:-1]:
        if not isinstance(row, dict):
            continue
        status = row.get("result", {}).get("status") if isinstance(row.get("result"), dict) else None
        if status not in {"planned", "complete"}:
            findings.append(
                ledger_finding(
                    "archive_batch_blocker",
                    f"{row.get('change', '(unknown)')}: archive result is {status or '(missing)'}",
                )
            )
    return findings


def ledger_finding(kind: str, detail: str) -> dict[str, str]:
    """Build a reconciliation-ledger backlog finding."""

    return make_finding(kind, "ladon-openspec-state-reconciliation", detail)
