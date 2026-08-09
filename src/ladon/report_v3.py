"""Canonical single-owner projections for Ladon report v3.

The v3 adapter consumes an already-built :class:`ReportV2`. It never invokes
discovery, Lean, or another analysis phase. Large payloads live only in
``sections``; phase, timing, and extension records contain metadata and JSON
references to those canonical owners.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from ladon.report_adapters import coerce_report_v2
from ladon.report_contract import (
    EXTENSION_NAMES,
    PHASE_NAMES,
    Diagnostic,
    ExtensionEnvelope,
    PhaseEnvelope,
    ReportModelError,
    copy_json,
    sorted_diagnostics,
    sorted_provenance,
)
from ladon.report_declaration_compaction import (
    compact_declaration_collections,
)
from ladon.report_model import ReportV2
from ladon.report_projection import project_sections
from ladon.report_projection_coverage import (
    bind_analysis_fingerprint,
    coverage_linked_omissions,
    project_coverage,
    rebind_review_region_coverage,
    register_projection_strata,
    synchronize_review_region_coverage,
)


REPORT_V3_VERSION = "ladon-report-v3"
PROJECTION_NAMES = ("summary", "review", "full")
DEFAULT_SUMMARY_ITEM_LIMIT = 20
DEFAULT_REVIEW_ITEM_LIMIT = 100
_SERIALIZATION_CHUNK_BYTES = 64 * 1024
_ANALYSIS_FINGERPRINT_ALGORITHM = "ladon-report-v3-raw-sections-v1"
_VOLATILE_CACHE_PATHS = frozenset(
    {
        ("sections", "discover", "cache"),
        ("sections", "lean_extraction", "cache"),
        ("sections", "module_dag", "source_index", "cache"),
    }
)
_VOLATILE_CACHE_COUNTERS = frozenset(
    {
        "lean_cache_bypassed",
        "lean_cache_hits",
        "lean_cache_misses",
        "source_cache_hits",
        "source_cache_rebuilt",
    }
)
_VOLATILE_RUNTIME_PATHS = frozenset(
    {
        ("sections", "lean_extraction", "helperElapsedSeconds"),
        ("sections", "module_dag", "helperElapsedSeconds"),
        (
            "sections",
            "module_dag",
            "run_resources",
            "observed",
            "observedWallSeconds",
        ),
        (
            "sections",
            "module_dag",
            "run_resources",
            "observed",
            "peakRssBytes",
        ),
        (
            "sections",
            "module_dag",
            "run_resources",
            "crossed",
            "observed",
        ),
    }
)


class ReportV3SizeLimitError(ReportModelError):
    """Raised before output is committed when v3 bytes exceed a caller limit."""


@dataclass(frozen=True)
class ReportV3:
    """One materialized v3 projection of an existing canonical analysis."""

    projection: str
    analysis_fingerprint: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.projection not in PROJECTION_NAMES:
            raise ReportModelError(f"unsupported report projection: {self.projection}")
        if not self.analysis_fingerprint.startswith("sha256:"):
            raise ReportModelError("analysis fingerprint must use sha256")
        if not isinstance(self.payload, Mapping):
            raise ReportModelError("report-v3 payload must be a mapping")

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible projection."""

        return copy_json(dict(self.payload))


@dataclass(frozen=True)
class SerializedReportV3Bytes:
    """Deterministic v3 bytes plus projection identity."""

    content: bytes
    projection: str
    analysis_fingerprint: str


@dataclass(frozen=True)
class WrittenReportV3:
    """One atomically committed v3 file without retaining its bytes."""

    path: Path
    byte_count: int
    projection: str
    analysis_fingerprint: str


