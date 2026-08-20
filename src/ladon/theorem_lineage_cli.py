"""CLI orchestration for database-backed theorem lineage."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from ladon.cli_execution import EXIT_OPERATIONAL, EXIT_SUCCESS, write_output_file
from ladon.proof_search_index import (
    capture_repository_snapshot,
    default_proof_search_index_path,
    inspect_proof_search_index,
)
from ladon.sqlite_publication import (
    acquire_publication_lock,
    release_publication_lock,
)
from ladon.theorem_capsule_planning import plan_theorem_capsule
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery
from ladon.theorem_lineage_summary import summarize_lineage
from ladon.theorem_lineage_store import LineageIdentity, ingest_theorem_lineage


def run_lineage_command(args: Any) -> int:
    repo_root = Path(args.repo_root).resolve()
    index = _index_path(args, repo_root)
    lock = None
    try:
        if args.refresh != "never":
            lock = acquire_publication_lock(index)
        return _run_lineage_command(args, repo_root, index)
    finally:
        if lock is not None:
            release_publication_lock(lock)


def _run_lineage_command(args: Any, repo_root: Path, index: Path) -> int:
    """Run lineage while any mutation-capable invocation owns publication."""

    status = inspect_proof_search_index(repo_root, index_path=index, verify_sources=True)
    if status.get("status") != "available":
        _progress("terminal", f"error:index-unavailable:{status.get('reason', 'unknown')}")
        raise RuntimeError(f"proof-search index unavailable: {status.get('reason', 'unknown')}")
    snapshot = capture_repository_snapshot(repo_root)
    identity = _identity(repo_root, snapshot, status)
    connection = sqlite3.connect(index)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    terminal_emitted = False
    try:
        closure_status = _closure_status(connection, identity, args.theorem)
        should_refresh = _should_refresh(args.refresh, closure_status)
        ingest_result = None
        if should_refresh:
            _progress("planning", args.theorem)
            plan = plan_theorem_capsule(repo_root, args.theorem, timeout_seconds=args.timeout, max_rss_bytes=_max_rss_bytes(args))
            _progress("persisting", args.theorem)
            ingest_result = ingest_theorem_lineage(
                connection,
                plan.payload,
                identity,
                max_bytes=int(args.max_database_mib) * 1024 * 1024,
            )
        elif args.refresh == "never" and closure_status["status"] != "fresh":
            result = {"schema": "ladon-theorem-lineage-result-v1", "operation": "lineage", "status": "unavailable", "theorem": args.theorem, "reason": closure_status.get("reason", closure_status["status"]), "refresh": {"policy": args.refresh, "performed": False}, "nonclaim": "No lexical or alternative-proof fallback is used."}
            code = _write_result(result, args)
            terminal_emitted = True
            return code
        result = summarize_lineage(connection, identity, args.theorem) if args.view == "summary" else _project(connection, identity, args)
        result["indexPath"] = str(index)
        result["refresh"] = {"policy": args.refresh, "performed": should_refresh}
        result["limits"] = {"completeDatabaseMaxBytes": int(args.max_database_mib) * 1024 * 1024}
        if ingest_result is not None:
            result["publication"] = ingest_result
        _progress("rendering", args.theorem)
        code = _write_result(result, args)
        terminal_emitted = True
        return code
    except Exception as exc:
        if not terminal_emitted:
            _progress("terminal", f"error:{type(exc).__name__}")
        raise
    finally:
        connection.close()


def _index_path(args: Any, repo_root: Path) -> Path:
    return Path(args.index).resolve() if args.index else default_proof_search_index_path(repo_root)


def _identity(repo_root: Path, snapshot: Any, status: dict[str, Any]) -> LineageIdentity:
    return LineageIdentity(
        repository=str(repo_root), source_fingerprint=snapshot.source_fingerprint,
        configuration_fingerprint=snapshot.configuration_fingerprint,
        toolchain_identity=snapshot.toolchain_identity,
        base_generation_identity=str(status.get("generationIdentity") or snapshot.generation_identity),
        helper_identity="lexical-navigation-v1;theorem-lineage-v1",
        schema_generation=str(status.get("schemaGeneration") or "sqlite-v2-fts1-lineage1"),
    )


def _should_refresh(policy: str, status: dict[str, Any]) -> bool:
    return policy == "always" or (policy == "missing" and status["status"] == "unavailable") or (policy == "stale" and status["status"].startswith("stale"))


def _project(connection: sqlite3.Connection, identity: LineageIdentity, args: Any) -> dict[str, Any]:
    view = "routes" if args.view == "spines" else args.view
    query = LineageQuery(
        theorem=args.theorem, boundary=args.boundary, roots=tuple(args.roots),
        edge_kind=args.edge_kind, include_generated=args.include_generated,
        max_depth=args.max_depth, max_nodes=args.max_nodes,
        max_edges=args.max_edges, max_routes=args.max_routes,
    )
    return project_lineage(connection, identity, ProjectionQuery(lineage=query, view=view))


def _closure_status(connection: sqlite3.Connection, identity: LineageIdentity, theorem: str) -> dict[str, Any]:
    from ladon.theorem_lineage_store import inspect_lineage_closure

    return inspect_lineage_closure(connection, theorem, identity)


def _write_result(result: dict[str, Any], args: Any) -> int:
    if args.format == "json":
        content = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    else:
        content = _render_text(result)
    if args.max_output_bytes is not None and len(content.encode()) > args.max_output_bytes:
        raise RuntimeError("lineage result exceeds output byte cap")
    if args.output == "-":
        sys.stdout.write(content)
    else:
        path = Path(args.output)
        if path.exists() and not path.is_file():
            raise RuntimeError(f"output is not a regular file: {path}")
        write_output_file(path, content)
    _progress("terminal", str(result.get("status", "unknown")))
    return EXIT_SUCCESS if result.get("status") == "available" else EXIT_OPERATIONAL


def _progress(phase: str, detail: str) -> None:
    print(json.dumps({"schema": "ladon-theorem-lineage-progress-v1", "phase": phase, "detail": detail}, sort_keys=True), file=sys.stderr, flush=True)


def _render_text(result: dict[str, Any]) -> str:
    lines = [f"Theorem lineage: {result.get('theorem', '')}", f"Status: {result.get('status', '')}"]
    for route in result.get("routes", []):
        lines.append("  " + " -> ".join(route["nodes"]))
    bottlenecks = result.get("bottlenecks", {}).get("chain", [])
    if bottlenecks:
        lines.append("Bottlenecks: " + " -> ".join(bottlenecks))
    if result.get("truncated"):
        lines.append("Truncated: yes")
    lines.extend(("", str(result.get("nonclaim", ""))))
    return "\n".join(lines) + "\n"


def _max_rss_bytes(args: Any) -> int | None:
    value = getattr(args, "max_rss_mib", None)
    return value * 1024 * 1024 if value is not None else None


__all__ = ["run_lineage_command"]
