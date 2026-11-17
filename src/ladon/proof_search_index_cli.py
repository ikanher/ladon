"""Index command dispatch for the installed proof-search CLI."""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    if args.index_operation in {"migrate", "ideas-sync", "ideas"}:
        return _dispatch_ideas(args, repo_root, index_path)
    if args.index_operation == "build":
        return _build_index(args, repo_root, index_path)
    if args.index_operation == "update":
        return update_proof_search_index(
            repo_root, index_path=index_path,
            max_history_bytes=args.max_history_mib * 1024 * 1024 if args.max_history_mib else None,
            archive_history=args.archive_history,
        ).payload
    if args.index_operation == "history-cleanup":
        return _dispatch_history_cleanup(args, repo_root, index_path)
    if args.index_operation == "history":
        from ladon.proof_search_history import list_history

        return list_history(repo_root, index_path=index_path, limit=args.limit, offset=args.offset)
    if args.index_operation == "list":
        return list_indexes(repo_root, directory=args.directory, limit=args.limit)
    if args.index_operation == "prune":
        return _dispatch_prune(args, repo_root)
    if args.index_operation in {"freshness", "status"}:
        return _dispatch_status(args, repo_root, index_path)
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


def _stage_reporter():
    started = time.monotonic()

    def report(fields):
        row = {"schema": "ladon-proof-search-progress-v1", "operation": "index.build",
               "elapsedSeconds": round(time.monotonic() - started, 6), **fields}
        print(json.dumps(row, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)

    return report


def _dispatch_ideas(args, repo_root, index_path):
    import sqlite3

    from ladon.idea_migration import migrate_index, read_ideas, sync_ideas
    from ladon.sqlite_publication import PublicationLockBusy

    try:
        if args.index_operation == "ideas":
            return read_ideas(repo_root, index_path=index_path, limit=args.limit)
        operation = migrate_index if args.index_operation == "migrate" else sync_ideas
        return operation(repo_root, index_path=index_path)
    except (sqlite3.Error, ValueError, PublicationLockBusy) as error:
        raise ProofSearchIndexError(str(error), exit_class="operational") from error


def _build_index(args, repo_root, index_path):
    return build_proof_search_index(
        repo_root,
        index_path=index_path,
        max_index_bytes=args.max_index_mib * 1024 * 1024,
        **({"progress": _stage_reporter()} if args.progress else {}),
    ).payload


def _dispatch_status(args, repo_root, index_path):
    if args.index_operation == "freshness":
        from ladon.proof_search_freshness import inspect_freshness

        return inspect_freshness(repo_root, index_path=index_path,
                                 expected_generation=args.expected_generation)
    payload = inspect_proof_search_index(
        repo_root, index_path=index_path, verify_sources=not args.no_verify_sources,
        changed_limit=1000 if args.changed else 5,
    )
    return {
        **payload, "detailsRequested": bool(args.details),
        "changedRequested": bool(args.changed),
    }


def _dispatch_history_cleanup(args, repo_root, index_path):
    from ladon.proof_search_history_cleanup import apply_history_cleanup, preview_history_cleanup

    if args.apply:
        if args.preview_file is None or args.snapshot or args.all_registered:
            raise ProofSearchIndexError("--apply requires --preview-file and no new selection")
        from ladon.investigation import load_plan

        return apply_history_cleanup(repo_root, load_plan(args.preview_file), index_path=index_path)
    if args.preview_file is not None:
        raise ProofSearchIndexError("--preview-file requires --apply")
    return preview_history_cleanup(repo_root, index_path=index_path,
                                   snapshots=args.snapshot, all_registered=args.all_registered)
