"""Deterministic populated SQLite fixtures for first-hand hardening packets."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Any

from ladon.proof_search_schema import create_proof_search_schema

THEOREM = "Fixture.Theorem.target"
CLOSURE_ID = "fixture-closure-v1"


def populated_connection(*, edge_fanout: int = 8, edge_layers: int = 6) -> sqlite3.Connection:
    """Create one deterministic populated index without any filesystem state."""

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    _seed_base(connection)
    seed_lineage(connection, edge_fanout=edge_fanout, edge_layers=edge_layers)
    connection.commit()
    return connection


def coverage_connection(mode: str) -> sqlite3.Connection:
    """Create lexical, partial, or complete semantic coverage variants."""

    if mode not in {"lexical", "partial", "complete"}:
        raise ValueError("unsupported fixture coverage mode")
    connection = populated_connection(edge_fanout=4, edge_layers=3)
    if mode != "lexical":
        status = "partial" if mode == "partial" else "complete"
        total_known = int(mode == "complete")
        connection.execute(
            "UPDATE evidence_coverage SET status=?, authority='fixture', reason=?, observed=?, total_known=? WHERE collection='declaration_dependencies'",
            (status, mode, int(mode == "complete"), total_known),
        )
        connection.execute(
            "UPDATE evidence_coverage SET status=?, authority='fixture', reason=?, observed=?, total_known=? WHERE collection='structure_fields'",
            (status, mode, int(mode == "complete"), total_known),
        )
    connection.commit()
    return connection


def owner_projection_fixture() -> dict[str, Any]:
    """Return a two-owner selected/global projection fixture."""

    return {
        "selectedModules": ["Fixture.OwnerA", "Fixture.OwnerB"],
        "coReachableModules": ["Fixture.Shared"],
        "globalCandidateCount": 10000,
        "globalSamples": [f"Global.candidate{index}" for index in range(3)],
    }


def _seed_base(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO modules(name,path,package,generated,source_sha256,source_bytes,line_count,evidence_status) VALUES (?,?,?,?,?,?,?,?)",
        ("Fixture", "Fixture.lean", "fixture", 0, "sha-fixture", 1, 1, "lexical-fallback"),
    )
    declarations = [
        ("fixture-target-id", THEOREM, "target", "Fixture", "theorem"),
        ("fixture-constructor-id", "Fixture.Record", "Record", "Fixture", "structure"),
    ]
    for declaration_id, name, candidate, module, kind in declarations:
        connection.execute(
            """INSERT INTO declarations(
                id,name,candidate_name,name_casefold,name_segments,namespace,kind,module,package,path,
                line,column_number,start_offset,end_offset,block_sha256,type_text,type_text_bytes,
                type_text_truncated,type_status,authority,privacy,locality,structure_name,doc_text,
                rendered_type,conclusion_text,fingerprint,head,arity,is_proposition,semantic_status,
                helper_identity,lean_identity
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                declaration_id, name, candidate, name.casefold(), candidate, "Fixture", kind, module,
                "fixture", "Fixture.lean", 1, 1, 0, 1, "block", "P", 1, 0,
                "lexical-signature", "lexical_text", "public", "global", None, "", "P", "P", "fp", "", 0,
                1, "unavailable", "", "",
            ),
        )
    connection.execute(
        "INSERT INTO symbols(name,declaration_id,kind,ownership) VALUES (?,?,?,?)",
        (THEOREM, "fixture-target-id", "theorem", "project"),
    )
    connection.execute(
        "INSERT INTO symbols(name,declaration_id,kind,ownership) VALUES (?,?,?,?)",
        ("Fixture.Record", "fixture-constructor-id", "structure", "project"),
    )
    connection.execute(
        "INSERT INTO structures(declaration_id,name,module,authority) VALUES (?,?,?,?)",
        ("fixture-constructor-id", "Fixture.Record", "Fixture", "lexical_text"),
    )
    connection.execute(
        "INSERT INTO evidence_coverage(collection,status,authority,reason,observed,total_known) VALUES (?,?,?,?,?,?)",
        ("declaration_dependencies", "not-populated", "fixture", "baseline", 0, 0),
    )
    connection.execute(
        "INSERT INTO evidence_coverage(collection,status,authority,reason,observed,total_known) VALUES (?,?,?,?,?,?)",
        ("structure_fields", "not-populated", "fixture", "baseline", 0, 0),
    )


