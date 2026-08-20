"""Adapters between pipeline/legacy dictionaries and the report-v2 model."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Any

from ladon.coverage import CoverageRegistry, legacy_unknown_coverage
from ladon.report_contract import (
    EXTENSION_NAMES,
    PHASE_DATA_TYPES,
    PHASE_NAMES,
    REPORT_VERSION,
    SECTION_PHASES,
    V1_REPORT_VERSION,
    Diagnostic,
    ExtensionEnvelope,
    Finding,
    PhaseEnvelope,
    Provenance,
    ReportMetadata,
    ReportModelError,
    UnsupportedReportVersionError,
    copy_json,
    default_phase_disposition,
)
from ladon.report_model import ReportV2
from ladon.snapshot import AnalysisSnapshot, SnapshotDecision


def build_report_v2(
    *,
    metadata: ReportMetadata,
    phase_records: Mapping[str, Any],
    phase_data: Mapping[str, Any],
    findings: Iterable[Mapping[str, Any]],
    warnings: Iterable[str] = (),
    coverage: CoverageRegistry | None = None,
    snapshot: AnalysisSnapshot | None = None,
    snapshot_decision: SnapshotDecision | None = None,
    copy_phase_data: bool = True,
    required_phases: Iterable[str] = (),
) -> ReportV2:
    """Adapt pipeline-owned values into a typed canonical report."""

    typed_findings = tuple(Finding.from_mapping(row) for row in findings)
    required = frozenset(required_phases)
    data = dict(phase_data)
    data["findings"] = [row.to_dict() for row in typed_findings]
    phases = {
        name: _adapt_phase(
            name,
            phase_records.get(name),
            data.get(name),
            copy_data=copy_phase_data,
            required=name in required,
        )
        for name in PHASE_NAMES
    }
    diagnostics = tuple(
        diagnostic
        for phase in phases.values()
        for diagnostic in phase.diagnostics
        if diagnostic.identifier == "report.invalid_phase_payload"
    )
    return ReportV2(
        metadata=metadata,
        phases=phases,
        findings=typed_findings,
        diagnostics=diagnostics,
        warnings=tuple(str(warning) for warning in warnings),
        extensions=_extensions_from_phases(phases),
        coverage=coverage if coverage is not None else CoverageRegistry(),
        snapshot=snapshot,
        snapshot_decision=snapshot_decision,
    )


def coerce_report_v2(payload: Mapping[str, Any] | ReportV2) -> ReportV2:
    """Return a typed model from canonical v2 or bounded v1 input."""

    if isinstance(payload, ReportV2):
        return payload
    version = report_version(payload)
    if version == REPORT_VERSION:
        return _report_from_v2_mapping(payload)
    if version == V1_REPORT_VERSION:
        return _report_from_v1_mapping(payload)
    raise UnsupportedReportVersionError(
        unsupported_version_message("report model", version)
    )


def supported_report_view(
    payload: Mapping[str, Any],
    *,
    consumer: str,
) -> dict[str, Any]:
    """Validate report-version dispatch and return a reader-compatible view."""

    version = report_version(payload)
    if version == REPORT_VERSION:
        return coerce_report_v2(payload).to_dict()
    if version == V1_REPORT_VERSION:
        return copy_json(dict(payload))
    raise UnsupportedReportVersionError(unsupported_version_message(consumer, version))


def report_version(payload: Mapping[str, Any]) -> str:
    """Return a report major, treating unlabeled pre-v2 fixtures as v1."""

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, Mapping):
        return "missing"
    value = metadata.get("report_version")
    return V1_REPORT_VERSION if value in {None, ""} else str(value)


def replace_report_phase(
    payload: Mapping[str, Any] | ReportV2,
    phase: PhaseEnvelope,
) -> dict[str, Any] | ReportV2:
    """Replace one phase through the typed boundary."""

    report = coerce_report_v2(payload)
    phases = dict(report.phases)
    phases[phase.name] = phase
    extensions = dict(report.extensions)
    if phase.name in {"proof_xray", "packet_evidence"}:
        extensions[phase.name] = _extension_from_phase(phase.name, phase)
    elif phase.name == "declaration_graph":
        extensions["elaborated_declarations"] = _elaborated_extension(phase)
    updated = replace(report, phases=phases, extensions=extensions)
    return _preserve_report_representation(payload, updated)


def mark_report_phase_required(
    payload: Mapping[str, Any] | ReportV2,
    name: str,
    *,
    required: bool = True,
) -> dict[str, Any] | ReportV2:
    """Mark a selected phase required without changing its result state."""

    report = coerce_report_v2(payload)
    if name not in report.phases:
        raise ReportModelError(f"unregistered phase: {name}")
    updated = replace_report_phase(
        report,
        replace(
            report.phases[name],
            required=required,
            disposition=default_phase_disposition(
                report.phases[name].status,
                required,
            ),
        ),
    )
    if not isinstance(updated, ReportV2):
        raise TypeError("typed phase replacement returned a mapping")
    return _preserve_report_representation(payload, updated)


def update_report_metadata(
    payload: Mapping[str, Any] | ReportV2,
    *,
    failure_policy: Mapping[str, Any] | None,
) -> dict[str, Any] | ReportV2:
    """Update CLI-owned failure-policy metadata through the model."""

    report = coerce_report_v2(payload)
    metadata = replace(report.metadata, failure_policy=failure_policy)
    updated = replace(report, metadata=metadata)
    return _preserve_report_representation(payload, updated)


def _preserve_report_representation(
    original: Mapping[str, Any] | ReportV2,
    report: ReportV2,
) -> dict[str, Any] | ReportV2:
    """Return a typed model only when the caller supplied one."""

    return report if isinstance(original, ReportV2) else report.to_dict()


def _adapt_phase(
    name: str,
    timing: Any,
    data: Any,
    *,
    copy_data: bool,
    required: bool = False,
) -> PhaseEnvelope:
    """Adapt one timing/data pair and fail invalid data structurally."""

    values = _timing_values(timing)
    if required:
        values["required"] = True
    status = _normalized_status(values["status"], name, data)
    reason = _normalized_reason(status, values["reason"], name)
    invalid = _invalid_phase_payload(name, data)
    if invalid:
        return _failed_adapter_phase(name, values, invalid)
    if copy_data:
        adapted_data = copy_json(data)
    else:
        adapted_data = data
    return PhaseEnvelope(
        name=name,
        status=status,
        required=values["required"],
        disposition=values["disposition"],
        elapsed_seconds=values["elapsed_seconds"],
        counters=values["counters"],
        reason=reason,
        diagnostics=_phase_diagnostics(
            name,
            values["diagnostics"],
            data,
        ),
        provenance=_phase_provenance(name),
        data=adapted_data,
    )


def _timing_values(timing: Any) -> dict[str, Any]:
    """Return normalized scalar fields from a timing object or dictionary."""

    return {
        "status": _timing_value(timing, "status", None),
        "reason": _timing_value(timing, "reason", None),
        "required": bool(_timing_value(timing, "required", False)),
        "disposition": _timing_value(timing, "disposition", None),
        "elapsed_seconds": float(_timing_value(timing, "elapsed_seconds", 0.0) or 0.0),
        "counters": _integer_counters(_timing_value(timing, "counters", {}) or {}),
        "diagnostics": [
            dict(row)
            for row in _mapping_rows(_timing_value(timing, "diagnostics", []) or [])
        ],
    }


def _normalized_status(raw: Any, name: str, data: Any) -> str:
    """Map pipeline timing states into report-v2 states."""

    return str(
        {
            "ok": "complete",
            "error": "failed",
            None: _missing_phase_status(name, data),
        }.get(raw, raw)
    )


def _normalized_reason(status: str, raw: Any, name: str) -> str | None:
    """Ensure every non-complete state has textual rationale."""

    if raw is not None:
        return str(raw)
    if status == "skipped":
        return _missing_phase_reason(name)
    if status == "failed":
        return "phase raised an error"
    if status == "partial":
        return "phase produced partial data"
    return None


def _failed_adapter_phase(
    name: str,
    values: Mapping[str, Any],
    message: str,
) -> PhaseEnvelope:
    """Return a failed phase for invalid owner payload data."""

    diagnostic = Diagnostic(
        identifier="report.invalid_phase_payload",
        severity="error",
        message=message,
        phase=name,
        subject=name,
        data={"expected": PHASE_DATA_TYPES[name].__name__},
    )
    return PhaseEnvelope.failed(
        name,
        message,
        diagnostics=(diagnostic,),
        required=bool(values["required"]),
        elapsed_seconds=float(values["elapsed_seconds"]),
        counters=values["counters"],
        provenance=_phase_provenance(name),
    )


def _report_from_v2_mapping(payload: Mapping[str, Any]) -> ReportV2:
    """Parse a canonical mapping through all typed component constructors."""

    raw_phases = payload.get("phases", {})
    if not isinstance(raw_phases, Mapping):
        raise ReportModelError("v2 phases must be an object")
    raw_extensions = payload.get("extensions", {})
    return ReportV2(
        metadata=_metadata_from_mapping(payload.get("metadata", {})),
        phases={
            name: _phase_from_mapping(name, raw_phases.get(name))
            for name in PHASE_NAMES
        },
        findings=tuple(
            Finding.from_mapping(row)
            for row in _mapping_rows(payload.get("findings", []))
        ),
        diagnostics=tuple(
            _diagnostic_from_mapping(row)
            for row in _mapping_rows(payload.get("diagnostics", []))
        ),
        warnings=tuple(str(row) for row in _list_value(payload.get("warnings", []))),
        extensions={
            name: _extension_from_mapping(name, _mapping_get(raw_extensions, name))
            for name in EXTENSION_NAMES
        },
        coverage=_legacy_coverage_registry(payload),
    )


def _report_from_v1_mapping(payload: Mapping[str, Any]) -> ReportV2:
    """Adapt a bounded legacy report into the canonical model."""

    timings = payload.get("pipeline", {})
    if isinstance(timings, Mapping):
        timings = timings.get("timings", {})
    if not isinstance(timings, Mapping):
        timings = {}
    phase_data = {
        phase_name: payload.get(section)
        for section, phase_name in SECTION_PHASES.items()
    }
    return build_report_v2(
        metadata=_metadata_from_mapping(payload.get("metadata", {})),
        phase_records=timings,
        phase_data=phase_data,
        findings=_mapping_rows(payload.get("findings", [])),
        warnings=(str(row) for row in _list_value(payload.get("warnings", []))),
        coverage=_legacy_coverage_registry(payload),
    )


def _legacy_coverage_registry(
    payload: Mapping[str, Any],
) -> CoverageRegistry:
    """Represent absent v1/v2 collection coverage as explicitly unknown."""

    scope = _legacy_scope(payload)
    rows = (
        (
            "report.findings",
            "#/sections/findings",
            payload.get("findings"),
            "selected findings",
            "ladon_analysis",
        ),
        (
            "report.review_regions",
            "#/sections/review_regions",
            payload.get("review_regions"),
            "selected review regions",
            "ladon_report_adapter",
        ),
        (
            "report.packet_evidence",
            "#/sections/packet_evidence",
            payload.get("packet_evidence"),
            "selected packet evidence",
            "ladon_report_adapter",
        ),
        (
            "declaration_graph.declarations",
            "#/sections/declaration_graph/declarations",
            _nested_value(payload.get("declaration_graph"), "declarations"),
            "selected declarations",
            "legacy_report",
        ),
    )
    registry = CoverageRegistry()
    for identity, pointer, value, population, authority in rows:
        registry = registry.register(
            legacy_unknown_coverage(
                identity=identity,
                pointer=pointer,
                visible=_collection_size(value),
                population=population,
                scope=scope,
                authority=authority,
            )
        )
    return registry


def _legacy_scope(payload: Mapping[str, Any]) -> str:
    """Return the best bounded scope label available in a legacy report."""

    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        for key in (
            "analysis_root_module",
            "analysis_root",
            "report_anchor_module",
            "report_anchor",
            "repo_root",
        ):
            value = metadata.get(key)
            if value:
                return str(value)
    return "legacy-report-unknown-scope"


def _nested_value(raw: Any, key: str) -> Any:
    """Read one optional mapping member without inventing a collection."""

    return raw.get(key) if isinstance(raw, Mapping) else None


def _collection_size(raw: Any) -> int:
    """Count visible legacy members while leaving their total unknown."""

    return len(raw) if isinstance(raw, (list, Mapping)) else 0


def _metadata_from_mapping(raw: Any) -> ReportMetadata:
    """Parse metadata with conservative legacy defaults."""

    metadata = raw if isinstance(raw, Mapping) else {}
    failure_policy = metadata.get("failure_policy")
    return ReportMetadata(
        repo_root=str(metadata.get("repo_root", "")),
        analysis_root=str(metadata.get("analysis_root", "")),
        analysis_root_module=str(metadata.get("analysis_root_module", "")),
        inventory_root=str(metadata.get("inventory_root", "")),
        extraction_backend=str(metadata.get("extraction_backend", "unknown")),
        report_anchor=(
            str(metadata["report_anchor"])
            if metadata.get("report_anchor") is not None
            else None
        ),
        report_anchor_module=(
            str(metadata["report_anchor_module"])
            if metadata.get("report_anchor_module") is not None
            else None
        ),
        generated_at_utc=(
            str(metadata["generated_at_utc"])
            if metadata.get("generated_at_utc") is not None
            else None
        ),
        failure_policy=(
            dict(failure_policy) if isinstance(failure_policy, Mapping) else None
        ),
        tool_version=str(metadata.get("tool_version", "0.1.0")),
    )


def _phase_from_mapping(name: str, raw: Any) -> PhaseEnvelope:
    """Parse one serialized phase, defaulting absent legacy additions."""

    if not isinstance(raw, Mapping):
        return PhaseEnvelope.skipped(name, _missing_phase_reason(name))
    return PhaseEnvelope(
        name=name,
        status=str(raw.get("status", "skipped")),
        required=bool(raw.get("required", False)),
        disposition=(
            str(raw["disposition"]) if raw.get("disposition") is not None else None
        ),
        elapsed_seconds=float(raw.get("elapsed_seconds", 0.0)),
        counters=_integer_counters(raw.get("counters", {})),
        reason=str(raw["reason"]) if raw.get("reason") is not None else None,
        diagnostics=tuple(
            _diagnostic_from_mapping(row)
            for row in _mapping_rows(raw.get("diagnostics", []))
        ),
        provenance=tuple(
            _provenance_from_mapping(row)
            for row in _mapping_rows(raw.get("provenance", []))
        ),
        data=copy_json(raw.get("data")),
    )


def _extensions_from_phases(
    phases: Mapping[str, PhaseEnvelope],
) -> dict[str, ExtensionEnvelope]:
    """Build explicit present or absent registered extension envelopes."""

    return {
        name: (
            _extension_from_phase(name, phases[name])
            if name in {"proof_xray", "packet_evidence"}
            else _elaborated_extension(phases["declaration_graph"])
            if name == "elaborated_declarations"
            else _absent_extension(name)
        )
        for name in EXTENSION_NAMES
    }


def _extension_from_phase(name: str, phase: PhaseEnvelope) -> ExtensionEnvelope:
    """Adapt an owner phase into its generic extension envelope."""

    return ExtensionEnvelope(
        namespace=name,
        version="1",
        status=phase.status,
        authority="capability-owner",
        provenance=phase.provenance,
        reason=phase.reason,
        payload=phase.data,
    )


def _elaborated_extension(phase: PhaseEnvelope) -> ExtensionEnvelope:
    """Project typed declaration surfaces from the declaration-graph phase."""

    if not isinstance(phase.data, Mapping):
        return _absent_extension("elaborated_declarations")
    summary = phase.data.get("elaborated_surface")
    if not isinstance(summary, Mapping):
        return _absent_extension("elaborated_declarations")
    status = str(summary.get("status", "skipped"))
    if status not in {"complete", "partial", "skipped", "failed"}:
        status = "partial"
    reason = summary.get("reason")
    payload = {
        "summary": copy_json(dict(summary)),
        "declarations": copy_json(phase.data.get("declarations", [])),
        "edges": copy_json(phase.data.get("elaborated_edges", [])),
        "caps": {
            "binders": 32,
            "dependenciesPerKind": 64,
            "premises": 32,
            "statementBytes": 1024,
            "renderedTypeBytes": 4096,
        },
    }
    return ExtensionEnvelope(
        namespace="elaborated_declarations",
        version="1",
        status=status,
        authority="lean-environment-direct",
        provenance=(
            Provenance(
                authority="lean_environment",
                source="Lean environment constant information",
                backend="lean_elaborated_helper",
                version=_surface_helper_version(payload["declarations"]),
            ),
        ),
        reason=str(reason) if reason is not None else None,
        payload=payload,
    )


def _surface_helper_version(rows: Any) -> str | None:
    """Return one stable helper version represented in declaration rows."""

    versions = sorted(
        {
            str(surface["helperVersion"])
            for row in _mapping_rows(rows)
            for surface in [row.get("surface")]
            if isinstance(surface, Mapping) and surface.get("helperVersion")
        }
    )
    return versions[0] if len(versions) == 1 else None


def _extension_from_mapping(name: str, raw: Any) -> ExtensionEnvelope:
    """Parse one serialized extension envelope."""

    if not isinstance(raw, Mapping):
        return _absent_extension(name)
    return ExtensionEnvelope(
        namespace=name,
        version=str(raw.get("version", "1")),
        status=str(raw.get("status", "skipped")),
        authority=str(raw.get("authority", "capability-owner")),
        provenance=tuple(
            _provenance_from_mapping(row)
            for row in _mapping_rows(raw.get("provenance", []))
        ),
        reason=str(raw["reason"]) if raw.get("reason") is not None else None,
        payload=copy_json(raw.get("payload")),
    )


def _absent_extension(name: str) -> ExtensionEnvelope:
    """Return the explicit absent state for one extension namespace."""

    return ExtensionEnvelope(
        namespace=name,
        version="1",
        status="skipped",
        authority="capability-owner",
        reason=f"{name} extension was not supplied",
    )


def _phase_diagnostics(
    name: str,
    timing_rows: Any,
    data: Any,
) -> tuple[Diagnostic, ...]:
    """Merge phase-record and owner-data diagnostics without duplicates."""

    rows = list(_mapping_rows(timing_rows))
    if isinstance(data, Mapping):
        rows.extend(_mapping_rows(data.get("diagnostics", [])))
    diagnostics: list[Diagnostic] = []
    seen: set[tuple[str, str | None, str]] = set()
    for row in rows:
        diagnostic = _diagnostic_from_owner_mapping(name, row)
        key = (
            diagnostic.identifier,
            diagnostic.subject,
            diagnostic.message,
        )
        if key not in seen:
            seen.add(key)
            diagnostics.append(diagnostic)
    return tuple(diagnostics)


def _diagnostic_from_owner_mapping(
    phase: str,
    row: Mapping[str, Any],
) -> Diagnostic:
    """Adapt a concrete owner's diagnostic without changing authority."""

    identifier = str(
        row.get("id") or row.get("ruleId") or row.get("kind") or f"{phase}.diagnostic"
    )
    severity = str(row.get("severity") or row.get("level") or "warning")
    if severity not in {"info", "warning", "error"}:
        severity = "warning"
    return Diagnostic(
        identifier=identifier,
        severity=severity,
        message=str(row.get("message", "")),
        phase=phase,
        subject=str(row["subject"]) if row.get("subject") is not None else None,
        data=dict(row),
    )


