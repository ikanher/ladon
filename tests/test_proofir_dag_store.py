from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_dag_store import query_dag_routes


def test_dag_is_normalized_and_routes_are_bounded_and_indexed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("theorem root : True := True.intro\n", encoding="utf-8")
    dag = {
        "artifactKind": "proof_ir_v2_obligation_dag", "schemaVersion": 2, "dagId": "dag.chain",
        "importedFacts": [{"id": "fact.start", "status": "established", "authority": ["lean_kernel"]}],
        "obligations": [{"id": "obl.middle", "status": "conditional", "authority": ["external"], "description": "middle"}],
        "producedFacts": [{"id": "fact.end", "status": "conditional", "authority": ["external"]}],
        "edges": [
            {"source": "fact.start", "target": "obl.middle", "kind": "uses", "obligationId": "obl.middle"},
            {"source": "obl.middle", "target": "fact.end", "kind": "produces", "obligationId": "obl.middle"},
        ],
    }
    (repo / "dag.json").write_text(json.dumps(dag), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["dag.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        forward = db.execute("EXPLAIN QUERY PLAN SELECT * FROM proofir_dag_edges WHERE dag_id=? AND source_node_id=?", ("dag.chain", "fact.start")).fetchall()
        assert any("idx_proofir_dag_edge_forward" in str(row) for row in forward)
        route = query_dag_routes(db, "dag.chain", "fact.start", "fact.end", max_depth=8)
    assert [row["nodeId"] for row in route["routes"]] == ["fact.start", "obl.middle", "fact.end"]
    assert route["routes"][1]["status"] == "conditional"


def test_dag_missing_endpoint_is_omitted_without_dangling_rows(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def x : Nat := 1\n", encoding="utf-8")
    dag = {"artifactKind": "proof_ir_v2_obligation_dag", "schemaVersion": 2, "dagId": "dag.bad",
           "importedFacts": [{"id": "start"}], "edges": [{"source": "start", "target": "missing", "kind": "uses"}]}
    (repo / "dag.json").write_text(json.dumps(dag), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["dag.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        assert db.execute("SELECT COUNT(*) FROM proofir_dag_edges").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM proofir_dags").fetchone()[0] == 0
    assert result.payload["counts"]["proofirDagOmissions"] == 1

