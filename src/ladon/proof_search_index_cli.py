"""Index command dispatch for the installed proof-search CLI."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    inspect_proof_search_index,
    query_proof_search_index,
    update_proof_search_index,
)
from ladon.proof_search_lifecycle import apply_prune, list_indexes, preview_prune


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
    if args.index_operation == "update":
        return update_proof_search_index(repo_root, index_path=index_path).payload
    if args.index_operation == "list":
        return list_indexes(repo_root, directory=args.directory, limit=args.limit)
    if args.index_operation == "prune":
        return _dispatch_prune(args, repo_root)
    if args.index_operation == "status":
        payload = inspect_proof_search_index(
            repo_root, index_path=index_path, verify_sources=not args.no_verify_sources,
            changed_limit=1000 if args.changed else 5,
        )
        return {
            **payload, "detailsRequested": bool(args.details),
            "changedRequested": bool(args.changed),
        }
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


def _dispatch_prune(args: argparse.Namespace, repo_root: Path) -> Mapping[str, Any]:
    if args.apply:
        if (
            args.preview_file is None or args.select or args.keep
            or args.older_than_days is not None or args.directory is not None
        ):
            raise ProofSearchIndexError("--apply requires --preview-file and no new selectors")
        return apply_prune(repo_root, args.preview_file)
    if args.preview_file is not None:
        raise ProofSearchIndexError("--preview-file is only valid with --apply")
    return preview_prune(
        repo_root, directory=args.directory, selected=tuple(args.select),
        older_than_days=args.older_than_days, keep=tuple(args.keep),
    )
