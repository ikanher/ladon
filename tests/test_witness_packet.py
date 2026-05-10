from __future__ import annotations

import json
from pathlib import Path

from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.cli import main
from ladon.render import render_text


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def test_packet_evidence_detects_complete_synthetic_packet(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    (packet / "witnesses" / "demo" / "artifacts").mkdir(parents=True)
    (packet / "witnesses" / "demo" / "tests").mkdir(parents=True)
    (packet / "witnesses" / "demo" / "check.py").write_text("print('ok')\n", encoding="utf-8")
    (packet / "witnesses" / "demo" / "tests" / "test_demo.py").write_text(
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    (packet / "witnesses" / "demo" / "artifacts" / "witness.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (packet / "manifest.json").write_text("{}\n", encoding="utf-8")
    (packet / "VERIFY_PACKET.sh").write_text("python check.py\n", encoding="utf-8")
    (packet / "README.md").write_text("Lean owner theorem: A.root\n", encoding="utf-8")

    summary = summarize_packet_evidence(packet)

    assert summary["status"] == "complete"
    assert summary["score"] == summary["max_score"]
    assert all(check["passed"] for check in summary["checks"])


def test_packet_evidence_reports_partial_missing_packet() -> None:
    summary = summarize_packet_evidence(Path("/definitely/missing/ladon/packet"))

    assert summary["exists"] is False
    assert summary["status"] == "missing"
    assert summary["score"] == 0


def test_cli_packet_dir_adds_packet_evidence_to_reports(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    packet.mkdir()
    (packet / "manifest.json").write_text("{}\n", encoding="utf-8")
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--packet-dir",
            str(packet),
            "--output-json",
            str(json_path),
            "--output-text",
            str(text_path),
        ]
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert status == 0
    assert payload["packet_evidence"][0]["packet_dir"] == str(packet)
    assert "Packet Evidence" in text_path.read_text(encoding="utf-8")


def test_text_report_renders_packet_evidence() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "A"},
        "warnings": [],
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
        },
        "findings": [],
        "packet_evidence": [
            {
                "packet_dir": "/packet",
                "status": "partial",
                "score": 2,
                "max_score": 6,
                "checks": [],
            }
        ],
    }

    text = render_text(payload)

    assert "Packet Evidence" in text
    assert "- /packet: partial score=2/6" in text
