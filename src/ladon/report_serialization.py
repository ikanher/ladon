"""Deterministic v2 and bounded v1 report serialization."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from typing import Any

from ladon.report_adapters import coerce_report_v2
from ladon.report_contract import (
    REPORT_VERSION,
    SECTION_PHASES,
    V1_REPORT_VERSION,
    ReportModelError,
    UnsupportedReportVersionError,
    copy_json,
)
from ladon.report_model import ReportV2


@dataclass(frozen=True)
class SerializationResult:
    """Serialized compatibility payload and caller-visible warnings."""

    payload: dict[str, Any]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SerializedReportBytes:
    """Deterministic JSON bytes and caller-visible compatibility warnings."""

    content: bytes
    warnings: tuple[str, ...] = ()


def serialize_report(
    report: Mapping[str, Any] | ReportV2,
    *,
    version: str = "v2",
) -> SerializationResult:
    """Serialize canonical data as v2 or through the v1 JSON adapter."""

    canonical = coerce_report_v2(report)
    if version in {"v2", REPORT_VERSION}:
        warning = (
            "report v2 compatibility output omits terminal phase dispositions; "
            "use report v3 to preserve acceptance and rejection reasons"
        )
        return SerializationResult(
            _v2_compatibility_payload(canonical),
            (warning,),
        )
    if version in {"v1", V1_REPORT_VERSION}:
        return serialize_v1_json(canonical)
    raise UnsupportedReportVersionError(
        f"report serializer received {version!r}; supported versions are v2 and v1"
    )


def serialize_report_bytes(
    report: Mapping[str, Any] | ReportV2,
    *,
    version: str = "v2",
) -> SerializedReportBytes:
    """Serialize an existing canonical payload without rerunning analysis."""

    result = serialize_report(report, version=version)
    content = (
        json.dumps(result.payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return SerializedReportBytes(content=content, warnings=result.warnings)


def serialize_v1_json(report: Mapping[str, Any] | ReportV2) -> SerializationResult:
    """Project canonical v2 data into bounded JSON-only `clean-core-1`."""

    canonical = coerce_report_v2(report)
    payload = canonical.to_dict()
    v1 = _v1_base_payload(payload)
    _attach_v1_sections(v1, canonical)
    v1["pipeline"] = {
        "timings": {
            name: _v1_timing(phase)
            for name, phase in sorted(canonical.phases.items())
            if name != "build"
        }
    }
    warning = (
        "clean-core-1 compatibility output loses explicit phase states, "
        "structured diagnostics, extension envelopes, finding identifiers, "
        "authority, provenance, and failure-policy metadata"
    )
    return SerializationResult(v1, (warning,))


def canonical_json_bytes(
    report: Mapping[str, Any] | ReportV2,
    *,
    normalize_timings: bool = False,
) -> bytes:
    """Return deterministic UTF-8 JSON bytes for the v2 compatibility form."""

    payload = _v2_compatibility_payload(coerce_report_v2(report))
    if normalize_timings:
        payload = normalized_report_payload(payload)
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def normalized_report_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize only documented volatile timing fields."""

    normalized = copy_json(dict(payload))
    _zero_elapsed_seconds(normalized.get("phases", {}))
    pipeline = normalized.get("pipeline", {})
    if isinstance(pipeline, dict):
        _zero_elapsed_seconds(pipeline.get("timings", {}))
    _zero_named_runtime_fields(normalized)
    return normalized


def load_report_schema() -> dict[str, Any]:
    """Load the installed report schema through package resources."""

    schema = (
        resources.files("ladon")
        .joinpath("schemas", "ladon-report-v2.schema.json")
        .read_text(encoding="utf-8")
    )
    payload = json.loads(schema)
    if not isinstance(payload, dict):
        raise ReportModelError("packaged report schema must be a JSON object")
    return payload


def _v2_compatibility_payload(report: ReportV2) -> dict[str, Any]:
    """Project the enriched typed model into the unchanged v2 wire shape."""

    return report.to_dict()


def _v1_base_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build fields representable in every v1 compatibility report."""

    metadata = dict(payload["metadata"])
    metadata["report_version"] = V1_REPORT_VERSION
    if metadata.get("generated_at_utc") is None:
        metadata.pop("generated_at_utc", None)
    metadata.pop("failure_policy", None)
    return {
        "metadata": metadata,
        "warnings": list(payload["warnings"]),
        "module_dag": payload["module_dag"],
        "findings": [_v1_finding(row) for row in payload["findings"]],
    }


def _attach_v1_sections(v1: dict[str, Any], canonical: ReportV2) -> None:
    """Attach only sections whose phase data is representable in v1."""

    for section, phase_name in SECTION_PHASES.items():
        if section == "module_dag":
            continue
        phase = canonical.phases[phase_name]
        if phase.status in {"complete", "partial"} and phase.data is not None:
            v1[section] = copy_json(phase.data)


def _v1_finding(row: Mapping[str, Any]) -> dict[str, Any]:
    """Drop common fields that did not exist in fixed v1 fixtures."""

    return {
        key: copy_json(value)
        for key, value in row.items()
        if key not in {"id", "authority", "evidence_count"}
    }


def _v1_timing(phase) -> dict[str, Any]:
    """Return one old timing row from a canonical phase."""

    return {
        "name": phase.name,
        "status": {
            "complete": "ok",
            "skipped": "skipped",
            "partial": "ok",
            "failed": "error",
        }[phase.status],
        "elapsed_seconds": phase.elapsed_seconds,
        "counters": dict(sorted(phase.counters.items())),
    }


def _zero_elapsed_seconds(raw: Any) -> None:
    """Normalize elapsed time in a serialized phase mapping."""

    if not isinstance(raw, dict):
        return
    for phase in raw.values():
        if isinstance(phase, dict):
            phase["elapsed_seconds"] = 0.0


def _zero_named_runtime_fields(raw: Any) -> None:
    """Recursively normalize registered nested wall-time measurements."""

    if isinstance(raw, list):
        for value in raw:
            _zero_named_runtime_fields(value)
        return
    if not isinstance(raw, dict):
        return
    if "helperElapsedSeconds" in raw:
        raw["helperElapsedSeconds"] = 0.0
    for value in raw.values():
        _zero_named_runtime_fields(value)