# Keep exact policy disposition in the typed boundary until v3 is materialized.
# A frozen v2 dictionary cannot recover strict or selector rejection state.
def build_report_v3(
    report: Mapping[str, Any] | ReportV2,
    *,
    projection: str = "review",
    summary_item_limit: int = DEFAULT_SUMMARY_ITEM_LIMIT,
    review_item_limit: int = DEFAULT_REVIEW_ITEM_LIMIT,
) -> ReportV3:
    """Project an existing v2 model without rerunning any analysis."""

    _validate_projection_options(
        projection,
        summary_item_limit=summary_item_limit,
        review_item_limit=review_item_limit,
    )
    _require_preserved_dispositions(report)
    canonical = coerce_report_v2(report)
    diagnostics, diagnostic_refs = _canonical_diagnostics(canonical)
    full_sections, raw_sections = _canonical_phase_sections(canonical)
    extension_rows = _extension_rows(canonical, full_sections, raw_sections)
    phase_rows = _phase_rows(canonical, diagnostic_refs, full_sections)
    canonical_coverage = canonical.coverage.to_dict()
    snapshot = _snapshot_identity(canonical)
    fingerprint = _analysis_fingerprint(
        canonical,
        diagnostics=diagnostics,
        phases=phase_rows,
        extensions=extension_rows,
        sections=full_sections,
        coverage=canonical_coverage,
        snapshot=snapshot,
    )
    projected_sections, omissions, item_limit, strata = project_sections(
        full_sections,
        projection=projection,
        summary_item_limit=summary_item_limit,
        review_item_limit=review_item_limit,
    )
    sections = compact_declaration_collections(
        projected_sections,
        pointer="#/sections",
    )
    bound_coverage = rebind_review_region_coverage(
        bind_analysis_fingerprint(canonical.coverage, fingerprint),
        sections,
    )
    coverage = project_coverage(
        bound_coverage,
        sections=sections,
        projection=projection,
        item_limit=item_limit,
    )
    coverage = register_projection_strata(
        coverage,
        strata,
        projection=projection,
        item_limit=item_limit,
    )
    sections = synchronize_review_region_coverage(sections, coverage)
    omissions = coverage_linked_omissions(omissions, coverage)
    payload = {
        "metadata": _v3_metadata(canonical),
        "projection": {
            "id": f"{REPORT_V3_VERSION}:{projection}",
            "name": projection,
            "analysis_fingerprint": fingerprint,
            "included_sections": sorted(sections),
            "omissions": omissions,
            "limits": _projection_limits(projection, item_limit),
            "ownerProjection": _owner_projection(full_sections, sections, projection, item_limit),
        },
        "warnings": list(canonical.warnings),
        "diagnostics": diagnostics,
        "coverage": coverage.to_dict(),
        "snapshot": snapshot,
        "phases": phase_rows,
        "extensions": extension_rows,
        "pipeline": {"timings": _timing_rows(canonical, full_sections)},
        "sections": sections,
    }
    return ReportV3(
        projection=projection,
        analysis_fingerprint=fingerprint,
        payload=payload,
    )


def _projection_limits(
    projection: str,
    item_limit: int | None,
) -> dict[str, Any]:
    """Describe global and stratum-aware projection bounds truthfully."""

    if projection == "full":
        return {
            "max_collection_items": None,
            "max_unstratified_collection_items": None,
            "max_items_per_present_stratum": None,
            "selection_policy": "unbounded",
        }
    return {
        "max_collection_items": None,
        "max_unstratified_collection_items": item_limit,
        "max_items_per_present_stratum": item_limit,
        "selection_policy": "per_present_stratum",
    }


def _owner_projection(
    canonical: Mapping[str, Any], projected: Mapping[str, Any], projection: str, item_limit: int | None
) -> dict[str, Any]:
    """Describe owner-first versus global populations without hiding omissions."""
    selected = sum(len(value) for value in projected.values() if isinstance(value, list))
    global_count = sum(len(value) for value in canonical.values() if isinstance(value, list))
    suppressed = max(0, global_count - selected)
    return {
        "policy": "owner-first-v1",
        "selectedPopulation": selected,
        "globalPopulation": global_count,
        "globalSuppressed": suppressed > 0 and projection != "full",
        "suppressedCount": suppressed if projection != "full" else 0,
        "globalSample": "opt-in-via-full-projection" if projection != "full" else "included",
        "cap": item_limit,
        "widening": "use --projection full or increase review/summary limits" if suppressed else None,
    }


def _require_preserved_dispositions(
    report: Mapping[str, Any] | ReportV2,
) -> None:
    """Reject lossy wire-to-v3 promotion that would invent policy state."""

    if isinstance(report, ReportV2):
        return
    phases = report.get("phases", {})
    if not isinstance(phases, Mapping):
        raise ReportModelError("report v3 projection requires typed phase dispositions")
    missing = [
        name
        for name in PHASE_NAMES
        if not isinstance(phases.get(name), Mapping)
        or phases[name].get("disposition") is None
    ]
    if missing:
        raise ReportModelError(
            "report v3 cannot preserve terminal phase dispositions from a "
            "frozen v2 mapping; supply a typed ReportV2 model"
        )


