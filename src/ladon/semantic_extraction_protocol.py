"""Versioned NDJSON contract for bounded Lean semantic extraction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


PROTOCOL = "ladon-lean-semantic-v1"


class Operation(StrEnum):
    EXTRACT = "extract"
    PING = "ping"


class FrameKind(StrEnum):
    HEADER = "header"
    DECLARATION = "declaration"
    DEPENDENCY = "dependency"
    STRUCTURE = "structure"
    FIELD = "field"
    DIAGNOSTIC = "diagnostic"
    SUMMARY = "summary"


class TerminalStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ExtractionBounds:
    max_frames: int = 100_000
    max_bytes: int = 16 * 1024 * 1024
    timeout_seconds: float = 120.0

    def __post_init__(self) -> None:
        if min(self.max_frames, self.max_bytes) < 1 or self.timeout_seconds <= 0:
            raise ValueError("semantic extraction bounds must be positive")


@dataclass(frozen=True)
class SemanticIdentity:
    repository: str
    module: str
    source_fingerprint: str
    helper_identity: str
    lean_identity: str

    def as_dict(self) -> dict[str, str]:
        return {"repository": self.repository, "module": self.module, "sourceFingerprint": self.source_fingerprint, "helperIdentity": self.helper_identity, "leanIdentity": self.lean_identity}


@dataclass(frozen=True)
class ExtractionRequest:
    request_id: str
    operation: Operation
    identity: SemanticIdentity
    bounds: ExtractionBounds = field(default_factory=ExtractionBounds)

    def as_frame(self) -> dict[str, Any]:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        return {"protocol": PROTOCOL, "frame": FrameKind.HEADER.value, "requestId": self.request_id, "operation": self.operation.value, "identity": self.identity.as_dict(), "bounds": {"maxFrames": self.bounds.max_frames, "maxBytes": self.bounds.max_bytes, "timeoutSeconds": self.bounds.timeout_seconds}}


@dataclass(frozen=True)
class TerminalSummary:
    status: TerminalStatus
    counts: Mapping[str, int]
    emitted_frames: int
    request_id: str
    identity: SemanticIdentity

    def as_frame(self) -> dict[str, Any]:
        if any(value < 0 for value in self.counts.values()) or self.emitted_frames < 0:
            raise ValueError("terminal counts must be non-negative")
        return {"protocol": PROTOCOL, "frame": FrameKind.SUMMARY.value, "requestId": self.request_id, "status": self.status.value, "counts": dict(sorted(self.counts.items())), "emittedFrames": self.emitted_frames, "identity": self.identity.as_dict()}


@dataclass(frozen=True)
class ValidatedCollection:
    """Validated prefix and terminal evidence from one helper stream."""

    frames: tuple[Mapping[str, Any], ...]
    summary: Mapping[str, Any] | None
    status: TerminalStatus
    diagnostics: tuple[str, ...] = ()


def collect_ndjson_frames(payload: str, request: ExtractionRequest) -> ValidatedCollection:
    """Validate an incremental NDJSON stream while retaining safe partial prefixes."""

    if len(payload.encode("utf-8")) > request.bounds.max_bytes:
        return ValidatedCollection((), None, TerminalStatus.PARTIAL, ("output cap exceeded",))
    try:
        records = _parse_records(payload)
    except json.JSONDecodeError as exc:
        return ValidatedCollection((), None, TerminalStatus.PARTIAL, (f"malformed frame: {exc.msg}",))
    frames, summary, diagnostics = _validate_records(records, request)
    if summary is None:
        diagnostics.append("missing terminal summary")
        return ValidatedCollection(tuple(frames), None, TerminalStatus.PARTIAL, tuple(diagnostics))
    status = TerminalStatus(str(summary.get("status", "failed")))
    _validate_summary_counts(summary, frames, diagnostics)
    if diagnostics and status == TerminalStatus.COMPLETE:
        status = TerminalStatus.PARTIAL
    return ValidatedCollection(tuple(frames), summary, status, tuple(diagnostics))


def _parse_records(payload: str) -> list[Any]:
    return [json.loads(line) for line in payload.splitlines() if line.strip()]


def _validate_records(records: list[Any], request: ExtractionRequest) -> tuple[list[Mapping[str, Any]], Mapping[str, Any] | None, list[str]]:
    frames: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    diagnostics: list[str] = []
    summary: Mapping[str, Any] | None = None
    for ordinal, frame in enumerate(records):
        if not isinstance(frame, Mapping):
            diagnostics.append("frame is not an object")
            break
        try:
            validate_frame(frame, request, ordinal=ordinal, seen=seen)
        except ValueError as exc:
            diagnostics.append(str(exc))
            break
        if frame.get("frame") == FrameKind.SUMMARY.value:
            summary = frame
            break
        frames.append(frame)
    return frames, summary, diagnostics


def _validate_summary_counts(summary: Mapping[str, Any], frames: list[Mapping[str, Any]], diagnostics: list[str]) -> None:
    if int(summary.get("emittedFrames", -1)) != len(frames):
        diagnostics.append("terminal frame count mismatch")
    expected_counts = summary.get("counts", {})
    if not isinstance(expected_counts, Mapping):
        diagnostics.append("terminal counts are not an object")
        return
    actual_counts: dict[str, int] = {}
    for frame in frames:
        key = str(frame.get("frame"))
        actual_counts[key] = actual_counts.get(key, 0) + 1
    for key, value in expected_counts.items():
        if int(value) != actual_counts.get(str(key), 0):
            diagnostics.append(f"terminal count mismatch: {key}")


def write_request_ndjson(request: ExtractionRequest) -> str:
    """Serialize exactly one request header for supervised helper stdin."""

    return json.dumps(request.as_frame(), sort_keys=True, separators=(",", ":")) + "\n"


def run_supervised_protocol(request: ExtractionRequest, runner: Any) -> ValidatedCollection:
    """Send one framed request through an injected supervised runner."""

    output = runner(write_request_ndjson(request), request.bounds)
    if not isinstance(output, str):
        raise TypeError("semantic protocol runner must return NDJSON text")
    return collect_ndjson_frames(output, request)


def adapt_elaborated_payload(payload: Mapping[str, Any], request: ExtractionRequest) -> str:
    """Translate an existing elaborated-helper payload into protocol frames."""

    lines = []
    identity = request.identity.as_dict()
    for key, kind in (("declarations", FrameKind.DECLARATION.value), ("dependencies", FrameKind.DEPENDENCY.value), ("structures", FrameKind.STRUCTURE.value), ("fields", FrameKind.FIELD.value)):
        for row in payload.get(key, ()):
            if isinstance(row, Mapping):
                frame = dict(row)
                frame.update({"protocol": PROTOCOL, "frame": kind, "requestId": request.request_id, "identity": identity})
                lines.append(json.dumps(frame, sort_keys=True, separators=(",", ":")))
    counts = {kind: sum(1 for row in payload.get(key, ()) if isinstance(row, Mapping)) for key, kind in (("declarations", FrameKind.DECLARATION.value), ("dependencies", FrameKind.DEPENDENCY.value), ("structures", FrameKind.STRUCTURE.value), ("fields", FrameKind.FIELD.value))}
    lines.append(json.dumps({"protocol": PROTOCOL, "frame": FrameKind.SUMMARY.value, "requestId": request.request_id, "status": TerminalStatus.COMPLETE.value, "counts": counts, "emittedFrames": len(lines), "identity": identity}, sort_keys=True, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def exact_expr_fingerprint_v1(expression: str) -> str:
    """Hash a canonical expression payload without pretty-print authority."""

    return "sha256:" + hashlib.sha256(json.dumps({"version": "exact_expr_fingerprint_v1", "expression": expression}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def search_shape_key_v1(*, head: str, arity: int, is_proposition: bool, binder_heads: tuple[str, ...] = ()) -> str:
    if arity < 0:
        raise ValueError("arity must be non-negative")
    payload = {"version": "search_shape_key_v1", "head": head, "arity": arity, "isProposition": bool(is_proposition), "binderHeads": list(binder_heads)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_frame(frame: Mapping[str, Any], request: ExtractionRequest, *, ordinal: int, seen: set[tuple[str, str]]) -> None:
    if frame.get("protocol") != PROTOCOL or frame.get("requestId") != request.request_id:
        raise ValueError("frame identity does not match request")
    kind = str(frame.get("frame", ""))
    if kind not in {item.value for item in FrameKind}:
        raise ValueError(f"unsupported semantic frame {kind!r}")
    if ordinal >= request.bounds.max_frames:
        raise ValueError("semantic frame limit exceeded")
    identity = frame.get("identity")
    if identity != request.identity.as_dict():
        raise ValueError("frame module identity does not match request")
    row_id = frame.get("id")
    if row_id is not None:
        key = (kind, str(row_id))
        if key in seen:
            raise ValueError(f"duplicate semantic frame {key}")
        seen.add(key)


__all__ = ["PROTOCOL", "Operation", "FrameKind", "TerminalStatus", "ExtractionBounds", "SemanticIdentity", "ExtractionRequest", "TerminalSummary", "ValidatedCollection", "collect_ndjson_frames", "write_request_ndjson", "run_supervised_protocol", "adapt_elaborated_payload", "exact_expr_fingerprint_v1", "search_shape_key_v1", "validate_frame"]
