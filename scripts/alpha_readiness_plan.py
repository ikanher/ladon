"""Pure packet-resolution and dependency planning for alpha readiness."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from release_gate_types import GateError

UNCHECKED_TASK_RE = re.compile(r"^- \[ \] (\d+(?:\.\d+)*)\b", re.MULTILINE)
TASK_ROW_RE = re.compile(r"^- \[(?P<state>[ xX])\] (?P<id>\d+(?:\.\d+)*)\b", re.MULTILINE)
DEFINED_TASK_RE = re.compile(r"\btask(?:s)?\s+(\d+(?:\.\d+)*)\b")
DEFINED_TASK_RANGE_RE = re.compile(
    r"\btask(?:s)?\s+(\d+)\.(\d+)-(\d+)\.(\d+)\b"
)
ARCHIVE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<change>.+)$")


@dataclass(frozen=True)
class ChildPacket:
    """One uniquely resolved active or archived child packet."""

    change: str
    path: Path
    state: str
    automation: tuple[str, ...]
    incomplete_tasks: tuple[str, ...]

    @property
    def complete(self) -> bool:
        """Return whether every task row is checked."""

        return not self.incomplete_tasks


@dataclass(frozen=True)
class Milestone:
    """One phase-qualified event declared by a child."""

    owner: str
    name: str
    phase: str
    defined_by: str
    gates: tuple[str, ...]
    gate_registry: str | None

    @property
    def event(self) -> str:
        """Return the globally unique milestone event name."""

        return f"{self.owner}#{self.name}"


@dataclass(frozen=True)
class ReadinessPlan:
    """Resolved child packets and their expanded event order."""

    ledger: Mapping[str, Any]
    packets: Mapping[str, ChildPacket]
    milestones: Mapping[str, Milestone]
    event_order: tuple[str, ...]

    @property
    def child_order(self) -> tuple[str, ...]:
        """Return child close order derived from the expanded graph."""

        suffix = "@close"
        return tuple(
            event.removesuffix(suffix)
            for event in self.event_order
            if event.endswith(suffix)
        )


def load_ledger(path: Path) -> dict[str, Any]:
    """Load and minimally validate one dependency ledger."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"cannot read dependency ledger {path}: {error}") from error
    children = payload.get("children")
    if not isinstance(children, list) or not children:
        raise GateError("dependency ledger must contain a non-empty children list")
    changes = [child.get("change") for child in children if isinstance(child, dict)]
    if len(changes) != len(children) or any(not isinstance(item, str) for item in changes):
        raise GateError("every dependency-ledger child must have a string change ID")
    if len(set(changes)) != len(changes):
        raise GateError("dependency-ledger child IDs must be unique")
    return payload


def build_readiness_plan(
    candidate_root: Path,
    ledger: Mapping[str, Any],
) -> ReadinessPlan:
    """Resolve packets and expand milestone-qualified dependency edges."""

    child_rows = tuple(ledger["children"])
    packets = {
        str(row["change"]): resolve_child_packet(candidate_root, str(row["change"]))
        for row in child_rows
    }
    milestones = collect_milestones(child_rows)
    event_order = topological_event_order(child_rows, milestones)
    return ReadinessPlan(
        ledger=ledger,
        packets=packets,
        milestones=milestones,
        event_order=event_order,
    )


def resolve_child_packet(candidate_root: Path, change: str) -> ChildPacket:
    """Resolve exactly one active path or one dated archive for a child."""

    changes_root = candidate_root / "openspec" / "changes"
    active = changes_root / change
    active_paths = [active] if active.is_dir() else []
    archives = matching_archives(changes_root / "archive", change)
    candidates = [*active_paths, *archives]
    if not candidates:
        raise GateError(
            f"child {change!r} is absent from active and archived change state"
        )
    if len(candidates) != 1:
        rendered = ", ".join(str(path.relative_to(candidate_root)) for path in candidates)
        raise GateError(f"child {change!r} resolves ambiguously: {rendered}")
    path = candidates[0]
    state = "active" if path == active else "archived"
    tasks = required_text(path / "tasks.md", f"child {change} tasks")
    automation = load_automation(path / "automation.json", change)
    return ChildPacket(
        change=change,
        path=path,
        state=state,
        automation=automation,
        incomplete_tasks=tuple(UNCHECKED_TASK_RE.findall(tasks)),
    )


