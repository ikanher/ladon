"""Canonical in-memory Ladon report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

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


@dataclass(frozen=True)
class ReportV2:
    """Typed analysis model with a frozen v2 dictionary projection."""

    metadata: ReportMetadata
    phases: Mapping[str, PhaseEnvelope]
    findings: tuple[Finding, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    warnings: tuple[str, ...] = ()
    extensions: Mapping[str, ExtensionEnvelope] = field(default_factory=dict)

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize the frozen v2 wire shape and compatibility projections."""

        phase_rows = {
            name: self.phases[name].to_v2_dict()
            for name in sorted(self.phases)
        }
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
                payload[section] = copy_json(data) if isinstance(data, dict) else {}
            elif data is not None:
                payload[section] = copy_json(data)

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
