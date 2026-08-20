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
from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_constructor import (
    ConstructorRequest,
    constructor_coverage,
    load_constructor_fields,
)
from ladon.proof_search_consumers import ConsumerRequest, query_consumers
from ladon.proof_search_index import (
    DEFAULT_MAX_INDEX_BYTES,
    SUPPORTED_INDEX_SCOPES,
    ProofSearchIndexError,
    build_proof_search_index,
    default_proof_search_index_path,
    inspect_proof_search_index,
    query_proof_search_index,
)
from ladon.proof_search_type_cli import dispatch_type_text
from ladon.proofir_derivation import (
    DerivationQueryBounds,
    analyze_alternatives,
    complete_derivation_slice,
    navigation_path,
)
from ladon.proofir_v3 import ProofIRV3Error, validate_envelope
from ladon.proofir_v3_queries import (
    query_v3_artifacts,
    query_v3_theorem_evidence,
    query_v3_triage,
)
from ladon.semantic_candidate_worker import (
    SemanticCandidateRequest,
    check_semantic_candidate,
)


class ProofSearchArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the ordinary callable CLI contract."""

    def error(self, message: str) -> None:
        raise ProofSearchIndexError(message)


def build_proof_search_parser() -> argparse.ArgumentParser:
    """Build the caller-neutral proof-search command tree."""

    parser = ProofSearchArgumentParser(
        prog="ladon proof-search",
        description="Build and query local Lean proof-navigation evidence.",
    )
    operations = parser.add_subparsers(dest="proof_search_operation", required=True)
    index = operations.add_parser(
        "index",
        help="Build, inspect, or query the persistent local index.",
    )
    commands = index.add_subparsers(dest="index_operation", required=True)

    build = commands.add_parser("build", help="Atomically build or replace the index.")
    _add_repository_options(build)
    _add_output_options(build)
    build.add_argument(
        "--max-index-mib",
        type=_positive_integer,
        default=DEFAULT_MAX_INDEX_BYTES // (1024 * 1024),
        help="Maximum database size in MiB; defaults to 512.",
    )

    status = commands.add_parser("status", help="Inspect index identity and freshness.")
    _add_repository_options(status)
    _add_output_options(status)
    status.add_argument(
        "--no-verify-sources",
        action="store_true",
        help="Read stored metadata without hashing current source/configuration bytes.",
    )

    query = commands.add_parser("query", help="Run a bounded declaration query.")
    _add_repository_options(query)
    _add_output_options(query)
    query.add_argument("--text", help="Literal name or lexical-signature substring.")
    query.add_argument(
        "--query-mode",
        choices=("all", "any", "phrase"),
        default="all",
        help="Boolean semantics for segmented name terms.",
    )
    query.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Folded name substring to exclude; repeatable.",
    )
    query.add_argument(
        "--scope",
        choices=sorted(SUPPORTED_INDEX_SCOPES),
        default="repository",
        help="Explicit candidate population; repository is the default.",
    )
    evidence = operations.add_parser("evidence", help="Query stored ProofIR evidence.")
    _add_repository_options(evidence)
    _add_output_options(evidence)
    evidence.add_argument(
        "kind",
        choices=("theorem", "artifact", "route", "slice", "alternatives", "triage"),
    )
    evidence.add_argument("name")
    evidence.add_argument("--start")
    evidence.add_argument("--end")
    evidence.add_argument("--limit", type=_bounded_limit, default=100)
    query.add_argument(
        "--root",
        action="append",
        default=[],
        help="Module, namespace, or file root required by the selected scope.",
    )
    query.add_argument(
        "--limit",
        type=_bounded_limit,
        default=20,
        help="Maximum rows returned, between 1 and 1000.",
    )
    query.add_argument("--min-matched-segments", type=_positive_integer, default=1)
    search = operations.add_parser(
        "search", help="Run the versioned name-search contract."
    )
    search_commands = search.add_subparsers(dest="search_operation", required=True)
    name = search_commands.add_parser(
        "name", help="Search declarations by normalized name."
    )
    _add_repository_options(name)
    _add_output_options(name)
    name.add_argument("--text", required=True)
    name.add_argument("--query-mode", choices=("all", "any", "phrase"), default="all")
    name.add_argument("--exclude", action="append", default=[])
    name.add_argument(
        "--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository"
    )
    name.add_argument("--root", action="append", default=[])
    name.add_argument("--limit", type=_bounded_limit, default=20)
    name.add_argument("--min-matched-segments", type=_positive_integer, default=1)
    name.add_argument("--freshness", choices=("verify", "stored"), default="verify")
    type_search = search_commands.add_parser(
        "type-text", aliases=["type"], help="Search declaration type text (lexical shortlist)."
    )
    _add_repository_options(type_search)
    _add_output_options(type_search)
    type_search.add_argument("--pattern", required=True)
    type_search.add_argument("--module")
    type_search.add_argument("--namespace")
    type_search.add_argument("--package")
    type_search.add_argument(
        "--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository"
    )
    type_search.add_argument("--root", action="append", default=[])
    type_search.add_argument("--limit", type=_bounded_limit, default=20)
    type_search.add_argument("--diagnostic-limit", type=_bounded_limit, default=0)
    type_search.add_argument(
        "--freshness", choices=("verify", "stored"), default="stored"
    )
    explain = operations.add_parser(
        "explain", help="Explain a bounded candidate/goal difference."
    )
    _add_repository_options(explain)
    _add_output_options(explain)
    explain.add_argument("--goal", required=True)
    explain.add_argument("--candidate", required=True)
    explain.add_argument("--module")
    explain.add_argument("--assumption", action="append", default=[])
    explain.add_argument("--suggestion-cap", type=_bounded_limit, default=10)
    explain.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    explain.add_argument(
        "--raw-signature",
        action="store_true",
        help="Use compatibility raw-signature comparison without binder normalization.",
    )
    consumers = operations.add_parser(
        "consumers", help="Find bounded declaration consumers."
    )
    _add_repository_options(consumers)
    _add_output_options(consumers)
    consumers.add_argument("--declaration", required=True)
    consumers.add_argument("--kind", choices=("all", "type", "value"), default="all")
    consumers.add_argument(
        "--ownership", choices=("all", "project", "external"), default="all"
    )
    consumers.add_argument("--limit", type=_bounded_limit, default=100)
    constructor = operations.add_parser(
        "constructor", help="Inspect bounded constructor field coverage."
    )
    _add_repository_options(constructor)
    _add_output_options(constructor)
    constructor.add_argument("--structure", required=True)
    constructor.add_argument("--module")
    constructor.add_argument("--argument", action="append", default=[])
    constructor.add_argument("--limit", type=_bounded_limit, default=100)
    constructor.add_argument(
        "--freshness", choices=("verify", "stored"), default="stored"
    )
    check = operations.add_parser(
        "check", help="Run an explicit bounded Lean checker operation."
    )
    check_commands = check.add_subparsers(dest="check_operation", required=True)
    candidate = check_commands.add_parser(
        "candidate", help="Check one closed candidate against one exact goal."
    )
    _add_repository_options(candidate)
    _add_output_options(candidate)
    candidate.add_argument("--module", required=True)
    candidate.add_argument("--goal", required=True)
    candidate.add_argument("--candidate", required=True)
    candidate.add_argument("--timeout-seconds", type=float, default=120.0)
    candidate.add_argument("--max-output-mib", type=_positive_integer, default=8)
    candidate.add_argument("--max-rss-mib", type=_positive_integer, default=2048)
    candidate.add_argument(
        "--toolchain-mode",
        choices=("ambient", "explicit"),
        default="ambient",
        help="Select ambient discovery (non-authoritative) or explicit pinned executables.",
    )
    candidate.add_argument("--lake-path", type=Path)
    candidate.add_argument("--lean-path", type=Path)
    return parser


def proof_search_main(argv: Sequence[str]) -> int:
    """Run one proof-search index operation with stable exit behavior."""

    parser = build_proof_search_parser()
    arguments = list(argv)
    operation = _operation_from_tokens(arguments)
    started = time.monotonic()
    try:
        args = parser.parse_args(arguments)
        operation = _operation_from_args(args)
        _emit_progress(args, operation, "started")
        payload = _dispatch(args)
        _write_payload(payload, output=args.output, output_format=args.output_format)
        _emit_progress(
            args,
            operation,
            "completed",
            elapsed_seconds=time.monotonic() - started,
        )
        return EXIT_SUCCESS
    except KeyboardInterrupt:
        _emit_terminal(
            operation, exit_class="interrupted", exit_code=EXIT_INTERRUPTED
        )
        return EXIT_INTERRUPTED
    except ProofSearchIndexError as exc:
        del exc
        _emit_terminal(operation, exit_class="invocation", exit_code=EXIT_INVOCATION)
        return EXIT_INVOCATION
    except (OSError, UnicodeError) as exc:
        del exc
        _emit_terminal(
            operation, exit_class="operational", exit_code=EXIT_OPERATIONAL
        )
        return EXIT_OPERATIONAL


def _emit_terminal(
    operation: str,
    *,
    exit_class: str,
    exit_code: int,
) -> None:
    """Write one stable terminal failure record without contaminating stdout."""

    print(
        json.dumps(
            {
                "exitClass": exit_class,
                "exitCode": exit_code,
                "operation": operation,
                "schema": "ladon-proof-search-terminal-v1",
                "status": "interrupted" if exit_class == "interrupted" else "failed",
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
    print(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )


def _operation_from_args(args: argparse.Namespace) -> str:
    index_operation = getattr(args, "index_operation", None)
    check_operation = getattr(args, "check_operation", None)
    top_operation = getattr(args, "proof_search_operation", "unknown")
    if check_operation:
        return f"{top_operation}.{check_operation}"
    return f"{top_operation}.{index_operation}" if index_operation else top_operation


def _operation_from_tokens(arguments: Sequence[str]) -> str:
    """Recover a bounded operation label even when argument parsing fails."""

    if not arguments:
        return "unknown"
    top_operation = arguments[0]
    if top_operation in {"index", "search", "check"} and len(arguments) > 1:
        return f"{top_operation}.{arguments[1]}"
    return top_operation


def _dispatch(args: argparse.Namespace) -> Mapping[str, Any]:
    """Dispatch a parsed index operation."""

    repo_root = Path(args.repo_root)
    index_path = Path(args.index_path) if args.index_path else None
    if getattr(args, "index_operation", None):
        return _dispatch_index(args, repo_root, index_path)
    handlers = {
        "evidence": _dispatch_evidence,
        "search": _dispatch_search,
        "explain": _dispatch_explain,
        "consumers": _dispatch_consumers,
        "constructor": _dispatch_constructor,
        "check": _dispatch_check_adapter,
    }
    handler = handlers.get(args.proof_search_operation)
    if handler is None:
        raise ProofSearchIndexError(
            f"unsupported proof-search operation {args.proof_search_operation!r}"
        )
    return handler(args, repo_root, index_path)


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
    """Run the sole explicit Lean-backed proof-search operation."""

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
        )
    except (ValueError, LeanToolchainError) as error:
        raise ProofSearchIndexError(str(error)) from error
    return check_semantic_candidate(request).to_dict()


def _dispatch_explain(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    import sqlite3

    request = DifferenceRequest(
        args.goal,
        args.candidate,
        args.module,
        tuple(args.assumption),
        args.suggestion_cap,
        args.freshness,
        args.raw_signature,
    )
    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id,name,type_text,type_status,authority,module,type_text_truncated FROM declarations WHERE name=? OR candidate_name=? ORDER BY path,line,id",
            (args.candidate, args.candidate),
        ).fetchall()
    if len(row) != 1:
        return {"schema": "ladon-proof-difference-result-v1", "schemaVersion": 2, "operation": "explain", "status": "unavailable", "reason": "candidate declaration is not unique", "goal": args.goal, "candidate": args.candidate}
    row = row[0]
    if row[6]:
        return {"schema": "ladon-proof-difference-result-v1", "schemaVersion": 2, "operation": "explain", "status": "unavailable", "reason": "candidate type text is truncated", "goal": args.goal, "candidate": args.candidate}
    evidence = (
        None
        if row is None
        else {
            "declarationId": row[0],
            "name": row[1],
            "typeText": row[2],
            "typeStatus": row[3],
            "authority": row[4],
            "module": row[5],
            "freshness": args.freshness,
        }
    )
    return analyze_difference(request, candidate_signature=str(row[2]), candidate_evidence=evidence)


def _dispatch_index(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    if args.index_operation == "build":
        payload = build_proof_search_index(
            repo_root,
            index_path=index_path,
            max_index_bytes=args.max_index_mib * 1024 * 1024,
        ).payload
        return payload
    if args.index_operation == "status":
        return inspect_proof_search_index(
            repo_root, index_path=index_path, verify_sources=not args.no_verify_sources
        )
    return query_proof_search_index(
        repo_root,
        index_path=index_path,
        text=args.text,
        scope=args.scope,
        roots=tuple(args.root),
        limit=args.limit,
        query_mode=args.query_mode,
        exclusions=tuple(args.exclude),
        min_matched_segments=args.min_matched_segments,
    )


def _dispatch_search(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    if args.search_operation in {"type-text", "type"}:
        payload = dispatch_type_text(args, repo_root, index_path)
        if args.search_operation == "type":
            payload = dict(payload)
            payload["migration"] = "use 'search type-text'; this alias remains for compatibility"
        return payload
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
    return result


def _dispatch_evidence(
    args: argparse.Namespace, repo_root: Path, index_path: Path | None
) -> Mapping[str, Any]:
    import sqlite3

    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        if args.kind == "theorem":
            return query_v3_theorem_evidence(connection, args.name, limit=args.limit)
        if args.kind == "artifact":
            return {
                "schema": "ladon-proofir-v3-artifact-evidence-v1",
                "artifact": args.name,
                "rows": query_v3_artifacts(connection, args.name, limit=args.limit),
            }
        if args.kind == "triage":
            return {
                "schema": "ladon-proofir-v3-triage-v1",
                "rows": query_v3_triage(connection, limit=args.limit),
            }
        return _dispatch_stored_derivation(connection, args)


def _dispatch_stored_derivation(
    connection: Any, args: argparse.Namespace
) -> Mapping[str, Any]:
    """Run a bounded native derivation query over one stored artifact."""
    if args.kind == "route" and not args.start:
        raise ProofSearchIndexError("route evidence requires --start")
    target_text = _parse_typed_statement(args.end)
    start_text = _parse_typed_statement(args.start) if args.kind == "route" else None
    row = connection.execute(
        "SELECT artifact_kind,canonical_json FROM proofir_v3_artifacts "
        "WHERE content_artifact_id=?",
        (args.name,),
    ).fetchone()
    if row is None:
        raise ProofSearchIndexError(
            f"stored derivation artifact not found: {args.name}"
        )
    if row[0] != "proofir.derivation":
        raise ProofSearchIndexError(
            "stored evidence artifact is not a proofir.derivation"
        )
    try:
        artifact = validate_envelope(json.loads(row[1])).to_dict()
    except (json.JSONDecodeError, ProofIRV3Error) as exc:
        raise ProofSearchIndexError(
            f"stored derivation artifact is invalid: {exc}"
        ) from exc
    target = _resolve_statement_ref(target_text, artifact)
    start = (
        _resolve_statement_ref(start_text, artifact) if start_text is not None else None
    )
    bounds = _derivation_query_bounds(args.limit)
    if args.kind == "route":
        return navigation_path(artifact, start, target, bounds=bounds)
    if args.kind == "slice":
        return complete_derivation_slice(artifact, target, bounds=bounds)
    return analyze_alternatives(artifact, target, bounds=bounds)


def _parse_typed_statement(value: str | None) -> str:
    """Parse the CLI's deliberately narrow typed statement reference syntax."""
    if (
        not isinstance(value, str)
        or not value.startswith("statement:")
        or not value[10:]
    ):
        raise ProofSearchIndexError(
            "derivation query references must be typed as statement:<local-id>"
        )
    return value[10:]