def matching_archives(archive_root: Path, change: str) -> list[Path]:
    """Return dated archive directories whose stable suffix is `change`."""

    if not archive_root.is_dir():
        return []
    return [
        path
        for path in sorted(archive_root.iterdir())
        if path.is_dir()
        and (match := ARCHIVE_DATE_RE.match(path.name)) is not None
        and match.group("change") == change
    ]


def load_automation(path: Path, change: str) -> tuple[str, ...]:
    """Return a non-empty string command registry for one child."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"cannot read automation for {change}: {error}") from error
    commands = payload.get("commands")
    if (
        not isinstance(commands, list)
        or not commands
        or any(not isinstance(command, str) or not command.strip() for command in commands)
    ):
        raise GateError(f"child {change!r} has an invalid automation registry")
    return tuple(commands)


def required_text(path: Path, label: str) -> str:
    """Read a required UTF-8 artifact with one deterministic error."""

    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise GateError(f"cannot read {label} at {path}: {error}") from error


def collect_milestones(
    children: Sequence[Mapping[str, Any]],
) -> dict[str, Milestone]:
    """Collect and validate uniquely named child milestone events."""

    milestones: dict[str, Milestone] = {}
    for child in children:
        owner = str(child["change"])
        for row in child.get("milestones", []):
            milestone = milestone_from_row(owner, row)
            if milestone.event in milestones:
                raise GateError(f"duplicate milestone event: {milestone.event}")
            milestones[milestone.event] = milestone
    return milestones


def milestone_from_row(owner: str, row: Mapping[str, Any]) -> Milestone:
    """Normalize one milestone ledger row."""

    name = row.get("name")
    phase = row.get("phase")
    if not isinstance(name, str) or not name:
        raise GateError(f"child {owner!r} has a milestone without a name")
    if phase not in {"pre-close", "post-archive"}:
        raise GateError(f"milestone {owner}#{name} has invalid phase {phase!r}")
    gates = row.get("gates", [])
    registry = row.get("gateRegistry")
    if registry is not None and not isinstance(registry, str):
        raise GateError(f"milestone {owner}#{name} has invalid gateRegistry")
    if not isinstance(gates, list) or any(not isinstance(gate, str) for gate in gates):
        raise GateError(f"milestone {owner}#{name} has invalid gates")
    return Milestone(
        owner=owner,
        name=name,
        phase=str(phase),
        defined_by=str(row.get("definedBy", "")),
        gates=tuple(gates),
        gate_registry=registry,
    )


def topological_event_order(
    children: Sequence[Mapping[str, Any]],
    milestones: Mapping[str, Milestone],
) -> tuple[str, ...]:
    """Expand child lifecycle/milestone edges and reject cycles."""

    child_ids = {str(row["change"]) for row in children}
    dependencies = base_event_dependencies(child_ids, milestones)
    for child in children:
        add_child_dependency_edges(child, dependencies, child_ids, milestones)
    return stable_topological_order(dependencies)


def base_event_dependencies(
    child_ids: set[str],
    milestones: Mapping[str, Milestone],
) -> dict[str, set[str]]:
    """Create lifecycle edges for child start/close and milestone phases."""

    dependencies = {
        event: set()
        for change in child_ids
        for event in (start_event(change), close_event(change))
    }
    for change in child_ids:
        dependencies[close_event(change)].add(start_event(change))
    for milestone in milestones.values():
        dependencies[milestone.event] = set()
        if milestone.phase == "pre-close":
            dependencies[milestone.event].add(start_event(milestone.owner))
            dependencies[close_event(milestone.owner)].add(milestone.event)
        else:
            dependencies[milestone.event].add(close_event(milestone.owner))
    return dependencies


def add_child_dependency_edges(
    child: Mapping[str, Any],
    dependencies: dict[str, set[str]],
    child_ids: set[str],
    milestones: Mapping[str, Milestone],
) -> None:
    """Attach start/integration/close dependency classes for one child."""

    change = str(child["change"])
    add_reference_edges(
        child.get("startAfter", []),
        destination=start_event(change),
        dependencies=dependencies,
        child_ids=child_ids,
        milestones=milestones,
    )
    for key in ("integrationDependsOn", "closeAfter"):
        add_reference_edges(
            child.get(key, []),
            destination=close_event(change),
            dependencies=dependencies,
            child_ids=child_ids,
            milestones=milestones,
        )
    for milestone in milestones.values():
        if milestone.owner != change:
            continue
        add_reference_edges(
            child.get("integrationDependsOn", []),
            destination=milestone.event,
            dependencies=dependencies,
            child_ids=child_ids,
            milestones=milestones,
        )
        if milestone.gate_registry:
            add_reference_edges(
                child.get("closeAfter", []),
                destination=milestone.event,
                dependencies=dependencies,
                child_ids=child_ids,
                milestones=milestones,
            )


def add_reference_edges(
    references: Any,
    *,
    destination: str,
    dependencies: dict[str, set[str]],
    child_ids: set[str],
    milestones: Mapping[str, Milestone],
) -> None:
    """Add validated reference events as prerequisites of `destination`."""

    if not isinstance(references, list) or any(
        not isinstance(reference, str) for reference in references
    ):
        raise GateError(f"invalid dependency references for {destination}")
    dependencies[destination].update(
        dependency_event(reference, child_ids, milestones)
        for reference in references
    )


def dependency_event(
    reference: str,
    child_ids: set[str],
    milestones: Mapping[str, Milestone],
) -> str:
    """Resolve a plain child or child#milestone dependency reference."""

    if "#" in reference:
        if reference not in milestones:
            raise GateError(f"dependency references unknown milestone {reference!r}")
        return reference
    if reference not in child_ids:
        raise GateError(f"dependency references unknown child {reference!r}")
    return close_event(reference)


