"""CLI transport for the verified-discovery vertical slice."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_index import ProofSearchIndexError
from ladon.verified_discovery import (
    DiscoveryRequest,
    discover_candidates,
    semantic_checker,
    semantic_scratch_replayer,
)


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
        )
    except (ValueError, LeanToolchainError) as error:
        raise ProofSearchIndexError(str(error)) from error
    rows = [{"candidateName": candidate} for candidate in args.candidate]
    return discover_candidates(
        request,
        rows,
        semantic_checker(request, toolchain),
        semantic_scratch_replayer(request, toolchain),
    )


def parse_local_context(value: str) -> dict[str, str]:
    if ":" not in value:
        raise ValueError("local context must use NAME:TYPE")
    name, type_text = value.split(":", 1)
    if not name or not type_text:
        raise ValueError("local context must use NAME:TYPE")
    return {"name": name, "type": type_text}


__all__ = ["dispatch_discover", "parse_local_context"]
