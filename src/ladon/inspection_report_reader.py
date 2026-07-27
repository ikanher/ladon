"""Version-aware, process-free report selection for inspection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.atlas_report_reader import inflate_declaration_evidence
from ladon.coverage import CoverageRegistry
from ladon.inspection_adapter_common import (
    artifact_fingerprint,
    coverage_registry,
    optional_mapping,
    optional_text,
    single_coverage_fingerprint,
)
from ladon.inspection_models import (
    ArtifactIdentity,
    InspectionCompatibilityError,
)
from ladon.report_adapters import report_version, supported_report_view
from ladon.report_v3 import REPORT_V3_VERSION


def inspection_report_view(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any], CoverageRegistry, ArtifactIdentity]:
    """Return canonical sections and preserved immutable report identity."""

    version = report_version(payload)
    if version == REPORT_V3_VERSION:
        return _v3_view(payload, version)
    return _legacy_view(payload, version)


def _v3_view(
    payload: Mapping[str, Any],
    version: str,
) -> tuple[Mapping[str, Any], CoverageRegistry, ArtifactIdentity]:
    sections = payload.get("sections")
    if not isinstance(sections, Mapping):
        raise InspectionCompatibilityError("report v3 sections are malformed")
    normalized = _inflate_sections(sections)
    coverage = coverage_registry(payload.get("coverage"))
    snapshot = optional_mapping(payload.get("snapshot"))
    projection = optional_mapping(payload.get("projection"))
    _validate_v3_identity(coverage, snapshot, projection)
    return (
        normalized,
        coverage,
        ArtifactIdentity(
            kind="report",
            schema=version,
            fingerprint=artifact_fingerprint(payload),
            source_fingerprint=optional_text(snapshot.get("sourceIndexFingerprint")),
            scope_fingerprint=single_coverage_fingerprint(
                coverage,
                "scope_fingerprint",
            ),
            analysis_fingerprint=optional_text(projection.get("analysis_fingerprint")),
        ),
    )


def _inflate_sections(sections: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return {
            str(key): inflate_declaration_evidence(value)
            for key, value in sections.items()
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise InspectionCompatibilityError(
            f"report v3 section evidence is malformed: {exc}"
        ) from exc


def _validate_v3_identity(
    coverage: CoverageRegistry,
    snapshot: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> None:
    """Reject disagreement among the report's recorded identity strata."""

    analysis = optional_text(projection.get("analysis_fingerprint"))
    if analysis is None:
        raise InspectionCompatibilityError("report v3 analysis fingerprint is missing")
    analysis_values = _coverage_fingerprints(
        coverage,
        "analysis_fingerprint",
    )
    if analysis_values and analysis_values != {analysis}:
        raise InspectionCompatibilityError(
            "report coverage analysis fingerprints are incompatible"
        )
    source = optional_text(snapshot.get("sourceIndexFingerprint"))
    source_values = _coverage_fingerprints(
        coverage,
        "source_fingerprint",
    )
    if source is not None and source_values and source_values != {source}:
        raise InspectionCompatibilityError(
            "report coverage source fingerprints are incompatible"
        )


def _coverage_fingerprints(
    coverage: CoverageRegistry,
    attribute: str,
) -> set[str]:
    return {
        value
        for row in coverage.collections.values()
        for value in [getattr(row, attribute)]
        if value is not None
    }


def _legacy_view(
    payload: Mapping[str, Any],
    version: str,
) -> tuple[Mapping[str, Any], CoverageRegistry, ArtifactIdentity]:
    try:
        view = supported_report_view(
            payload,
            consumer="inspection report adapter",
        )
    except ValueError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc
    dag = optional_mapping(view.get("module_dag"))
    source_index = optional_mapping(dag.get("source_index"))
    source_fingerprint = optional_text(
        source_index.get("fingerprint")
        or optional_mapping(source_index.get("cache")).get("fingerprint")
    )
    scope_fingerprint = optional_text(
        optional_mapping(dag.get("analysis_scope")).get("fingerprint")
    )
    return (
        view,
        CoverageRegistry(),
        ArtifactIdentity(
            kind="report",
            schema=version,
            fingerprint=artifact_fingerprint(payload),
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        ),
    )


__all__ = ["inspection_report_view"]
