"""Offline projection using the archived observation, never a live identity."""
from __future__ import annotations

from dataclasses import replace

from ladon.evidence_dimensions import validate_transition
from ladon.evidence_receipt import build_evidence_receipt, validate_evidence_receipt
from ladon.proof_search_history import open_history_snapshot
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_schema import evidence_schema_generation
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
            schema_generation=evidence_schema_generation(metadata["schemaGeneration"]),
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
            "schema": _history_schema(result),
            "selectionBasis": "historical-snapshot", "snapshotId": entry["snapshotId"],
            "indexPath": str(index), "currentAssociation": "not-established",
            "freshness": "historical", "historicalAssociation": status["status"],
            "originalObservation": dict(metadata),
            "refresh": {"policy": "never", "performed": False},
        })
        _mark_historical_coverage(result)
        return _write_result(result, args)


def _history_schema(result):
    if str(result.get("schema", "")).endswith("-v2"):
        return "ladon-theorem-lineage-history-result-v2"
    return "ladon-theorem-lineage-history-result-v1"


def _mark_historical_coverage(result):
    coverage = result.get("coverage")
    if isinstance(coverage, dict) and isinstance(coverage.get("sourceClosure"), dict):
        coverage["sourceClosure"].update({
            "freshness": "historical",
            "currentAssociation": "not-established",
        })
        if result.get("projection") == "closure":
            from ladon.theorem_lineage_closure import refresh_closure_fingerprint

            refresh_closure_fingerprint(result)
    receipt = result.get("evidenceReceipt")
    if not isinstance(receipt, dict):
        return
    parent = validate_evidence_receipt(receipt)
    child = replace(parent, source_freshness="not-assessed")
    validate_transition(parent, child, projection_kind="sqlite-row")
    result["evidenceReceipt"] = build_evidence_receipt(
        subject=receipt["subject"],
        environment_ref=receipt["environmentRef"],
        check_run_ref=receipt["checkRunRef"],
        limitations=[
            *receipt["limitations"],
            "historical-snapshot-current-source-freshness-not-assessed",
        ],
        **child.__dict__,
    )