def _diagnostic_from_mapping(row: Mapping[str, Any]) -> Diagnostic:
    """Parse one generic serialized diagnostic."""

    data = row.get("data", {})
    return Diagnostic(
        identifier=str(row.get("id", "report.diagnostic")),
        severity=str(row.get("severity", "warning")),
        message=str(row.get("message", "")),
        phase=str(row["phase"]) if row.get("phase") is not None else None,
        subject=str(row["subject"]) if row.get("subject") is not None else None,
        data=dict(data) if isinstance(data, Mapping) else {},
    )


def _provenance_from_mapping(row: Mapping[str, Any]) -> Provenance:
    """Parse one generic serialized provenance row."""

    return Provenance(
        authority=str(row.get("authority", "unknown")),
        source=str(row.get("source", "unknown")),
        backend=str(row["backend"]) if row.get("backend") is not None else None,
        version=str(row["version"]) if row.get("version") is not None else None,
    )


def _phase_provenance(name: str) -> tuple[Provenance, ...]:
    """Return report-owned boundary provenance for one phase."""

    return (Provenance("ladon-analysis", f"ladon.pipeline:{name}"),)


def _missing_phase_status(name: str, data: Any) -> str:
    """Choose an explicit state when old timing data is absent."""

    if data is not None or name == "rendering":
        return "complete"
    return "skipped"


