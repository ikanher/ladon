"""Ordinary Ladon CLI for bounded ProofIR v3 artifact operations."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from ladon.cli_execution import (
    EXIT_INTERRUPTED,
    EXIT_INVOCATION,
    EXIT_OPERATIONAL,
    EXIT_SUCCESS,
)
from ladon.proofir_v3 import canonical_bytes, validate_envelope

DEFAULT_MAX_INPUT_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_OUTPUT_BYTES = 8 * 1024 * 1024


class ProofIRCLIInvocationError(ValueError):
    """Raised when a supported artifact command receives invalid arguments."""


class ProofIRArgumentParser(argparse.ArgumentParser):
    """Return supported-command parser errors through the callable CLI API."""

    def error(self, message: str) -> None:
        if "invalid choice: 'convert'" in message:
            super().error(message)
        raise ProofIRCLIInvocationError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = ProofIRArgumentParser(
        description="Validate and inspect ProofIR v3 artifacts"
    )
    sub = parser.add_subparsers(dest="operation", required=True)
    for name in ("validate", "canonicalize", "inspect"):
        command = sub.add_parser(name)
        command.add_argument("artifact", type=Path)
        command.add_argument("--out", type=Path)
        _add_execution_options(command)
    return parser


def _add_execution_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-input-mib",
        type=_positive_float,
        default=DEFAULT_MAX_INPUT_BYTES / (1024 * 1024),
    )
    parser.add_argument(
        "--max-output-mib",
        type=_positive_float,
        default=DEFAULT_MAX_OUTPUT_BYTES / (1024 * 1024),
    )
    parser.add_argument("--deadline-seconds", type=_positive_float, default=30.0)
    parser.add_argument("--progress", action="store_true")


def proofir_v3_main(argv: Sequence[str] | None = None) -> int:
    """Run one bounded artifact operation and translate failures at the boundary."""

    arguments = list(argv) if argv is not None else list(sys.argv[1:])
    operation = arguments[0] if arguments else "unknown"
    try:
        return _run_artifact_operation(arguments)
    except KeyboardInterrupt:
        _emit_terminal(
            operation,
            exit_class="interrupted",
            exit_code=EXIT_INTERRUPTED,
        )
        return EXIT_INTERRUPTED
    except ProofIRCLIInvocationError as exc:
        _emit_terminal(
            operation,
            exit_class="invocation",
            exit_code=EXIT_INVOCATION,
            diagnostic_code="invocation-failure",
            message=str(exc),
        )
        return EXIT_INVOCATION
    except OSError as exc:
        _emit_terminal(
            operation,
            exit_class="operational",
            exit_code=EXIT_OPERATIONAL,
            diagnostic_code="operational-failure",
            message=str(exc),
        )
        return EXIT_OPERATIONAL
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        _emit_terminal(
            operation,
            exit_class="invocation",
            exit_code=EXIT_INVOCATION,
            diagnostic_code="artifact-invalid",
            message=str(exc),
        )
        return EXIT_INVOCATION


def _run_artifact_operation(arguments: list[str]) -> int:
    started = time.monotonic()
    args = build_parser().parse_args(arguments)
    _emit_progress(args, "read", "started")
    raw = args.artifact.read_bytes()
    if len(raw) > int(args.max_input_mib * 1024 * 1024):
        raise ValueError("artifact exceeds configured input byte limit")
    _check_deadline(started, args.deadline_seconds)
    source = json.loads(raw.decode("utf-8"))
    if not isinstance(source, dict):
        raise TypeError("artifact must be a JSON object")
    _emit_progress(args, "read", "completed", input_bytes=len(raw))
    artifact = validate_envelope(source)
    _check_deadline(started, args.deadline_seconds)
    output = _operation_result(args.operation, source, artifact.content_id)
    output_bytes = _bounded_output_bytes(
        source if args.operation == "canonicalize" else output,
        int(args.max_output_mib * 1024 * 1024),
    )
    _check_deadline(started, args.deadline_seconds)
    _publish_result(args.out, output_bytes)
    _emit_progress(
        args,
        args.operation,
        "completed",
        input_bytes=len(raw),
        output_bytes=len(output_bytes),
    )
    return EXIT_SUCCESS


def _operation_result(
    operation: str, source: dict[str, object], artifact_id: str
) -> dict[str, object]:
    if operation == "validate":
        return {
            "schema": "ladon-proofir-validate-result-v1",
            "operation": "validate",
            "status": "valid",
            "proofirVersion": source["proofirVersion"],
            "artifactId": artifact_id,
            "artifactKind": source["artifactKind"],
        }
    if operation == "canonicalize":
        return source
    return {
        "schema": "ladon-proofir-inspect-result-v1",
        "operation": "inspect",
        "proofirVersion": source["proofirVersion"],
        "artifactId": artifact_id,
        "artifactKind": source["artifactKind"],
        "subjects": source["subjectRefs"],
        "coverage": source["coverage"],
    }


def _publish_result(path: Path | None, payload: bytes) -> None:
    if path is None:
        sys.stdout.write(payload.decode("utf-8"))
    else:
        _atomic_write(path, payload)


def _emit_terminal(
    operation: str,
    *,
    exit_class: str,
    exit_code: int,
    diagnostic_code: str | None = None,
    message: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "exitClass": exit_class,
        "exitCode": exit_code,
        "operation": operation,
        "schema": "ladon-proofir-terminal-v1",
        "status": "interrupted" if exit_class == "interrupted" else "failed",
    }
    if diagnostic_code is not None and message is not None:
        payload["diagnostic"] = {"code": diagnostic_code, "message": message}
    print(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )


def _bounded_output_bytes(payload: object, max_bytes: int) -> bytes:
    try:
        return canonical_bytes(payload, max_bytes=max_bytes)
    except ValueError as exc:
        if "byte limit" in str(exc):
            raise ValueError("result exceeds configured output byte limit") from exc
        raise


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _check_deadline(started: float, deadline_seconds: float) -> None:
    if time.monotonic() - started > deadline_seconds:
        raise ValueError("operation exceeded configured deadline")


def _accounting(started: float, input_bytes: int) -> dict[str, object]:
    return {
        "inputBytes": input_bytes,
        "elapsedSeconds": round(time.monotonic() - started, 6),
    }


def _emit_progress(
    args: argparse.Namespace,
    phase: str,
    status: str,
    *,
    input_bytes: int | None = None,
    output_bytes: int | None = None,
) -> None:
    if not args.progress:
        return
    payload: dict[str, object] = {
        "schema": "ladon-proofir-progress-v1",
        "phase": phase,
        "status": status,
    }
    if input_bytes is not None:
        payload["inputBytes"] = input_bytes
    if output_bytes is not None:
        payload["outputBytes"] = output_bytes
    print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


__all__ = [
    "DEFAULT_MAX_INPUT_BYTES",
    "DEFAULT_MAX_OUTPUT_BYTES",
    "EXIT_INTERRUPTED",
    "proofir_v3_main",
]
