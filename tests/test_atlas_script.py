from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def test_atlas_export_script_writes_json_and_markdown(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.joinpath("quux").mkdir(parents=True)
    reports.joinpath("quux", "owner.json").write_text(
        json.dumps(
            {
                "metadata": {"analysis_root_module": "Quux.Root"},
                "module_dag": {"module_count": 1, "edge_count": 0},
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    output_json = tmp_path / "atlas.json"
    output_md = tmp_path / "atlas.md"
    output_sqlite = tmp_path / "atlas.sqlite"
    output_cards = tmp_path / "cards.md"

    status = script_main()(
        [
            "--reports-root",
            str(reports),
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_md),
            "--output-sqlite",
            str(output_sqlite),
            "--output-cards",
            str(output_cards),
        ]
    )

    assert status == 0
    assert json.loads(output_json.read_text(encoding="utf-8"))["summary"]["reports"] == 1
    assert "# Ladon Report Atlas" in output_md.read_text(encoding="utf-8")
    assert output_sqlite.exists()
    assert "# Ladon Atlas Reviewer Cards" in output_cards.read_text(encoding="utf-8")


def script_main():
    script = Path(__file__).parents[1] / "scripts" / "ladon_atlas_export.py"
    spec = importlib.util.spec_from_file_location("ladon_atlas_export", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main
