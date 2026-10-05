"""Ordinary CLI operations for source-bound goal observation."""
from __future__ import annotations

import argparse
import hashlib
import re
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.compiler_goal_query import parse_compiler_goal_query
from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_semantic_cli import enforce_semantic_execution_policy
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.source_association_io import _MODULE, _AssociationError, _read_regular, _source_path
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion_cli import dispatch_completion

_SCHEMA = "ladon-source-goal-query-result-v1"
_MAX_DIAGNOSTIC_BYTES = 8 * 1024 * 1024


def register_goal_parser(operations: Any, add_repository_options, add_output_options) -> None:
    goal = operations.add_parser("goal", help="Capture a source goal or query compiler text.")
    actions = goal.add_subparsers(dest="goal_operation", required=True)
    capture = actions.add_parser("capture", help="Observe a goal at an exact source position.")
    _base(capture, add_repository_options, add_output_options)
    capture.add_argument("--source", dest="source_path", required=True)
    capture.add_argument("--module", required=True)
    capture.add_argument("--line", type=int, required=True)
    capture.add_argument("--column", type=int, required=True)
    capture.add_argument("--goal-ordinal", type=int)
    capture.add_argument("--expected-source-digest")
    _toolchain(capture)
    diagnostic = actions.add_parser("diagnostic", help="Query a saved plain Lean diagnostic.")
    _base(diagnostic, add_repository_options, add_output_options)
    diagnostic.add_argument("--diagnostic-file", type=Path, required=True)
    diagnostic.add_argument("--source", dest="source_path")
    diagnostic.add_argument("--module", required=True)
    diagnostic.add_argument("--diagnostic-ordinal", type=int)
    diagnostic.add_argument("--goal-ordinal", type=int)
    diagnostic.add_argument("--expected-source-digest")
    _toolchain(diagnostic)
    complete = actions.add_parser("complete", help="Check a full term against a captured source goal and replay it.")
    _base(complete, add_repository_options, add_output_options)
    complete.add_argument("--capture-file", type=Path, required=True)
    complete.add_argument("--term", required=True)
    _toolchain(complete)


def _base(parser, add_repository_options, add_output_options):
    add_repository_options(parser)
    add_output_options(parser)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-output-mib", type=int, default=8)
    parser.add_argument("--max-rss-mib", type=int, default=32768)
    parser.add_argument("--require-isolation", action="store_true")


def _toolchain(parser):
    parser.add_argument("--toolchain-mode", choices=("explicit",), default="explicit")
    parser.add_argument("--lean-path", type=Path, required=True)
    parser.add_argument("--lake-path", type=Path, required=True)


def dispatch_goal(args: argparse.Namespace, repo_root: Path) -> Mapping[str, Any]:
    _validate_report_destination(args, repo_root)
    if args.goal_operation == "complete":
        _validate_bounds(args)
        return dispatch_completion(args, repo_root)
    _validate_common_args(args)
    if args.goal_operation == "capture":
        source_path, line, column = args.source_path, args.line, args.column
        query = None
    else:
        query = _read_query(args)
        if query["status"] != "parsed":
            return _result(query, None)
        selected = query["selected"]
        source_path, failure = _source_from_record(
            repo_root, selected["file"], args.source_path, args.module,
        )
        if failure is not None:
            return _result(query, None, failure)
        line, column = selected["line"], selected["column"]
    _validate_request_args(args, repo_root, source_path, line, column)
    try:
        capture_result = _capture(args, repo_root, source_path, line, column)
    except ProofSearchIndexError as error:
        if query is None:
            raise
        return _result(query, None, _failure(error.code, str(error)))
    return _result(query, capture_result)


def _validate_request_args(args, repo_root, source_path, line, column) -> None:
    _validate_position(line, column)
    _validate_source_owner(args, repo_root, source_path)


def _validate_common_args(args) -> None:
    _validate_bounds(args)
    _validate_ordinals(args)
    _validate_module(args.module)
    _validate_digest(args.expected_source_digest)


def _validate_bounds(args) -> None:
    try:
        validate_semantic_bounds(
            args.timeout_seconds, args.max_output_mib * 1024**2, args.max_rss_mib * 1024**2,
        )
    except (TypeError, ValueError) as error:
        raise ProofSearchIndexError(str(error), code="invalid-goal-bounds") from error


def _validate_position(line, column) -> None:
    if type(line) is not int or type(column) is not int or line < 1 or column < 0:
        raise ProofSearchIndexError("source position requires a positive line and nonnegative column", code="invalid-source-position")


