"""Read-only CLI queries for stored ProofIR and semantic registry evidence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.evidence_receipt_readers import derivation_query_receipt
from ladon.proof_search_index import ProofSearchIndexError, default_proof_search_index_path
from ladon.proof_search_semantic_cli import dispatch_semantic_evidence
from ladon.proofir_derivation import (
    DerivationQueryBounds,
    _fit_output,
    analyze_alternatives,
    complete_derivation_slice,
    navigation_path,
)
from ladon.proofir_triage_cli import proofir_triage_payload
from ladon.proofir_v3 import ProofIRV3Error, validate_envelope
from ladon.proofir_v3_queries import query_v3_artifacts, query_v3_theorem_evidence


def dispatch_evidence(
    args: Any,
    repo_root: Path,
    index_path: Path | None,
) -> Mapping[str, Any]:
    """Dispatch one bounded read from the lexical or semantic evidence store."""

    if args.kind.startswith("semantic-"):
        return dispatch_semantic_evidence(args, repo_root)
    path = index_path or default_proof_search_index_path(repo_root)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        if args.kind == "theorem":
            try:
                return query_v3_theorem_evidence(connection, args.name, limit=args.limit)
            except (ValueError, ProofIRV3Error) as error:
                raise ProofSearchIndexError(
                    str(error), exit_class="operational", code="invalid-stored-evidence-receipt",
                ) from error
        if args.kind == "artifact":
            return {
                "schema": "ladon-proofir-v3-artifact-evidence-v1",
                "artifact": args.name,
                "rows": query_v3_artifacts(connection, args.name, limit=args.limit),
            }
        if args.kind == "triage":
            return proofir_triage_payload(connection, args.limit)
        return _dispatch_stored_derivation(connection, args)


def _dispatch_stored_derivation(connection: Any, args: Any) -> Mapping[str, Any]:
    """Run a bounded native derivation query over one stored artifact."""

    if args.kind == "route" and not args.start:
        raise ProofSearchIndexError("route evidence requires --start")
    target_text = _parse_typed_statement(args.end)
    start_text = _parse_typed_statement(args.start) if args.kind == "route" else None
    checked = _read_stored_derivation(connection, args.name)
    artifact = checked.to_dict()
    target = _resolve_statement_ref(target_text, artifact)
    start = _resolve_statement_ref(start_text, artifact) if start_text is not None else None
    bounds = _derivation_query_bounds(args.limit)
    if args.kind == "route":
        result = navigation_path(artifact, start, target, bounds=bounds)
    elif args.kind == "slice":
        result = complete_derivation_slice(artifact, target, bounds=bounds)
    else:
        result = analyze_alternatives(artifact, target, bounds=bounds)
    request = {
        "queryKind": result["queryKind"], "artifactRef": checked.content_id,
        "targetRef": target, "startRef": start, "bounds": bounds.to_dict(),
    }
    result["evidenceReceipt"] = derivation_query_receipt(
        checked.content_id, request, invalid=result["status"] == "invalid",
    )
    return _fit_output(result, bounds.max_output_bytes)


def _read_stored_derivation(connection: Any, artifact_ref: str) -> Any:
    """Validate stored content against the exact lookup owner before traversal."""

    row = connection.execute(
        "SELECT artifact_kind,canonical_json FROM proofir_v3_artifacts "
        "WHERE content_artifact_id=?",
        (artifact_ref,),
    ).fetchone()
    if row is None:
        raise ProofSearchIndexError(f"stored derivation artifact not found: {artifact_ref}")
    if row[0] != "proofir.derivation":
        raise ProofSearchIndexError("stored evidence artifact is not a proofir.derivation")
    try:
        checked = validate_envelope(json.loads(row[1]))
    except (json.JSONDecodeError, ProofIRV3Error) as exc:
        raise ProofSearchIndexError(f"stored derivation artifact is invalid: {exc}") from exc
    if checked.content_id != artifact_ref:
        raise ProofSearchIndexError("stored derivation artifact content owner does not match its lookup identity")
    return checked


def _parse_typed_statement(value: str | None) -> str:
    if not isinstance(value, str) or not value.startswith("statement:") or not value[10:]:
        raise ProofSearchIndexError(
            "derivation query references must be typed as statement:<local-id>"
        )
    return value[10:]


def _resolve_statement_ref(local_id: str, artifact: Mapping[str, Any]) -> dict[str, str]:
    """Accept both bare local IDs and producer-prefixed IDs in CLI fixtures."""

    subjects = artifact.get("subjectRefs", [])
    available = {
        row.get("localId")
        for row in subjects
        if isinstance(row, Mapping) and row.get("kind") == "statement"
    }
    for candidate in (local_id, f"statement:{local_id}"):
        if candidate in available:
            return {"kind": "statement", "localId": candidate}
    return {"kind": "statement", "localId": local_id}


def _derivation_query_bounds(limit: int) -> DerivationQueryBounds:
    return DerivationQueryBounds(
        max_depth=min(limit, 64),
        max_visited_refs=limit,
        max_evaluated_steps=limit,
        max_premise_slots=limit,
        max_alternatives=limit,
        max_output_bytes=max(1024, limit * 4096),
    )


__all__ = ["dispatch_evidence"]
