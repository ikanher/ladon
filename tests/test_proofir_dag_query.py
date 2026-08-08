from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_dag_store import query_dag_routes


def _route_db(tmp_path: Path, edges: list[tuple[str, str, str]], *, statuses: dict[str, tuple[str, list[str]]] | None = None) -> sqlite3.Connection:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def root : Nat := 1\n", encoding="utf-8")
    statuses = statuses or {}
    nodes = sorted({node for edge in edges for node in edge[:2]})
    rows = []
    for node in nodes:
        status, authority = statuses.get(node, ("established", ["external"]))
        key = "importedFacts" if node.startswith("fact") else ("producedFacts" if node.startswith("claim") else "obligations")
        rows.append((key, {"id": node, "status": status, "authority": authority}))
    grouped = {"importedFacts": [], "obligations": [], "producedFacts": []}
    for key, row in rows:
        grouped[key].append(row)
    payload = {"artifactKind": "proof_ir_v2_obligation_dag", "schemaVersion": 2, "dagId": "dag.query", **grouped,
               "edges": [{"source": source, "target": target, "kind": kind, "obligationId": "obl.route"} for source, target, kind in edges]}
    (repo / "dag.json").write_text(json.dumps(payload), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["dag.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    return sqlite3.connect(result.index_path)


def test_forward_and_reverse_routes_are_endpoint_correct(tmp_path: Path) -> None:
    db = _route_db(tmp_path, [("fact.start", "obl.one", "uses"), ("obl.one", "claim.end", "produces"), ("fact.other", "claim.other", "produces")])
    try:
        forward = query_dag_routes(db, "dag.query", "fact.start", "claim.end")
        reverse = query_dag_routes(db, "dag.query", "claim.end", "fact.start", reverse=True)
    finally:
        db.close()
    assert [[node["nodeId"] for node in path["nodes"]] for path in forward["paths"]] == [["fact.start", "obl.one", "claim.end"]]
    assert [[node["nodeId"] for node in path["nodes"]] for path in reverse["paths"]] == [["claim.end", "obl.one", "fact.start"]]
    assert all(node["nodeId"] not in {"fact.other", "claim.other"} for node in forward["routes"])


def test_unreachable_is_distinct_from_truncated(tmp_path: Path) -> None:
    db = _route_db(tmp_path, [("fact.start", "claim.end", "produces")])
    try:
        result = query_dag_routes(db, "dag.query", "fact.start", "claim.missing")
    finally:
        db.close()
    assert result["reachable"] is False
    assert result["truncated"] is False
    assert result["minimumDepth"] is None


def test_diamond_paths_are_shortest_and_selected_subgraph_is_deduplicated(tmp_path: Path) -> None:
    db = _route_db(tmp_path, [("fact.start", "obl.a", "uses"), ("fact.start", "obl.b", "uses"), ("obl.a", "claim.end", "produces"), ("obl.b", "claim.end", "produces")])
    try:
        result = query_dag_routes(db, "dag.query", "fact.start", "claim.end", max_routes=2)
    finally:
        db.close()
    assert result["minimumDepth"] == 2
    assert len(result["paths"]) == 2
    assert len(result["selectedSubgraph"]["nodes"]) == 4


def test_cycles_terminate_and_bounds_are_validated(tmp_path: Path) -> None:
    db = _route_db(tmp_path, [("fact.start", "obl.loop", "uses"), ("obl.loop", "fact.start", "produces"), ("obl.loop", "claim.end", "produces")])
    try:
        result = query_dag_routes(db, "dag.query", "fact.start", "claim.end", max_depth=8)
    finally:
        db.close()
    assert result["reachable"] is True
    assert result["paths"][0]["depth"] == 2
    with pytest.raises(ValueError, match="bounds"):
        query_dag_routes(sqlite3.connect(":memory:"), "dag.query", "start", "end", max_depth=0)

