"""Additive historical attribution schema, separate from Lean evidence."""

import sqlite3

HISTORY_TABLES = frozenset(
    {
        "ideas",
        "historical_sources",
        "idea_attributions",
        "declaration_ideas",
        "declaration_idea_bindings",
        "idea_dependencies",
        "idea_catalog_state",
    }
)

DDL = """
CREATE TABLE ideas (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, statement TEXT NOT NULL,
    scope_note TEXT NOT NULL
);
CREATE TABLE historical_sources (
    id TEXT PRIMARY KEY, citation TEXT NOT NULL, version TEXT NOT NULL,
    url TEXT, artifact_path TEXT, artifact_sha256 TEXT
);
CREATE TABLE idea_attributions (
    id TEXT PRIMARY KEY, idea_id TEXT NOT NULL REFERENCES ideas(id),
    source_id TEXT REFERENCES historical_sources(id), source_locator TEXT,
    year_start INTEGER, year_end INTEGER,
    precision TEXT NOT NULL CHECK(precision IN ('year','decade','range','unknown')),
    dating_basis TEXT NOT NULL CHECK(length(trim(dating_basis))>0),
    review_status TEXT NOT NULL CHECK(review_status IN ('proposed','reviewed','disputed','rejected')),
    reviewer TEXT, reviewed_at TEXT,
    is_selected INTEGER NOT NULL CHECK(is_selected IN (0,1)),
    CHECK((precision='unknown' AND year_start IS NULL AND year_end IS NULL)
       OR (precision!='unknown' AND year_start IS NOT NULL AND year_end IS NOT NULL
           AND typeof(year_start)='integer' AND typeof(year_end)='integer'
           AND year_start BETWEEN 1 AND 9999 AND year_end BETWEEN year_start AND 9999)),
    CHECK(precision!='year' OR (year_start=year_end AND source_id IS NOT NULL
           AND source_locator IS NOT NULL AND length(trim(source_locator))>0)),
    CHECK(precision!='decade' OR (year_start%10=0 AND year_end=year_start+9)),
    CHECK(review_status!='reviewed' OR (reviewer IS NOT NULL AND length(trim(reviewer))>0
           AND reviewed_at IS NOT NULL AND length(trim(reviewed_at))>0)),
    CHECK(is_selected=0 OR review_status='reviewed')
);
CREATE UNIQUE INDEX idea_selected_attribution ON idea_attributions(idea_id) WHERE is_selected=1;
CREATE INDEX idea_attribution_source ON idea_attributions(source_id);
CREATE INDEX idea_attribution_idea ON idea_attributions(idea_id);
CREATE TABLE declaration_ideas (
    id TEXT PRIMARY KEY, idea_id TEXT NOT NULL REFERENCES ideas(id),
    package TEXT NOT NULL, module TEXT NOT NULL, declaration_name TEXT NOT NULL,
    statement_sha256 TEXT NOT NULL CHECK(length(statement_sha256)=64),
    relation TEXT NOT NULL CHECK(relation IN ('formalizes','generalizes','adapts','uses_ingredient')),
    review_status TEXT NOT NULL CHECK(review_status IN ('proposed','reviewed','disputed','rejected')),
    evidence_locator TEXT NOT NULL, note TEXT NOT NULL
);
CREATE INDEX idea_link_idea ON declaration_ideas(idea_id);
CREATE TABLE declaration_idea_bindings (
    link_id TEXT PRIMARY KEY REFERENCES declaration_ideas(id) ON DELETE CASCADE,
    declaration_id TEXT REFERENCES declarations(id) ON DELETE SET NULL,
    resolution TEXT NOT NULL CHECK(resolution IN ('resolved','stale','missing','ambiguous'))
);
CREATE INDEX idea_binding_declaration ON declaration_idea_bindings(declaration_id);
CREATE TABLE idea_dependencies (
    id TEXT PRIMARY KEY,
    parent_idea_id TEXT NOT NULL REFERENCES ideas(id),
    child_idea_id TEXT NOT NULL REFERENCES ideas(id),
    evidence TEXT NOT NULL CHECK(length(trim(evidence))>0),
    review_status TEXT NOT NULL CHECK(review_status IN ('proposed','reviewed','disputed','rejected')),
    CHECK(parent_idea_id!=child_idea_id), UNIQUE(parent_idea_id,child_idea_id)
);
CREATE INDEX idea_dependency_child ON idea_dependencies(child_idea_id);
CREATE TABLE idea_catalog_state (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    input_sha256 TEXT NOT NULL, source_path TEXT NOT NULL
);
CREATE VIEW idea_dates AS
SELECT i.id AS idea_id, i.title,
       CASE WHEN a.precision='year' THEN a.year_start END AS idea_year,
       CASE WHEN a.precision='decade' THEN a.year_start END AS guess_of_the_decade,
       a.year_start, a.year_end, COALESCE(a.precision,'unknown') AS precision,
       COALESCE(a.review_status,'unassessed') AS status,
       a.dating_basis, a.source_id, a.source_locator
FROM ideas i LEFT JOIN idea_attributions a ON a.idea_id=i.id AND a.is_selected=1;
CREATE VIEW declaration_idea_dates AS
SELECT b.declaration_id, b.resolution, l.id AS link_id, l.review_status AS link_status,
       l.relation, d.*
FROM declaration_ideas l JOIN declaration_idea_bindings b ON b.link_id=l.id
JOIN idea_dates d ON d.idea_id=l.idea_id;
"""


def create_history_schema(connection: sqlite3.Connection) -> None:
    # Execute individually: executescript would implicitly commit the caller's transaction.
    for statement in DDL.split(";"):
        if statement.strip():
            connection.execute(statement)
