"""Caller-independent execution rules for Ladon's public command line.

This module owns syntax and process-policy decisions.  It does not inspect
Lean source or render reports, which keeps the ordinary CLI usable by people,
scripts, and models through exactly the same contract.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ladon.report_model import ReportV2


EXIT_SUCCESS = 0
EXIT_OPERATIONAL = 1
EXIT_INVOCATION = 2
EXIT_POLICY = 3
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


class InvocationError(ValueError):
    """Invalid CLI syntax or configuration detected before analysis."""


@dataclass(frozen=True)
class OutputTarget:
    """One selected report representation and its destination."""

    format: str
    destination: str


@dataclass(frozen=True)
class OutputPlan:
    """Validated report outputs for one invocation."""

    targets: tuple[OutputTarget, ...]
    report_version: str
    projection: str = "review"
    legacy: bool = False

    @property
    def uses_stdout(self) -> bool:
        """Whether this plan sends its sole representation to stdout."""

        return any(target.destination == "-" for target in self.targets)


@dataclass(frozen=True)
class FailureSelector:
    """One exact, repeatable finding-policy selector."""

    raw: str
    category: str
    value: str
    phase_status: str | None = None


def output_plan(args: Any) -> OutputPlan:
    """Resolve canonical or one-release legacy report-output flags."""

    legacy_json = getattr(args, "legacy_json", None)
    legacy_text = getattr(args, "legacy_text", None)
    emit_values = tuple(getattr(args, "emit", ()) or ())
    output_format = getattr(args, "output_format", None)
    destination = getattr(args, "output", None)
    requested_report_version = getattr(args, "report_version", None)
    report_version = requested_report_version or (
        "v2" if legacy_json or legacy_text else "v3"
    )
    projection = getattr(args, "projection", "review")
    if legacy_json or legacy_text:
        return legacy_output_plan(
            legacy_json=legacy_json,
            legacy_text=legacy_text,
            emit_values=emit_values,
            output_format=output_format,
            destination=destination,
            report_version=report_version,
            projection=projection,
        )
    if emit_values:
        return emit_output_plan(
            emit_values,
            report_version,
            projection=projection,
            output_format=output_format,
            destination=destination,
        )
    return single_output_plan(
        output_format,
        destination,
        report_version,
        projection=projection,
    )


def legacy_output_plan(
    *,
    legacy_json: str | None,
    legacy_text: str | None,
    emit_values: Sequence[str],
    output_format: str | None,
    destination: str | None,
    report_version: str,
    projection: str,
) -> OutputPlan:
    """Validate and build the bounded compatibility output plan."""

    if emit_values or output_format is not None or destination is not None:
        raise InvocationError(
            "legacy --json/--text options cannot be mixed with --emit, "
            "--format, or --output"
        )
    targets = legacy_targets(legacy_json, legacy_text)
    validate_report_version(
        report_version,
        targets,
        legacy=True,
        projection=projection,
    )
    return OutputPlan(
        targets,
        report_version,
        projection=projection,
        legacy=True,
    )


def emit_output_plan(
    emit_values: Sequence[str],
    report_version: str,
    *,
    projection: str,
    output_format: str | None,
    destination: str | None,
) -> OutputPlan:
    """Validate canonical multi-output syntax before analysis."""

    if output_format is not None or destination is not None:
        raise InvocationError("--emit cannot be mixed with --format or --output")
    targets = canonical_emit_targets(emit_values)
    validate_report_version(
        report_version,
        targets,
        legacy=False,
        projection=projection,
    )
    return OutputPlan(targets, report_version, projection=projection)


def single_output_plan(
    output_format: str | None,
    destination: str | None,
    report_version: str,
    *,
    projection: str,
) -> OutputPlan:
    """Build the canonical one-representation compatibility plan."""

    targets = (OutputTarget(output_format or "text", destination or "-"),)
    validate_report_version(
        report_version,
        targets,
        legacy=False,
        projection=projection,
    )
    return OutputPlan(targets, report_version, projection=projection)


def canonical_emit_targets(values: Sequence[str]) -> tuple[OutputTarget, ...]:
    """Parse and validate repeatable canonical ``FORMAT=PATH`` destinations."""

    targets = tuple(parse_emit_target(value) for value in values)
    formats = [target.format for target in targets]
    destinations = [
        normalized_destination(target.destination) for target in targets
    ]
    if len(set(formats)) != len(formats):
        raise InvocationError("--emit formats must be unique")
    if sum(target.destination == "-" for target in targets) > 1:
        raise InvocationError("--emit permits at most one stdout destination")
    if len(set(destinations)) != len(destinations):
        raise InvocationError("--emit destinations must be unique")
    return targets


def parse_emit_target(value: str) -> OutputTarget:
    """Parse one canonical output target without accepting implicit defaults."""

    selected_format, separator, destination = value.partition("=")
    if separator != "=" or selected_format not in {"json", "text"}:
        raise InvocationError(
            "--emit expects FORMAT=PATH with FORMAT equal to json or text"
        )
    if not destination:
        raise InvocationError("--emit destination must be non-empty")
    return OutputTarget(selected_format, destination)


def normalized_destination(destination: str) -> str:
    """Resolve existing parent aliases without requiring the output leaf."""

    if destination == "-":
        return destination
    try:
        return os.path.normcase(str(Path(destination).resolve(strict=False)))
    except (OSError, RuntimeError) as exc:
        raise InvocationError(
            f"--emit destination cannot be resolved safely: {destination}"
        ) from exc


def legacy_targets(
    output_json: str | None,
    output_text: str | None,
) -> tuple[OutputTarget, ...]:
    """Normalize bounded legacy file flags without permitting mixed stdout."""

    targets = tuple(
        target
        for target in (
            OutputTarget("json", output_json) if output_json else None,
            OutputTarget("text", output_text) if output_text else None,
        )
        if target is not None
    )
    if any(target.destination == "-" for target in targets):
        raise InvocationError("legacy --json/--text destinations must be regular file paths")
    if (
        len(
            {
                normalized_destination(target.destination)
                for target in targets
            }
        )
        != len(targets)
    ):
        raise InvocationError("legacy JSON and text outputs must use distinct file paths")
    return targets


def validate_report_version(
    version: str,
    targets: Sequence[OutputTarget],
    *,
    legacy: bool,
    projection: str = "review",
) -> None:
    """Enforce the bounded JSON-only report-v1 compatibility surface."""

    if version not in {"v1", "v2", "v3"}:
        raise InvocationError(f"unsupported report version: {version}")
    if version != "v3" and projection != "review":
        raise InvocationError(
            "--projection is available only with report version v3"
        )
    if version == "v1" and (
        len(targets) != 1
        or targets[0].format != "json"
        or (legacy and len(targets) > 1)
    ):
        raise InvocationError(
            "report version v1 is available only for a sole JSON representation"
        )


def validate_output_destinations(plan: OutputPlan) -> None:
    """Reject directory or unwritable report destinations before analysis."""

    for target in plan.targets:
        if target.destination == "-":
            continue
        path = Path(target.destination)
        if path.exists() and not path.is_file():
            raise OSError(f"report destination is not a regular file: {path}")
        parent = existing_parent(path)
        if not os.access(parent, os.W_OK):
            raise OSError(f"report destination is not writable: {path}")


def existing_parent(path: Path) -> Path:
    """Return the nearest existing parent used for a writability preflight."""

    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not parent.is_dir():
        raise OSError(f"report destination parent is not a directory: {parent}")
    return parent


def write_output_plan(
    plan: OutputPlan,
    content_by_format: Mapping[str, str],
    *,
    stdout: TextIOBase | None = None,
) -> None:
    """Write every planned representation without mixing diagnostics."""

    stream = stdout or sys.stdout
    for target in plan.targets:
        content = content_by_format[target.format]
        if target.destination == "-":
            stream.write(content)
        else:
            write_output_file(Path(target.destination), content)


def write_output_file(path: Path, content: str) -> None:
    """Atomically replace one UTF-8 report destination."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def parse_failure_selectors(values: Iterable[str]) -> tuple[FailureSelector, ...]:
    """Parse the exact case-sensitive ``--fail-on`` grammar."""

    selectors = tuple(parse_failure_selector(value) for value in values)
    return selectors


