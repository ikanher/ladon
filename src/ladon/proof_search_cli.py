"""Ordinary installed CLI for Ladon's persistent proof-search index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from ladon.cli_execution import (
    EXIT_INVOCATION,
    EXIT_OPERATIONAL,
    EXIT_SUCCESS,
    write_output_file,
)
from ladon.proof_search_index import (
    DEFAULT_MAX_INDEX_BYTES,
    SUPPORTED_INDEX_SCOPES,
    ProofSearchIndexError,
    build_proof_search_index,
    inspect_proof_search_index,
    query_proof_search_index,
    default_proof_search_index_path,
)
from ladon.proofir_queries import query_artifact_evidence, query_theorem_dossier
from ladon.proofir_dag_store import query_dag_routes
from ladon.proofir_triage import query_proofir_triage
from ladon.semantic_build_mode import SemanticBuildRequest
from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_consumers import ConsumerRequest, query_consumers
from ladon.proof_search_constructor import ConstructorRequest, constructor_coverage


def build_proof_search_parser() -> argparse.ArgumentParser:
    """Build the caller-neutral proof-search command tree."""

    parser = argparse.ArgumentParser(
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
    build.add_argument("--mode", choices=("lexical", "semantic", "hybrid"), default="lexical")
    build.add_argument("--lean-timeout", type=float, default=120.0)
    build.add_argument("--semantic-completeness", choices=("allow-partial", "require-complete"), default="allow-partial")

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
    evidence.add_argument("kind", choices=("theorem", "artifact", "route", "dag", "triage"))
    evidence.add_argument("name")
    evidence.add_argument("--dag")
    evidence.add_argument("--start")
    evidence.add_argument("--end")
    evidence.add_argument("--reverse", action="store_true")
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
    search = operations.add_parser("search", help="Run the versioned name-search contract.")
    search_commands = search.add_subparsers(dest="search_operation", required=True)
    name = search_commands.add_parser("name", help="Search declarations by normalized name.")
    _add_repository_options(name)
    _add_output_options(name)
    name.add_argument("--text", required=True)
    name.add_argument("--query-mode", choices=("all", "any", "phrase"), default="all")
    name.add_argument("--exclude", action="append", default=[])
    name.add_argument("--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository")
    name.add_argument("--root", action="append", default=[])
    name.add_argument("--limit", type=_bounded_limit, default=20)
    name.add_argument("--freshness", choices=("verify", "stored"), default="verify")
    type_search = search_commands.add_parser("type", help="Search declarations by type pattern.")
    _add_repository_options(type_search)
    _add_output_options(type_search)
    type_search.add_argument("--pattern", required=True)
    type_search.add_argument("--module")
    type_search.add_argument("--namespace")
    type_search.add_argument("--package")
    type_search.add_argument("--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository")
    type_search.add_argument("--limit", type=_bounded_limit, default=20)
    type_search.add_argument("--diagnostic-limit", type=_bounded_limit, default=0)
    type_search.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    explain = operations.add_parser("explain", help="Explain a bounded candidate/goal difference.")
    _add_repository_options(explain)
    _add_output_options(explain)
    explain.add_argument("--goal", required=True)
    explain.add_argument("--candidate", required=True)
    explain.add_argument("--module")
    explain.add_argument("--assumption", action="append", default=[])
    explain.add_argument("--suggestion-cap", type=_bounded_limit, default=10)
    explain.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    consumers = operations.add_parser("consumers", help="Find bounded declaration consumers.")
    _add_repository_options(consumers)
    _add_output_options(consumers)
    consumers.add_argument("--declaration", required=True)
    consumers.add_argument("--kind", choices=("all", "type", "value"), default="all")
    consumers.add_argument("--ownership", choices=("all", "project", "external"), default="all")
    consumers.add_argument("--limit", type=_bounded_limit, default=100)
    constructor = operations.add_parser("constructor", help="Inspect bounded constructor field coverage.")
    _add_repository_options(constructor)
    _add_output_options(constructor)
    constructor.add_argument("--structure", required=True)
    constructor.add_argument("--module")
    constructor.add_argument("--argument", action="append", default=[])
    constructor.add_argument("--limit", type=_bounded_limit, default=100)
    constructor.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    return parser


def proof_search_main(argv: Sequence[str]) -> int:
    """Run one proof-search index operation with stable exit behavior."""

    parser = build_proof_search_parser()
    try:
        args = parser.parse_args(list(argv))
        payload = _dispatch(args)
        _write_payload(payload, output=args.output, output_format=args.output_format)
        return EXIT_SUCCESS
    except ProofSearchIndexError as exc:
        print(f"ladon proof-search: invalid invocation: {exc}", file=sys.stderr)
        return EXIT_INVOCATION
    except (OSError, UnicodeError) as exc:
        print(f"ladon proof-search: operational failure: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL


def _dispatch(args: argparse.Namespace) -> Mapping[str, Any]:
    """Dispatch a parsed index operation."""

    repo_root = Path(args.repo_root)
    index_path = Path(args.index_path) if args.index_path else None
    if getattr(args, "index_operation", None):
        return _dispatch_index(args, repo_root, index_path)
    if args.proof_search_operation == "evidence":
        return _dispatch_evidence(args, repo_root, index_path)
    if args.proof_search_operation == "search":
        return _dispatch_search(args, repo_root, index_path)
    if args.proof_search_operation == "explain":
        return analyze_difference(DifferenceRequest(args.goal, args.candidate, args.module, tuple(args.assumption), args.suggestion_cap, args.freshness))
    if args.proof_search_operation == "consumers":
        import sqlite3
        path = index_path or default_proof_search_index_path(repo_root)
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return query_consumers(connection, ConsumerRequest(args.declaration, args.kind, args.ownership, args.limit))
    if args.proof_search_operation == "constructor":
        return constructor_coverage(ConstructorRequest(args.structure, args.module, tuple(args.argument), args.limit, args.freshness), ())
    raise ProofSearchIndexError(
        f"unsupported proof-search operation {getattr(args, 'index_operation', args.proof_search_operation)!r}"
    )


def _dispatch_index(args: argparse.Namespace, repo_root: Path, index_path: Path | None) -> Mapping[str, Any]:
    if args.index_operation == "build":
        mode = SemanticBuildRequest(args.mode, args.lean_timeout, args.semantic_completeness)
        payload = build_proof_search_index(repo_root, index_path=index_path, max_index_bytes=args.max_index_mib * 1024 * 1024, build_mode=mode.mode, lean_timeout=mode.lean_timeout, semantic_completeness=mode.completeness).payload
        return payload
    if args.index_operation == "status":
        return inspect_proof_search_index(repo_root, index_path=index_path, verify_sources=not args.no_verify_sources)
    return query_proof_search_index(
        repo_root,
        index_path=index_path,
        text=args.text,
        scope=args.scope,
        roots=tuple(args.root),
        limit=args.limit,
        query_mode=args.query_mode,
        exclusions=tuple(args.exclude),
    )


def _dispatch_search(args: argparse.Namespace, repo_root: Path, index_path: Path | None) -> Mapping[str, Any]:
    if args.search_operation == "type":
        import sqlite3
        path = index_path or default_proof_search_index_path(repo_root)
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return query_type_shortlist(connection, TypeSearchRequest(pattern=args.pattern, module=args.module, namespace=args.namespace, package=args.package, scope=args.scope, limit=args.limit, diagnostic_limit=args.diagnostic_limit, freshness=args.freshness))
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
        freshness=args.freshness,
    )
    result = dict(payload)
    result["operation"] = "search-name"
    result["schema"] = "ladon-proof-search-name-result-v2"
    result["matchMode"] = "exact-name+fts" if args.text else "bounded"
    result["normalization"] = "semantic-name-segments-v1"
    result.pop("rows", None)
    return result


def _dispatch_evidence(args: argparse.Namespace, repo_root: Path, index_path: Path | None) -> Mapping[str, Any]:
    import sqlite3
    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        if args.kind == "theorem":
            return query_theorem_dossier(connection, args.name)
        if args.kind == "artifact":
            return query_artifact_evidence(connection, args.name, args.limit)
        if args.kind == "triage":
            return query_proofir_triage(connection, limit=args.limit)
        return _dispatch_route(connection, args)


def _dispatch_route(connection: Any, args: argparse.Namespace) -> Mapping[str, Any]:
    dag_id = args.dag or args.name.split(":", 1)[0]
    start = args.start or (args.name.split(":", 1)[-1] if ":" in args.name else None)
    if not start:
        raise ProofSearchIndexError("route evidence requires --start")
    return query_dag_routes(connection, dag_id, start, args.end, reverse=args.reverse, max_routes=args.limit)


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
    lines = [f"proof-search {operation}: {payload.get('status', 'unknown')}", f"path: {payload.get('indexPath', 'unavailable')}"]
    for key, label in (("generationIdentity", "generation"), ("freshness", "freshness"), ("evidenceStatus", "evidence"), ("databaseBytes", "bytes"), ("elapsedSeconds", "elapsed_seconds")):
        if payload.get(key) is not None:
            lines.append(f"{label}: {payload[key]}")
    counts = payload.get("counts")
    if isinstance(counts, Mapping):
        lines.append("counts: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
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
    lines = [f"{section}: returned={value.get('returned', 0)} matched={value.get('matched', 0)} truncated={str(bool(value.get('truncated'))).lower()}"]
    for item in value.get("rows", []):
        if isinstance(item, Mapping):
            identity = item.get("surfaceId") or item.get("claimId") or item.get("replayId") or item.get("diagnosticId") or "<unknown>"
            lines.append(f"- {identity} [{item.get('status', item.get('surfaceStatus', item.get('reason', 'observed')))}]")
    return lines


def _render_paths(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    paths = payload.get("paths")
    if isinstance(paths, list):
        lines.append(f"paths: returned={len(paths)} minimum_depth={payload.get('minimumDepth')}")
        for path in paths:
            if isinstance(path, Mapping):
                names = " -> ".join(str(node.get("nodeId")) for node in path.get("nodes", []) if isinstance(node, Mapping))
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
    lines = [f"warning: {row.get('message', row)}" for row in payload.get("warnings", []) if isinstance(row, Mapping)]
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
