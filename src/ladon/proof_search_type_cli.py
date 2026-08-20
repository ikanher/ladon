"""CLI transport helpers for the bounded type-text search contract."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from ladon.proof_search_index import (
    ProofSearchIndexError,
    default_proof_search_index_path,
    inspect_proof_search_index,
)
from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist


def dispatch_type_text(
    args: Any, repo_root: Path, index_path: Path | None
) -> dict[str, Any]:
    evidence = type_text_freshness(args, repo_root, index_path)
    request = TypeSearchRequest(
        pattern=args.pattern,
        module=args.module,
        namespace=args.namespace,
        package=args.package,
        scope=args.scope,
        limit=args.limit,
        diagnostic_limit=args.diagnostic_limit,
        freshness=args.freshness,
    )
    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        payload = query_type_shortlist(
            connection,
            request,
            verifier=(lambda _candidates, _pattern: {}) if args.freshness == "verify" else None,
        )
    if evidence:
        payload["freshnessEvidence"] = evidence
    return payload


def type_text_freshness(
    args: Any, repo_root: Path, index_path: Path | None
) -> dict[str, Any]:
    if args.freshness != "verify":
        return {}
    status = inspect_proof_search_index(repo_root, index_path=index_path, verify_sources=True)
    if status.get("freshness") != "fresh":
        raise ProofSearchIndexError("type-text index is stale or unavailable")
    fields = (
        "generationIdentity", "currentGenerationIdentity", "sourceFingerprint",
        "configurationFingerprint", "toolchainIdentity", "indexSchema",
    )
    return {key: status.get(key) for key in fields if status.get(key) is not None}


__all__ = ["dispatch_type_text", "type_text_freshness"]