def _resolve_statement_ref(
    local_id: str, artifact: Mapping[str, Any]
) -> dict[str, str]:
    """Accept both bare local IDs and producer-prefixed IDs in CLI fixtures."""
    subjects = artifact.get("subjectRefs", [])
    available = {
        row.get("localId")
        for row in subjects
        if isinstance(row, Mapping) and row.get("kind") == "statement"
    }
    candidates = (local_id, f"statement:{local_id}")
    for candidate in candidates:
        if candidate in available:
            return {"kind": "statement", "localId": candidate}
    return {"kind": "statement", "localId": local_id}


def _derivation_query_bounds(limit: int) -> DerivationQueryBounds:
    """Translate the CLI result cap into finite native query resource bounds."""
    return DerivationQueryBounds(
        max_depth=min(limit, 64),
        max_visited_refs=limit,
        max_evaluated_steps=limit,
        max_premise_slots=limit,
        max_alternatives=limit,
        max_output_bytes=max(1024, limit * 4096),
    )


def _add_repository_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Lean repository owning the index.",
    )
    parser.add_argument(
        "--index",
        dest="index_path",
        help="Override the default <repo>/.ladon/index/proof-search.sqlite path.",
    )


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Result representation.",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Result path, or - for standard output.",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Write bounded JSON progress records to standard error.",
    )


