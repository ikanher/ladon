from __future__ import annotations

from test_theorem_lineage_closure import (
    THEOREM,
    _closure,
    _database,
    _diamond,
)


def test_closure_fingerprint_and_rows_ignore_sqlite_insertion_order():
    names, edges = _diamond(layers=3)
    forward = _database([(name, False) for name in names], edges)
    reverse = _database([(name, False) for name in reversed(names)], list(reversed(edges)))

    first = _closure(forward)
    second = _closure(reverse)

    assert first["projectionFingerprint"] == second["projectionFingerprint"]
    assert first["nodes"] == second["nodes"]
    assert first["edges"] == second["edges"]
    assert first["coverage"] == second["coverage"]
    assert first["theorem"] == second["theorem"] == THEOREM
    assert first["closureId"] == second["closureId"]
