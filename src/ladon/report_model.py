"""Canonical in-memory Ladon report model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ladon.coverage import CoverageRegistry
from ladon.report_contract import (
    EXTENSION_NAMES,
    PHASE_NAMES,
    SECTION_PHASES,
    Diagnostic,
    ExtensionEnvelope,
    Finding,
    PhaseEnvelope,
    ReportMetadata,
    ReportModelError,
    copy_json,
    sorted_diagnostics,
)
from ladon.snapshot import AnalysisSnapshot, SnapshotDecision

_V3_ONLY_DECLARATION_SHAPE_COVERAGE = "declaration_integrity.source_shape_similarities"
_V3_ONLY_DECLARATION_SHAPE_FIELD = "declaration_source_shape_coverage"
_V3_ONLY_DECLARATION_SHAPE_COLLECTION = "sourceShapeSimilarityCandidates"
_V3_ONLY_INSPECTION_NAVIGATION_FIELDS = (
    "inspection_navigation",
    "inspection_option_coverage",
    "inspection_proof_mechanism_coverage",
    "auditProducerRegistrations",
    "resourceProducerRegistrations",
    "audit_command_coverage",
    "resource_review_coverage",
    "resource_directive_coverage",
    "text_declaration_coverage",
)
_V3_ONLY_AUDIT_CANDIDATE_FIELDS = (
    "candidateMatches",
    "candidateCoverage",
    "candidateDeclarationId",
    "candidateReferencedDeclaration",
    "candidateReferencedOwner",
    "candidateAuthority",
    "candidateSourceIndexFingerprint",
    "candidateNonclaim",
)


@dataclass(frozen=True)
class ReportV2:
    """Typed analysis model with a frozen v2 dictionary projection."""

    metadata: ReportMetadata
    phases: Mapping[str, PhaseEnvelope]
    findings: tuple[Finding, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    warnings: tuple[str, ...] = ()
    extensions: Mapping[str, ExtensionEnvelope] = field(default_factory=dict)
    coverage: CoverageRegistry = field(default_factory=CoverageRegistry)
    snapshot: AnalysisSnapshot | None = None
    snapshot_decision: SnapshotDecision | None = None

    def __post_init__(self) -> None:
        self._require_complete_registry(
            actual=set(self.phases),
            expected=set(PHASE_NAMES),
            label="phases",
        )
        self._require_complete_registry(
            actual=set(self.extensions),
            expected=set(EXTENSION_NAMES),
            label="extensions",
        )
        self._require_snapshot_coverage_compatibility()
        if self.snapshot is None and self.snapshot_decision is not None:
            raise ReportModelError(
                "snapshot decision requires a captured analysis snapshot"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the frozen v2 wire shape and compatibility projections."""

        phase_rows = {
            name: self.phases[name].to_v2_dict() for name in sorted(self.phases)
        }
        module_phase = phase_rows.get("module_dag")
        if isinstance(module_phase, dict):
            module_phase["data"] = _v2_module_dag(module_phase.get("data"))
        payload = self._base_payload(phase_rows)
        self._attach_known_sections(payload)
        return payload

    def _base_payload(
        self,
        phase_rows: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build fields that are always present."""

        return {
            "metadata": self.metadata.to_dict(),
            "warnings": list(self.warnings),
            "diagnostics": [
                row.to_dict() for row in sorted_diagnostics(self.diagnostics)
            ],
            "findings": [
                row.to_dict()
                for row in sorted(
                    self.findings,
                    key=lambda finding: (
                        finding.kind,
                        finding.subject,
                        finding.identifier,
                    ),
                )
            ],
            "phases": phase_rows,
            "extensions": {
                name: self.extensions[name].to_dict()
                for name in sorted(self.extensions)
            },
            "pipeline": {"timings": phase_rows},
        }

    def _attach_known_sections(self, payload: dict[str, Any]) -> None:
        """Attach only schema-registered compatibility sections."""

        for section, phase_name in SECTION_PHASES.items():
            data = self.phases[phase_name].data
            if section == "module_dag":
                payload[section] = _v2_module_dag(data)
            elif data is not None:
                payload[section] = copy_json(data)

    def _require_snapshot_coverage_compatibility(self) -> None:
        """Reject coverage rows that claim a different captured input set."""

        if self.snapshot is None:
            return
        source_fingerprints = {
            row.source_fingerprint
            for row in self.coverage.collections.values()
            if row.source_fingerprint is not None
        }
        if source_fingerprints - {self.snapshot.source_index_fingerprint}:
            raise ReportModelError(
                "report coverage source fingerprint does not match snapshot"
            )
        snapshot_scope = self.snapshot.configuration.get("scopeFingerprint")
        scope_fingerprints = {
            row.scope_fingerprint
            for row in self.coverage.collections.values()
            if row.scope_fingerprint is not None
        }
        if snapshot_scope is not None and scope_fingerprints - {snapshot_scope}:
            raise ReportModelError(
                "report coverage scope fingerprint does not match snapshot"
            )

    @staticmethod
    def _require_complete_registry(
        *,
        actual: set[str],
        expected: set[str],
        label: str,
    ) -> None:
        """Reject missing or unknown registered entries."""

        missing = expected - actual
        if missing:
            raise ReportModelError(f"missing registered {label}: {sorted(missing)}")
        unknown = actual - expected
        if unknown:
            raise ReportModelError(f"unknown registered {label}: {sorted(unknown)}")


def _v2_module_dag(value: Any) -> dict[str, Any]:
    """Omit additive v3-only surfaces from the frozen v2 wire."""

    if not isinstance(value, dict):
        return {}
    dag = copy_json(value)
    dag.pop(_V3_ONLY_DECLARATION_SHAPE_FIELD, None)
    for key in _V3_ONLY_INSPECTION_NAVIGATION_FIELDS:
        dag.pop(key, None)
    _strip_v3_audit_candidates(dag)
    integrity = dag.get("declaration_integrity")
    if not isinstance(integrity, dict):
        return dag
    integrity.pop(_V3_ONLY_DECLARATION_SHAPE_COLLECTION, None)
    coverage = integrity.get("coverage")
    if isinstance(coverage, dict):
        coverage.pop(_V3_ONLY_DECLARATION_SHAPE_COVERAGE, None)
    if integrity.get("schema") == "ladon-declaration-integrity-v2":
        integrity["schema"] = "ladon-declaration-integrity-v1"
    return dag


def _strip_v3_audit_candidates(dag: dict[str, Any]) -> None:
    """Keep v2 audit summaries without duplicating v3 lexical owner rows."""

    surfaces = dag.get("audit_surfaces")
    if not isinstance(surfaces, list):
        return
    commands = [
        command
        for surface in surfaces
        if isinstance(surface, dict)
        for command in surface.get("auditCommands", ())
        if isinstance(command, dict)
    ]
    for command in commands:
        for key in _V3_ONLY_AUDIT_CANDIDATE_FIELDS:
            command.pop(key, None)
