"""CLI orchestration for database-backed theorem lineage."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import time
from itertools import chain
from pathlib import Path
from typing import Any

from ladon.cli_execution import EXIT_OPERATIONAL, EXIT_SUCCESS
from ladon.evidence_receipt import project_evidence_receipt
from ladon.evidence_receipt_readers import receipt_text_lines
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
from ladon.theorem_lineage_projection import (
    ProjectionQuery,
    TheoremLineageInvocationError,
    project_lineage,
)
from ladon.theorem_lineage_query import LineageQuery, lineage_query_receipt
from ladon.theorem_lineage_store import LineageIdentity, ingest_theorem_lineage
from ladon.theorem_lineage_summary import summarize_lineage


def run_lineage_command(args: Any) -> int:
    started = time.monotonic()
    repo_root = Path(args.repo_root).resolve()
    index = _index_path(args, repo_root)
    if getattr(args, "history", None) is not None:
        from ladon.theorem_lineage_history import run_historical_lineage

        return run_historical_lineage(args, repo_root, index)
    lock = None
    try:
        if args.refresh != "never":
            lock = acquire_publication_lock(index)
        return _run_lineage_command(args, repo_root, index, started)
    finally:
        if lock is not None:
            release_publication_lock(lock)


def _run_lineage_command(
    args: Any, repo_root: Path, index: Path, started: float
) -> int:
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
            result["evidenceReceipt"] = lineage_query_receipt(closure_status, args.theorem)
            code = _write_result(result, args)
            terminal_emitted = True
            return code
        result = summarize_lineage(connection, identity, args.theorem) if args.view == "summary" else _project(connection, identity, args)
        result["indexPath"] = str(index)
        result["refresh"] = {"policy": args.refresh, "performed": should_refresh}
        result["limits"] = {"completeDatabaseMaxBytes": int(args.max_database_mib) * 1024 * 1024}
        result["acquisitionElapsedSeconds"] = round(time.monotonic() - started, 6)
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
    from ladon.proof_search_schema import evidence_schema_generation

    evidence_schema = evidence_schema_generation(status.get("schemaGeneration") or "sqlite-v2-fts1-lineage1")
    return LineageIdentity(
        repository=str(repo_root), source_fingerprint=snapshot.source_fingerprint,
        configuration_fingerprint=snapshot.configuration_fingerprint,
        toolchain_identity=snapshot.toolchain_identity,
        base_generation_identity=str(status.get("generationIdentity") or snapshot.generation_identity),
        helper_identity="lexical-navigation-v1;theorem-lineage-v1",
        schema_generation=str(evidence_schema or "sqlite-v2-fts1-lineage1"),
    )


def _should_refresh(policy: str, status: dict[str, Any]) -> bool:
    return policy == "always" or (policy == "missing" and status["status"] == "unavailable") or (policy == "stale" and status["status"].startswith("stale"))


def _project(connection: sqlite3.Connection, identity: LineageIdentity, args: Any) -> dict[str, Any]:
    view = "routes" if args.view == "spines" else args.view
    if view == "closure":
        _reject_inapplicable_closure_options(args)
    query = LineageQuery(
        theorem=args.theorem,
        boundary=getattr(args, "boundary", "trust"),
        roots=tuple(getattr(args, "roots", ())),
        edge_kind=args.edge_kind, include_generated=args.include_generated,
        direction=getattr(args, "direction", "ancestry"),
        max_depth=getattr(args, "max_depth", 32), max_nodes=args.max_nodes,
        max_edges=args.max_edges, max_routes=getattr(args, "max_routes", 20),
        max_traversal_edges=getattr(args, "max_traversal_edges", 100000),
    )
    return project_lineage(
        connection,
        identity,
        ProjectionQuery(
            lineage=query,
            view=view,
            max_dominator_rows=getattr(args, "max_dominators", 100),
        ),
    )


def _reject_inapplicable_closure_options(args: Any) -> None:
    explicit = set(getattr(args, "_lineage_explicit_options", ()))
    if getattr(args, "roots", ()):
        explicit.add("roots")
    inapplicable = {
        "boundary": "--from",
        "roots": "--root",
        "direction": "--direction",
        "max_depth": "--max-depth",
        "max_routes": "--max-routes",
        "max_traversal_edges": "--max-traversal-edges",
        "max_dominators": "--max-dominators",
    }
    used = [option for key, option in inapplicable.items() if key in explicit]
    if used:
        raise TheoremLineageInvocationError(
            "--view closure does not use route selectors or route limits: "
            + ", ".join(used)
        )


def _closure_status(connection: sqlite3.Connection, identity: LineageIdentity, theorem: str) -> dict[str, Any]:
    from ladon.theorem_lineage_store import inspect_lineage_closure

    return inspect_lineage_closure(connection, theorem, identity)


def _write_result(result: dict[str, Any], args: Any) -> int:
    result = dict(result)
    result["evidenceReceipt"] = project_evidence_receipt(
        result["evidenceReceipt"], projection_kind="json-renderer",
    )
    chunks = (
        chain(
            json.JSONEncoder(ensure_ascii=False, sort_keys=True, indent=2).iterencode(result),
            ("\n",),
        )
        if args.format == "json" else (_render_text(result),)
    )
    _write_bounded_output(chunks, args.output, int(getattr(args, "max_output_bytes", None) or 33554432))
    _progress("terminal", str(result.get("status", "unknown")))
    return EXIT_SUCCESS if result.get("status") == "available" else EXIT_OPERATIONAL


def _write_bounded_output(chunks, destination: str, byte_cap: int) -> None:
    """Stage a bounded report before stdout or atomic file publication."""

    with tempfile.SpooledTemporaryFile(
        max_size=1024 * 1024, mode="w+", encoding="utf-8", newline=""
    ) as staged:
        byte_count = 0
        for chunk in chunks:
            byte_count += len(chunk.encode("utf-8"))
            if byte_count > byte_cap:
                raise RuntimeError("lineage result exceeds output byte cap")
            staged.write(chunk)
        staged.flush()
        staged.seek(0)
        if destination == "-":
            _copy_text(staged, sys.stdout)
            return
        path = Path(destination)
        if path.exists() and not path.is_file():
            raise RuntimeError(f"output is not a regular file: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
                _copy_text(staged, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary_path, path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise


def _copy_text(source, destination) -> None:
    source.seek(0)
    while chunk := source.read(65536):
        destination.write(chunk)


def _progress(phase: str, detail: str) -> None:
    print(json.dumps({"schema": "ladon-theorem-lineage-progress-v1", "phase": phase, "detail": detail}, sort_keys=True), file=sys.stderr, flush=True)


def _render_text(result: dict[str, Any]) -> str:
    lines = [f"Theorem lineage: {result.get('theorem', '')}", f"Status: {result.get('status', '')}"]
    if result.get("selectionBasis") == "historical-snapshot":
        lines.extend((f"Historical snapshot: {result['snapshotId']}",
                      f"Original association: {result['historicalAssociation']}",
                      "Current compiled association: not established"))
    lines.extend(receipt_text_lines(result.get("evidenceReceipt")))
    coverage = result.get("coverage", {})
    graph_coverage = coverage.get("selectedGraph", {})
    if graph_coverage:
        lines.append(
            "Selected graph: "
            f"{graph_coverage.get('returnedUniqueNodes', 0)}/"
            f"{graph_coverage.get('selectedUniqueNodes', 0)} nodes, "
            f"{graph_coverage.get('returnedTypedEdges', 0)}/"
            f"{graph_coverage.get('selectedTypedEdges', 0)} typed edges "
            f"({graph_coverage.get('status', 'unknown')})"
        )
        lines.append(
            "Source closure: "
            f"{coverage.get('sourceClosure', {}).get('status', 'unknown')}; "
            f"external scope: {coverage.get('externalExpansion', {}).get('scope', 'unknown')}"
        )
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
