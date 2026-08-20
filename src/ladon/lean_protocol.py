"""Versioned framed protocol for bounded Lean extraction batches.

The Python runner sends one JSON request on stdin.  The helper answers with
newline-delimited JSON: one ordered module frame per request and one terminal
summary frame.  This module validates transport only; payload interpretation
remains in :mod:`ladon.lean_extraction`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PROTOCOL_VERSION = "ladon-lean-batch-v1"
HELPER_VERSION = "ladon-parser-helper-v2"


@dataclass(frozen=True)
class ModuleRequest:
    """One stable module slot in a batch request."""

    request_index: int
    module: str
    file: str

    def to_dict(self) -> dict[str, Any]:
        """Return the helper-facing request shape."""

        return {
            "requestIndex": self.request_index,
            "module": self.module,
            "file": self.file,
        }


@dataclass(frozen=True)
class BatchRequest:
    """One ordered, versioned helper request."""

    modules: tuple[ModuleRequest, ...]
    protocol_version: str = PROTOCOL_VERSION

    def to_json(self) -> str:
        """Serialize one compact request terminated for stdin transport."""

        return json.dumps(
            {
                "protocolVersion": self.protocol_version,
                "modules": [module.to_dict() for module in self.modules],
            },
            sort_keys=True,
        ) + "\n"


@dataclass(frozen=True)
class ModuleDiagnostic:
    """One module- or batch-scoped extraction failure."""

    identifier: str
    severity: str
    message: str
    module: str | None = None
    request_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the report-owner diagnostic shape."""

        return {
            "id": self.identifier,
            "severity": self.severity,
            "message": self.message,
            "subject": self.module,
            "requestIndex": self.request_index,
        }


@dataclass(frozen=True)
class ModuleRecord:
    """One validated module result or diagnostic frame."""

    request: ModuleRequest
    status: str
    payload: Mapping[str, Any] | None = None
    diagnostic: ModuleDiagnostic | None = None


@dataclass(frozen=True)
class BatchSummary:
    """Validated terminal helper summary."""

    protocol_version: str
    helper_version: str
    lean_version: str
    requested: int
    completed: int
    failed: int

    def to_dict(self) -> dict[str, Any]:
        """Return stable report-facing summary fields."""

        return {
            "protocolVersion": self.protocol_version,
            "helperVersion": self.helper_version,
            "leanVersion": self.lean_version,
            "requested": self.requested,
            "completed": self.completed,
            "failed": self.failed,
        }


@dataclass(frozen=True)
class BatchOutcome:
    """Deterministically ordered records plus terminal transport evidence."""

    records: tuple[ModuleRecord, ...]
    summary: BatchSummary | None
    diagnostics: tuple[ModuleDiagnostic, ...] = ()

    @property
    def successful_records(self) -> tuple[ModuleRecord, ...]:
        """Return payload-bearing records in request order."""

        return tuple(record for record in self.records if record.status == "ok")

    @property
    def failed_count(self) -> int:
        """Count module failures plus batch-level transport failures."""

        return sum(record.status != "ok" for record in self.records) + len(
            self.diagnostics
        )


class ProtocolFrameError(ValueError):
    """A helper frame violates the batch transport contract."""


class LeanProtocolError(RuntimeError):
    """Strict-mode rejection retaining every validated row and diagnostic."""

    def __init__(self, outcome: BatchOutcome) -> None:
        super().__init__("Lean helper batch did not satisfy the strict protocol")
        self.outcome = outcome


class BatchFrameCollector:
    """Incrementally validate ordered module frames and a terminal summary."""

    def __init__(
        self,
        expected: Sequence[ModuleRequest],
        *,
        protocol_version: str = PROTOCOL_VERSION,
    ) -> None:
        self.expected = tuple(expected)
        self.protocol_version = protocol_version
        self.records: list[ModuleRecord] = []
        self.summary: BatchSummary | None = None

    def feed_line(self, line: str) -> None:
        """Validate and retain one non-empty NDJSON frame."""

        if not line.strip():
            return
        if self.summary is not None:
            raise ProtocolFrameError("helper emitted data after terminal summary")
        frame = decoded_frame(line)
        self._validate_version(frame)
        if frame.get("frame") == "module":
            self.records.append(self._module_record(frame))
            return
        if frame.get("frame") == "summary":
            self.summary = summary_from_frame(frame)
            return
        raise ProtocolFrameError(f"unsupported helper frame kind: {frame.get('frame')!r}")

    def finish(self) -> BatchOutcome:
        """Validate terminal counts and fill any missing module slots."""

        diagnostics: list[ModuleDiagnostic] = []
        if self.summary is None:
            diagnostics.append(batch_diagnostic("missing terminal summary"))
        else:
            diagnostics.extend(self._summary_diagnostics(self.summary))
        return self._outcome(diagnostics)

    def partial_outcome(self, reason: str) -> BatchOutcome:
        """Preserve accepted rows after malformed transport or interruption."""

        return self._outcome([batch_diagnostic(reason)])

    def _validate_version(self, frame: Mapping[str, Any]) -> None:
        actual = frame.get("protocolVersion")
        if actual != self.protocol_version:
            raise ProtocolFrameError(
                f"helper protocol version mismatch: expected "
                f"{self.protocol_version!r}, got {actual!r}"
            )

    def _module_record(self, frame: Mapping[str, Any]) -> ModuleRecord:
        position = len(self.records)
        if position >= len(self.expected):
            raise ProtocolFrameError("helper emitted more module frames than requested")
        request = self.expected[position]
        validate_module_identity(frame, request)
        status = frame.get("status")
        if status == "ok":
            payload = frame.get("payload")
            if not isinstance(payload, Mapping):
                raise ProtocolFrameError(
                    f"module {request.module} success frame has no object payload"
                )
            return ModuleRecord(request, "ok", dict(payload))
        if status == "failed":
            return ModuleRecord(
                request,
                "failed",
                diagnostic=diagnostic_from_frame(frame, request),
            )
        raise ProtocolFrameError(
            f"module {request.module} has unsupported status {status!r}"
        )

    def _summary_diagnostics(
        self,
        summary: BatchSummary,
    ) -> list[ModuleDiagnostic]:
        expected_counts = (
            len(self.expected),
            sum(record.status == "ok" for record in self.records),
            sum(record.status != "ok" for record in self.records),
        )
        actual_counts = (summary.requested, summary.completed, summary.failed)
        if actual_counts == expected_counts and len(self.records) == len(self.expected):
            return []
        return [
            batch_diagnostic(
                "terminal summary counts do not match validated module frames: "
                f"expected {expected_counts}, got {actual_counts}"
            )
        ]

    def _outcome(
        self,
        diagnostics: Iterable[ModuleDiagnostic],
    ) -> BatchOutcome:
        records = list(self.records)
        for request in self.expected[len(records):]:
            records.append(missing_record(request))
        return BatchOutcome(tuple(records), self.summary, tuple(diagnostics))


