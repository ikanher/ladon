from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.atlas import build_report_atlas
from ladon.atlas_sqlite import run_canned_query, write_atlas_sqlite


def test_write_atlas_sqlite_creates_query_tables(tmp_path: Path) -> None:
    atlas = sample_atlas(tmp_path)
    db_path = tmp_path / "atlas.sqlite"

    write_atlas_sqlite(atlas, db_path)

    with sqlite3.connect(db_path) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "nodes",
                "edges",
                "reports",
                "findings",
                "review_regions",
                "signals",
                "declaration_highlights",
                "module_highlights",
            )
        }

    assert counts["reports"] == 2
    assert counts["findings"] == 2
    assert counts["review_regions"] == 2
    assert counts["signals"] == 2
    assert counts["declaration_highlights"] == 2
    assert counts["module_highlights"] >= 2


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
