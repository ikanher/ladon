"""Authored historical catalogues and honest current-declaration correspondence.

An attribution is historical metadata, never Lean evidence. Indexed type text
is hashed byte-for-byte; a changed signature requires a new reviewed link.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

CATALOGUE_NAME = "ladon-ideas.json"
MAX_CATALOGUE_BYTES = 8 * 1024 * 1024
TABLES = {
    "ideas": ("ideas", "id title statement scope_note"),
    "sources": ("historical_sources", "id citation version url artifact_path artifact_sha256"),
    "attributions": (
        "idea_attributions",
        "id idea_id source_id source_locator year_start year_end precision dating_basis review_status reviewer reviewed_at is_selected",
    ),
    "links": (
        "declaration_ideas",
        "id idea_id package module declaration_name statement_sha256 relation review_status evidence_locator note",
    ),
    "dependencies": ("idea_dependencies", "id parent_idea_id child_idea_id evidence review_status"),
}
NULLABLE = {
    "url",
    "artifact_path",
    "artifact_sha256",
    "source_id",
    "source_locator",
    "year_start",
    "year_end",
    "reviewer",
    "reviewed_at",
}


def available(db):
    return (
        db.execute("SELECT 1 FROM sqlite_master WHERE name='ideas' AND type='table'").fetchone()
        is not None
    )


def _validate(data):
    if (
        not isinstance(data, dict)
        or set(data) != {"schema", *TABLES}
        or data["schema"] != "ladon-ideas-v1"
    ):
        raise ValueError("expected complete ladon-ideas-v1 catalogue")
    for key, (_, columns) in TABLES.items():
        if not isinstance(data[key], list):
            raise ValueError(f"{key} must be an array")  # noqa: TRY004 -- external JSON
        for row in data[key]:
            _validate_record(key, columns, row)
    _validate_graph(data)


def _validate_record(key, columns, row):
    if not isinstance(row, dict) or set(row) != set(columns.split()):
        raise ValueError(f"invalid {key} fields")
    for name, value in row.items():
        _validate_field(name, value)
    if not row["id"].strip():
        raise ValueError("empty record id")


def _validate_field(name, value):
    if value is None and name in NULLABLE:
        return
    if name in {"year_start", "year_end", "is_selected"}:
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    elif not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    elif name.endswith("sha256") and (
        len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError(f"invalid {name}")


def _validate_graph(data):
    nodes = {row["id"] for row in data["ideas"]}
    adjacency = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for edge in data["dependencies"]:
        a, b = edge["parent_idea_id"], edge["child_idea_id"]
        if a not in nodes or b not in nodes:
            raise ValueError("unknown idea dependency endpoint")
        adjacency[a].append(b)
        indegree[b] += 1
    _require_acyclic(adjacency, indegree)


def _require_acyclic(adjacency, indegree):
    ready = [node for node, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for child in adjacency[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if visited != len(indegree):
        raise ValueError("historical prerequisite cycle")


def catalogue_digest(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def apply_catalogue(db, data, *, source_path):
    """Replace only historical records in one rollback-safe savepoint."""
    _validate(data)
    db.execute("SAVEPOINT historical_catalogue")
    try:
        db.execute("DELETE FROM declaration_idea_bindings")
        for table, _ in reversed(list(TABLES.values())):
            db.execute(f"DELETE FROM {table}")
        for key, (table, names) in TABLES.items():
            columns = names.split()
            db.executemany(
                f"INSERT INTO {table}({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                [tuple(row[c] for c in columns) for row in data[key]],
            )
        # Also validate when callers have foreign_keys disabled (e.g. an external reader).
        if db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("catalogue contains invalid references")
        rebind_links(db)
        db.execute(
            "INSERT OR REPLACE INTO idea_catalog_state VALUES (1,?,?)",
            (catalogue_digest(data), str(source_path)),
        )
    except (sqlite3.Error, ValueError) as error:
        db.execute("ROLLBACK TO historical_catalogue")
        db.execute("RELEASE historical_catalogue")
        raise ValueError(f"invalid historical catalogue: {error}") from error
    db.execute("RELEASE historical_catalogue")


def rebind_links(db):
    if not available(db):
        return
    for link, package, module, name, digest in db.execute(
        "SELECT id,package,module,declaration_name,statement_sha256 FROM declaration_ideas"
    ).fetchall():
        rows = db.execute(
            "SELECT id,type_text,type_text_truncated FROM declarations WHERE package=? AND module=? AND name=?",
            (package, module, name),
        ).fetchall()
        identity = rows[0][0] if len(rows) == 1 else None
        if not rows:
            status = "missing"
        elif len(rows) > 1:
            status = "ambiguous"
        elif (
            rows[0][2]
            or rows[0][1] is None
            or hashlib.sha256(rows[0][1].encode()).hexdigest() != digest
        ):
            status = "stale"
        else:
            status = "resolved"
        db.execute(
            "INSERT OR REPLACE INTO declaration_idea_bindings VALUES (?,?,?)",
            (link, identity, status),
        )


def load_catalogue(repo):
    path = Path(repo) / CATALOGUE_NAME
    if not path.exists():
        return None
    with path.open("rb") as stream:
        raw = stream.read(MAX_CATALOGUE_BYTES + 1)
    if len(raw) > MAX_CATALOGUE_BYTES:
        raise ValueError("historical catalogue exceeds 8 MiB")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=unique_object)


def ingest_catalogue(db, repo):
    data = load_catalogue(repo)
    if data is not None:
        apply_catalogue(db, data, source_path=CATALOGUE_NAME)
    else:
        rebind_links(db)


def historical_projection(db, declaration_ids):
    unknown = {
        "idea_id": None,
        "idea_year": None,
        "guess_of_the_decade": None,
        "precision": "unknown",
        "status": "unassessed",
        "dating_basis": None,
    }
    result = {identity: [] for identity in declaration_ids}
    if available(db):
        keys = list(result)
        for start in range(0, len(keys), 400):
            batch = keys[start : start + 400]
            cursor = db.execute(
                f"SELECT * FROM declaration_idea_dates WHERE declaration_id IN ({','.join('?' for _ in batch)}) ORDER BY declaration_id,idea_id,link_id",
                batch,
            )
            names = [col[0] for col in cursor.description]
            for row in cursor:
                item = dict(zip(names, row))
                # A stale association remains visible but is never presented as resolved dating.
                if item["resolution"] != "resolved":
                    item.update(idea_year=None, guess_of_the_decade=None, status=item["resolution"])
                result[item["declaration_id"]].append(item)
    return {key: values or [dict(unknown)] for key, values in result.items()}


def catalogue_summary(db, *, limit=1000):
    if not 1 <= limit <= 1000:
        raise ValueError("historical query limit must be between 1 and 1000")
    if not available(db):
        return {"status": "unavailable", "ideas": [], "dependencies": []}
    result = {"status": "available", "schema": "ladon-idea-history-v1", "tables": {}}
    for table in [*(t for t, _ in TABLES.values()), "declaration_idea_bindings", "idea_dates"]:
        cursor = db.execute(f"SELECT * FROM {table} ORDER BY 1 LIMIT ?", (limit + 1,))
        names = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        result["tables"][table] = {
            "rows": [dict(zip(names, row)) for row in rows[:limit]],
            "truncated": len(rows) > limit,
        }
    result["coverage"] = {
        "declarations": db.execute("SELECT count(*) FROM declarations").fetchone()[0],
        "resolvedDeclarations": db.execute(
            "SELECT count(DISTINCT declaration_id) FROM declaration_idea_bindings WHERE resolution='resolved'"
        ).fetchone()[0],
        "selectedIdeas": db.execute(
            "SELECT count(*) FROM idea_attributions WHERE is_selected=1"
        ).fetchone()[0],
        "nonclaim": "Historical coverage is not proof authority or historical truth verification.",
    }
    result["input"] = db.execute(
        "SELECT input_sha256,source_path FROM idea_catalog_state"
    ).fetchone()
    return result


def attach_lineage_history(db, nodes):
    """Attach annotations only when the indexed owner/name is unambiguous."""
    matches = {}
    names = sorted({node["name"] for node in nodes})
    for start in range(0, len(names), 400):
        batch = names[start : start + 400]
        for identity, name, module in db.execute(
            f"SELECT id,candidate_name,module FROM declarations WHERE candidate_name IN ({','.join('?' for _ in batch)})",
            batch,
        ):
            matches.setdefault((name, module), []).append(identity)
    ids = [values[0] for values in matches.values() if len(values) == 1]
    history = historical_projection(db, [*ids, None])
    for node in nodes:
        values = matches.get((node["name"], node["ownerModule"]), [])
        node["historicalIdeas"] = history[values[0] if len(values) == 1 else None]


def refuse_unrecoverable_rebuild(destination, repo):
    """Do not erase authored records when their reproducible input has disappeared."""
    if not destination.exists() or (Path(repo) / CATALOGUE_NAME).exists():
        return
    from ladon.proof_search_index import ProofSearchIndexError

    with sqlite3.connect(destination.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if available(db) and any(
            db.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() for table, _ in TABLES.values()
        ):
            raise ProofSearchIndexError(
                "historical catalogue is missing; restore ladon-ideas.json before rebuilding this index"
            )


def attach_declaration_history(db, rows, *, id_key):
    history = historical_projection(db, [row[id_key] for row in rows])
    for row in rows:
        row["historicalIdeas"] = history[row[id_key]]
