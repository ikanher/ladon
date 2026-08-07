from __future__ import annotations

from test_theorem_lineage_query import lineage_database

from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery


def test_store_query_projection_preserves_authority_and_contiguous_edges() -> None:
    connection, identity = lineage_database()
    result = project_lineage(
        connection,
        identity,
        ProjectionQuery(
            lineage=LineageQuery(theorem="Demo.target", boundary="trust"),
            view="graph",
        ),
    )
    assert result["authority"] == "lean_environment"
    assert result["closureId"]
    for route in result["routes"]:
        assert route["nodes"][0] == route["root"]
        assert route["nodes"][-1] == "Demo.target"
        assert len(route["edges"]) == len(route["nodes"]) - 1
        assert all(
            {"source": source, "target": target} in result["edges"]
            for source, target in zip(route["nodes"], route["nodes"][1:])
        )
    assert "alternative proofs" in result["nonclaim"]
