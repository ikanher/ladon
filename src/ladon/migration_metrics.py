"""Read-only, content-based preservation gates for additive SQLite migrations.

Fractions count failed table/query invariants, not allegedly lost theorem counts.
New enrichment coverage is deliberately not a migration-preservation metric.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import deque
from contextlib import closing
from pathlib import Path


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def _connect(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    return db


def _tables(db):
    return [
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _columns(db, table):
    return [row[1] for row in db.execute(f"PRAGMA table_info({_quote(table)})")]


def _encoded(row):
    # Preserve SQLite value types, including BLOBs, while streaming large tables.
    return (
        json.dumps(
            [
                [type(value).__name__, value.hex() if isinstance(value, bytes) else value]
                for value in row
            ],
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )


def _digest(db, table, columns, metadata_changes=None):
    selected = ",".join(map(_quote, columns))
    digest, count = hashlib.sha256(), 0
    for row in db.execute(f"SELECT {selected} FROM {_quote(table)} ORDER BY {selected}"):
        if table == "metadata" and metadata_changes and row[0] in metadata_changes:
            row = (row[0], metadata_changes[row[0]])
        digest.update(_encoded(row))
        count += 1
    return {"rows": count, "sha256": digest.hexdigest()}


def _fraction(failed, checked):
    return {"failed": failed, "checked": checked, "fraction": failed / checked if checked else None}


def has_idea_cycle(db):
    """Check directed historical prerequisite edges, not ordinary citations."""
    if "idea_dependencies" not in _tables(db):
        return False
    outgoing, indegree = {}, {}
    for parent, child in db.execute("SELECT parent_idea_id,child_idea_id FROM idea_dependencies"):
        outgoing.setdefault(parent, []).append(child)
        indegree.setdefault(parent, 0)
        indegree[child] = indegree.get(child, 0) + 1
    ready = deque(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        node = ready.popleft()
        visited += 1
        for child in outgoing.get(node, ()):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return visited != len(indegree)


def _integrity_violations(left, right):
    violations = []
    for label, db in [("before", left), ("after", right)]:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            violations.append(f"{label}: integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            violations.append(f"{label}: broken foreign key")
    return violations


def _table_observation(left, right, table, new_tables, metadata):
    columns = _columns(left, table)
    valid = table in new_tables and set(columns) <= set(_columns(right, table))
    old_digest = _digest(left, table, columns, metadata)
    new_digest = _digest(right, table, columns) if valid else None
    old_layout = list(left.execute(f"PRAGMA table_info({_quote(table)})"))
    new_layout = list(right.execute(f"PRAGMA table_info({_quote(table)})"))
    old_keys = sorted(left.execute(f"PRAGMA foreign_key_list({_quote(table)})"))
    new_keys = sorted(right.execute(f"PRAGMA foreign_key_list({_quote(table)})"))
    sql = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
    definition_preserved = (
        left.execute(sql, (table,)).fetchone() == right.execute(sql, (table,)).fetchone()
    )
    structure = new_layout == old_layout and old_keys == new_keys and definition_preserved
    return {
        "before": old_digest,
        "after": new_digest,
        "preserved": old_digest == new_digest and structure,
        "structurePreserved": structure,
        "hasForeignKeys": bool(old_keys),
    }


def _object_violations(left, right):
    violations = []
    for kind, name, sql in left.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE type IN ('index','view','trigger') AND sql IS NOT NULL"
    ):
        current = right.execute(
            "SELECT sql FROM sqlite_master WHERE type=? AND name=?", (kind, name)
        ).fetchone()
        if current != (sql,):
            violations.append(f"{kind} {name}: schema object changed or missing")
    return violations


def _query_observation(left, right, sql):
    try:
        old_rows, new_rows = left.execute(sql).fetchall(), right.execute(sql).fetchall()
        return {
            "preserved": old_rows == new_rows,
            "beforeRows": len(old_rows),
            "afterRows": len(new_rows),
        }
    except sqlite3.Error as error:
        return {"preserved": False, "error": str(error)}


def compare_databases(before, after, *, expected_metadata=None, queries=None):
    """Compare every old table/definition and selected stable SQL observations.

    Only exact caller-declared metadata substitutions are permitted. Neither
    database is modified; mismatches are returned as hard violations. Queries
    must specify a stable ORDER BY when result order matters. This additive
    migration contract permits new objects, not changes to old definitions.
    """
    expected_metadata = expected_metadata or {}
    queries = queries or {}
    with closing(_connect(before)) as left, closing(_connect(after)) as right:
        violations = _integrity_violations(left, right) + _object_violations(left, right)
        new_tables = set(_tables(right))
        tables = {
            table: _table_observation(left, right, table, new_tables, expected_metadata)
            for table in _tables(left)
        }
        query_results = {
            name: _query_observation(left, right, sql) for name, sql in queries.items()
        }
        if has_idea_cycle(right):
            violations.append("idea_dependencies: cycle detected")
    violations.extend(_failed_observations(tables, "protected table"))
    violations.extend(_failed_observations(query_results, "query"))
    links = [row for row in tables.values() if row["hasForeignKeys"]]
    return {
        "schema": "ladon-migration-metrics-v1",
        "accepted": not violations,
        "hardViolationCount": len(violations),
        "violations": violations,
        "dataLoss": _loss_fraction(tables.values()),
        "linkLoss": _loss_fraction(links),
        "queryLoss": _loss_fraction(query_results.values()),
        "sizeRatio": Path(after).stat().st_size / Path(before).stat().st_size,
        "tables": tables,
        "queries": query_results,
        "nonclaim": "Preservation checks are not new theorem verification or historical review.",
    }


def _loss_fraction(rows):
    rows = list(rows)
    return _fraction(sum(not row["preserved"] for row in rows), len(rows))


def _failed_observations(observations, kind):
    return [
        f"{kind} {name}: changed or unavailable"
        for name, row in observations.items()
        if not row["preserved"]
    ]
