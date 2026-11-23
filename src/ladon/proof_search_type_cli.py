"""CLI transport helpers for the bounded type-text search contract."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Any

from ladon.proof_search_index import (
    ProofSearchIndexError,
    _metadata,
    _open_readonly,
    _require_query_schema,
    default_proof_search_index_path,
)
from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist


def dispatch_type_text(
    args: Any, repo_root: Path, index_path: Path | None
) -> dict[str, Any]:
    try:
        request = TypeSearchRequest(
            pattern=getattr(args, "pattern", None),
            module=args.module,
            namespace=args.namespace,
            package=args.package,
            scope=args.scope,
            roots=tuple(args.root),
            limit=args.limit,
            diagnostic_limit=args.diagnostic_limit,
            freshness=args.freshness,
            fragments=tuple(getattr(args, "fragment", ()) or ()),
        )
    except ValueError as exc:
        raise ProofSearchIndexError(str(exc)) from exc
    evidence = type_text_freshness(args, repo_root, index_path)
    path = index_path or default_proof_search_index_path(repo_root)
    with closing(_open_readonly(path)) as connection:
        connection.execute("BEGIN")
        metadata = _metadata(connection)
        _require_query_schema(metadata)
        if evidence and evidence.get("generationIdentity") != metadata.get("generationIdentity"):
            raise ProofSearchIndexError("index generation changed after freshness verification")
        payload = query_type_shortlist(
            connection,
            request,
            verifier=(lambda _candidates, _pattern: {}) if args.freshness == "verify" else None,
        )
    payload.update(
        generationIdentity=metadata.get("generationIdentity"), indexPath=str(path.resolve()),
        generationIdentityMeaning="stored rows in the queried index",
        freshnessStatus="verified-fresh" if evidence else "unchecked",
        currentGenerationIdentity=evidence.get("currentGenerationIdentity"),
    )
    if evidence:
        payload["freshnessEvidence"] = evidence
    return payload


def type_text_freshness(
    args: Any, repo_root: Path, index_path: Path | None
) -> dict[str, Any]:
    if args.freshness != "verify":
        return {}
    from ladon.proof_search_freshness import inspect_freshness

    status = inspect_freshness(repo_root, index_path=index_path)
    if status.get("freshness") != "fresh":
        raise ProofSearchIndexError("type-text index is stale or unavailable")
    fields = (
        "generationIdentity", "currentGenerationIdentity", "sourceFingerprint",
        "configurationFingerprint", "toolchainIdentity", "helperIdentity", "indexSchema",
    )
    return {key: status.get(key) for key in fields if status.get(key) is not None}


__all__ = ["dispatch_type_text", "type_text_freshness"]
