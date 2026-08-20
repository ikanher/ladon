"""Strict report-set ingestion for deterministic Ladon runset bundles."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.runset_contract import (
    BUNDLE_ARTIFACT_KIND,
    BUNDLE_SCHEMA,
    BUNDLE_SCHEMA_VERSION,
    ENTRY_STATUSES,
    REPORT_VERSION_NAMES,
    require_sha256,
)
from ladon.runset_reports import (
    decode_report_reference,
    validate_bundle_reports,
)
from ladon.runset_validation import (
    require_portable_relative_path,
    validate_diagnostics,
)


class BundleValidationError(ValueError):
    """A bundle cannot be trusted as a report-set input."""


@dataclass(frozen=True)
class ValidatedBundle:
    """One checked bundle and its exact referenced report population."""

    path: Path
    payload: Mapping[str, Any]
    report_paths: tuple[str, ...]
    workflow_diagnostics: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class BundleReportSet:
    """Materialized reports plus non-report workflow state from their bundle."""

    root: Path
    workflow_diagnostics: tuple[Mapping[str, Any], ...]


def load_validated_bundle(path: str | Path) -> ValidatedBundle:
    """Load a supported bundle and validate every report backreference."""

    source = Path(path).resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleValidationError(f"cannot load bundle {source}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise BundleValidationError("bundle must be a JSON object")
    validate_bundle_header(payload)
    report_paths = validate_bundle_entries(payload.get("entries"))
    failures = validate_bundle_reports(payload, bundle_dir=source.parent)
    if failures:
        raise BundleValidationError("; ".join(failures))
    return ValidatedBundle(
        source,
        dict(payload),
        report_paths,
        bundle_workflow_diagnostics(payload.get("entries")),
    )


def validate_bundle_header(payload: Mapping[str, Any]) -> None:
    """Require exact artifact and schema majors before reading entries."""

    expected = (
        (payload.get("artifactKind"), BUNDLE_ARTIFACT_KIND, "artifactKind"),
        (payload.get("schema"), BUNDLE_SCHEMA, "schema"),
    )
    for actual, supported, label in expected:
        if actual != supported:
            raise BundleValidationError(
                f"unsupported bundle {label} {actual!r}; expected {supported!r}"
            )
    version = payload.get("schemaVersion")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != BUNDLE_SCHEMA_VERSION
    ):
        raise BundleValidationError(
            f"unsupported bundle schemaVersion {version!r}; "
            f"expected {BUNDLE_SCHEMA_VERSION!r}"
        )
    try:
        require_sha256(
            str(payload.get("runsetFingerprint", "")),
            "bundle runset fingerprint",
        )
    except ValueError as exc:
        raise BundleValidationError(str(exc)) from exc


def validate_bundle_entries(raw: Any) -> tuple[str, ...]:
    """Validate identities, terminal states, references, and uniqueness."""

    if not isinstance(raw, list) or not raw:
        raise BundleValidationError("bundle entries must be a non-empty array")
    identifiers: set[str] = set()
    reports: list[str] = []
    for index, entry in enumerate(raw):
        identifier, report = validate_bundle_entry(entry, index)
        if identifier in identifiers:
            raise BundleValidationError(
                f"bundle contains duplicate entry id {identifier!r}"
            )
        identifiers.add(identifier)
        if report is not None:
            reports.append(report)
    if len(set(reports)) != len(reports):
        raise BundleValidationError("bundle contains duplicate report paths")
    return tuple(reports)


def validate_bundle_entry(raw: Any, index: int) -> tuple[str, str | None]:
    """Validate one entry and return its optional portable report path."""

    if not isinstance(raw, Mapping):
        raise BundleValidationError(f"bundle entry {index} must be an object")
    identifier = raw.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise BundleValidationError(f"bundle entry {index} has no stable id")
    status = raw.get("status")
    if status not in ENTRY_STATUSES:
        raise BundleValidationError(
            f"bundle entry {identifier} has unsupported status {status!r}"
        )
    validate_workflow_fields(raw, identifier)
    report = raw.get("report")
    if report is None:
        if status in {"complete", "resume-hit"}:
            raise BundleValidationError(
                f"bundle entry {identifier} {status} state has no report"
            )
        return identifier, None
    if not isinstance(report, Mapping):
        raise BundleValidationError(
            f"bundle entry {identifier} report reference is malformed"
        )
    version = report.get("version")
    if version not in REPORT_VERSION_NAMES.values():
        raise BundleValidationError(
            f"bundle entry {identifier} has unsupported report version "
            f"{version!r}"
        )
    decoded = decode_report_reference(report)
    if decoded is None:
        raise BundleValidationError(
            f"bundle entry {identifier} report reference is malformed"
        )
    return identifier, decoded.path


def validate_workflow_fields(
    raw: Mapping[str, Any],
    identifier: str,
) -> None:
    """Validate bundle-owned fields quoted by workflow diagnostics."""

    root = raw.get("root")
    if not isinstance(root, str):
        raise BundleValidationError(
            f"bundle entry {identifier} root is malformed"
        )
    try:
        require_portable_relative_path(root, f"bundle entry {identifier} root")
    except ValueError as exc:
        raise BundleValidationError(str(exc)) from exc
    if not isinstance(raw.get("required"), bool):
        raise BundleValidationError(
            f"bundle entry {identifier} required state is malformed"
        )
    diagnostics = raw.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise BundleValidationError(
            f"bundle entry {identifier} diagnostics are malformed"
        )
    try:
        validate_diagnostics(diagnostics)
    except ValueError as exc:
        raise BundleValidationError(
            f"bundle entry {identifier}: {exc}"
        ) from exc


def bundle_workflow_diagnostics(
    raw: Any,
) -> tuple[Mapping[str, Any], ...]:
    """Quote terminal entries that have no canonical analysis report."""

    if not isinstance(raw, list):
        return ()
    return tuple(
        workflow_diagnostic(row)
        for row in raw
        if (
            isinstance(row, Mapping)
            and row.get("report") is None
            and row.get("status") not in {"complete", "resume-hit"}
        )
    )


def workflow_diagnostic(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Build one bundle-authoritative state row without analysis claims."""

    diagnostics = [
        dict(row)
        for row in entry.get("diagnostics", [])
        if isinstance(row, Mapping)
    ]
    bundle_status = str(entry["status"])
    return {
        "authority": "ladon_analysis_bundle",
        "bundleStatus": bundle_status,
        "diagnostics": diagnostics,
        "entryId": str(entry["id"]),
        "nonclaim": (
            "Bundle workflow state only; no canonical analysis report was "
            "available, so this row contains no module, declaration, finding, "
            "proof, or theorem evidence."
        ),
        "reason": workflow_reason(bundle_status, diagnostics),
        "reportPresent": False,
        "required": bool(entry["required"]),
        "root": str(entry["root"]),
        "severity": workflow_severity(bundle_status, diagnostics),
        "state": workflow_state(bundle_status, diagnostics),
    }


