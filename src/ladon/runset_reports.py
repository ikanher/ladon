"""Canonical report publication and hash-verified resume decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.runset_contract import (
    REPORT_VERSION_NAMES,
    BundleEntry,
    EntryValidity,
    ReportReference,
    RunsetBundle,
    RunsetEntry,
    content_sha256,
)
from ladon.runset_runtime import AnalysisOutcome
from ladon.runset_storage import atomic_write_bytes
from ladon.runset_support import (
    diagnostic,
    failed_record,
    resume_reuse_record,
)


def validate_bundle_reports(
    bundle: RunsetBundle | Mapping[str, Any],
    *,
    bundle_dir: str | Path,
) -> tuple[str, ...]:
    """Validate every relative report reference after a bundle move."""

    payload = bundle.to_payload() if isinstance(bundle, RunsetBundle) else bundle
    rows = payload.get("entries")
    if not isinstance(rows, list):
        return ("bundle entries are malformed",)
    failures: list[str] = []
    root = Path(bundle_dir)
    for row in rows:
        failure = _bundle_entry_reference_failure(root, row)
        if failure is not None:
            failures.append(failure)
    return tuple(failures)


def _bundle_entry_reference_failure(
    root: Path,
    raw: Any,
) -> str | None:
    if not isinstance(raw, Mapping):
        return "bundle entry is malformed"
    report = raw.get("report")
    if report is None:
        return None
    failure = validate_reference(root, report)
    if failure is None:
        return None
    return f"{raw.get('id', '<unknown>')}: {failure}"


def record_outcome(
    entry: RunsetEntry,
    destination: Path,
    validity: EntryValidity,
    fingerprint: str,
    reuse: Mapping[str, Any],
    outcome: AnalysisOutcome,
    max_report_bytes: int | None,
) -> BundleEntry:
    """Publish any report and convert the analyzer result to bundle state."""

    report: ReportReference | None = None
    phase_summary: Mapping[str, int] = {}
    status = outcome.status
    diagnostics = outcome.diagnostics
    if outcome.report_bytes is not None:
        try:
            report, phase_summary, report_complete = publish_report(
                entry,
                destination,
                outcome.report_bytes,
                max_report_bytes=max_report_bytes,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return failed_record(
                entry,
                validity,
                fingerprint,
                "invalid_report_output",
                str(exc),
                reuse=reuse,
            )
        if status == "complete" and not report_complete:
            status = "partial"
            diagnostics = (
                *diagnostics,
                diagnostic(
                    "runset.required_phase_incomplete",
                    "canonical report has an incomplete required phase",
                ),
            )
    return BundleEntry(
        identifier=entry.identifier,
        run_identity=entry.run_identity,
        root=entry.root,
        scope=entry.scope,
        required=entry.required,
        status=status,
        entry_fingerprint=fingerprint,
        validity=validity,
        report=report,
        reuse=reuse,
        phase_summary=phase_summary,
        resource_counters=outcome.resource_counters,
        diagnostics=tuple(diagnostics),
    )


def publish_report(
    entry: RunsetEntry,
    destination: Path,
    content: bytes,
    *,
    max_report_bytes: int | None,
) -> tuple[ReportReference, Mapping[str, int], bool]:
    """Validate and atomically publish one independently canonical report."""

    _, version, phase_summary, complete = report_metadata(content, entry)
    report_path = destination / entry.output
    atomic_write_bytes(report_path, content, max_bytes=max_report_bytes)
    return (
        ReportReference(
            path=entry.output,
            version=version,
            sha256=content_sha256(content),
            bytes=len(content),
        ),
        phase_summary,
        complete,
    )


def report_metadata(
    content: bytes,
    entry: RunsetEntry,
) -> tuple[Mapping[str, Any], str, Mapping[str, int], bool]:
    """Validate report identity fields needed at the orchestration boundary."""

    payload = json.loads(content)
    if not isinstance(payload, Mapping):
        raise TypeError("canonical report must be a JSON object")
    version = validated_report_header(payload, entry)
    validate_report_projection(payload, entry, version)
    summary, required_complete = phase_completion(payload.get("phases"))
    return payload, version, summary, required_complete


def validated_report_header(
    payload: Mapping[str, Any],
    entry: RunsetEntry,
) -> str:
    """Require report major and extraction backend to match the entry."""

    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping):
        raise TypeError("canonical report metadata is missing")
    version = metadata.get("report_version")
    expected = REPORT_VERSION_NAMES[entry.report_version]
    if version != expected:
        raise ValueError(
            f"canonical report version {version!r} does not match {expected!r}"
        )
    if metadata.get("extraction_backend") != entry.backend:
        raise ValueError("canonical report backend does not match runset entry")
    return str(version)


def validate_report_projection(
    payload: Mapping[str, Any],
    entry: RunsetEntry,
    version: str,
) -> None:
    """Require the selected v3 projection without constraining v2."""

    if version != "ladon-report-v3":
        return
    projection = payload.get("projection")
    if not isinstance(projection, Mapping):
        raise TypeError("report-v3 projection is missing")
    if projection.get("name") != entry.projection:
        raise ValueError("report projection does not match runset entry")


def phase_completion(phases: Any) -> tuple[Mapping[str, int], bool]:
    """Summarize explicit phase states and required-phase completeness."""

    if not isinstance(phases, Mapping):
        raise TypeError("canonical report phases are missing")
    summary = {status: 0 for status in ("complete", "skipped", "partial", "failed")}
    required_complete = True
    for phase in phases.values():
        if not isinstance(phase, Mapping):
            raise TypeError("canonical report phase is malformed")
        status = phase.get("status")
        if status not in summary:
            raise ValueError(f"canonical report phase status is invalid: {status!r}")
        summary[str(status)] += 1
        if phase.get("required") is True and status != "complete":
            required_complete = False
    return summary, required_complete


def validated_resume_hit(
    entry: RunsetEntry,
    validity: EntryValidity,
    fingerprint: str,
    destination: Path,
    state: Mapping[str, Any],
) -> BundleEntry | None:
    """Return a zero-launch hit only after state and report validation."""

    candidate = resume_candidate(entry, fingerprint, state)
    if candidate is None:
        return None
    raw, report = candidate
    phase_summary = validated_resume_report(entry, destination, report)
    if phase_summary is None:
        return None
    return BundleEntry(
        identifier=entry.identifier,
        run_identity=entry.run_identity,
        root=entry.root,
        scope=entry.scope,
        required=entry.required,
        status="resume-hit",
        entry_fingerprint=fingerprint,
        validity=validity,
        report=report,
        reuse=resume_reuse_record(validity),
        phase_summary=phase_summary,
        resource_counters=decoded_counters(raw.get("resourceCounters")),
        diagnostics=decoded_diagnostics(raw.get("diagnostics")),
    )


def resume_candidate(
    entry: RunsetEntry,
    fingerprint: str,
    state: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ReportReference] | None:
    """Decode a state candidate before touching its report path."""

    entries = state.get("entries")
    if not isinstance(entries, Mapping):
        return None
    raw = entries.get(entry.identifier)
    if not isinstance(raw, Mapping):
        return None
    if raw.get("status") != "complete":
        return None
    if raw.get("entryFingerprint") != fingerprint:
        return None
    report = decode_report_reference(raw.get("report"))
    if report is None or report.path != entry.output:
        return None
    return raw, report


def validated_resume_report(
    entry: RunsetEntry,
    destination: Path,
    report: ReportReference,
) -> Mapping[str, int] | None:
    """Validate content hash, version, bytes, and required completion."""

    try:
        content = (destination / report.path).read_bytes()
        _, version, phase_summary, complete = report_metadata(content, entry)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    actual_identity = (
        version,
        len(content),
        content_sha256(content),
    )
    expected_identity = (report.version, report.bytes, report.sha256)
    if not complete or actual_identity != expected_identity:
        return None
    return phase_summary


def decode_report_reference(raw: Any) -> ReportReference | None:
    """Decode state or bundle report metadata conservatively."""

    if not isinstance(raw, Mapping):
        return None
    try:
        return ReportReference(
            path=str(raw["path"]),
            version=str(raw["version"]),
            sha256=str(raw["sha256"]),
            bytes=int(raw["bytes"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def decoded_counters(raw: Any) -> dict[str, int]:
    """Retain only valid non-negative state counters."""

    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key): value
        for key, value in raw.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }


def decoded_diagnostics(raw: Any) -> tuple[Mapping[str, Any], ...]:
    """Retain only structured state diagnostics."""

    if not isinstance(raw, list):
        return ()
    return tuple(dict(row) for row in raw if isinstance(row, Mapping))


def validate_reference(bundle_dir: Path, raw: Any) -> str | None:
    """Validate one report reference without depending on bundle location."""

    report = decode_report_reference(raw)
    if report is None:
        return "report reference is malformed"
    try:
        content = (bundle_dir / report.path).read_bytes()
    except OSError as exc:
        return f"cannot read report: {exc}"
    identity_failure = _reference_identity_failure(report, content)
    if identity_failure is not None:
        return identity_failure
    return _reference_payload_failure(report, content)


def _reference_identity_failure(
    report: ReportReference,
    content: bytes,
) -> str | None:
    if len(content) != report.bytes:
        return "report byte count does not match"
    if content_sha256(content) != report.sha256:
        return "report content hash does not match"
    return None


def _reference_payload_failure(
    report: ReportReference,
    content: bytes,
) -> str | None:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return "report is not valid JSON"
    if not isinstance(payload, Mapping):
        return "report is not a JSON object"
    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping):
        return "report metadata is missing"
    if metadata.get("report_version") != report.version:
        return "report version does not match"
    return None
