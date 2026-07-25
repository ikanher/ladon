"""Typed values and registries for the Ladon report-v2 contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


REPORT_VERSION = "ladon-report-v2"
V1_REPORT_VERSION = "clean-core-1"
PHASE_STATUSES = frozenset({"complete", "skipped", "partial", "failed"})
PHASE_DISPOSITIONS = frozenset(
    {
        "accepted",
        "complete",
        "failed",
        "required-rejection",
        "selector-rejection",
        "skipped",
        "strict-rejection",
    }
)
PHASE_NAMES = (
    "build",
    "discover",
    "lean_extraction",
    "indexing",
    "module_dag",
    "declaration_graph",
    "module_readiness",
    "architecture_policy",
    "source_patterns",
    "import_diet",
    "proof_xray",
    "quality_baseline",
    "findings",
    "refactoring_prescriptions",
    "packet_evidence",
    "review_regions",
    "rendering",
)
SECTION_PHASES = {
    "module_dag": "module_dag",
    "declaration_graph": "declaration_graph",
    "module_readiness": "module_readiness",
    "architecture_policy": "architecture_policy",
    "source_patterns": "source_patterns",
    "import_diet": "import_diet",
    "proof_xray": "proof_xray",
    "quality_baseline": "quality_baseline",
    "refactoring_prescriptions": "refactoring_prescriptions",
    "packet_evidence": "packet_evidence",
    "review_regions": "review_regions",
}
PHASE_DATA_TYPES: dict[str, type] = {
    "discover": dict,
    "lean_extraction": dict,
    "module_dag": dict,
    "declaration_graph": dict,
    "module_readiness": dict,
    "architecture_policy": dict,
    "source_patterns": dict,
    "import_diet": dict,
    "proof_xray": dict,
    "quality_baseline": dict,
    "findings": list,
    "refactoring_prescriptions": dict,
    "packet_evidence": list,
    "review_regions": list,
}
EXTENSION_NAMES = (
    "atlas",
    "elaborated_declarations",
    "packet_evidence",
    "proof_xray",
)


class ReportModelError(ValueError):
    """Raised when report data cannot cross the typed v2 boundary."""


class UnsupportedReportVersionError(ValueError):
    """Raised when a reader receives a report major it cannot interpret."""


@dataclass(frozen=True)
class Provenance:
    """Authority and source identity attached to report evidence."""

    authority: str
    source: str
    backend: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.authority or not self.source:
            raise ReportModelError("provenance authority and source must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Return the schema-facing provenance shape."""

        return {
            "authority": self.authority,
            "source": self.source,
            "backend": self.backend,
            "version": self.version,
        }


