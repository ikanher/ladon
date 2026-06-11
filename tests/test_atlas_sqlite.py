from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.atlas import build_report_atlas
from ladon.atlas_sqlite import run_canned_query, write_atlas_sqlite


QUERY_TABLES = (
    "nodes",
    "edges",
    "reports",
    "findings",
    "review_regions",
    "signals",
    "declaration_highlights",
    "module_highlights",
    "packet_evidence",
    "bridge_joins",
    "bridge_diagnostics",
)


def test_write_atlas_sqlite_creates_query_tables(tmp_path: Path) -> None:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"

    write_atlas_sqlite(atlas, db_path)

    counts = table_counts(db_path)

    assert counts["reports"] == 2
    assert counts["findings"] == 2
    assert counts["review_regions"] == 2
    assert counts["signals"] == 2
    assert counts["declaration_highlights"] == 2
    assert counts["module_highlights"] >= 2
    assert counts["packet_evidence"] == 2
    assert counts["bridge_joins"] == 0
    assert counts["bridge_diagnostics"] == 0


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


def test_atlas_sqlite_low_confidence_join_query(tmp_path: Path) -> None:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"
    write_atlas_sqlite(atlas, db_path, bridge_reports=[sample_bridge_report()])

    rows = run_canned_query(db_path, "low_confidence_joins")

    assert rows == [
        {
            "root": "Quux.One",
            "surface_id": "surface.name_only",
            "declaration_name": "target",
            "match_kind": "basename_only",
            "confidence": "low",
            "warning_only": 1,
        }
    ]


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


def sample_bridge_report() -> dict:
    return {
        "reviewerCards": [{"root": "Quux.One"}],
        "joins": [
            {
                "surfaceId": "surface.name_only",
                "declarationName": "target",
                "matchKind": "basename_only",
                "confidence": "low",
                "warningOnly": True,
            }
        ],
        "diagnostics": [
            {
                "ruleId": "proofir.name_only_join_warning",
                "level": "warning",
            }
        ],
    }
