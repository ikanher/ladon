"""CLI transport for the verified-discovery vertical slice."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_index import ProofSearchIndexError
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.verified_discovery import (
    DiscoveryRequest,
    discover_candidates,
    semantic_checker,
    semantic_scratch_replayer,
)


def register_discover_parser(
    operations: Any,
    add_repository_options: Any,
    add_output_options: Any,
    bounded_limit: Any,
    positive_integer: Any,
    scopes: Any,
) -> None:
    discover = operations.add_parser("discover", help="Check a bounded candidate set against one exact goal.")
    add_repository_options(discover)
    add_output_options(discover)
    discover.add_argument("--module", required=True)
    discover.add_argument("--goal", required=True)
    discover.add_argument("--candidate", action="append", required=True)
    discover.add_argument("--local", action="append", default=[], help="Typed local as NAME:TYPE; repeatable.")
    discover.add_argument("--max-candidates", type=bounded_limit, default=20)
    discover.add_argument("--batch-size", type=bounded_limit, default=8)
    discover.add_argument("--scope", choices=sorted(scopes), default="repository")
    discover.add_argument("--root", action="append", default=[])
    discover.add_argument("--freshness", choices=("stored", "verify"), default="stored")
    discover.add_argument("--timeout-seconds", type=float, default=120.0)
    discover.add_argument("--max-output-mib", type=positive_integer, default=8)
    discover.add_argument("--max-rss-mib", type=positive_integer, default=2048)
    discover.add_argument("--toolchain-mode", choices=("ambient", "explicit"), default="ambient")
    discover.add_argument("--lake-path", type=Path)
    discover.add_argument("--lean-path", type=Path)


def dispatch_discover(args: argparse.Namespace, repo_root: Path) -> dict[str, Any]:
    try:
        toolchain = resolve_toolchain_context(
            repo_root.resolve(),
            lake_path=args.lake_path,
            lean_path=args.lean_path,
            selection_mode=args.toolchain_mode,
        )
        request = DiscoveryRequest(
            repo_root.resolve(),
            args.module,
            args.goal,
            tuple(parse_local_context(item) for item in args.local),
            args.max_candidates,
            args.batch_size,
            args.timeout_seconds,
            args.max_output_mib * 1024 * 1024,
            args.max_rss_mib * 1024 * 1024,
            args.scope,
            tuple(args.root),
            args.freshness,
            toolchain.context_identity if toolchain else None,
        )
    except (ValueError, LeanToolchainError) as error:
        raise ProofSearchIndexError(str(error)) from error
    rows = [{"candidateName": candidate} for candidate in args.candidate]
    return discover_candidates(
        request,
        rows,
        semantic_checker(request, toolchain),
        semantic_scratch_replayer(request, toolchain),
        lambda names: _batch_results(request, names, toolchain),
    )


def _batch_results(
    request: DiscoveryRequest, names: tuple[str, ...], toolchain: Any
) -> dict[str, Mapping[str, Any]]:
    batch = check_semantic_candidates(request_to_semantic(request, toolchain), names)
    if batch.status != "available":
        diagnostic = batch.diagnostic or {"code": "batch-failed"}
        return {name: {"status": "unassessed", "diagnostic": diagnostic} for name in names}
    return {str(row["candidate"]): dict(row) for row in batch.rows}


def request_to_semantic(request: DiscoveryRequest, toolchain: Any) -> Any:
    from ladon.semantic_candidate_worker import SemanticCandidateRequest

    return SemanticCandidateRequest(
        request.repo_root,
        request.module,
        request.goal,
        "batch-placeholder",
        timeout_seconds=request.timeout_seconds,
        max_output_bytes=request.max_output_bytes,
        max_rss_bytes=request.max_rss_bytes,
        toolchain=toolchain,
    )


def parse_local_context(value: str) -> dict[str, str]:
    if ":" not in value:
        raise ValueError("local context must use NAME:TYPE")
    name, type_text = value.split(":", 1)
    if not name or not type_text:
        raise ValueError("local context must use NAME:TYPE")
    return {"name": name, "type": type_text}


__all__ = ["dispatch_discover", "parse_local_context", "register_discover_parser"]
