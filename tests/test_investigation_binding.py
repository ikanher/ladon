"""Digest changes must reject even when all quoted lines stay identical."""

import json
from datetime import UTC, datetime

import pytest

from ladon.investigation import assess, initialize
from ladon.investigation_cli import investigation_main


def test_same_lines_different_bytes_reject(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"An assertion.\n")
    now = datetime.now(UTC)
    plan = initialize(source, tmp_path, now=now)
    source.write_bytes(b"An assertion.\r\n")
    with pytest.raises(ValueError, match="stale source digest"):
        assess(plan, tmp_path, now=now)


def test_symlink_loop_rejected_without_crash(tmp_path, capsys):

    source = tmp_path / "source.txt"
    source.write_text("An assertion.\n")
    plan = initialize(source, tmp_path)
    (tmp_path / "loop").symlink_to("loop")
    plan["scope"]["path"] = "loop"
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="unavailable"):
        assess(plan, tmp_path)
    assert investigation_main(["status", "--plan", str(plan_path), "--root", str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
    assert (
        investigation_main(
            [
                "init",
                "--text",
                str(tmp_path / "loop"),
                "--root",
                str(tmp_path),
                "--output",
                str(tmp_path / "new.json"),
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
