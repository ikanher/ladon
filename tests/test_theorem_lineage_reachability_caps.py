from __future__ import annotations

from test_theorem_lineage_closure import IDENTITY, THEOREM, _database

from ladon.theorem_lineage_query import LineageQuery, query_lineage


def test_traversal_work_cap_uses_one_probe_to_report_omitted_adjacency():
    connection = _database(
        [(THEOREM, False), ("Fixture.a", False), ("Fixture.b", False)],
        [(THEOREM, "Fixture.a", "value"), (THEOREM, "Fixture.b", "type")],
    )

    result = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_traversal_edges=1),
    )

    assert result["acquisition"]["traversalWorkLimitReached"] is True
    assert result["truncation"]["traversalWorkLimited"] is True
    assert result["truncated"] is True


def test_reverse_direction_terminates_on_cycles_and_uses_minimum_depth():
    nodes = [(name, False) for name in
             (THEOREM, "Fixture.a", "Fixture.b", "Fixture.c")]
    edges = [
        ("Fixture.a", THEOREM, "value"),
        ("Fixture.b", "Fixture.a", "type"),
        ("Fixture.a", "Fixture.b", "value"),
        ("Fixture.c", "Fixture.b", "value"),
    ]
    connection = _database(nodes, edges)

    result = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", direction="dependencies"),
    )

    assert result["acquisition"]["distinctNodesExpanded"] <= len(nodes)
    assert result["routes"]
    assert all(len(route["nodes"]) == route["depth"] + 1 for route in result["routes"])


def test_route_limit_does_not_change_distinct_reachability_population():
    names = [THEOREM, "Fixture.a", "Fixture.b", "Fixture.join"]
    edges = [
        (THEOREM, "Fixture.a", "value"),
        (THEOREM, "Fixture.b", "type"),
        ("Fixture.a", "Fixture.join", "value"),
        ("Fixture.b", "Fixture.join", "value"),
    ]
    connection = _database([(name, False) for name in names], edges)
    small = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_routes=1),
    )
    large = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_routes=20),
    )

    assert {node["name"] for node in small["nodes"]} == {
        node["name"] for node in large["nodes"]
    }
    assert small["acquisition"] == large["acquisition"]
    assert small["returned"]["uniqueTypedRouteEdges"] <= large["returned"]["uniqueTypedRouteEdges"]


def test_unreturned_route_probe_does_not_consume_route_edge_cap():
    connection = _database(
        [(THEOREM, False), ("Fixture.a", False), ("Fixture.b", False)],
        [(THEOREM, "Fixture.a", "value"), (THEOREM, "Fixture.b", "type")],
    )

    result = query_lineage(
        connection, IDENTITY,
        LineageQuery(
            theorem=THEOREM,
            boundary="project",
            max_routes=1,
            max_edges=1,
        ),
    )

    assert len(result["routes"]) == 1
    assert result["returned"]["routeEdgeOccurrences"] == 1
    assert result["truncation"]["routeLimited"] is True
    assert result["truncation"]["edgeLimited"] is False
