"""Replay the retained gradient lineage closure by its stored identity only."""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from ladon.theorem_lineage_cli import _write_result
from ladon.theorem_lineage_history import _mark_historical_coverage
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery
from ladon.theorem_lineage_store import LineageIdentity


THEOREM = (
    "Mf.Optimization.StochasticApproximation."
    "gradientProcess_local_power_noise_average_clt"
)


def main() -> int:
    args = _parser().parse_args()
    started = time.monotonic()
    uri = f"file:{Path(args.index).resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        closure = _closure_record(connection)
        identity = _stored_identity(closure)
        query = LineageQuery(
            theorem=THEOREM,
            max_nodes=args.max_nodes,
            max_edges=args.max_edges,
        )
        result = project_lineage(
            connection, identity, ProjectionQuery(lineage=query, view="closure")
        )
        _historicalize(result)
        status = _write_result(
            result,
            argparse.Namespace(
                format="json",
                output=args.output,
                max_output_bytes=args.max_output_bytes,
            ),
        )
        if status != 0:
            raise RuntimeError(f"closure projection ended with status {status}")
        actual = json.loads(Path(args.output).read_text(encoding="utf-8"))
        summary = _compare_rows(connection, closure, actual)
        summary.update({
            "closureId": closure["closure_id"],
            "sourceFingerprint": closure["source_fingerprint"],
            "configurationFingerprint": closure["configuration_fingerprint"],
            "toolchainIdentity": closure["toolchain_identity"],
            "maxNodes": args.max_nodes,
            "maxEdges": args.max_edges,
            "maxOutputBytes": args.max_output_bytes,
            "outputBytes": Path(args.output).stat().st_size,
            "wallSeconds": round(time.monotonic() - started, 6),
        })
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["matchesStoredRows"] else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-nodes", type=int, default=100000)
    parser.add_argument("--max-edges", type=int, default=200000)
    parser.add_argument("--max-output-bytes", type=int, default=33554432)
    return parser


def _closure_record(connection: sqlite3.Connection) -> dict:
    row = connection.execute(
        "SELECT * FROM lineage_closures WHERE theorem_name=? AND active=1",
        (THEOREM,),
    ).fetchone()
    if row is None:
        raise RuntimeError("retained field closure is missing")
    return dict(row)


def _stored_identity(row: dict) -> LineageIdentity:
    return LineageIdentity(
        repository=row["repository"],
        source_fingerprint=row["source_fingerprint"],
        configuration_fingerprint=row["configuration_fingerprint"],
        toolchain_identity=row["toolchain_identity"],
        base_generation_identity=row["base_generation_identity"],
        helper_identity=row["helper_identity"],
        schema_generation=row["schema_generation"],
    )


def _historicalize(result: dict) -> None:
    result.update({
        "schema": "ladon-theorem-lineage-history-result-v2",
        "selectionBasis": "historical-snapshot",
        "freshness": "historical",
        "currentAssociation": "not-established",
    })
    _mark_historical_coverage(result)


def _compare_rows(
    connection: sqlite3.Connection, closure: dict, result: dict
) -> dict:
    closure_id = closure["closure_id"]
    expected_nodes = {row[0] for row in connection.execute(
        "SELECT name FROM lineage_nodes WHERE closure_id=?", (closure_id,)
    )}
    expected_edges = {(source, target, kind) for source, target, kind in connection.execute(
        "SELECT source,target,kind FROM lineage_edges WHERE closure_id=?", (closure_id,)
    )}
    actual_nodes = {row["name"] for row in result["nodes"]}
    actual_edges = {(row["source"], row["target"], row["kind"])
                    for row in result["edges"]}
    matches = expected_nodes == actual_nodes and expected_edges == actual_edges
    return {
        "status": result["status"],
        "freshness": result["freshness"],
        "currentAssociation": result["currentAssociation"],
        "receiptSourceFreshness": result["evidenceReceipt"]["sourceFreshness"],
        "selectedGraphCoverage": result["coverage"]["selectedGraph"]["status"],
        "sourceClosureStatus": result["coverage"]["sourceClosure"]["status"],
        "storedNodes": len(expected_nodes),
        "returnedNodes": len(actual_nodes),
        "missingNodes": len(expected_nodes - actual_nodes),
        "extraNodes": len(actual_nodes - expected_nodes),
        "storedTypedEdges": len(expected_edges),
        "returnedTypedEdges": len(actual_edges),
        "missingTypedEdges": len(expected_edges - actual_edges),
        "extraTypedEdges": len(actual_edges - expected_edges),
        "returnedCountsAgree": (
            result["returned"]["nodes"] == len(result["nodes"])
            and result["returned"]["edges"] == len(result["edges"])
        ),
        "truncated": result["truncated"],
        "matchesStoredRows": matches,
    }


if __name__ == "__main__":
    raise SystemExit(main())