def _write_payload(
    payload: Mapping[str, Any],
    *,
    output: str,
    output_format: str,
) -> None:
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
    lines = _render_header(payload)
    lines.extend(_render_core_rows(payload))
    lines.extend(_render_evidence_sections(payload))
    lines.extend(_render_warnings(payload))
    return "\n".join(lines) + "\n"


def _render_header(payload: Mapping[str, Any]) -> list[str]:
    operation = str(payload.get("operation", "index"))
    lines = [
        f"proof-search {operation}: {payload.get('status', 'unknown')}",
        f"path: {payload.get('indexPath', 'unavailable')}",
    ]
    for key, label in (
        ("generationIdentity", "generation"),
        ("freshness", "freshness"),
        ("evidenceStatus", "evidence"),
        ("databaseBytes", "bytes"),
        ("elapsedSeconds", "elapsed_seconds"),
    ):
        if payload.get(key) is not None:
            lines.append(f"{label}: {payload[key]}")
    counts = payload.get("counts")
    if isinstance(counts, Mapping):
        lines.append(
            "counts: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts))
        )
    return lines


def _render_core_rows(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    rows = payload.get("rows", payload.get("results"))
    if isinstance(rows, list):
        lines.extend(_render_query_rows(rows))
        lines.append(f"returned: {payload.get('returned', len(rows))}")
        lines.append(f"truncated: {str(bool(payload.get('truncated'))).lower()}")
    return lines


def _render_evidence_sections(payload: Mapping[str, Any]) -> list[str]:
    lines = _render_tabular_sections(payload)
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
        lines.append(
            f"paths: returned={len(paths)} minimum_depth={payload.get('minimumDepth')}"
        )
        for path in paths:
            if isinstance(path, Mapping):
                names = " -> ".join(
                    str(node.get("nodeId"))
                    for node in path.get("nodes", [])
                    if isinstance(node, Mapping)
                )
                lines.append(
                    f"- {path.get('pathId', '?')} depth={path.get('depth', '?')}: {names}"
                )
    return lines


def _render_coverage(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    coverage = payload.get("coverage")
    if isinstance(coverage, Mapping):
        lines.append(
            f"coverage: {json.dumps(coverage, sort_keys=True, ensure_ascii=False)}"
        )
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
            f"- {name} [{row.get('kind', 'unknown')}; "
            f"{row.get('authority', 'unknown')}] {location}"
        )
    return rendered


def _bounded_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be an integer") from exc
    if parsed < 1 or parsed > 1000:
        raise argparse.ArgumentTypeError("limit must be between 1 and 1000")
    return parsed


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


__all__ = ["build_proof_search_parser", "proof_search_main"]
