"""SQLite query surface for Ladon report atlases."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.artifact_versions import require_atlas_v1, require_bridge_v1


CANNED_QUERIES = {
    "hotspots": """
        SELECT subject, kind, COUNT(DISTINCT report_id) AS report_count, SUM(count) AS total_count
        FROM findings
        WHERE subject != ''
        GROUP BY subject, kind
        ORDER BY report_count DESC, total_count DESC, subject ASC, kind ASC
    """,
    "recurring_declarations": """
        SELECT declaration, metric, COUNT(DISTINCT report_id) AS report_count, SUM(value) AS total_value
        FROM declaration_highlights
        GROUP BY declaration, metric
        HAVING report_count > 1
        ORDER BY report_count DESC, total_value DESC, declaration ASC, metric ASC
    """,
    "declaration_dependencies": """
        SELECT source, target, kind, authority
        FROM declaration_dependencies
        ORDER BY source ASC, kind ASC, target ASC
    """,
    "review_region_pressure": """
        SELECT kind, COUNT(DISTINCT report_id) AS report_count, SUM(signal_count) AS total_signals
        FROM review_regions
        GROUP BY kind
        ORDER BY report_count DESC, total_signals DESC, kind ASC
    """,
    "proof_family_pressure": """
        SELECT subject, source_kind, COUNT(DISTINCT report_id) AS report_count, SUM(count) AS total_count
        FROM (
            SELECT report_id, subject, kind AS source_kind, count
            FROM findings
            WHERE kind LIKE '%proof_family%' OR subject LIKE '%proof%'
            UNION ALL
            SELECT report_id, subject, kind AS source_kind, count
            FROM signals
            WHERE kind LIKE '%proof_family%' OR subject LIKE '%proof%'
        )
        WHERE subject != ''
        GROUP BY subject, source_kind
        ORDER BY report_count DESC, total_count DESC, subject ASC, source_kind ASC
    """,
    "packet_evidence_gaps": """
        SELECT reports.path, rows, incomplete, missing, partial, stale
        FROM packet_evidence
        JOIN reports ON reports.id = packet_evidence.report_id
        WHERE incomplete > 0 OR missing > 0 OR partial > 0 OR stale > 0
        ORDER BY incomplete DESC, stale DESC, missing DESC, reports.path ASC
    """,
    "low_confidence_joins": """
        SELECT root, surface_id, declaration_name, match_kind, confidence, warning_only
        FROM bridge_joins
        WHERE confidence IN ('low', 'none') OR warning_only = 1 OR match_kind = 'unmatched'
        ORDER BY root ASC, surface_id ASC, declaration_name ASC
    """,
}

ATLAS_QUERY_RESULT_SCHEMA = "ladon-atlas-query-result-v1"


@dataclass(frozen=True)
class QueryRequirement:
    """Coverage contract for one installed canned query."""

    collections: tuple[str, ...]
    subset_safe: bool


QUERY_REQUIREMENTS = {
    "hotspots": QueryRequirement(("report.findings",), True),
    "recurring_declarations": QueryRequirement(
        ("declaration_graph.declarations",),
        True,
    ),
    "declaration_dependencies": QueryRequirement(
        ("declaration_graph.declarations",),
        True,
    ),
    "review_region_pressure": QueryRequirement(
        ("report.review_regions",),
        True,
    ),
    "proof_family_pressure": QueryRequirement(
        ("report.findings", "report.review_regions"),
        True,
    ),
    "packet_evidence_gaps": QueryRequirement(
        ("report.packet_evidence",),
        True,
    ),
    "low_confidence_joins": QueryRequirement((), True),
}


def write_atlas_sqlite(
    atlas: dict[str, Any],
    db_path: Path,
    *,
    external_evidence: list[dict[str, Any]] | None = None,
) -> None:
    """Write a deterministic SQLite database from an atlas JSON payload."""

    require_atlas_v1(atlas, consumer="atlas SQLite reader")
    for report in external_evidence or []:
        require_bridge_v1(report, consumer="atlas SQLite bridge reader")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as connection:
        create_schema(connection)
        insert_atlas(connection, atlas, external_evidence or [])


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the compact atlas query schema."""

    connection.executescript(
        """
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            label TEXT NOT NULL,
            data_json TEXT NOT NULL
        );
        CREATE TABLE edges (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            kind TEXT NOT NULL,
            data_json TEXT NOT NULL
        );
        CREATE TABLE reports (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            analysis_root_module TEXT NOT NULL,
            module_count INTEGER NOT NULL,
            declaration_count INTEGER NOT NULL,
            finding_count INTEGER NOT NULL,
            review_region_count INTEGER NOT NULL
        );
        CREATE TABLE collection_coverage (
            report_id TEXT NOT NULL,
            collection_id TEXT NOT NULL,
            completeness TEXT NOT NULL,
            total_known INTEGER NOT NULL,
            population TEXT NOT NULL,
            scope TEXT NOT NULL,
            authority TEXT NOT NULL,
            analysis_fingerprint TEXT,
            source_fingerprint TEXT,
            coverage_json TEXT NOT NULL,
            PRIMARY KEY(report_id, collection_id)
        );
        CREATE TABLE packet_evidence (
            report_id TEXT PRIMARY KEY,
            rows INTEGER NOT NULL,
            incomplete INTEGER NOT NULL,
            missing INTEGER NOT NULL,
            partial INTEGER NOT NULL,
            stale INTEGER NOT NULL
        );
        CREATE TABLE bridge_joins (
            root TEXT NOT NULL,
            surface_id TEXT NOT NULL,
            declaration_name TEXT NOT NULL,
            match_kind TEXT NOT NULL,
            confidence TEXT NOT NULL,
            warning_only INTEGER NOT NULL
        );
        CREATE TABLE bridge_diagnostics (
            root TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            level TEXT NOT NULL,
            count INTEGER NOT NULL
        );
        CREATE TABLE findings (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            count INTEGER NOT NULL
        );
        CREATE TABLE review_regions (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            signal_count INTEGER NOT NULL
        );
        CREATE TABLE signals (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            region_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            count INTEGER NOT NULL
        );
        CREATE TABLE declaration_highlights (
            report_id TEXT NOT NULL,
            declaration TEXT NOT NULL,
            metric TEXT NOT NULL,
            rank INTEGER NOT NULL,
            value INTEGER NOT NULL
        );
        CREATE TABLE declaration_dependencies (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            kind TEXT NOT NULL,
            authority TEXT NOT NULL
        );
        CREATE TABLE module_highlights (
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            metric TEXT NOT NULL,
            rank INTEGER NOT NULL,
            value INTEGER NOT NULL
        );
        """
    )