def _missing_phase_reason(name: str) -> str:
    """Return a stable reason for a missing optional phase."""

    if name == "build":
        return "build phase was not requested"
    return f"{name} phase was not selected or did not produce data"


def _invalid_phase_payload(name: str, data: Any) -> str | None:
    """Return an adapter diagnostic for a wrong owner payload type."""

    expected = PHASE_DATA_TYPES.get(name)
    if data is None or expected is None or isinstance(data, expected):
        return None
    return (
        f"invalid {name} phase payload: expected {expected.__name__}, "
        f"received {type(data).__name__}"
    )


def _timing_value(timing: Any, key: str, default: Any) -> Any:
    """Read a timing field from a mapping or typed timing object."""

    if isinstance(timing, Mapping):
        return timing.get(key, default)
    return getattr(timing, key, default)


def _integer_counters(raw: Any) -> dict[str, int]:
    """Keep only schema-valid non-negative integer counters."""

    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key): int(value)
        for key, value in raw.items()
        if isinstance(value, int) and value >= 0
    }


def unsupported_version_message(consumer: str, version: str) -> str:
    """Return the shared actionable report-version diagnostic."""

    return (
        f"{consumer} cannot read Ladon report version {version!r}; "
        f"supported versions are {REPORT_VERSION!r} and {V1_REPORT_VERSION!r}"
    )


def _mapping_rows(raw: Any) -> list[Mapping[str, Any]]:
    """Return only object rows from a list-like owner value."""

    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, Mapping)]


def _list_value(raw: Any) -> list[Any]:
    """Return a list or the stable empty fallback."""

    return raw if isinstance(raw, list) else []


def _mapping_get(raw: Any, key: str) -> Any:
    """Read a key only when a serialized container is an object."""

    return raw.get(key) if isinstance(raw, Mapping) else None
