"""Ordinary installed CLI for Ladon's persistent proof-search index."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.cli_execution import (
    EXIT_INTERRUPTED,
    EXIT_INVOCATION,
    EXIT_OPERATIONAL,
    EXIT_SUCCESS,
    write_output_file,
)
from ladon.evidence_receipt import project_evidence_receipt
from ladon.evidence_receipt_readers import receipt_text_lines
from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_constructor import (
    ConstructorRequest,
    constructor_coverage,
    load_constructor_fields,
)
from ladon.proof_search_consumers import ConsumerRequest, query_consumers
from ladon.proof_search_discovery_cli import dispatch_discover
from ladon.proof_search_evidence_cli import dispatch_evidence
from ladon.proof_search_explain import dispatch_explain as _dispatch_explain_impl
from ladon.proof_search_goal_cli import dispatch_goal, render_goal_text
from ladon.proof_search_index import (
    ProofSearchIndexError,
    default_proof_search_index_path,
    query_proof_search_index,
)
from ladon.proof_search_parser import (
    ProofSearchArgumentParser as _ProofSearchArgumentParser,
)
from ladon.proof_search_parser import (
    build_proof_search_parser as _build_proof_search_parser,
)
from ladon.proof_search_semantic_cli import (
    SEMANTIC_TEXT_SCHEMAS,
    deliver_semantic_payload,
    enforce_semantic_execution_policy,
    render_semantic_candidates,
    render_semantic_omissions,
)
from ladon.proof_search_terminal import (
    bounded_message,
    emit_terminal,
    exception_diagnostic,
    semantic_payload_failed,
    semantic_progress_fields,
)
from ladon.proof_search_type_cli import dispatch_type_text
from ladon.semantic_candidate_worker import (
    SemanticCandidateRequest,
    check_semantic_candidate,
)

__all__ = ["build_proof_search_parser", "proof_search_main"]
ProofSearchArgumentParser = _ProofSearchArgumentParser

NATIVE_EVIDENCE_KINDS = (
    "theorem",
    "artifact",
    "route",
    "slice",
    "alternatives",
    "triage",
    "semantic-artifact",
    "semantic-environment",
    "semantic-check",
)


def build_proof_search_parser() -> argparse.ArgumentParser:
    """Build the command tree with the CLI's native evidence contract."""

    return _build_proof_search_parser(evidence_kinds=NATIVE_EVIDENCE_KINDS)


def proof_search_main(argv: Sequence[str]) -> int:
    """Run one proof-search index operation with stable exit behavior."""

    if list(argv)[:2] == ["proof", "slice"]:
        from ladon.correspondence_cli import proof_slice_main

        return proof_slice_main(list(argv)[2:])

    parser = build_proof_search_parser()
    arguments = list(argv)
    operation = _operation_from_tokens(arguments)
    started = time.monotonic()
    if arguments[:2] == ["search", "type"]:
        _emit_type_text_migration_diagnostic()
        return EXIT_INVOCATION
    try:
        args = parser.parse_args(arguments)
        operation = _operation_from_args(args)
        _emit_progress(args, operation, "started")
        return _run_parsed_operation(args, operation, started)
    except KeyboardInterrupt:
        emit_terminal(operation, exit_class="interrupted", exit_code=EXIT_INTERRUPTED)
        return EXIT_INTERRUPTED
    except ProofSearchIndexError as exc:
        exit_class = exc.exit_class
        exit_code = EXIT_OPERATIONAL if exit_class == "operational" else EXIT_INVOCATION
        emit_terminal(
            operation,
            exit_class=exit_class,
            exit_code=exit_code,
            diagnostic=exception_diagnostic(exc),
        )
        return exit_code
    except (OSError, UnicodeError) as exc:
        emit_terminal(
            operation,
            exit_class="operational",
            exit_code=EXIT_OPERATIONAL,
            diagnostic={"code": "operational-failure", "message": bounded_message(exc)},
        )
        return EXIT_OPERATIONAL