def insert_atlas(
    connection: sqlite3.Connection,
    atlas: dict[str, Any],
    external_evidence: list[dict[str, Any]],
) -> None:
    """Insert normalized atlas graph rows."""

    nodes = {node["id"]: node for node in atlas.get("nodes", [])}
    edges = list(atlas.get("edges", []))
    insert_nodes(connection, nodes.values())
    insert_edges(connection, edges)
    insert_reports(connection, nodes.values())
    insert_collection_coverage(connection, nodes.values())
    insert_packet_evidence(connection, nodes.values())
    insert_external_evidence(connection, external_evidence)
    insert_joined_rows(connection, nodes, edges)


def insert_nodes(connection: sqlite3.Connection, nodes: Any) -> None:
    """Insert raw graph node rows."""

    connection.executemany(
        "INSERT INTO nodes(id, kind, label, data_json) VALUES (?, ?, ?, ?)",
        [
            (
                node["id"],
                node["kind"],
                node["label"],
                json.dumps(node.get("data", {}), sort_keys=True),
            )
            for node in nodes
        ],
    )


def insert_edges(connection: sqlite3.Connection, edges: list[dict[str, Any]]) -> None:
    """Insert raw graph edge rows."""

    connection.executemany(
        "INSERT INTO edges(source, target, kind, data_json) VALUES (?, ?, ?, ?)",
        [
            (
                row["source"],
                row["target"],
                row["kind"],
                json.dumps(row.get("data", {}), sort_keys=True),
            )
            for row in edges
        ],
    )


