"""Ordered, bounded builds for theorem capsule replay."""

from __future__ import annotations

import heapq
import math
import unicodedata
from collections.abc import Callable, Mapping
from time import monotonic
from typing import Any

_MAX_MODULES = 4096
_MAX_EDGES = 262144


def _module_name(value: Any) -> bool:
    """Return whether value is a safe dotted Lean module identity."""
    if not isinstance(value, str) or not value or len(value) > 1024:
        return False
    return all(_valid_component(component) for component in value.split("."))


def _valid_component(component: str) -> bool:
    if not component:
        return False
    return all(_valid_character(character, index) for index, character in enumerate(component))


def _valid_character(character: str, index: int) -> bool:
    category = unicodedata.category(character)[0]
    if character == "_" or category == "L":
        return True
    if character == "'":
        return index > 0
    return category == "N" and index > 0


def _graph_parts(plan: Any) -> tuple[Any, Any, Any]:
    try:
        graph = plan.payload["buildGraph"]
        return graph["modules"], graph["edges"], plan.target["module"]
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("capsule build graph is malformed") from exc


def _validated_modules(rows: Any, target: Any) -> list[str]:
    if not isinstance(rows, list) or len(rows) > _MAX_MODULES:
        raise ValueError("capsule build graph has an invalid module count")
    modules: list[str] = []
    for row in rows:
        name = row.get("module") if isinstance(row, Mapping) else None
        if not _module_name(name):
            raise ValueError("capsule build graph contains an invalid module identity")
        modules.append(name)
    if len(set(modules)) != len(modules):
        raise ValueError("capsule build graph contains duplicate modules")
    if not _module_name(target) or target not in set(modules):
        raise ValueError("capsule target module is absent from the build graph")
    return modules


def _validate_edge_rows(rows: Any) -> None:
    if not isinstance(rows, list):
        raise ValueError("capsule build graph edges are malformed")  # noqa: TRY004
    if len(rows) > _MAX_EDGES:
        raise ValueError("capsule build graph has an invalid edge count")


def _dependency_maps(modules: list[str], rows: Any) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    _validate_edge_rows(rows)
    module_set = set(modules)
    dependencies = {name: set() for name in modules}
    dependents = {name: set() for name in modules}
    for edge in rows:
        if not isinstance(edge, Mapping):
            raise ValueError("capsule build graph contains a malformed edge")  # noqa: TRY004
        source, dependency = edge.get("source"), edge.get("target")
        if (not _module_name(source) or not _module_name(dependency)
                or source not in module_set or dependency not in module_set):
            raise ValueError("capsule build graph edge has an unknown endpoint")
        dependencies[source].add(dependency)
        dependents[dependency].add(source)
    return dependencies, dependents


def _topological_order(
    modules: list[str], dependencies: dict[str, set[str]], dependents: dict[str, set[str]]
) -> list[str]:
    ready = [name for name in modules if not dependencies[name]]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        name = heapq.heappop(ready)
        ordered.append(name)
        for dependent in sorted(dependents[name]):
            dependencies[dependent].remove(name)
            if not dependencies[dependent]:
                heapq.heappush(ready, dependent)
    if len(ordered) != len(modules):
        raise ValueError("capsule build graph contains a dependency cycle")
    return ordered


def ordered_modules(plan: Any) -> list[str]:
    """Validate the capsule module graph and return dependencies before users."""
    module_rows, edge_rows, target = _graph_parts(plan)
    modules = _validated_modules(module_rows, target)
    dependencies, dependents = _dependency_maps(modules, edge_rows)
    return _topological_order(modules, dependencies, dependents)


