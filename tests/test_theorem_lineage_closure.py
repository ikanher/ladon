from __future__ import annotations

import sqlite3

from ladon.proof_search_schema import create_proof_search_schema
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery
from ladon.theorem_lineage_store import LineageIdentity

THEOREM = "Fixture.target"
CLOSURE = "closure-test-v1"
IDENTITY = LineageIdentity(
    repository="/fixture",
    source_fingerprint="source",
    configuration_fingerprint="config",
    toolchain_identity="lean",
    base_generation_identity="base",
    helper_identity="helper",
    schema_generation="schema",
)


def _database(nodes: list[tuple[str, bool]], edges: list[tuple[str, str, str]], sccs=()):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    connection.execute(
        """INSERT INTO lineage_closures(
            closure_id,theorem_name,theorem_module,theorem_path,plan_identity,
            semantic_closure_fingerprint,repository,source_fingerprint,
            configuration_fingerprint,toolchain_identity,helper_identity,
            base_generation_identity,schema_generation,authority,semantic_status,
            active,unsupported_facets_json,node_count,edge_count,created_identity
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (CLOSURE, THEOREM, "Fixture", None, "plan", "fingerprint", "/fixture",
         "source", "config", "lean", "helper", "base", "schema",
         "lean_environment", "complete", 1, "[]", len(nodes), len(edges), CLOSURE),
    )
    connection.executemany(
        """INSERT INTO lineage_nodes(
            closure_id,name,owner_module,kind,project_owned,external_frontier,
            compiler_generated,declared_axiom,unsafe,source_status
        ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        ((CLOSURE, name, "Fixture", "theorem", 1, 0, int(generated), 0, 0,
          "unavailable") for name, generated in nodes),
    )
    connection.executemany(
        """INSERT INTO lineage_edges(
            closure_id,source,target,kind,target_owner_module,target_kind
        ) VALUES (?,?,?,?,?,?)""",
        ((CLOSURE, source, target, kind, "Fixture", "theorem")
         for source, target, kind in edges),
    )
    connection.executemany(
        "INSERT INTO lineage_scc_members VALUES (?,?,?,?)",
        ((CLOSURE, component, member, int(cyclic))
         for component, member, cyclic in sccs),
    )
    connection.commit()
    return connection


def _diamond(layers: int = 20):
    names = [THEOREM]
    expected_edges = set()
    previous = [THEOREM]
    for layer in range(layers):
        current = [f"Fixture.L{layer}.a", f"Fixture.L{layer}.b"]
        names.extend(current)
        expected_edges.update((source, target, "value")
                              for source in previous for target in current)
        previous = current
    expected_edges.update((source, THEOREM, "value") for source in previous)
    return names, sorted(expected_edges)


def _closure(connection, *, max_nodes=100, max_edges=400, max_routes=20,
             include_generated=True, edge_kind="all"):
    return project_lineage(
        connection,
        IDENTITY,
        ProjectionQuery(
            lineage=LineageQuery(
                theorem=THEOREM,
                max_nodes=max_nodes,
                max_edges=max_edges,
                max_routes=max_routes,
                include_generated=include_generated,
                edge_kind=edge_kind,
            ),
            view="closure",
        ),
    )


def _node_names(result):
    return {row["name"] for row in result["nodes"]}


def _typed_edges(result):
    return {(row["source"], row["target"], row["kind"])
            for row in result["edges"]}


def test_closure_matches_input_sets_on_shared_twenty_layer_graph():
    names, edges = _diamond()
    connection = _database([(name, False) for name in names], edges)

    result = _closure(connection)

    assert result["status"] == "available"
    assert _node_names(result) == set(names)
    assert _typed_edges(result) == set(edges)
    assert all(source in _node_names(result) and target in _node_names(result)
               for source, target, _kind in _typed_edges(result))
    assert result["returned"]["nodes"] == len(names)
    assert result["returned"]["edges"] == len(edges)
    assert result["truncated"] is False
    assert result["coverage"]["selectedGraph"]["status"] == "complete"


def test_closure_ignores_route_limit_and_keeps_parallel_typed_edges_and_sccs():
    nodes = [(name, False) for name in (THEOREM, "Fixture.a", "Fixture.b", "Fixture.disconnected")]
    edges = [
        (THEOREM, "Fixture.a", "value"),
        ("Fixture.a", "Fixture.b", "type"),
        ("Fixture.a", "Fixture.b", "value"),
        ("Fixture.b", "Fixture.b", "value"),
        ("Fixture.disconnected", "Fixture.a", "type"),
    ]
    sccs = [("scc-b", "Fixture.b", True)]
    connection = _database(nodes, edges, sccs)

    one = _closure(connection, max_routes=1)
    many = _closure(connection, max_routes=100)

    assert _node_names(one) == {name for name, _generated in nodes}
    assert _typed_edges(one) == set(edges)
    assert _typed_edges(one) == _typed_edges(many)
    assert one["returned"]["edges"] == len(one["edges"]) == len(edges)
    assert sum(edge[:2] == ("Fixture.a", "Fixture.b") for edge in _typed_edges(one)) == 2
    assert next(node for node in one["nodes"] if node["name"] == "Fixture.b")["sccId"] == "scc-b"


def test_closure_caps_are_exact_and_keep_returned_edges_endpoint_closed():
    names, edges = _diamond(layers=2)
    connection = _database([(name, False) for name in names], edges)
    exact = _closure(connection, max_nodes=len(names), max_edges=len(edges))

    assert exact["truncated"] is False
    assert exact["coverage"]["selectedGraph"]["status"] == "complete"


def test_node_cap_reports_partial_endpoint_closed_population():
    names, edges = _diamond(layers=2)
    connection = _database([(name, False) for name in names], edges)
    over_node = _closure(connection, max_nodes=len(names) - 1, max_edges=len(edges))

    assert over_node["truncated"] is True
    assert over_node["coverage"]["selectedGraph"]["status"] == "partial"
    included = _node_names(over_node)
    assert all(source in included and target in included
               for source, target, _kind in _typed_edges(over_node))
    assert over_node["returned"]["nodes"] == len(over_node["nodes"])
    assert over_node["returned"]["edges"] == len(over_node["edges"])


def test_edge_cap_reports_partial_typed_edge_population():
    names, edges = _diamond(layers=2)
    connection = _database([(name, False) for name in names], edges)
    over_edge = _closure(connection, max_nodes=len(names), max_edges=len(edges) - 1)

    assert over_edge["truncated"] is True
    assert over_edge["coverage"]["selectedGraph"]["status"] == "partial"
    assert over_edge["returned"]["edges"] == len(over_edge["edges"])


def test_generated_filter_removes_incident_edges_without_a_synthetic_bridge():
    nodes = [(name, name == "Fixture.generated") for name in
             (THEOREM, "Fixture.a", "Fixture.generated", "Fixture.c", "Fixture.isolated")]
    edges = [
        (THEOREM, "Fixture.a", "value"),
        ("Fixture.a", "Fixture.generated", "value"),
        ("Fixture.generated", "Fixture.c", "value"),
    ]
    connection = _database(nodes, edges)

    result = _closure(connection, include_generated=False)

    assert _node_names(result) == {THEOREM, "Fixture.a", "Fixture.c", "Fixture.isolated"}
    assert _typed_edges(result) == {(THEOREM, "Fixture.a", "value")}
    assert ("Fixture.a", "Fixture.c", "value") not in _typed_edges(result)
    assert result["coverage"]["selectedGraph"]["omissions"]["generatedNodes"] == 1
