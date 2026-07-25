"""Execution engine for the materialized alpha-readiness plan."""

from __future__ import annotations

import json
import shlex
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from alpha_readiness_plan import (
    ChildPacket,
    Milestone,
    ReadinessPlan,
    milestone_tasks_complete,
)
from release_gate_runtime import run_checked
from release_gate_types import GateError


FORBIDDEN_COMMAND_TOKENS = frozenset(
    {"&&", "||", ";", "|", ">", ">>", "<", "2>", "2>>"}
)
REQUIRED_AUTHORITY_CLASSES = frozenset(
    {
        "ladon_report_metadata",
        "lean_elaborated",
        "lexical_text",
        "parser_candidate",
        "quoted_external",
    }
)
REPORT_AUTHORITY_VOCABULARY = frozenset(
    {
        "capability-owner",
        "external_tool_quoted",
        "ladon-analysis",
        "ladon_derived_heuristic",
        "lean-environment-direct",
        "lean_elaborated",
        "lean_environment",
        "lean_parser",
        "lexical_text",
        "module_import_graph",
        "parser_observed",
        "source_declaration_inventory",
        "unknown",
    }
)


class ReadinessFailure(GateError):
    """A fail-fast readiness error carrying its machine-readable ledger."""

    def __init__(self, message: str, summary: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.summary = dict(summary)


def execute_readiness_plan(
    plan: ReadinessPlan,
    *,
    candidate_root: Path,
    environment: Mapping[str, str],
    require_all_children: bool,
) -> dict[str, Any]:
    """Execute milestone and child registries in expanded dependency order."""

    require_authority_ledger(plan.ledger)
    blockers = child_blockers(plan)
    if require_all_children and blockers:
        summary = readiness_summary(plan, candidate_root, blockers, ())
        raise ReadinessFailure(
            "incomplete alpha children: " + json.dumps(blockers, sort_keys=True),
            summary,
        )
    executed: set[tuple[str, str]] = set()
    results: list[dict[str, str]] = []
    for event in plan.event_order:
        try:
            execute_readiness_event(
                plan,
                event,
                candidate_root,
                environment,
                executed,
                results,
            )
        except GateError as error:
            owner = event_owner(event)
            blockers.setdefault(owner, []).append(f"required gate failed: {error}")
            summary = readiness_summary(plan, candidate_root, blockers, results)
            raise ReadinessFailure(
                f"child {owner} gate failed: {error}",
                summary,
            ) from error
    return readiness_summary(plan, candidate_root, blockers, results)


def execute_readiness_event(
    plan: ReadinessPlan,
    event: str,
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Execute one milestone or child-close event."""

    if event in plan.milestones:
        execute_milestone(
            plan,
            plan.milestones[event],
            candidate_root,
            environment,
            executed,
            results,
        )
    elif event.endswith("@close"):
        change = event.removesuffix("@close")
        execute_child_registry(
            plan.packets[change],
            candidate_root,
            environment,
            executed,
            results,
        )


def event_owner(event: str) -> str:
    """Return the child ID that owns a lifecycle or milestone event."""

    return event.split("#", 1)[0].removesuffix("@start").removesuffix("@close")


def child_blockers(plan: ReadinessPlan) -> dict[str, list[str]]:
    """Return every unresolved child completion blocker."""

    return {
        change: [
            f"unchecked task {task_id}"
            for task_id in packet.incomplete_tasks
        ]
        for change, packet in sorted(plan.packets.items())
        if packet.incomplete_tasks
    }


def require_authority_ledger(ledger: Mapping[str, Any]) -> None:
    """Require every report authority class named by the umbrella contract."""

    rows = ledger.get("authorityClasses")
    if not isinstance(rows, list):
        raise GateError("dependency ledger omits authorityClasses")
    child_ids = authority_owner_ids(ledger)
    present = authority_class_ids(rows)
    missing = sorted(REQUIRED_AUTHORITY_CLASSES - present)
    if missing:
        raise GateError(f"dependency ledger omits authority classes: {missing}")
    unknown_classes = sorted(present - REQUIRED_AUTHORITY_CLASSES)
    if unknown_classes:
        raise GateError(
            f"dependency ledger has unknown authority classes: {unknown_classes}"
        )
    values: set[str] = set()
    for row in rows:
        values.update(require_valid_authority_row(row, child_ids))
    unknown = sorted(values - REPORT_AUTHORITY_VOCABULARY)
    if unknown:
        raise GateError(f"dependency ledger has unknown report authority values: {unknown}")
    omitted = sorted(REPORT_AUTHORITY_VOCABULARY - values)
    if omitted:
        raise GateError(f"dependency ledger omits report authority values: {omitted}")


def authority_owner_ids(ledger: Mapping[str, Any]) -> frozenset[str]:
    """Return the child IDs eligible to own authority classes."""

    children = ledger.get("children")
    if not isinstance(children, list):
        raise GateError("dependency ledger omits children for authority ownership")
    ids = {
        str(row.get("change"))
        for row in children
        if isinstance(row, Mapping) and isinstance(row.get("change"), str)
    }
    if len(ids) != len(children):
        raise GateError("dependency ledger has invalid authority-owner children")
    return frozenset(ids)


def authority_class_ids(rows: Sequence[Any]) -> set[str]:
    """Return unique authority class IDs and reject malformed duplicates."""

    ids = [
        str(row.get("id"))
        for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    ]
    if len(ids) != len(rows) or len(set(ids)) != len(ids):
        raise GateError("dependency ledger has invalid or duplicate authority classes")
    return set(ids)


def require_valid_authority_row(
    row: Any,
    child_ids: frozenset[str],
) -> tuple[str, ...]:
    """Validate one authority row and return its concrete report values."""

    assert isinstance(row, Mapping)
    owner = row.get("owner")
    values = row.get("reportValues")
    if owner not in child_ids:
        raise GateError(f"authority class {row['id']!r} has unknown owner {owner!r}")
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(value, str) or not value for value in values)
    ):
        raise GateError(f"authority class {row['id']!r} has invalid reportValues")
    return tuple(values)


def execute_milestone(
    plan: ReadinessPlan,
    milestone: Milestone,
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Validate milestone phase/task state and execute its gates."""

    packet = plan.packets[milestone.owner]
    require_milestone_attained(packet, milestone)
    for command in milestone.gates:
        execute_registered_command(
            milestone.event,
            command,
            candidate_root,
            environment,
            executed,
            results,
        )
    if milestone.gate_registry:
        require_matching_registry(milestone)
        execute_commands(
            packet,
            packet.automation,
            candidate_root,
            environment,
            executed,
            results,
        )


def require_milestone_attained(
    packet: ChildPacket,
    milestone: Milestone,
) -> None:
    """Reject unattained pre-close or post-archive milestone predicates."""

    if milestone.phase == "post-archive":
        if packet.state != "archived" or not packet.complete:
            raise GateError(
                f"post-archive milestone {milestone.event} requires one complete archive"
            )
        return
    if not milestone_tasks_complete(packet, milestone):
        raise GateError(
            f"pre-close milestone {milestone.event} has incomplete defining tasks"
        )


def require_matching_registry(milestone: Milestone) -> None:
    """Require `change#automation` to name the milestone owner."""

    expected = f"{milestone.owner}#automation"
    if milestone.gate_registry != expected:
        raise GateError(
            f"milestone {milestone.event} references unsupported registry "
            f"{milestone.gate_registry!r}; expected {expected!r}"
        )


def execute_child_registry(
    packet: ChildPacket,
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Validate one child and execute every preserved automation command."""

    if packet.state == "archived":
        validate_archived_packet(packet, candidate_root, environment)
    else:
        validate_active_packet(
            packet,
            candidate_root,
            environment,
            executed,
            results,
        )
    execute_commands(
        packet,
        packet.automation,
        candidate_root,
        environment,
        executed,
        results,
    )


def execute_commands(
    packet: ChildPacket,
    commands: Sequence[str],
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Execute a child registry, substituting archived active-ID validation."""

    for command in commands:
        if packet.state == "archived" and is_stale_active_validation(
            command,
            packet.change,
        ):
            results.append(
                {
                    "owner": packet.change,
                    "command": command,
                    "status": "substituted-isolated-archive-validation",
                }
            )
            continue
        execute_registered_command(
            packet.change,
            command,
            candidate_root,
            environment,
            executed,
            results,
        )


def execute_registered_command(
    owner: str,
    command: str,
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Run one registry command once for an owner."""

    arguments = normalized_command(command, candidate_root)
    execute_command_arguments(
        owner,
        command,
        arguments,
        candidate_root,
        environment,
        executed,
        results,
    )


def execute_command_arguments(
    owner: str,
    command: str,
    arguments: Sequence[str],
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Run parsed command arguments once and retain owned failure evidence."""

    key = (owner.split("#", 1)[0], command)
    if key in executed:
        results.append(
            {"owner": owner, "command": command, "status": "already-passed"}
        )
        return
    try:
        run_checked(arguments, cwd=candidate_root, environment=environment)
    except GateError as error:
        results.append(
            {
                "owner": owner,
                "command": command,
                "status": "failed",
                "error": str(error),
            }
        )
        raise
    executed.add(key)
    results.append({"owner": owner, "command": command, "status": "passed"})


def normalized_command(command: str, candidate_root: Path) -> list[str]:
    """Parse one non-shell command and bind worktree candidates explicitly."""

    if "\n" in command or "\r" in command:
        raise GateError(f"automation command contains a newline: {command!r}")
    try:
        arguments = shlex.split(command)
    except ValueError as error:
        raise GateError(f"invalid automation command {command!r}: {error}") from error
    if not arguments or any(token in FORBIDDEN_COMMAND_TOKENS for token in arguments):
        raise GateError(f"automation command requires unsupported shell syntax: {command}")
    return replace_worktree_candidate(arguments, candidate_root)


def replace_worktree_candidate(
    arguments: Sequence[str],
    candidate_root: Path,
) -> list[str]:
    """Replace only explicit `--candidate worktree` registry selections."""

    replaced = list(arguments)
    for index, argument in enumerate(replaced):
        if argument == "--candidate" and index + 1 < len(replaced):
            if replaced[index + 1] == "worktree":
                replaced[index + 1] = str(candidate_root)
        elif argument == "--candidate=worktree":
            replaced[index] = f"--candidate={candidate_root}"
    return replaced


def is_stale_active_validation(command: str, change: str) -> bool:
    """Return whether an archived registry asks OpenSpec for an active ID."""

    arguments = normalized_command(command, Path("/candidate"))
    try:
        index = arguments.index("openspec")
    except ValueError:
        return False
    return arguments[index:index + 3] == ["openspec", "validate", change]


def validate_active_packet(
    packet: ChildPacket,
    candidate_root: Path,
    environment: Mapping[str, str],
    executed: set[tuple[str, str]],
    results: list[dict[str, str]],
) -> None:
    """Strictly validate an active child independently of its registry."""

    command = f"openspec validate {packet.change} --type change --strict"
    execute_command_arguments(
        packet.change,
        command,
        [
            "openspec",
            "validate",
            packet.change,
            "--type",
            "change",
            "--strict",
        ],
        candidate_root,
        environment,
        executed,
        results,
    )


def validate_archived_packet(
    packet: ChildPacket,
    candidate_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Validate archived artifacts through an isolated active change root."""

    with tempfile.TemporaryDirectory(prefix="ladon-archived-change-") as temporary:
        project = Path(temporary)
        openspec_root = project / "openspec"
        (openspec_root / "changes").mkdir(parents=True)
        shutil.copytree(
            packet.path,
            openspec_root / "changes" / packet.change,
        )
        copy_optional(candidate_root / "openspec" / "specs", openspec_root / "specs")
        copy_optional_file(
            candidate_root / "openspec" / "config.yaml",
            openspec_root / "config.yaml",
        )
        run_checked(
            [
                "openspec",
                "validate",
                packet.change,
                "--type",
                "change",
                "--strict",
            ],
            cwd=project,
            environment=environment,
        )


def copy_optional(source: Path, destination: Path) -> None:
    """Copy an optional directory into an isolated validation project."""

    if source.is_dir():
        shutil.copytree(source, destination)


def copy_optional_file(source: Path, destination: Path) -> None:
    """Copy an optional file into an isolated validation project."""

    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def readiness_summary(
    plan: ReadinessPlan,
    candidate_root: Path,
    blockers: Mapping[str, list[str]],
    results: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Return a machine-readable final readiness ledger."""

    return {
        "artifactKind": "ladon_alpha_readiness",
        "program": plan.ledger.get("program"),
        "candidate": str(candidate_root),
        "ready": not blockers,
        "authorityClasses": plan.ledger.get("authorityClasses", []),
        "publication": plan.ledger.get("publication", {}),
        "children": [
            {
                "change": change,
                "state": packet.state,
                "complete": packet.complete,
                "blockers": blockers.get(change, []),
            }
            for change, packet in sorted(plan.packets.items())
        ],
        "eventOrder": list(plan.event_order),
        "commands": [dict(row) for row in results],
    }