def run_ordered_build(
    plan: Any,
    replay_root: Any,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    environment: Mapping[str, str],
    run_stage: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Build each capsule module's deps and Lean artifacts under one deadline."""
    modules = ordered_modules(plan)
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("ordered build timeout must be finite and greater than zero")
    return _execute_steps(
        modules, replay_root, timeout_seconds, max_rss_bytes, environment, run_stage
    )


def _commands(module: str) -> tuple[tuple[str, list[str]], ...]:
    return (
        ("deps", ["lake", "--no-build", "build", f"+{module}:deps"]),
        ("leanArts", ["lake", "build", f"+{module}:leanArts"]),
    )


def _timeout_step(module: str, role: str, command: list[str]) -> dict[str, Any]:
    return {
        "module": module,
        "role": role,
        "command": command,
        "returncode": None,
        "timedOut": True,
        "outputLimited": False,
        "memoryLimited": False,
        "peakRssBytes": None,
        "timeoutBeforeLaunch": True,
        "diagnostic": "ordered build deadline expired before process launch",
    }


def _record_step(
    module: str, role: str, outcome: dict[str, Any], steps: list[dict[str, Any]],
    peaks: list[int], observations: list[dict[str, Any]],
) -> None:
    child_row = dict(outcome.get("row") or {})
    child_row.update(module=module, role=role)
    steps.append(child_row)
    peak = child_row.get("peakRssBytes")
    if peak is None and outcome.get("result") is not None:
        peak = getattr(outcome["result"], "peak_rss_bytes", None)
    if isinstance(peak, int) and not isinstance(peak, bool) and peak >= 0:
        peaks.append(peak)
    resource = child_row.get("resourceObservations")
    if isinstance(resource, dict):
        observations.append(resource)
    else:
        observations.append({"version": 1, "status": "unavailable"})


def _aggregate_observations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ("maxLeanProcesses", "largestLeanRssBytes", "maxDescendantProcesses")
    available = _available_observations(rows)
    partial = _observations_partial(rows, available)
    summary: dict[str, Any] = {
        "version": 1,
        "status": "unavailable" if not available else "partial" if partial else "sampled",
        "leanMeasurement": "unavailable" if not available else "partial" if partial else "sampled",
    }
    summary.update({field: _max_observed_value(field, available) for field in fields})
    return summary


def _available_observations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("status") != "unavailable"]


def _observations_partial(
    rows: list[dict[str, Any]], available: list[dict[str, Any]]
) -> bool:
    return len(available) != len(rows) or any(
        row.get("status") == "partial" or row.get("leanMeasurement") == "partial"
        for row in available
    )


def _max_observed_value(field: str, rows: list[dict[str, Any]]) -> int | None:
    values = [
        row[field] for row in rows
        if isinstance(row.get(field), int) and not isinstance(row[field], bool)
    ]
    return max(values, default=None)


def _build_row(
    timeout_seconds: float, steps: list[dict[str, Any]], peaks: list[int],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "stage": "lean_build",
        "buildTimeoutSeconds": timeout_seconds,
        "steps": steps,
        "peakRssBytes": max(peaks, default=None),
        "timedOut": any(step.get("timedOut", False) for step in steps),
        "memoryLimited": any(step.get("memoryLimited", False) for step in steps),
        "outputLimited": any(step.get("outputLimited", False) for step in steps),
        "resourceObservations": _aggregate_observations(observations),
    }
    for step in reversed(steps):
        if step.get("diagnostic"):
            row["diagnostic"] = step["diagnostic"]
            break
    return row


def _execute_steps(
    modules: list[str], replay_root: Any, timeout_seconds: float,
    max_rss_bytes: int | None, environment: Mapping[str, str],
    run_stage: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    deadline = monotonic() + timeout_seconds
    steps: list[dict[str, Any]] = []
    peaks: list[int] = []
    observations: list[dict[str, Any]] = []
    last_result: Any = None
    final_status: str | None = None
    for module in modules:
        for role, command in _commands(module):
            remaining = deadline - monotonic()
            if remaining <= 0:
                final_status = "resource-limit"
                steps.append(_timeout_step(module, role, command))
                return _build_result(final_status, last_result, timeout_seconds,
                                     steps, peaks, observations)
            outcome = run_stage(
                command,
                replay_root,
                remaining,
                max_rss_bytes,
                environment,
                stage="lean_build",
                display_command=tuple(command),
            )
            last_result = outcome.get("result")
            _record_step(module, role, outcome, steps, peaks, observations)
            status = outcome.get("status")
            if status is not None:
                final_status = _failure_status(role, status, steps[-1])
                return _build_result(final_status, last_result, timeout_seconds,
                                     steps, peaks, observations)
    return _build_result(final_status, last_result, timeout_seconds,
                         steps, peaks, observations)


def _build_result(
    status: str | None, result: Any, timeout_seconds: float,
    steps: list[dict[str, Any]], peaks: list[int], observations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": status,
        "result": result,
        "row": _build_row(timeout_seconds, steps, peaks, observations),
    }


def _failure_status(role: str, status: str, step: dict[str, Any]) -> str:
    if status == "resource-limit" or role != "deps":
        return status
    step["originalStatus"] = status
    step["diagnostic"] = (
        "Ordered build dependency preflight failed: required imported artifacts "
        "or Lake facets are unavailable. No unrestricted compilation fallback was run."
    )
    return "unsupported-facet"