def parse_framed_stream(
    text: str,
    expected: Sequence[ModuleRequest],
    *,
    strict: bool = False,
) -> BatchOutcome:
    """Parse a complete framed stream while preserving validated prefixes."""

    collector = BatchFrameCollector(expected)
    try:
        for line in text.splitlines():
            collector.feed_line(line)
        outcome = collector.finish()
    except ProtocolFrameError as exc:
        outcome = collector.partial_outcome(str(exc))
    if strict and outcome.failed_count:
        raise LeanProtocolError(outcome)
    return outcome


def decoded_frame(line: str) -> Mapping[str, Any]:
    """Decode one JSON object frame with a concise protocol error."""

    try:
        frame = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProtocolFrameError(f"malformed helper JSON frame: {exc.msg}") from exc
    if not isinstance(frame, Mapping):
        raise ProtocolFrameError("helper frame must be a JSON object")
    return frame


def validate_module_identity(
    frame: Mapping[str, Any],
    request: ModuleRequest,
) -> None:
    """Require exact position/module/file identity for deterministic assembly."""

    actual = (
        frame.get("requestIndex"),
        frame.get("module"),
        frame.get("file"),
    )
    expected = (request.request_index, request.module, request.file)
    if actual != expected:
        raise ProtocolFrameError(
            f"out-of-order helper module frame: expected {expected!r}, got {actual!r}"
        )


def diagnostic_from_frame(
    frame: Mapping[str, Any],
    request: ModuleRequest,
) -> ModuleDiagnostic:
    """Normalize one helper-owned module diagnostic."""

    raw = frame.get("diagnostic")
    if not isinstance(raw, Mapping):
        raise ProtocolFrameError(
            f"module {request.module} failure frame has no diagnostic object"
        )
    return ModuleDiagnostic(
        identifier=str(raw.get("id") or "lean.module_failure"),
        severity=normalized_severity(raw.get("severity")),
        message=str(raw.get("message") or "Lean helper module failure"),
        module=request.module,
        request_index=request.request_index,
    )


def normalized_severity(value: Any) -> str:
    """Restrict helper severities to the report contract."""

    severity = str(value or "error")
    return severity if severity in {"info", "warning", "error"} else "error"


def summary_from_frame(frame: Mapping[str, Any]) -> BatchSummary:
    """Normalize one terminal frame or raise a transport error."""

    try:
        summary = BatchSummary(
            protocol_version=str(frame["protocolVersion"]),
            helper_version=str(frame["helperVersion"]),
            lean_version=str(frame["leanVersion"]),
            requested=int(frame["requested"]),
            completed=int(frame["completed"]),
            failed=int(frame["failed"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProtocolFrameError("terminal summary has invalid fields") from exc
    if min(summary.requested, summary.completed, summary.failed) < 0:
        raise ProtocolFrameError("terminal summary counts must be non-negative")
    return summary


def batch_diagnostic(message: str) -> ModuleDiagnostic:
    """Build one stable batch-transport diagnostic."""

    return ModuleDiagnostic(
        identifier="lean.protocol_failure",
        severity="error",
        message=message,
    )


def missing_record(request: ModuleRequest) -> ModuleRecord:
    """Build the deterministic failure row for an absent module frame."""

    diagnostic = ModuleDiagnostic(
        identifier="lean.module_record_missing",
        severity="error",
        message="helper did not emit a validated module frame",
        module=request.module,
        request_index=request.request_index,
    )
    return ModuleRecord(request, "failed", diagnostic=diagnostic)
