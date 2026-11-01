from __future__ import annotations

import hashlib
import json

from test_theorem_lineage_closure import IDENTITY, THEOREM, _database

from ladon.theorem_lineage_history import _mark_historical_coverage
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery


def test_historical_coverage_mutation_refreshes_closure_fingerprint():
    connection = _database(
        [(THEOREM, False), ("Fixture.dep", False)],
        [(THEOREM, "Fixture.dep", "value")],
    )
    result = project_lineage(
        connection,
        IDENTITY,
        ProjectionQuery(LineageQuery(theorem=THEOREM), view="closure"),
    )
    live_fingerprint = result["projectionFingerprint"]

    _mark_historical_coverage(result)

    assert result["projectionFingerprint"] != live_fingerprint
    assert result["coverage"]["sourceClosure"]["freshness"] == "historical"
    payload = {
        "selection": result["query"]["selection"],
        "edgeKind": result["query"]["edgeKind"],
        "includeGenerated": result["query"]["includeGenerated"],
        "maxNodes": result["bounds"]["maxNodes"],
        "maxEdges": result["bounds"]["maxEdges"],
        "nodes": [row["name"] for row in result["nodes"]],
        "edges": [
            (row["source"], row["target"], row["kind"])
            for row in result["edges"]
        ],
        "coverage": result["coverage"],
    }
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    assert result["projectionFingerprint"] == expected