def stable_topological_order(
    dependencies: Mapping[str, set[str]],
) -> tuple[str, ...]:
    """Return a stable topological order or report the cyclic event set."""

    remaining = {event: set(required) for event, required in dependencies.items()}
    order: list[str] = []
    while remaining:
        ready = sorted(event for event, required in remaining.items() if not required)
        if not ready:
            cycle = ", ".join(sorted(remaining))
            raise GateError(f"alpha dependency graph has an unresolvable cycle: {cycle}")
        for event in ready:
            order.append(event)
            remaining.pop(event)
        for required in remaining.values():
            required.difference_update(ready)
    return tuple(order)


def milestone_task_ids(milestone: Milestone) -> tuple[str, ...]:
    """Return explicit task IDs named by a milestone definition."""

    task_ids = list(DEFINED_TASK_RE.findall(milestone.defined_by))
    for major, start, end_major, end in DEFINED_TASK_RANGE_RE.findall(
        milestone.defined_by
    ):
        if major != end_major:
            raise GateError(
                f"milestone {milestone.event} uses a cross-section task range"
            )
        task_ids.extend(
            f"{major}.{index}"
            for index in range(int(start), int(end) + 1)
        )
    return tuple(dict.fromkeys(task_ids))


def milestone_tasks_complete(packet: ChildPacket, milestone: Milestone) -> bool:
    """Return whether every explicitly named milestone task is checked."""

    requested = milestone_task_ids(milestone)
    if not requested:
        return True
    tasks = required_text(packet.path / "tasks.md", f"child {packet.change} tasks")
    states = {
        match.group("id"): match.group("state").lower() == "x"
        for match in TASK_ROW_RE.finditer(tasks)
    }
    return all(states.get(task_id, False) for task_id in requested)


def start_event(change: str) -> str:
    """Return the child start event name."""

    return f"{change}@start"


def close_event(change: str) -> str:
    """Return the child close event name."""

    return f"{change}@close"
