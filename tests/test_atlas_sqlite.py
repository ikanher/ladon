from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ladon.atlas import build_report_atlas
from ladon.atlas_sqlite import (
    run_canned_query,
    run_coverage_aware_query,
    write_atlas_sqlite,
)
from ladon.sqlite_publication import (
    PublicationLockBusy,
    acquire_publication_lock,
    release_publication_lock,
)


QUERY_TABLES = (
    "nodes",
    "edges",
    "reports",
    "collection_coverage",
    "findings",
    "review_regions",
    "signals",
    "declaration_highlights",
    "declaration_dependencies",
    "module_highlights",
    "packet_evidence",
)


def test_write_atlas_sqlite_creates_query_tables(tmp_path: Path) -> None:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"

    write_atlas_sqlite(atlas, db_path)

    counts = table_counts(db_path)

    assert_primary_table_counts(counts)
    assert_optional_table_counts(counts)


def test_atlas_publication_preserves_prior_database_and_honors_shared_lock(
    tmp_path: Path, monkeypatch
) -> None:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"
    write_atlas_sqlite(atlas, db_path)
    prior = db_path.read_bytes()

    owner = acquire_publication_lock(db_path)
    try:
        with pytest.raises(PublicationLockBusy):
            write_atlas_sqlite(atlas, db_path)
    finally:
        release_publication_lock(owner)

    monkeypatch.setattr(
        "ladon.atlas_sqlite.insert_atlas",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected")),
    )
    with pytest.raises(RuntimeError, match="injected"):
        write_atlas_sqlite(atlas, db_path)
    assert db_path.read_bytes() == prior
    assert not list(tmp_path.glob(".atlas.sqlite.*.tmp"))


def assert_primary_table_counts(counts: dict[str, int]) -> None:
    """Check core query tables populated by the two-report sample."""

    assert counts["reports"] == 2
    assert counts["findings"] == 2
    assert counts["review_regions"] == 2
    assert counts["signals"] == 2
    assert counts["declaration_highlights"] == 2
    assert counts["declaration_dependencies"] == 0


def assert_optional_table_counts(counts: dict[str, int]) -> None:
    """Check optional module and packet query tables."""

    assert counts["module_highlights"] >= 2
    assert counts["packet_evidence"] == 2
    assert counts["collection_coverage"] == 8


def table_counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in QUERY_TABLES
        }


def test_atlas_sqlite_hotspot_query_groups_findings(tmp_path: Path) -> None:
    db_path = write_sample_db(tmp_path)

    rows = run_canned_query(db_path, "hotspots")

    assert rows[0]["subject"] == "Shared.Hotspot"
    assert rows[0]["report_count"] == 2


def test_atlas_sqlite_recurring_declarations_query(tmp_path: Path) -> None:
    db_path = write_sample_db(tmp_path)

    rows = run_canned_query(db_path, "recurring_declarations")

    assert rows == [
        {
            "declaration": "Shared.Hotspot",
            "metric": "declaration_fan_in",
            "report_count": 2,
            "total_value": 16,
        }
    ]


def test_atlas_sqlite_review_region_pressure_query(tmp_path: Path) -> None:
    db_path = write_sample_db(tmp_path)

    rows = run_canned_query(db_path, "review_region_pressure")

    assert rows[0]["kind"] == "proof_family_region"
    assert rows[0]["report_count"] == 2
    assert rows[0]["total_signals"] == 2


def test_atlas_sqlite_proof_family_pressure_query(tmp_path: Path) -> None:
    db_path = write_sample_db(tmp_path)

    rows = run_canned_query(db_path, "proof_family_pressure")

    assert rows[0]["subject"] == "proof family repeated suffix"
    assert rows[0]["report_count"] == 2


def test_atlas_sqlite_packet_evidence_gap_query(tmp_path: Path) -> None:
    db_path = write_sample_db(tmp_path)

    rows = run_canned_query(db_path, "packet_evidence_gaps")

    assert rows[0]["incomplete"] == 1
    assert rows[0]["partial"] == 1


def test_atlas_sqlite_declaration_dependencies_keep_kind_and_authority(
    tmp_path: Path,
) -> None:
    source = {
        "id": "declaration:repo:A.root",
        "kind": "declaration",
        "label": "A.root",
        "data": {},
    }
    target = {
        "id": "declaration:repo:A.target",
        "kind": "declaration",
        "label": "A.target",
        "data": {},
    }
    atlas = {
        "schema": "ladon-report-atlas-v1",
        "summary": {},
        "nodes": [source, target],
        "edges": [
            {
                "source": source["id"],
                "target": target["id"],
                "kind": kind,
                "data": {"authority": authority},
            }
            for kind, authority in (
                ("parser_candidate_dependency", "lean_parser"),
                ("type_dependency", "lean_environment"),
                ("value_dependency", "lean_environment"),
            )
        ],
    }
    db_path = tmp_path / "dependencies.sqlite"

    write_atlas_sqlite(atlas, db_path)

    assert run_canned_query(db_path, "declaration_dependencies") == [
        {
            "source": "A.root",
            "target": "A.target",
            "kind": kind,
            "authority": authority,
        }
        for kind, authority in (
            ("parser_candidate_dependency", "lean_parser"),
            ("type_dependency", "lean_environment"),
            ("value_dependency", "lean_environment"),
        )
    ]