def serialize_report_v3_bytes(
    report: Mapping[str, Any] | ReportV2 | ReportV3,
    *,
    projection: str | None = None,
    summary_item_limit: int = DEFAULT_SUMMARY_ITEM_LIMIT,
    review_item_limit: int = DEFAULT_REVIEW_ITEM_LIMIT,
    max_bytes: int | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> SerializedReportV3Bytes:
    """Return deterministic JSON bytes, enforcing a finite limit when supplied."""

    projected = _coerce_report_v3(
        report,
        projection=projection,
        summary_item_limit=summary_item_limit,
        review_item_limit=review_item_limit,
    )
    content_buffer = bytearray()
    for chunk in _iter_buffered_json_bytes(projected.payload):
        _enforce_byte_limit(len(content_buffer) + len(chunk), max_bytes)
        content_buffer.extend(chunk)
        if progress_callback is not None:
            progress_callback(len(content_buffer))
    content = bytes(content_buffer)
    return SerializedReportV3Bytes(
        content=content,
        projection=projected.projection,
        analysis_fingerprint=projected.analysis_fingerprint,
    )


def write_report_v3_file(
    report: Mapping[str, Any] | ReportV2 | ReportV3,
    path: str | Path,
    *,
    projection: str | None = None,
    summary_item_limit: int = DEFAULT_SUMMARY_ITEM_LIMIT,
    review_item_limit: int = DEFAULT_REVIEW_ITEM_LIMIT,
    max_bytes: int | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> WrittenReportV3:
    """Atomically write bounded deterministic v3 JSON to ``path``."""

    projected = _coerce_report_v3(
        report,
        projection=projection,
        summary_item_limit=summary_item_limit,
        review_item_limit=review_item_limit,
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    byte_count = 0
    try:
        with os.fdopen(descriptor, "wb") as stream:
            for chunk in _iter_buffered_json_bytes(projected.payload):
                byte_count += len(chunk)
                _enforce_byte_limit(byte_count, max_bytes)
                stream.write(chunk)
                if progress_callback is not None:
                    progress_callback(byte_count)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return WrittenReportV3(
        path=destination,
        byte_count=byte_count,
        projection=projected.projection,
        analysis_fingerprint=projected.analysis_fingerprint,
    )


def load_report_v3_schema() -> dict[str, Any]:
    """Load the packaged v3 schema through distribution resources."""

    raw = (
        resources.files("ladon")
        .joinpath("schemas", "ladon-report-v3.schema.json")
        .read_text(encoding="utf-8")
    )
    schema = json.loads(raw)
    if not isinstance(schema, dict):
        raise ReportModelError("packaged report-v3 schema must be a JSON object")
    return schema


def _validate_projection_options(
    projection: str,
    *,
    summary_item_limit: int,
    review_item_limit: int,
) -> None:
    """Reject ambiguous or unbounded projection controls."""

    if projection not in PROJECTION_NAMES:
        supported = ", ".join(PROJECTION_NAMES)
        raise ReportModelError(
            f"unsupported report projection {projection!r}; expected {supported}"
        )
    if summary_item_limit <= 0 or review_item_limit <= 0:
        raise ReportModelError("projection item limits must be positive")


def _coerce_report_v3(
    report: Mapping[str, Any] | ReportV2 | ReportV3,
    *,
    projection: str | None,
    summary_item_limit: int,
    review_item_limit: int,
) -> ReportV3:
    """Return a v3 object or adapt an existing v2 object."""

    if isinstance(report, ReportV3):
        if projection is not None and projection != report.projection:
            raise ReportModelError(
                f"cannot reproject materialized {report.projection!r} report "
                f"as {projection!r}; rebuild from ReportV2"
            )
        return report
    return build_report_v3(
        report,
        projection=projection or "review",
        summary_item_limit=summary_item_limit,
        review_item_limit=review_item_limit,
    )


def _v3_metadata(report: ReportV2) -> dict[str, Any]:
    """Preserve analysis metadata while identifying the new representation."""

    metadata = report.metadata.to_dict()
    metadata["source_report_version"] = metadata["report_version"]
    metadata["report_version"] = REPORT_V3_VERSION
    return metadata


def _snapshot_identity(report: ReportV2) -> dict[str, Any] | None:
    """Expose snapshot identity without duplicating its manifest in each report."""

    if report.snapshot is None:
        return None
    return {
        "schema": report.snapshot.schema,
        "identity": report.snapshot.identity,
        "sourceIndexFingerprint": report.snapshot.source_index_fingerprint,
        "decision": (
            report.snapshot_decision.to_dict()
            if report.snapshot_decision is not None
            else None
        ),
    }


# Diagnostics have one canonical table; phase rows only carry references.
def _canonical_diagnostics(
    report: ReportV2,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """Deduplicate diagnostics and return stable phase references."""

    registered: dict[str, dict[str, Any]] = {}
    phase_refs: dict[str, list[str]] = {name: [] for name in PHASE_NAMES}
    for row in sorted_diagnostics(report.diagnostics):
        _register_diagnostic(registered, row)
    for phase_name in PHASE_NAMES:
        for row in sorted_diagnostics(report.phases[phase_name].diagnostics):
            reference = _register_diagnostic(registered, row)
            phase_refs[phase_name].append(reference)
    return [registered[key] for key in sorted(registered)], phase_refs


def _register_diagnostic(
    registered: dict[str, dict[str, Any]],
    diagnostic: Diagnostic,
) -> str:
    """Register one diagnostic by normalized content."""

    row = diagnostic.to_dict()
    digest = _json_digest(row)
    reference = f"diagnostic:{digest}"
    registered.setdefault(reference, {"ref": reference, **row})
    return reference


def _canonical_phase_sections(
    report: ReportV2,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one raw canonical owner for every non-null phase payload."""

    sections: dict[str, Any] = {}
    raw_sections: dict[str, Any] = {}
    for name in PHASE_NAMES:
        phase = report.phases[name]
        if phase.data is None:
            continue
        if name == "findings":
            data = [
                finding.to_dict()
                for finding in sorted(
                    report.findings,
                    key=lambda row: (row.kind, row.subject, row.identifier),
                )
            ]
        else:
            data = phase.data
        raw_sections[name] = data
        sections[name] = data
    return sections, raw_sections


def _phase_rows(
    report: ReportV2,
    diagnostic_refs: Mapping[str, list[str]],
    sections: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return phase metadata with references and no embedded payload."""

    return {
        name: _phase_row(
            report.phases[name],
            diagnostic_refs=diagnostic_refs[name],
            payload_ref=_section_ref(name) if name in sections else None,
        )
        for name in PHASE_NAMES
    }


def _phase_row(
    phase: PhaseEnvelope,
    *,
    diagnostic_refs: list[str],
    payload_ref: str | None,
) -> dict[str, Any]:
    """Serialize the scalar/report-reference portion of a phase."""

    return {
        "name": phase.name,
        "status": phase.status,
        "required": phase.required,
        "disposition": phase.disposition,
        "elapsed_seconds": phase.elapsed_seconds,
        "counters": dict(sorted(phase.counters.items())),
        "reason": phase.reason,
        "diagnosticRefs": list(diagnostic_refs),
        "provenance": [row.to_dict() for row in sorted_provenance(phase.provenance)],
        "payloadRef": payload_ref,
    }


def _timing_rows(
    report: ReportV2,
    sections: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return the legacy timing view without embedding phase data."""

    return {
        name: {
            "name": name,
            "status": report.phases[name].status,
            "elapsed_seconds": report.phases[name].elapsed_seconds,
            "counters": dict(sorted(report.phases[name].counters.items())),
            "payloadRef": _section_ref(name) if name in sections else None,
        }
        for name in PHASE_NAMES
    }


def _extension_rows(
    report: ReportV2,
    sections: dict[str, Any],
    raw_sections: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Reference phase-owned or extension-owned payloads without embedding them."""

    rows: dict[str, dict[str, Any]] = {}
    for name in EXTENSION_NAMES:
        extension = report.extensions[name]
        payload_ref, payload_view = _extension_payload_reference(
            extension,
            sections=sections,
            raw_sections=raw_sections,
        )
        rows[name] = {
            "namespace": extension.namespace,
            "version": extension.version,
            "status": extension.status,
            "authority": extension.authority,
            "provenance": [
                row.to_dict() for row in sorted_provenance(extension.provenance)
            ],
            "reason": extension.reason,
            "payloadRef": payload_ref,
            "payloadView": payload_view,
        }
    return rows


def _extension_payload_reference(
    extension: ExtensionEnvelope,
    *,
    sections: dict[str, Any],
    raw_sections: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    """Find or create the canonical owner for an extension payload."""

    if extension.payload is None:
        return None, None
    for section_name in sorted(raw_sections):
        if extension.payload == raw_sections[section_name]:
            return _section_ref(section_name), None
    elaborated = _elaborated_declaration_view(extension, raw_sections)
    if elaborated is not None:
        caps = elaborated.pop("caps")
        if caps is not None:
            caps_section = "elaborated_declaration_caps"
            sections[caps_section] = copy_json(caps)
            elaborated["capsRef"] = _section_ref(caps_section)
        return _section_ref("declaration_graph"), elaborated
    section_name = f"extension.{extension.namespace}"
    sections[section_name] = extension.payload
    return _section_ref(section_name), None


def _elaborated_declaration_view(
    extension: ExtensionEnvelope,
    raw_sections: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Recognize the v2 elaborated extension as a declaration-graph view."""

    if extension.namespace != "elaborated_declarations":
        return None
    payload = extension.payload
    graph = raw_sections.get("declaration_graph")
    if not isinstance(payload, Mapping) or not isinstance(graph, Mapping):
        return None
    if payload.get("declarations") != graph.get("declarations"):
        return None
    if payload.get("edges") != graph.get("elaborated_edges"):
        return None
    if payload.get("summary") != graph.get("elaborated_surface"):
        return None
    return {
        "kind": "elaborated_declaration_graph_view",
        "summaryPointer": "/elaborated_surface",
        "declarationsPointer": "/declarations",
        "edgesPointer": "/elaborated_edges",
        "caps": payload.get("caps"),
    }


# The semantic fingerprint excludes only registered runtime/cache volatility.
def _analysis_fingerprint(
    report: ReportV2,
    *,
    diagnostics: list[dict[str, Any]],
    phases: Mapping[str, Any],
    extensions: Mapping[str, Any],
    sections: Mapping[str, Any],
    coverage: Mapping[str, Any],
    snapshot: Mapping[str, Any] | None,
) -> str:
    """Hash normalized analysis content independently of projection and timing."""

    metadata = _v3_metadata(report)
    metadata["generated_at_utc"] = None
    normalized_coverage = copy_json(dict(coverage))
    collections = normalized_coverage.get("collections", {})
    if isinstance(collections, Mapping):
        for row in collections.values():
            if isinstance(row, dict):
                row["analysisFingerprint"] = None
    normalized_phases = copy_json(dict(phases))
    for phase in normalized_phases.values():
        phase["elapsed_seconds"] = 0.0
    content = {
        "fingerprintAlgorithm": _ANALYSIS_FINGERPRINT_ALGORITHM,
        "metadata": metadata,
        "warnings": list(report.warnings),
        "diagnostics": diagnostics,
        "coverage": normalized_coverage,
        "snapshot": snapshot,
        "phases": normalized_phases,
        "extensions": extensions,
        "sections": sections,
    }
    digest = hashlib.sha256()
    for chunk in _iter_fingerprint_bytes(content):
        digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _json_digest(value: Any) -> str:
    """Return a compact deterministic digest suffix."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def _section_ref(name: str) -> str:
    """Return one canonical section JSON pointer."""

    return f"#/sections/{_pointer_token(name)}"


def _pointer_token(value: str) -> str:
    """Escape one RFC 6901 JSON Pointer token."""

    return value.replace("~", "~0").replace("/", "~1")


def _enforce_byte_limit(actual: int, limit: int | None) -> None:
    """Reject invalid or exceeded serialization limits."""

    if limit is None:
        return
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ReportModelError("max_bytes must be a positive integer")
    if actual > limit:
        raise ReportV3SizeLimitError(
            "report_bytes limit exceeded during serialization.json: "
            f"observed {actual}, configured limit {limit}"
        )


# Streaming preserves deterministic ordering without a second encoded copy.
def _iter_json_bytes(
    value: Any,
    *,
    trailing_newline: bool = True,
) -> Iterator[bytes]:
    """Yield deterministic UTF-8 chunks without a report-sized text string."""

    encoder = json.JSONEncoder(
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    for chunk in encoder.iterencode(value):
        yield chunk.encode("utf-8")
    if trailing_newline:
        yield b"\n"


def _iter_buffered_json_bytes(
    value: Any,
    *,
    trailing_newline: bool = True,
) -> Iterator[bytes]:
    """Coalesce encoder tokens so large reports do not perform tiny writes."""

    buffer = bytearray()
    for chunk in _iter_json_bytes(
        value,
        trailing_newline=trailing_newline,
    ):
        buffer.extend(chunk)
        if len(buffer) >= _SERIALIZATION_CHUNK_BYTES:
            yield bytes(buffer)
            buffer.clear()
    if buffer:
        yield bytes(buffer)


def _iter_fingerprint_bytes(
    value: Any,
    *,
    path: tuple[str, ...] = (),
) -> Iterator[bytes]:
    """Yield canonical JSON while normalizing registered volatile runtimes."""

    normalized = _normalized_fingerprint_value(value, path=path)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    for start in range(0, len(encoded), _SERIALIZATION_CHUNK_BYTES):
        yield encoded[start : start + _SERIALIZATION_CHUNK_BYTES].encode(
            "utf-8"
        )


def _normalized_fingerprint_value(
    value: Any,
    *,
    path: tuple[str, ...],
) -> Any:
    """Shallow-copy only branches containing registered volatile fields."""

    if path:
        return _normalized_fingerprint_branch(value, path)
    normalized = _replace_fingerprint_paths(
        value,
        _VOLATILE_CACHE_PATHS,
        True,
    )
    normalized = _replace_fingerprint_paths(
        normalized,
        _VOLATILE_RUNTIME_PATHS,
        0.0,
    )
    return _normalize_phase_cache_counters(normalized)


def _replace_fingerprint_paths(
    value: Any,
    paths: frozenset[tuple[str, ...]],
    replacement: Any,
) -> Any:
    """Replace a family of registered paths through shallow branch copies."""

    normalized = value
    for path in paths:
        normalized = _replace_fingerprint_path(
            normalized,
            path,
            replacement,
        )
    return normalized


def _normalize_phase_cache_counters(value: Any) -> Any:
    """Replace registered cache counters in every phase mapping."""

    phases = value.get("phases") if isinstance(value, Mapping) else None
    if not isinstance(phases, Mapping):
        return value
    normalized = value
    for phase_name, phase in phases.items():
        normalized = _normalize_one_phase_cache_counters(
            normalized,
            phase_name=phase_name,
            phase=phase,
        )
    return normalized


def _normalize_one_phase_cache_counters(
    value: Any,
    *,
    phase_name: Any,
    phase: Any,
) -> Any:
    """Replace registered cache counters for one well-formed phase."""

    if not isinstance(phase_name, str) or not isinstance(phase, Mapping):
        return value
    counters = phase.get("counters")
    if not isinstance(counters, Mapping):
        return value
    normalized = value
    for counter in _VOLATILE_CACHE_COUNTERS & counters.keys():
        normalized = _replace_fingerprint_path(
            normalized,
            ("phases", phase_name, "counters", counter),
            0,
        )
    return normalized


def _normalized_fingerprint_branch(
    value: Any,
    path: tuple[str, ...],
) -> Any:
    """Retain the private path-aware helper contract for focused callers."""

    if path in _VOLATILE_CACHE_PATHS:
        return True
    if path in _VOLATILE_RUNTIME_PATHS:
        return 0.0
    return value


def _replace_fingerprint_path(
    value: Any,
    path: tuple[str, ...],
    replacement: Any,
) -> Any:
    """Copy mappings along one existing path and replace its terminal value."""

    if not path:
        return replacement
    if not isinstance(value, Mapping) or path[0] not in value:
        return value
    child = value[path[0]]
    updated = _replace_fingerprint_path(
        child,
        path[1:],
        replacement,
    )
    if updated is child:
        return value
    return {**value, path[0]: updated}


__all__ = [
    "DEFAULT_REVIEW_ITEM_LIMIT",
    "DEFAULT_SUMMARY_ITEM_LIMIT",
    "PROJECTION_NAMES",
    "REPORT_V3_VERSION",
    "ReportV3",
    "ReportV3SizeLimitError",
    "SerializedReportV3Bytes",
    "WrittenReportV3",
    "build_report_v3",
    "load_report_v3_schema",
    "serialize_report_v3_bytes",
    "write_report_v3_file",
]