def seed_lineage(connection: sqlite3.Connection, *, edge_fanout: int = 8, edge_layers: int = 6) -> None:
    """Seed a bounded, high-fan-out closure with stable names and edge counts."""

    if edge_fanout < 2 or edge_layers < 2:
        raise ValueError("lineage fixture needs at least two fanout and layers")
    nodes, layer_names = _lineage_nodes(edge_fanout, edge_layers)
    connection.execute(
        """INSERT INTO lineage_closures(
            closure_id,theorem_name,theorem_module,theorem_path,plan_identity,
            semantic_closure_fingerprint,repository,source_fingerprint,configuration_fingerprint,
            toolchain_identity,helper_identity,base_generation_identity,schema_generation,authority,
            semantic_status,active,unsupported_facets_json,node_count,edge_count,created_identity
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (CLOSURE_ID, THEOREM, "Fixture", "Fixture.lean", "plan-v1", "closure-v1", "/fixture", "source", "config", "lean", "helper", "base", "schema", "lean_environment", "complete", 1, "[]", 0, 0, "fixture"),
    )
    connection.executemany(
        """INSERT INTO lineage_nodes(
            closure_id,name,owner_module,kind,project_owned,external_frontier,
            compiler_generated,declared_axiom,unsafe,source_path,source_line,source_column,
            source_status,type_fingerprint,value_fingerprint
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ((CLOSURE_ID, name, module, kind, project, external, 0, int(kind == "axiom"), 0, None, None, None, "unavailable", None, None) for name, module, kind, project, external in nodes),
    )
    edges = _lineage_edges(layer_names, edge_fanout)
    connection.executemany(
        "INSERT INTO lineage_edges(closure_id,source,target,kind,target_owner_module,target_kind) VALUES (?,?,?,?,?,?)",
        edges,
    )
    connection.execute(
        "UPDATE lineage_closures SET node_count=?,edge_count=? WHERE closure_id=?",
        (len(nodes), len(edges), CLOSURE_ID),
    )
    connection.executemany(
        "INSERT INTO lineage_trust(closure_id,kind,scope,target) VALUES (?,?,?,?)",
        ((CLOSURE_ID, "axiom", "declaration", f"External.axiom{index}") for index in range(edge_fanout)),
    )


def _lineage_nodes(edge_fanout: int, edge_layers: int) -> tuple[list[tuple[Any, ...]], list[list[str]]]:
    nodes = [(THEOREM, "Fixture", "theorem", 1, 0)]
    layers: list[list[str]] = []
    for layer in range(edge_layers):
        names = [f"Fixture.layer{layer}.node{index}" for index in range(edge_fanout**min(layer + 1, 3))]
        layers.append(names)
        nodes.extend((name, "Fixture", "declaration", 1, 0) for name in names)
    nodes.extend((f"External.axiom{index}", "External", "axiom", 0, 1) for index in range(edge_fanout))
    return nodes, layers


def _lineage_edges(layers: list[list[str]], edge_fanout: int) -> list[tuple[str, str, str, str, str, str]]:
    edges: list[tuple[str, str, str, str, str, str]] = []
    previous = [THEOREM]
    for targets in layers:
        edges.extend(
            (CLOSURE_ID, source, targets[(source_index * edge_fanout + offset) % len(targets)], "value", "Fixture", "declaration")
            for source_index, source in enumerate(previous)
            for offset in range(edge_fanout)
        )
        previous = targets
    edges.extend(
        (CLOSURE_ID, source, f"External.axiom{index % edge_fanout}", "type", "External", "axiom")
        for index, source in enumerate(previous[:edge_fanout])
    )
    return edges


def fixture_fingerprint(connection: sqlite3.Connection) -> str:
    """Hash deterministic row counts and edge samples, not SQLite page layout."""

    counts: dict[str, int] = {}
    for table in ("modules", "declarations", "symbols", "lineage_nodes", "lineage_edges"):
        counts[table] = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    edge_sample = [tuple(row) for row in connection.execute("SELECT source,target,kind FROM lineage_edges ORDER BY source,target,kind LIMIT 32")]
    payload = repr((counts, edge_sample)).encode()
    return hashlib.sha256(payload).hexdigest()


def table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return counts for baseline evidence and test diagnostics."""

    tables = ("modules", "declarations", "symbols", "lineage_closures", "lineage_nodes", "lineage_edges")
    return {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}


def database_resource_snapshot(connection: sqlite3.Connection, tables: tuple[str, ...]) -> dict[str, Any]:
    """Capture baseline page/free-space/object-byte evidence without production hooks."""

    page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
    freelist_count = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
    try:
        object_rows = connection.execute("SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY name").fetchall()
    except sqlite3.Error:
        object_rows = []
    return {
        "pageSize": page_size,
        "pageCount": page_count,
        "allocatedBytes": page_size * page_count,
        "freelistPages": freelist_count,
        "objectBytes": {str(name): int(size or 0) for name, size in object_rows},
        "rowCounts": {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in sorted(tables)},
    }


def query_plan(connection: sqlite3.Connection, sql: str, parameters: tuple[Any, ...] = ()) -> list[str]:
    """Return normalized SQLite plan rows for a baseline assertion."""

    return [" ".join(str(value) for value in row) for row in connection.execute("EXPLAIN QUERY PLAN " + sql, parameters)]