def parse_failure_selector(value: str) -> FailureSelector:
    """Parse one kind, severity, or phase selector."""

    parts = value.split(":")
    selector = parse_two_part_selector(value, parts)
    if selector is None:
        selector = parse_phase_selector(value, parts)
    if selector is not None:
        return selector
    raise InvocationError(
        f"invalid --fail-on selector {value!r}; expected "
        "kind:<finding-kind>, severity:<info|warning|error>, or "
        "phase:<name>:<skipped|partial>"
    )


def parse_two_part_selector(
    value: str,
    parts: Sequence[str],
) -> FailureSelector | None:
    """Parse a kind or minimum-severity selector when valid."""

    if len(parts) != 2:
        return None
    category, selected = parts
    if category == "kind" and selected:
        return FailureSelector(value, category, selected)
    if category == "severity" and selected in SEVERITY_ORDER:
        return FailureSelector(value, category, selected)
    return None


def parse_phase_selector(
    value: str,
    parts: Sequence[str],
) -> FailureSelector | None:
    """Parse an optional-phase status selector when valid."""

    if len(parts) != 3:
        return None
    category, name, status = parts
    if category != "phase" or not name or status not in {"skipped", "partial"}:
        return None
    return FailureSelector(value, category, name, status)


def failure_policy(
    payload: Mapping[str, Any] | ReportV2,
    selectors: Sequence[FailureSelector],
) -> dict[str, Any]:
    """Return ordered selector metadata and deterministic matching rows."""

    if not selectors:
        return {"selectors": [], "matches": []}
    matches: list[dict[str, Any]] = []
    findings = sorted(finding_rows(payload), key=stable_row_key)
    phases = sorted(phase_rows(payload), key=stable_row_key)
    for selector in selectors:
        matches.extend(selector_matches(selector, findings, phases))
    return {
        "selectors": [selector.raw for selector in selectors],
        "matches": matches,
    }