def test_coverage_aware_query_labels_visible_subset_results(
    tmp_path: Path,
) -> None:
    db_path = write_sample_db(tmp_path)

    payload = run_coverage_aware_query(db_path, "hotspots")

    assert payload["status"] == "non_exhaustive"
    assert payload["exhaustive"] is False
    assert payload["rows"][0]["subject"] == "Shared.Hotspot"
    assert "repository-wide absence" in payload["nonclaim"]
    assert {
        row["completeness"] for row in payload["requiredCoverage"]
    } == {"unavailable"}


def test_exhaustive_query_refuses_incomplete_required_collections(
    tmp_path: Path,
) -> None:
    db_path = write_sample_db(tmp_path)

    payload = run_coverage_aware_query(
        db_path,
        "declaration_dependencies",
        exhaustive=True,
    )

    assert payload["status"] == "unavailable"
    assert payload["rows"] == []
    assert payload["diagnostics"][0]["collections"] == [
        "declaration_graph.declarations"
    ]
    assert "not evidence" in payload["nonclaim"]


def test_exhaustive_query_succeeds_with_exact_complete_coverage(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "complete.sqlite"
    write_atlas_sqlite(complete_hotspot_atlas(), db_path)

    payload = run_coverage_aware_query(
        db_path,
        "hotspots",
        exhaustive=True,
    )

    assert payload["status"] == "complete"
    assert payload["exhaustive"] is True
    assert payload["rows"] == [
        {
            "subject": "Pkg.hotspot",
            "kind": "declaration_fan_in_hotspot",
            "report_count": 1,
            "total_count": 7,
        }
    ]
    assert payload["diagnostics"] == []
    assert payload["nonclaim"] is None
    assert [
        (
            row["collectionId"],
            row["completeness"],
            row["totalKnown"],
        )
        for row in payload["requiredCoverage"]
    ] == [("report.findings", "complete", True)]


def complete_hotspot_atlas() -> dict:
    """Return one atlas whose hotspot population has exact authority."""

    report_id = "report:complete.json"
    finding_id = "finding:complete.json:hotspot"
    return {
        "schema": "ladon-report-atlas-v1",
        "summary": {},
        "nodes": [
            {
                "id": report_id,
                "kind": "report",
                "label": "complete.json",
                "data": {
                    "analysis_root_module": "Pkg",
                    "finding_count": 1,
                    "coverage": {
                        "schema": "ladon-collection-coverage-v1",
                        "collections": {
                            "report.findings": exact_finding_coverage()
                        },
                    },
                },
            },
            {
                "id": finding_id,
                "kind": "finding",
                "label": "declaration_fan_in_hotspot: Pkg.hotspot",
                "data": {
                    "kind": "declaration_fan_in_hotspot",
                    "subject": "Pkg.hotspot",
                    "count": 7,
                },
            },
        ],
        "edges": [
            {
                "source": report_id,
                "target": finding_id,
                "kind": "has_finding",
                "data": {},
            }
        ],
    }

def exact_finding_coverage() -> dict:
    """Return exact coverage for the one visible hotspot fixture row."""

    return {
        "id": "report.findings",
        "pointer": "#/sections/findings",
        "visible": 1,
        "observedLowerBound": 1,
        "totalKnown": True,
        "total": 1,
        "omitted": 0,
        "completeness": "complete",
        "population": "selected findings",
        "scope": "Pkg",
        "authority": "ladon_analysis",
        "sourceFingerprint": "sha256:source",
        "scopeFingerprint": "sha256:scope",
        "analysisFingerprint": "sha256:analysis",
        "causes": [],
    }


def write_sample_db(tmp_path: Path) -> Path:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"
    write_atlas_sqlite(atlas, db_path)
    return db_path


def sample_atlas(tmp_path: Path) -> dict:
    write_report(tmp_path / "reports" / "quux" / "one.json", sample_report("Quux.One"))
    write_report(tmp_path / "reports" / "mf" / "two.json", sample_report("Mf.Two"))
    return build_report_atlas(tmp_path / "reports")


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def sample_report(root: str) -> dict:
    return {
        "metadata": {"analysis_root_module": root},
        "module_dag": {
            "module_count": 2,
            "edge_count": 1,
            "top_fan_in": [{"module": "Shared.Module", "fan_in": 4}],
            "top_fan_out": [],
        },
        "declaration_graph": {
            "declaration_count": 1,
            "edge_count": 0,
            "top_fan_in": [{"declaration": "Shared.Hotspot", "fan_in": 8}],
            "top_fan_out": [],
        },
        "findings": [
            {
                "kind": "declaration_fan_in_hotspot",
                "subject": "Shared.Hotspot",
                "count": 8,
            }
        ],
        "packet_evidence": [
            {
                "packet_dir": "/packets/review",
                "status": "partial",
                "profile_status": "partial",
            }
        ],
        "review_regions": [
            {
                "kind": "proof_family_region",
                "title": "Proof family pressure",
                "signal_count": 1,
                "signals": [
                    {
                        "kind": "proof_family_similarity",
                        "subject": "proof family repeated suffix",
                        "count": 3,
                    }
                ],
            }
        ],
    }
