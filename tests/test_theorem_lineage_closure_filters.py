from __future__ import annotations

from test_theorem_lineage_closure import (
    IDENTITY,
    THEOREM,
    _closure,
    _database,
    _node_names,
    _typed_edges,
)

from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery
from ladon.theorem_lineage_store import LineageIdentity


def test_edge_kind_filter_preserves_only_that_typed_edge_population():
    nodes = [(name, False) for name in
             (THEOREM, "Fixture.a", "Fixture.b", "Fixture.disconnected")]
    edges = [
        (THEOREM, "Fixture.a", "value"),
        ("Fixture.a", "Fixture.b", "type"),
        ("Fixture.a", "Fixture.b", "value"),
        ("Fixture.disconnected", "Fixture.b", "value"),
    ]
    result = _closure(_database(nodes, edges), edge_kind="type")

    assert _node_names(result) == {name for name, _generated in nodes}
    assert _typed_edges(result) == {("Fixture.a", "Fixture.b", "type")}
    assert result["coverage"]["selectedGraph"]["selectedTypedEdges"] == 1
    assert result["coverage"]["selectedGraph"]["omissions"]["filteredTypedEdges"] == 3


def test_generated_target_remains_the_required_closure_anchor():
    nodes = [(THEOREM, True), ("Fixture.a", False)]
    edges = [(THEOREM, "Fixture.a", "value")]
    result = _closure(_database(nodes, edges), include_generated=False)

    assert _node_names(result) == {THEOREM, "Fixture.a"}
    assert _typed_edges(result) == set(edges)
    assert result["coverage"]["selectedGraph"]["omissions"]["generatedNodes"] == 0


def test_closure_projection_fails_closed_on_stale_identity():
    connection = _database([(THEOREM, False)], [])
    stale = LineageIdentity(
        repository=IDENTITY.repository,
        source_fingerprint="changed",
        configuration_fingerprint=IDENTITY.configuration_fingerprint,
        toolchain_identity=IDENTITY.toolchain_identity,
        base_generation_identity=IDENTITY.base_generation_identity,
        helper_identity=IDENTITY.helper_identity,
        schema_generation=IDENTITY.schema_generation,
    )

    result = project_lineage(
        connection, stale,
        ProjectionQuery(lineage=LineageQuery(theorem=THEOREM), view="closure"),
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "stale-source"
    assert "nodes" not in result