def selector_matches(
    selector: FailureSelector,
    findings: Sequence[dict[str, Any]],
    phases: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return stable matches for one selector."""

    if selector.category == "phase":
        return [
            policy_match(selector, "phase", row)
            for row in phases
            if row.get("name") == selector.value
            and row.get("status") == selector.phase_status
        ]
    return [
        policy_match(selector, "finding", row)
        for row in findings
        if finding_matches(selector, row)
    ]


def finding_matches(selector: FailureSelector, row: Mapping[str, Any]) -> bool:
    """Whether one finding satisfies a kind or minimum-severity selector."""

    if selector.category == "kind":
        return row.get("kind") == selector.value
    severity = str(row.get("severity", "info"))
    return (
        severity in SEVERITY_ORDER
        and SEVERITY_ORDER[severity] >= SEVERITY_ORDER[selector.value]
    )


def policy_match(
    selector: FailureSelector,
    target_kind: str,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one compact, reproducible policy-match record."""

    return {
        "selector": selector.raw,
        "target_kind": target_kind,
        "stable_key": stable_row_key(row),
    }


def stable_row_key(row: Mapping[str, Any]) -> str:
    """Return a deterministic key for report-policy ordering."""

    return json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)


def finding_rows(
    payload: Mapping[str, Any] | ReportV2,
) -> list[dict[str, Any]]:
    """Extract normalized finding rows from report v2 or compatibility data."""

    if isinstance(payload, ReportV2):
        return [row.to_dict() for row in payload.findings]
    rows = payload.get("findings", [])
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def phase_rows(
    payload: Mapping[str, Any] | ReportV2,
) -> list[dict[str, Any]]:
    """Extract phase rows from canonical v2 or the prior timing envelope."""

    if isinstance(payload, ReportV2):
        return [phase.to_v2_dict() for phase in payload.phases.values()]
    rows = payload.get("phases", [])
    if isinstance(rows, list):
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    timings = payload.get("pipeline", {})
    if not isinstance(timings, Mapping):
        return []
    by_name = timings.get("timings", {})
    if not isinstance(by_name, Mapping):
        return []
    return [
        {"name": str(name), **dict(row)}
        for name, row in by_name.items()
        if isinstance(row, Mapping)
    ]


def has_required_phase_failure(
    payload: Mapping[str, Any] | ReportV2,
) -> bool:
    """Whether canonical phase data contains an incomplete required phase."""

    if isinstance(payload, ReportV2):
        return any(
            phase.required and phase.status in {"partial", "failed"}
            for phase in payload.phases.values()
        )
    return any(
        bool(row.get("required")) and row.get("status") in {"partial", "failed"}
        for row in phase_rows(payload)
    )
