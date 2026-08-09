from __future__ import annotations

import json

from ladon.theorem_lineage_cli import _progress


def test_lineage_progress_is_versioned_json_on_stderr(capsys) -> None:
    _progress("planning", "Fixture.target")
    event = json.loads(capsys.readouterr().err)
    assert event == {"schema": "ladon-theorem-lineage-progress-v1", "phase": "planning", "detail": "Fixture.target"}
