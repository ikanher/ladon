from __future__ import annotations

from test_theorem_lineage_closure import IDENTITY, THEOREM, _database, _diamond

from ladon.theorem_lineage_query import LineageQuery, query_lineage


def test_depth_cap_probes_for_eligible_unseen_neighbor_but_not_exhausted_frontier():
    target = _database(
        [(THEOREM, False), ("Fixture.a", False), ("Fixture.b", False)],
        [(THEOREM, "Fixture.a", "value"), ("Fixture.a", "Fixture.b", "value")],
    )
    exhausted = _database(
        [(THEOREM, False), ("Fixture.a", False)],
        [(THEOREM, "Fixture.a", "value")],
    )

    cut = query_lineage(
        target, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_depth=1),
    )
    complete = query_lineage(
        exhausted, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_depth=1),
    )

    assert cut["truncation"]["depthLimited"] is True
    assert complete["truncation"]["depthLimited"] is False


def test_generated_declarations_do_not_bridge_route_reachability():
    connection = _database(
        [(THEOREM, False), ("Fixture.a", False), ("Fixture.generated", True),
         ("Fixture.c", False)],
        [(THEOREM, "Fixture.a", "value"),
         ("Fixture.a", "Fixture.generated", "value"),
         ("Fixture.generated", "Fixture.c", "value")],
    )

    result = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", include_generated=False),
    )

    route_nodes = {name for route in result["routes"] for name in route["nodes"]}
    assert "Fixture.generated" not in route_nodes
    assert "Fixture.c" not in route_nodes


def test_route_work_on_shared_diamond_is_bounded_by_unique_graph_rows():
    names, edges = _diamond()
    connection = _database([(name, False) for name in names], edges)

    result = query_lineage(
        connection, IDENTITY,
        LineageQuery(theorem=THEOREM, boundary="project", max_depth=41,
                     max_nodes=len(names), max_routes=1, max_traversal_edges=len(edges)),
    )

    assert result["acquisition"]["distinctNodesExpanded"] == len(names)
    assert result["acquisition"]["typedAdjacencyRowsExamined"] <= len(edges)
    assert result["acquisition"]["traversalWorkLimitReached"] is False
