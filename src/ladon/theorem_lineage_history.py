"""Offline projection using the archived observation, never a live identity."""
from __future__ import annotations

from ladon.proof_search_history import open_history_snapshot
from ladon.proof_search_index import ProofSearchIndexError
from ladon.theorem_lineage_query import lineage_query_receipt
from ladon.theorem_lineage_store import LineageIdentity
from ladon.theorem_lineage_summary import summarize_lineage


def run_historical_lineage(args, repo_root, index):
    from ladon.theorem_lineage_cli import _closure_status, _project, _write_result

    if args.refresh != "never":
        raise ProofSearchIndexError("historical selection cannot refresh; use --refresh never")
    with open_history_snapshot(repo_root, index, args.history) as (connection, entry, metadata):
        identity = LineageIdentity(
            repository=metadata["repository"],
            source_fingerprint=metadata["sourceFingerprint"],
            configuration_fingerprint=metadata["configurationFingerprint"],
            toolchain_identity=metadata["toolchainIdentity"],
            base_generation_identity=metadata["generationIdentity"],
            helper_identity="lexical-navigation-v1;theorem-lineage-v1",
            schema_generation=metadata["schemaGeneration"],
        )
        status = _closure_status(connection, identity, args.theorem)
        if status["status"] != "fresh":
            result = {
                "schema": "ladon-theorem-lineage-result-v1", "operation": "lineage",
                "status": "unavailable", "theorem": args.theorem,
                "reason": status.get("reason", status["status"]),
                "evidenceReceipt": lineage_query_receipt(status, args.theorem),
                "nonclaim": "No current or alternative-proof fallback is used.",
            }
        else:
            result = (summarize_lineage(connection, identity, args.theorem)
                      if args.view == "summary" else _project(connection, identity, args))
        result.update({
            "schema": "ladon-theorem-lineage-history-result-v1",
            "selectionBasis": "historical-snapshot", "snapshotId": entry["snapshotId"],
            "indexPath": str(index), "currentAssociation": "not-established",
            "freshness": "historical", "historicalAssociation": status["status"],
            "originalObservation": dict(metadata),
            "refresh": {"policy": "never", "performed": False},
        })
        return _write_result(result, args)