def insert_reports(connection: sqlite3.Connection, nodes: Any) -> None:
    """Insert report convenience rows."""

    rows = []
    for node in nodes:
        if node["kind"] != "report":
            continue
        data = node.get("data", {})
        rows.append(
            (
                node["id"],
                node["label"],
                data.get("analysis_root_module", ""),
                int(data.get("module_count", 0)),
                int(data.get("declaration_count", 0)),
                int(data.get("finding_count", 0)),
                int(data.get("review_region_count", 0)),
            )
        )
    connection.executemany(
        """
        INSERT INTO reports(
            id, path, analysis_root_module, module_count, declaration_count,
            finding_count, review_region_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_collection_coverage(
    connection: sqlite3.Connection,
    nodes: Any,
) -> None:
    """Persist per-report collection authority for query-time decisions."""

    rows = [
        _collection_coverage_sql_row(node["id"], identity, coverage)
        for node in nodes
        if node.get("kind") == "report"
        for identity, coverage in _coverage_rows(node).items()
    ]
    connection.executemany(
        """
        INSERT INTO collection_coverage(
            report_id, collection_id, completeness, total_known,
            population, scope, authority, analysis_fingerprint,
            source_fingerprint, coverage_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _coverage_rows(node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return typed registry rows embedded in one report atlas node."""

    registry = node.get("data", {}).get("coverage", {})
    collections = (
        registry.get("collections")
        if isinstance(registry, dict)
        else None
    )
    if not isinstance(collections, dict):
        return {}
    return {
        str(identity): row
        for identity, row in collections.items()
        if isinstance(row, dict)
    }


def _collection_coverage_sql_row(
    report_id: str,
    identity: str,
    coverage: dict[str, Any],
) -> tuple[Any, ...]:
    """Normalize one canonical coverage row for SQLite."""

    return (
        report_id,
        identity,
        str(coverage.get("completeness", "unavailable")),
        int(coverage.get("totalKnown") is True),
        str(coverage.get("population", "")),
        str(coverage.get("scope", "")),
        str(coverage.get("authority", "")),
        coverage.get("analysisFingerprint"),
        coverage.get("sourceFingerprint"),
        json.dumps(coverage, sort_keys=True, separators=(",", ":")),
    )


def insert_packet_evidence(connection: sqlite3.Connection, nodes: Any) -> None:
    """Insert report-level packet evidence summaries."""

    rows = []
    for node in nodes:
        if node["kind"] != "report":
            continue
        packet = node.get("data", {}).get("packet_evidence", {})
        rows.append(
            (
                node["id"],
                int(packet.get("rows", 0)),
                int(packet.get("incomplete", 0)),
                int(packet.get("missing", 0)),
                int(packet.get("partial", 0)),
                int(packet.get("stale", 0)),
            )
        )
    connection.executemany(
        """
        INSERT INTO packet_evidence(report_id, rows, incomplete, missing, partial, stale)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_external_evidence(
    connection: sqlite3.Connection,
    external_evidence: list[dict[str, Any]],
) -> None:
    """Insert optional ProofIR bridge joins and diagnostics."""

    for report in external_evidence:
        root = external_evidence_root(report)
        insert_bridge_joins(connection, root, report.get("joins", []))
        insert_bridge_diagnostics(connection, root, report.get("diagnostics", []))


def insert_bridge_joins(connection: sqlite3.Connection, root: str, joins: Any) -> None:
    """Insert bridge join rows for low-confidence query support."""

    if not isinstance(joins, list):
        return
    connection.executemany(
        """
        INSERT INTO bridge_joins(
            root, surface_id, declaration_name, match_kind, confidence, warning_only
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                root,
                str(row.get("surfaceId", "")),
                str(row.get("declarationName", "")),
                str(row.get("matchKind", "")),
                str(row.get("confidence", "")),
                int(row.get("warningOnly") is True),
            )
            for row in joins
            if isinstance(row, dict)
        ],
    )


def insert_bridge_diagnostics(connection: sqlite3.Connection, root: str, diagnostics: Any) -> None:
    """Insert grouped bridge diagnostic rows."""

    if not isinstance(diagnostics, list):
        return
    counts: dict[tuple[str, str], int] = {}
    for row in diagnostics:
        if isinstance(row, dict) and row.get("ruleId"):
            key = (str(row["ruleId"]), str(row.get("level", "")))
            counts[key] = counts.get(key, 0) + 1
    connection.executemany(
        """
        INSERT INTO bridge_diagnostics(root, rule_id, level, count)
        VALUES (?, ?, ?, ?)
        """,
        [(root, rule_id, level, count) for (rule_id, level), count in sorted(counts.items())],
    )


def external_evidence_root(report: dict[str, Any]) -> str:
    """Return the first reviewer-card root named in a bridge report."""

    cards = report.get("reviewerCards", [])
    if isinstance(cards, list):
        for card in cards:
            if isinstance(card, dict) and card.get("root"):
                return str(card["root"])
    return ""


def insert_joined_rows(
    connection: sqlite3.Connection,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    """Insert query-oriented rows by joining edge endpoints."""

    for row in edges:
        source = row["source"]
        target = row["target"]
        target_node = nodes.get(target)
        if target_node is None:
            continue
        data = target_node.get("data", {})
        edge_data = row.get("data", {})
        match row["kind"]:
            case "has_finding":
                insert_finding(connection, target, source, data)
            case "has_review_region":
                insert_review_region(connection, target, source, target_node, data)
            case "has_signal":
                insert_signal(connection, nodes, target, source, target_node, data)
            case "highlights_declaration":
                insert_declaration_highlight(connection, target_node, source, edge_data)
            case "highlights_module":
                insert_module_highlight(connection, target_node, source, edge_data)
            case (
                "parser_candidate_dependency"
                | "type_dependency"
                | "value_dependency"
            ):
                source_node = nodes.get(source)
                if source_node is not None:
                    insert_declaration_dependency(
                        connection,
                        source_node,
                        target_node,
                        row["kind"],
                        edge_data,
                    )


def insert_finding(
    connection: sqlite3.Connection,
    finding_id: str,
    report_id: str,
    data: dict[str, Any],
) -> None:
    """Insert one finding row."""

    connection.execute(
        "INSERT INTO findings(id, report_id, kind, subject, count) VALUES (?, ?, ?, ?, ?)",
        (
            finding_id,
            report_id,
            data.get("kind", ""),
            data.get("subject", ""),
            int(data.get("count", 0)),
        ),
    )


def insert_declaration_dependency(
    connection: sqlite3.Connection,
    source_node: dict[str, Any],
    target_node: dict[str, Any],
    kind: str,
    data: dict[str, Any],
) -> None:
    """Insert one parser- or Lean-authority declaration dependency."""

    connection.execute(
        """
        INSERT INTO declaration_dependencies(source, target, kind, authority)
        VALUES (?, ?, ?, ?)
        """,
        (
            source_node.get("label", ""),
            target_node.get("label", ""),
            kind,
            data.get("authority", "unknown"),
        ),
    )


def insert_review_region(
    connection: sqlite3.Connection,
    region_id: str,
    report_id: str,
    region_node: dict[str, Any],
    data: dict[str, Any],
) -> None:
    """Insert one review-region row."""

    connection.execute(
        """
        INSERT INTO review_regions(id, report_id, kind, title, signal_count)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            region_id,
            report_id,
            data.get("kind", ""),
            region_node.get("label", ""),
            int(data.get("signal_count", 0)),
        ),
    )


def insert_signal(
    connection: sqlite3.Connection,
    nodes: dict[str, dict[str, Any]],
    signal_id: str,
    region_id: str,
    signal_node: dict[str, Any],
    data: dict[str, Any],
) -> None:
    """Insert one review-region signal row."""

    report_id = report_for_region(nodes, region_id)
    connection.execute(
        "INSERT INTO signals(id, report_id, region_id, kind, subject, count) VALUES (?, ?, ?, ?, ?, ?)",
        (
            signal_id,
            report_id,
            region_id,
            data.get("kind", ""),
            data.get("subject", signal_node.get("label", "")),
            int(data.get("count", 0)),
        ),
    )


def insert_declaration_highlight(
    connection: sqlite3.Connection,
    declaration_node: dict[str, Any],
    report_id: str,
    edge_data: dict[str, Any],
) -> None:
    """Insert one declaration-highlight row."""

    connection.execute(
        """
        INSERT INTO declaration_highlights(report_id, declaration, metric, rank, value)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            report_id,
            declaration_node["label"],
            edge_data.get("metric", ""),
            int(edge_data.get("rank", 0)),
            int(edge_data.get("value", 0)),
        ),
    )


def insert_module_highlight(
    connection: sqlite3.Connection,
    module_node: dict[str, Any],
    report_id: str,
    edge_data: dict[str, Any],
) -> None:
    """Insert one module-highlight row."""

    connection.execute(
        """
        INSERT INTO module_highlights(report_id, module, metric, rank, value)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            report_id,
            module_node["label"],
            edge_data.get("metric", ""),
            int(edge_data.get("rank", 0)),
            int(edge_data.get("value", 0)),
        ),
    )


def report_for_region(nodes: dict[str, dict[str, Any]], region_id: str) -> str:
    """Infer owning report ID from region node ID."""

    if not region_id.startswith("region:"):
        return ""
    relative = region_id.removeprefix("region:").rsplit(":", 1)[0]
    report_id = f"report:{relative}"
    return report_id if report_id in nodes else ""


def run_canned_query(db_path: Path, query_name: str) -> list[dict[str, Any]]:
    """Run one named atlas query and return dictionaries."""

    if query_name not in CANNED_QUERIES:
        known = ", ".join(sorted(CANNED_QUERIES))
        raise ValueError(f"unknown atlas query {query_name!r}; expected one of: {known}")
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(CANNED_QUERIES[query_name]).fetchall()
    return [dict(row) for row in rows]


def run_coverage_aware_query(
    db_path: Path,
    query_name: str,
    *,
    exhaustive: bool = False,
) -> dict[str, Any]:
    """Run a canned query with explicit completeness and subset semantics."""

    requirement = _query_requirement(query_name)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        coverage = _required_query_coverage(connection, requirement)
        incomplete = [
            row
            for row in coverage
            if not _coverage_row_is_complete(row)
        ]
        if exhaustive and incomplete:
            return _unavailable_query_result(
                query_name,
                coverage,
                incomplete,
            )
        rows = [
            dict(row)
            for row in connection.execute(CANNED_QUERIES[query_name])
        ]
    return _available_query_result(
        query_name,
        rows,
        coverage,
        incomplete,
        exhaustive=exhaustive,
        subset_safe=requirement.subset_safe,
    )


def _query_requirement(query_name: str) -> QueryRequirement:
    """Return one registered query contract or reject an unknown name."""

    if query_name not in CANNED_QUERIES:
        known = ", ".join(sorted(CANNED_QUERIES))
        raise ValueError(
            f"unknown atlas query {query_name!r}; expected one of: {known}"
        )
    return QUERY_REQUIREMENTS[query_name]


def _required_query_coverage(
    connection: sqlite3.Connection,
    requirement: QueryRequirement,
) -> list[dict[str, Any]]:
    """Load coverage rows for every report/collection required by a query."""

    rows: list[dict[str, Any]] = []
    for identity in requirement.collections:
        query_rows = connection.execute(
            """
            SELECT report_id, collection_id, completeness, total_known,
                   population, scope, authority, analysis_fingerprint,
                   source_fingerprint, coverage_json
            FROM collection_coverage
            WHERE collection_id = ?
            ORDER BY report_id ASC
            """,
            (identity,),
        ).fetchall()
        rows.extend(_coverage_query_row(identity, row) for row in query_rows)
        rows.extend(
            _missing_coverage_rows(connection, identity, query_rows)
        )
    return sorted(
        rows,
        key=lambda row: (row["reportId"], row["collectionId"]),
    )


def _coverage_query_row(
    identity: str,
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Adapt one persisted coverage row to query-result metadata."""

    return {
        "reportId": str(row["report_id"]),
        "collectionId": identity,
        "completeness": str(row["completeness"]),
        "totalKnown": bool(row["total_known"]),
        "population": str(row["population"]),
        "scope": str(row["scope"]),
        "authority": str(row["authority"]),
        "analysisFingerprint": row["analysis_fingerprint"],
        "sourceFingerprint": row["source_fingerprint"],
        "coverage": json.loads(str(row["coverage_json"])),
    }


def _missing_coverage_rows(
    connection: sqlite3.Connection,
    identity: str,
    present: list[sqlite3.Row],
) -> list[dict[str, Any]]:
    """Represent missing per-report coverage as unavailable, never empty."""

    present_reports = {str(row["report_id"]) for row in present}
    report_ids = [
        str(row[0])
        for row in connection.execute(
            "SELECT id FROM reports ORDER BY id ASC"
        )
    ]
    if not report_ids and not present_reports:
        report_ids = ["atlas:unscoped"]
    return [
        {
            "reportId": report_id,
            "collectionId": identity,
            "completeness": "unavailable",
            "totalKnown": False,
            "population": "unknown",
            "scope": "unknown",
            "authority": "missing_collection_coverage",
            "analysisFingerprint": None,
            "sourceFingerprint": None,
            "coverage": None,
        }
        for report_id in report_ids
        if report_id not in present_reports
    ]


def _coverage_row_is_complete(row: dict[str, Any]) -> bool:
    """Return whether one required source population is exhaustive."""

    return (
        row.get("totalKnown") is True
        and row.get("completeness") == "complete"
    )


def _unavailable_query_result(
    query_name: str,
    coverage: list[dict[str, Any]],
    incomplete: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a structured refusal for an unsupported exhaustive claim."""

    return {
        "schema": ATLAS_QUERY_RESULT_SCHEMA,
        "query": query_name,
        "status": "unavailable",
        "exhaustive": False,
        "rows": [],
        "requiredCoverage": coverage,
        "diagnostics": [
            {
                "id": "atlas.query.incomplete_authority",
                "message": (
                    "Exhaustive query unavailable because required source "
                    "collections are incomplete."
                ),
                "collections": sorted(
                    {
                        str(row["collectionId"])
                        for row in incomplete
                    }
                ),
            }
        ],
        "nonclaim": (
            "An empty row list is not evidence that the requested relationship "
            "is absent."
        ),
    }


def _available_query_result(
    query_name: str,
    rows: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    incomplete: list[dict[str, Any]],
    *,
    exhaustive: bool,
    subset_safe: bool,
) -> dict[str, Any]:
    """Return complete or explicitly visible-subset query results."""

    non_exhaustive = bool(incomplete) or not exhaustive
    status = "non_exhaustive" if non_exhaustive else "complete"
    return {
        "schema": ATLAS_QUERY_RESULT_SCHEMA,
        "query": query_name,
        "status": status,
        "exhaustive": not non_exhaustive,
        "rows": rows if subset_safe or not incomplete else [],
        "requiredCoverage": coverage,
        "diagnostics": [],
        "nonclaim": (
            "Rows are sound only for visible source collections and do not "
            "establish repository-wide absence or exhaustive totals."
            if non_exhaustive
            else None
        ),
    }
