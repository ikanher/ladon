from __future__ import annotations

import json
from pathlib import Path

from ladon.proof_search_cli import proof_search_main


def test_progress_is_bounded_json_stderr_and_result_isolated_on_stdout(
    tmp_path: Path, capsys
) -> None:
    assert (
        proof_search_main(
            [
                "index",
                "status",
                "--repo-root",
                str(tmp_path),
                "--format",
                "json",
                "--progress",
            ]
        )
        == 0
    )
    streams = capsys.readouterr()
    assert json.loads(streams.out)["status"] == "unavailable"
    progress = [json.loads(line) for line in streams.err.splitlines()]
    assert progress == [
        {
            "operation": "index.status",
            "phase": "dispatch",
            "schema": "ladon-proof-search-progress-v1",
            "status": "started",
        },
        {
            "elapsedSeconds": progress[1]["elapsedSeconds"],
            "operation": "index.status",
            "phase": "dispatch",
            "schema": "ladon-proof-search-progress-v1",
            "status": "completed",
        },
    ]
    assert isinstance(progress[1]["elapsedSeconds"], float)
    assert progress[1]["elapsedSeconds"] >= 0