@dataclass(frozen=True)
class Diagnostic:
    """Structured report-boundary diagnostic."""

    identifier: str
    severity: str
    message: str
    phase: str | None = None
    subject: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ReportModelError("diagnostic identifier must be non-empty")
        if self.severity not in {"info", "warning", "error"}:
            raise ReportModelError(f"unsupported diagnostic severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        """Return the schema-facing diagnostic shape."""

        return {
            "id": self.identifier,
            "severity": self.severity,
            "message": self.message,
            "phase": self.phase,
            "subject": self.subject,
            "data": copy_json(dict(self.data)),
        }


@dataclass(frozen=True)
class Finding:
    """Common typed fields for one analysis finding."""

    identifier: str
    kind: str
    severity: str
    subject: str
    message: str
    authority: str
    evidence_count: int
    details: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> Finding:
        """Adapt one owner finding without claiming its payload schema."""

        details = copy_json(dict(row))
        kind = str(row.get("kind", "unknown"))
        subject = str(row.get("subject", ""))
        return cls(
            identifier=str(row.get("id") or finding_identifier(details)),
            kind=kind,
            severity=str(row.get("severity", "info")),
            subject=subject,
            message=str(row.get("message", "")),
            authority=finding_authority(row),
            evidence_count=finding_evidence_count(row),
            details=details,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return owner fields plus required common finding fields."""

        row = copy_json(dict(self.details))
        row.update(
            {
                "id": self.identifier,
                "kind": self.kind,
                "severity": self.severity,
                "subject": self.subject,
                "message": self.message,
                "authority": self.authority,
                "evidence_count": self.evidence_count,
            }
        )
        return row


@dataclass(frozen=True)
class PhaseEnvelope:
    """Discriminated state and data for one registered report phase."""

    name: str
    status: str
    required: bool = False
    disposition: str | None = None
    elapsed_seconds: float = 0.0
    counters: Mapping[str, int] = field(default_factory=dict)
    reason: str | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    data: Any = None

    def __post_init__(self) -> None:
        _validate_phase_identity(self.name, self.status)
        if self.disposition is None:
            object.__setattr__(
                self,
                "disposition",
                default_phase_disposition(self.status, self.required),
            )
        _validate_phase_disposition(self.disposition)
        _validate_phase_metrics(self.elapsed_seconds, self.counters)
        _validate_phase_reason(self.name, self.status, self.reason)
        copy_json(self.data)

    @classmethod
    def complete(
        cls,
        name: str,
        *,
        data: Any = None,
        required: bool = False,
        elapsed_seconds: float = 0.0,
        counters: Mapping[str, int] | None = None,
        diagnostics: Iterable[Diagnostic] = (),
        provenance: Iterable[Provenance] = (),
    ) -> PhaseEnvelope:
        """Build a successful phase, including a successful empty phase."""

        return cls(
            name=name,
            status="complete",
            required=required,
            elapsed_seconds=elapsed_seconds,
            counters=counters or {},
            diagnostics=tuple(diagnostics),
            provenance=tuple(provenance),
            data=data,
        )

    @classmethod
    def skipped(
        cls,
        name: str,
        reason: str,
        *,
        required: bool = False,
    ) -> PhaseEnvelope:
        """Build an explicitly skipped phase."""

        return cls(name=name, status="skipped", required=required, reason=reason)

    @classmethod
    def failed(
        cls,
        name: str,
        reason: str,
        *,
        diagnostics: Iterable[Diagnostic],
        data: Any = None,
        required: bool = False,
        elapsed_seconds: float = 0.0,
        counters: Mapping[str, int] | None = None,
        provenance: Iterable[Provenance] = (),
    ) -> PhaseEnvelope:
        """Build a failed phase with structured diagnostics."""

        return cls(
            name=name,
            status="failed",
            required=required,
            elapsed_seconds=elapsed_seconds,
            counters=counters or {},
            reason=reason,
            diagnostics=tuple(diagnostics),
            provenance=tuple(provenance),
            data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the lossless typed-model phase shape."""

        return {
            "name": self.name,
            "status": self.status,
            "required": self.required,
            "disposition": self.disposition,
            "elapsed_seconds": self.elapsed_seconds,
            "counters": dict(sorted(self.counters.items())),
            "reason": self.reason,
            "diagnostics": [row.to_dict() for row in sorted_diagnostics(self.diagnostics)],
            "provenance": [row.to_dict() for row in sorted_provenance(self.provenance)],
            "data": copy_json(self.data),
        }

    def to_v2_dict(self) -> dict[str, Any]:
        """Return the frozen v2 wire shape without v3-owned disposition."""

        row = self.to_dict()
        row.pop("disposition")
        return row


def _validate_phase_identity(name: str, status: str) -> None:
    """Reject unknown phase names and states before inspecting their payload."""

    if name not in PHASE_NAMES:
        raise ReportModelError(f"unregistered phase: {name}")
    if status not in PHASE_STATUSES:
        raise ReportModelError(f"unsupported phase status: {status}")


def _validate_phase_disposition(disposition: str | None) -> None:
    """Reject dispositions outside the registered report vocabulary."""

    if disposition not in PHASE_DISPOSITIONS:
        raise ReportModelError(f"unsupported phase disposition: {disposition}")


def _validate_phase_metrics(
    elapsed_seconds: float,
    counters: Mapping[str, int],
) -> None:
    """Validate non-negative phase timing and counter observations."""

    if elapsed_seconds < 0:
        raise ReportModelError("phase elapsed_seconds must be non-negative")
    if any(not isinstance(value, int) or value < 0 for value in counters.values()):
        raise ReportModelError("phase counters must be non-negative integers")


def _validate_phase_reason(
    name: str,
    status: str,
    reason: str | None,
) -> None:
    """Require an explanatory reason for every non-complete phase."""

    if status != "complete" and not reason:
        raise ReportModelError(f"{name} {status} phase requires textual reason")


def default_phase_disposition(status: str, required: bool) -> str:
    """Return the caller-independent disposition for one terminal phase."""

    if status == "complete":
        return "complete"
    if status == "partial":
        return "required-rejection" if required else "accepted"
    if status == "skipped":
        return "required-rejection" if required else "skipped"
    return "failed"


@dataclass(frozen=True)
class ExtensionEnvelope:
    """Versioned generic envelope for one owner-defined payload."""

    namespace: str
    version: str
    status: str
    authority: str
    provenance: tuple[Provenance, ...] = ()
    reason: str | None = None
    payload: Any = None

    def __post_init__(self) -> None:
        if self.namespace not in EXTENSION_NAMES:
            raise ReportModelError(f"unregistered extension namespace: {self.namespace}")
        if self.status not in PHASE_STATUSES:
            raise ReportModelError(f"unsupported extension status: {self.status}")
        if not self.version or not self.authority:
            raise ReportModelError("extension version and authority must be non-empty")
        if self.status != "complete" and not self.reason:
            raise ReportModelError(
                f"{self.namespace} {self.status} extension requires textual reason"
            )
        copy_json(self.payload)

    def to_dict(self) -> dict[str, Any]:
        """Return the schema-facing extension shape."""

        return {
            "namespace": self.namespace,
            "version": self.version,
            "status": self.status,
            "authority": self.authority,
            "provenance": [row.to_dict() for row in sorted_provenance(self.provenance)],
            "reason": self.reason,
            "payload": copy_json(self.payload),
        }


@dataclass(frozen=True)
class ReportMetadata:
    """Stable metadata for one canonical report."""

    repo_root: str
    analysis_root: str
    analysis_root_module: str
    inventory_root: str
    extraction_backend: str
    generated_at_utc: str | None = None
    failure_policy: Mapping[str, Any] | None = None
    tool_name: str = "ladon"
    tool_version: str = "0.1.0"
    report_version: str = REPORT_VERSION

    def __post_init__(self) -> None:
        if self.report_version != REPORT_VERSION:
            raise ReportModelError(f"canonical metadata must use {REPORT_VERSION}")
        if self.tool_name != "ladon":
            raise ReportModelError("canonical metadata tool_name must be ladon")
        if self.failure_policy is not None:
            copy_json(dict(self.failure_policy))

    def to_dict(self) -> dict[str, Any]:
        """Return the schema-facing metadata shape."""

        row = {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "report_version": self.report_version,
            "generated_at_utc": self.generated_at_utc,
            "repo_root": self.repo_root,
            "analysis_root": self.analysis_root,
            "analysis_root_module": self.analysis_root_module,
            "inventory_root": self.inventory_root,
            "extraction_backend": self.extraction_backend,
        }
        if self.failure_policy is not None:
            row["failure_policy"] = copy_json(dict(self.failure_policy))
        return row


def copy_json(value: Any) -> Any:
    """Copy and validate one JSON value."""

    try:
        return json.loads(json.dumps(value, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise ReportModelError(f"report value is not JSON-serializable: {exc}") from exc


def sorted_diagnostics(rows: Iterable[Diagnostic]) -> list[Diagnostic]:
    """Return diagnostics in canonical order."""

    return sorted(
        rows,
        key=lambda row: (
            row.phase or "",
            row.severity,
            row.identifier,
            row.subject or "",
            row.message,
        ),
    )


def sorted_provenance(rows: Iterable[Provenance]) -> list[Provenance]:
    """Return provenance rows in canonical order."""

    return sorted(
        rows,
        key=lambda row: (
            row.authority,
            row.source,
            row.backend or "",
            row.version or "",
        ),
    )


def finding_identifier(row: Mapping[str, Any]) -> str:
    """Return a stable identifier for an owner finding."""

    encoded = json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:16]
    return f"finding:{row.get('kind', 'unknown')}:{digest}"


def finding_authority(row: Mapping[str, Any]) -> str:
    """Return an explicit owner authority or a conservative default."""

    for key in ("authority", "authorityLabel", "evidenceAuthority"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return "ladon-analysis"


def finding_evidence_count(row: Mapping[str, Any]) -> int:
    """Return a stable evidence count for one finding."""

    for key in ("evidence_count", "evidenceCount", "count"):
        value = row.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    evidence = row.get("evidence")
    return len(evidence) if isinstance(evidence, list) else 0