def _validate_ordinals(args) -> None:
    if args.goal_ordinal is not None and (type(args.goal_ordinal) is not int or args.goal_ordinal < 0):
        raise ProofSearchIndexError("goal ordinal must be nonnegative", code="invalid-goal-ordinal")
    ordinal = getattr(args, "diagnostic_ordinal", None)
    if ordinal is not None and (type(ordinal) is not int or ordinal < 0):
        raise ProofSearchIndexError("diagnostic ordinal must be nonnegative", code="invalid-diagnostic-ordinal")


def _validate_module(module) -> None:
    if not isinstance(module, str) or not _MODULE.fullmatch(module):
        raise ProofSearchIndexError("module must be an ordinary qualified Lean name", code="invalid-source-module")


def _validate_source_owner(args, repo_root, source_path) -> None:
    if args.goal_operation == "capture":
        try:
            _source_path(repo_root.resolve(strict=True), source_path, args.module)
        except _AssociationError as error:
            raise ProofSearchIndexError(str(error), code=error.code) from error


def _validate_digest(digest) -> None:
    if digest is not None and (not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None):
        raise ProofSearchIndexError("expected source digest must be a lowercase sha256 digest", code="invalid-source-digest")


def _read_query(args: argparse.Namespace) -> dict[str, Any]:
    try:
        raw = _read_regular(args.diagnostic_file, _MAX_DIAGNOSTIC_BYTES)
    except _AssociationError as error:
        return _unsupported_input(error.code, str(error))
    except OSError as error:
        return _unsupported_input("diagnostic-read-failed", str(error))
    if len(raw) > _MAX_DIAGNOSTIC_BYTES:
        return _unsupported_input("diagnostic-too-large", "diagnostic exceeds the 8 MiB limit")
    try:
        stream = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _unsupported_input(
            "diagnostic-not-utf8", "diagnostic is not valid UTF-8",
            "sha256:" + hashlib.sha256(raw).hexdigest(),
        )
    return parse_compiler_goal_query(stream, args.diagnostic_ordinal)


def _capture(args, repo_root, source_path, line, column):
    enforce_semantic_execution_policy(args)
    try:
        context = resolve_toolchain_context(
            repo_root, lean_path=args.lean_path, lake_path=args.lake_path,
            selection_mode="explicit",
        )
    except (LeanToolchainError, OSError) as error:
        raise ProofSearchIndexError(
            str(error), exit_class="operational", code="goal-toolchain-unavailable",
        ) from error
    request = SourceGoalCaptureRequest(
        repo_root=repo_root, source_path=source_path, module=args.module,
        line=line, column=column, goal_ordinal=args.goal_ordinal,
        expected_source_digest=args.expected_source_digest, toolchain=context,
        timeout_seconds=args.timeout_seconds,
        max_output_bytes=args.max_output_mib * 1024 * 1024,
        max_rss_bytes=args.max_rss_mib * 1024 * 1024,
        require_isolation=args.require_isolation,
    )
    return capture_source_goal(request)


def _validate_report_destination(args: argparse.Namespace, repo_root: Path) -> None:
    if args.output == "-":
        return
    root = repo_root.resolve(strict=True)
    destination = Path(args.output).resolve(strict=False)
    suffix = destination.name.lower()
    protected_suffixes = (".olean", ".olean.server", ".olean.private", ".ir", ".ir.sig", ".lean")
    if (destination == root or root in destination.parents
        or suffix.endswith(protected_suffixes)):
        raise ProofSearchIndexError(
            "goal reports must be written outside the target repository",
            code="source-report-destination",
        )
    protected = [args.lean_path.resolve(strict=False), args.lake_path.resolve(strict=False)]
    if args.goal_operation == "diagnostic":
        protected.append(args.diagnostic_file.resolve(strict=False))
    if args.goal_operation == "complete":
        protected.append(args.capture_file.resolve(strict=False))
        protected.append(Path(str(resources.files("ladon").joinpath(
            "lean", "ladon_source_goal_completion_helper.lean",
        ))).resolve(strict=False))
    helper = Path(str(resources.files("ladon").joinpath(
        "lean", "ladon_source_goal_helper.lean",
    ))).resolve(strict=False)
    protected.append(helper)
    if destination in protected:
        raise ProofSearchIndexError(
            "goal report destination collides with a selected input or executable",
            code="source-report-destination",
        )