def _run_parsed_operation(args, operation: str, started: float) -> int:
    payload = _dispatch(args)
    _write_payload(payload, output=args.output, output_format=args.output_format)
    exit_code = (
        EXIT_OPERATIONAL
        if semantic_payload_failed(operation, payload) or (
            operation == "index.prune" and payload.get("status") == "partial"
        )
        else EXIT_SUCCESS
    )
    _emit_progress(
        args,
        operation,
        "completed" if exit_code == EXIT_SUCCESS else "failed",
        elapsed_seconds=time.monotonic() - started,
        extra=semantic_progress_fields(operation, payload, exit_code),
    )
    return exit_code


def _emit_type_text_migration_diagnostic() -> None:
    print(
        json.dumps(
            {
                "exitClass": "invocation",
                "exitCode": EXIT_INVOCATION,
                "migration": "use 'search type-text'",
                "operation": "search.type",
                "schema": "ladon-proof-search-terminal-v1",
                "status": "failed",
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=sys.stderr,
        flush=True,
    )


def _emit_progress(
    args: argparse.Namespace,
    operation: str,
    status: str,
    *,
    elapsed_seconds: float | None = None,
    extra: Mapping[str, object] | None = None,
) -> None:
    """Emit one bounded machine-readable progress row on stderr."""

    if not args.progress:
        return
    payload: dict[str, object] = {
        "operation": operation,
        "phase": "dispatch",
        "schema": "ladon-proof-search-progress-v1",
        "status": status,
    }
    if elapsed_seconds is not None:
        payload["elapsedSeconds"] = round(elapsed_seconds, 6)
    payload.update(extra or {})
    print(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )


def _operation_from_args(args: argparse.Namespace) -> str:
    top_operation = getattr(args, "proof_search_operation", "unknown")
    for selector in ("check_operation", "goal_operation", "index_operation"):
        selected = getattr(args, selector, None)
        if selected:
            return f"{top_operation}.{selected}"
    return top_operation


def _operation_from_tokens(arguments: Sequence[str]) -> str:
    """Recover a bounded operation label even when argument parsing fails."""

    if not arguments:
        return "unknown"
    top_operation = arguments[0]
    if top_operation in {"index", "search", "check", "goal"} and len(arguments) > 1:
        return f"{top_operation}.{arguments[1]}"
    return top_operation


def _dispatch(args: argparse.Namespace) -> Mapping[str, Any]:
    """Dispatch a parsed index operation."""

    repo_root = Path(args.repo_root)
    index_path = Path(args.index_path) if args.index_path else None
    if getattr(args, "index_operation", None):
        return _dispatch_index(args, repo_root, index_path)
    handlers = {
        "evidence": dispatch_evidence,
        "search": _dispatch_search,
        "explain": _dispatch_explain,
        "consumers": _dispatch_consumers,
        "constructor": _dispatch_constructor,
        "check": _dispatch_check_adapter,
        "discover": lambda args, repo_root, index_path: dispatch_discover(
            args, repo_root, index_path
        ),
        "goal": lambda args, repo_root, index_path: dispatch_goal(args, repo_root),
    }
    handler = handlers.get(args.proof_search_operation)
    if handler is None:
        raise ProofSearchIndexError(
            f"unsupported proof-search operation {args.proof_search_operation!r}"
        )
    payload = handler(args, repo_root, index_path)
    if args.proof_search_operation == "discover" or (
        args.proof_search_operation == "check"
        and getattr(args, "check_operation", None) == "candidate"
    ):
        return deliver_semantic_payload(args, repo_root, payload)
    return payload


def _dispatch_consumers(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    import sqlite3

    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return query_consumers(
            connection,
            ConsumerRequest(args.declaration, args.kind, args.ownership, args.limit),
        )


def _dispatch_constructor(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    import sqlite3

    request = ConstructorRequest(
        args.structure,
        args.module,
        tuple(args.argument),
        args.limit,
        args.freshness,
    )
    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        fields, coverage = load_constructor_fields(connection, request)
        return constructor_coverage(request, fields, coverage_status=coverage)


def _dispatch_check_adapter(
    args: argparse.Namespace, repo_root: Path, _index_path: Path | None
) -> Mapping[str, Any]:
    return _dispatch_check(args, repo_root)


def _dispatch_check(args: argparse.Namespace, repo_root: Path) -> Mapping[str, Any]:
    """Dispatch one explicit Lean-backed proof-search operation."""

    enforce_semantic_execution_policy(args)
    if args.check_operation == "source":
        from ladon.source_association_cli import dispatch_source_association

        return dispatch_source_association(args, repo_root)
    if args.check_operation != "candidate":
        raise ProofSearchIndexError("unsupported checker operation")
    try:
        toolchain = resolve_toolchain_context(
            repo_root.resolve(),
            lake_path=args.lake_path,
            lean_path=args.lean_path,
            selection_mode=args.toolchain_mode,
        )
        request = SemanticCandidateRequest(
            repo_root.resolve(),
            args.module,
            args.goal,
            args.candidate,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_mib * 1024 * 1024,
            max_rss_bytes=args.max_rss_mib * 1024 * 1024,
            toolchain=toolchain,
            require_isolation=getattr(args, "require_isolation", False),
        )
    except LeanToolchainError as error:
        raise ProofSearchIndexError(
            str(error),
            exit_class="operational",
            code="toolchain-unavailable",
            remediation="Run 'ladon doctor --json' and correct the reported Lean/Lake posture.",
        ) from error
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error
    return check_semantic_candidate(request).to_dict()


def _dispatch_explain(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    return _dispatch_explain_impl(args, repo_root, index_path)


def _dispatch_index(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    from ladon.proof_search_index_cli import _dispatch_index as dispatch

    return dispatch(args, repo_root, index_path)


def _dispatch_search(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    if args.search_operation == "type-text":
        return dispatch_type_text(args, repo_root, index_path)
    if args.search_operation != "name":
        raise ProofSearchIndexError("unsupported search operation")
    payload = query_proof_search_index(
        repo_root,
        index_path=index_path,
        text=args.text,
        scope=args.scope,
        roots=tuple(args.root),
        limit=args.limit,
        query_mode=args.query_mode,
        exclusions=tuple(args.exclude),
        min_matched_segments=args.min_matched_segments,
        freshness=args.freshness,
    )
    result = dict(payload)
    result["operation"] = "search-name"
    result["schema"] = "ladon-proof-search-name-result-v2"
    result["matchMode"] = "exact-name+fts" if args.text else "bounded"
    result["normalization"] = "semantic-name-segments-v1"
    result.pop("rows", None)
    if args.text and not result.get("results"):
        result["suggestions"] = [
            {
                "operation": "search-type-text",
                "reason": "no-name-results",
                "message": (
                    "No declaration name matched every requested segment; try "
                    "proof-search search type-text for stored signature text."
                ),
            }
        ]
    return result






def _write_payload(
    payload: Mapping[str, Any],
    *,
    output: str,
    output_format: str,
) -> None:
    if payload.get("evidenceReceipt") is not None:
        project_evidence_receipt(payload["evidenceReceipt"], projection_kind="json-renderer")
    content = (
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if output_format == "json"
        else _render_text(payload)
    )
    if output == "-":
        sys.stdout.write(content)
        return
    write_output_file(Path(output), content)


def _render_text(payload: Mapping[str, Any]) -> str:
    if payload.get("schema") == "ladon-proof-search-index-history-v1":
        from ladon.proof_search_history import render_history

        return render_history(payload)
    if payload.get("schema") == "ladon-proof-search-index-lifecycle-v1":
        from ladon.proof_search_index_text import render_lifecycle

        return render_lifecycle(payload)
    if payload.get("schema") == "ladon-source-goal-completion-result-v1":
        from ladon.source_goal_completion_cli import render_completion_text

        return render_completion_text(payload)
    if payload.get("schema") in {
        "ladon-source-goal-query-result-v1", "ladon-source-goal-capture-result-v1",
    }:
        return render_goal_text(payload)
    if payload.get("schema") == "ladon-source-association-v1":
        return _render_source_association(payload)
    lines = _render_header(payload)
    if payload.get("schema") in {
        "ladon-semantic-candidate-check-result-v1", "ladon-verified-discovery-result-v1",
    }:
        lines.append("audit source: original observations; execution binding is not revalidated in this view.")
    lines.extend(_render_core_rows(payload))
    if payload.get("schema") in SEMANTIC_TEXT_SCHEMAS:
        lines.extend(render_semantic_omissions(payload))
    lines.extend(_render_evidence_sections(payload))
    lines.extend(_render_warnings(payload))
    return "\n".join(lines) + "\n"


def _render_source_association(payload: Mapping[str, Any]) -> str:
    """Render the independent source result without semantic projection."""

    lines = [
        f"proof-search check.source: {payload.get('status', 'unknown')}",
        f"schema: {payload.get('schema')}",
        f"operation: {payload.get('operation')}",
    ]
    for key in sorted(set(payload) - {"schema", "operation", "status"}):
        lines.append(f"{key}: {json.dumps(payload[key], sort_keys=True, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def _render_header(payload: Mapping[str, Any]) -> list[str]:
    from ladon.proof_search_index_text import _render_header as render

    return render(payload)


def _render_core_rows(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    rows = payload.get("rows", payload.get("results"))
    if isinstance(rows, list):
        lines.extend(_render_query_rows(rows))
        lines.append(f"returned: {payload.get('returned', len(rows))}")
        lines.append(f"truncated: {str(bool(payload.get('truncated'))).lower()}")
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        lines.extend(render_semantic_candidates(
            candidates, include_projected_evidence=payload.get("schema") in SEMANTIC_TEXT_SCHEMAS
        ))
        lines.append(f"candidates: {len(candidates)}")
    candidate = payload.get("candidate")
    if isinstance(candidate, Mapping):
        lines.extend(render_semantic_candidates(
            [candidate], include_projected_evidence=payload.get("schema") in SEMANTIC_TEXT_SCHEMAS
        ))
    return lines


def _render_evidence_sections(payload: Mapping[str, Any]) -> list[str]:
    lines = _render_tabular_sections(payload)
    lines.extend(receipt_text_lines(payload.get("evidenceReceipt")))
    for name in ("observations", "checks"):
        section = payload.get(name, {})
        if isinstance(section, Mapping):
            for row in section.get("rows", []):
                lines.extend(receipt_text_lines(row.get("evidenceReceipt")))
    lines.extend(_render_paths(payload))
    lines.extend(_render_coverage(payload))
    return lines


def _render_tabular_sections(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    for section in ("surfaces", "claims", "replay", "diagnostics"):
        value = payload.get(section)
        lines.extend(_render_one_section(section, value))
    return lines


def _render_one_section(section: str, value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    lines = [
        f"{section}: returned={value.get('returned', 0)} matched={value.get('matched', 0)} truncated={str(bool(value.get('truncated'))).lower()}"
    ]
    for item in value.get("rows", []):
        if isinstance(item, Mapping):
            identity = (
                item.get("surfaceId")
                or item.get("claimId")
                or item.get("replayId")
                or item.get("diagnosticId")
                or "<unknown>"
            )
            lines.append(
                f"- {identity} [{item.get('status', item.get('surfaceStatus', item.get('reason', 'observed')))}]"
            )
    return lines


def _render_paths(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    paths = payload.get("paths")
    if isinstance(paths, list):
        lines.append(f"paths: returned={len(paths)} minimum_depth={payload.get('minimumDepth')}")
        for path in paths:
            if isinstance(path, Mapping):
                names = " -> ".join(
                    str(node.get("nodeId"))
                    for node in path.get("nodes", [])
                    if isinstance(node, Mapping)
                )
                lines.append(f"- {path.get('pathId', '?')} depth={path.get('depth', '?')}: {names}")
    return lines


def _render_coverage(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    coverage = payload.get("coverage")
    if isinstance(coverage, Mapping):
        lines.append(f"coverage: {json.dumps(coverage, sort_keys=True, ensure_ascii=False)}")
    nonclaims = payload.get("nonclaims")
    if isinstance(nonclaims, list):
        lines.extend(f"nonclaim: {item}" for item in nonclaims)
    return lines


def _render_warnings(payload: Mapping[str, Any]) -> list[str]:
    lines = [
        f"warning: {row.get('message', row)}"
        for row in payload.get("warnings", [])
        if isinstance(row, Mapping)
    ]
    if payload.get("reason"):
        lines.append(f"reason: {payload['reason']}")
    return lines


def _render_query_rows(rows: list[Any]) -> list[str]:
    """Render compact source-linked declaration candidates."""

    rendered = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        name = row.get("candidateName") or row.get("name") or "<unknown>"
        location = f"{row.get('path', '?')}:{row.get('line', '?')}"
        rendered.append(
            f"- {name} [{row.get('kind', 'unknown')}; {row.get('authority', 'unknown')}] {location}"
        )
    return rendered