def workflow_reason(
    status: str,
    diagnostics: list[dict[str, Any]],
) -> str:
    """Return the first quoted bundle reason or a neutral state summary."""

    for diagnostic in diagnostics:
        message = diagnostic.get("message")
        if isinstance(message, str) and message:
            return message
    return f"bundle entry ended in {status} state without a canonical report"


def workflow_state(
    status: str,
    diagnostics: list[dict[str, Any]],
) -> str:
    """Distinguish explicit cancellation from other interruptions."""

    if status != "interrupted":
        return status
    cancellation_text = " ".join(
        f"{row.get('id', '')} {row.get('message', '')}"
        for row in diagnostics
    ).casefold()
    return "cancelled" if "cancel" in cancellation_text else status


def workflow_severity(
    status: str,
    diagnostics: list[dict[str, Any]],
) -> str:
    """Retain the strongest quoted severity with a state-based fallback."""

    rank = {"info": 0, "warning": 1, "error": 2}
    severities = [
        str(row.get("severity"))
        for row in diagnostics
        if row.get("severity") in rank
    ]
    if severities:
        return max(severities, key=rank.__getitem__)
    return "warning" if status == "skipped" else "error"


@contextmanager
def bundle_report_set(
    bundle_path: str | Path,
) -> Iterator[BundleReportSet]:
    """Yield exact reports and quoted state from one validated bundle."""

    bundle = load_validated_bundle(bundle_path)
    with tempfile.TemporaryDirectory(prefix="ladon-bundle-reports-") as raw:
        root = Path(raw)
        for relative in bundle.report_paths:
            source = bundle.path.parent / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        yield BundleReportSet(root, bundle.workflow_diagnostics)


@contextmanager
def bundle_reports_root(
    bundle_path: str | Path,
) -> Iterator[Path]:
    """Yield only validated referenced reports for compatibility callers."""

    with bundle_report_set(bundle_path) as report_set:
        yield report_set.root