def _source_from_record(repo_root: Path, filename: str, override: str | None, module: str):
    root = repo_root.resolve(strict=True)
    record_path = Path(filename)
    if record_path.is_absolute():
        resolved = record_path.resolve(strict=False)
        if not resolved.is_relative_to(root):
            return None, _failure("diagnostic-source-outside-repository", "diagnostic source path is outside the repository")
        record_relative = resolved.relative_to(root).as_posix()
    else:
        record_relative = record_path.as_posix()
    try:
        canonical_record = _source_path(root, record_relative, module)
    except _AssociationError as error:
        return None, _failure(error.code, str(error))
    except OSError as error:
        return None, _failure("diagnostic-source-unavailable", str(error))
    if override is None:
        return record_relative, None
    try:
        canonical_override = _source_path(root, override, module)
    except (_AssociationError, OSError):
        canonical_override = None
    if canonical_override is None or canonical_record != canonical_override:
        return None, _failure("diagnostic-source-mismatch", "--source does not match the diagnostic's selected file")
    return override, None


def _unsupported_input(code: str, message: str, digest: str | None = None) -> dict[str, Any]:
    return {
        "schema": "ladon-compiler-goal-query-v1", "status": "unsupported",
        "inputDigest": digest, "evidenceBasis": "caller-supplied-compiler-text",
        "recordCount": 0, "selected": None, "diagnostic": {"code": code, "message": message},
    }


def _failure(code: str, message: str) -> dict[str, Any]:
    return {
        "schema": "ladon-source-goal-capture-result-v1", "operation": "capture-source-goal",
        "status": "unavailable", "capture": None, "diagnostic": {"code": code, "message": message},
    }


def _result(query, capture_result, failure=None):
    if query is None:
        return capture_result
    capture_status = capture_result.get("status") if capture_result else None
    status = "captured" if capture_status == "captured" else capture_status
    if failure is not None:
        status = failure["status"]
    if status is None:
        status = "ambiguous" if query.get("status") == "ambiguous" else "unavailable"
    diagnostic = failure.get("diagnostic") if failure else (
        capture_result.get("diagnostic") if capture_result else query.get("diagnostic")
    )
    return {
        "schema": _SCHEMA, "operation": "capture-diagnostic-goal", "status": status,
        "queryEvidence": query, "captureResult": capture_result, "diagnostic": diagnostic,
    }


def render_goal_text(payload: Mapping[str, Any]) -> str:
    lines = [f"status: {payload.get('status')}"]
    query = payload.get("queryEvidence")
    _append_query_text(lines, query)
    capture_result = payload.get("captureResult") if payload.get("schema") == _SCHEMA else payload
    capture = capture_result.get("capture") if isinstance(capture_result, Mapping) else None
    if not isinstance(capture, Mapping):
        _append_failure_text(lines, payload)
    else:
        _append_capture_text(lines, capture, query is not None)
    return "\n".join(lines) + "\n"


def _append_query_text(lines, query):
    if isinstance(query, Mapping) and query.get("selected"):
        selected = query["selected"]
        lines.extend([
            "caller-supplied compiler fragments (not an observed goal):",
            f"  {selected['expression']} : {selected['actualType']} (expected {selected['expectedType']})",
        ])


def _append_failure_text(lines, payload):
    diagnostic = payload.get("diagnostic")
    lines.append("source goal: unavailable")
    if isinstance(diagnostic, Mapping):
        lines.append(f"diagnostic: {diagnostic.get('code')}: {diagnostic.get('message')}")


def _append_capture_text(lines, capture, has_query):
    goal = capture.get("goal", {})
    if goal.get("typeDisplay"):
        lines.append(f"goal: {goal['typeDisplay']}")
    _append_locals(lines, goal.get("localContext", []))
    lines.append(f"source selection: {capture.get('source', {}).get('path')}:{capture.get('source', {}).get('position', {}).get('line')}:{capture.get('source', {}).get('position', {}).get('column')}")
    lines.append("capture scope: ordinary Lean frontend; replay: not-run")
    lines.append(f"observed goal ordinal: {goal.get('ordinal')}; goal ID: {goal.get('goalId')}")
    lines.append(f"capture identity: {capture.get('captureId')}")
    capture_ref = "#/captureResult/capture" if has_query else "#/capture"
    lines.append(f"canonical evidence references: {capture_ref} and {capture_ref}/goal/localContext in JSON.")


def _append_locals(lines, rows):
    lines.append("visible locals:")
    for row in rows:
        value = f" := {row['valueDisplay']}" if row.get("valueDisplay") else ""
        if row.get("implementationDetail"):
            lines.append(
                f"internal local: {row.get('userName')}: {row.get('typeDisplay')}{value} "
                f"(id {row.get('localId')}; {row.get('binderInfo')}) [internal]"
            )
        else:
            lines.append(f"  {row.get('userName')}: {row.get('typeDisplay')}{value} (id {row.get('localId')}; {row.get('binderInfo')})")
