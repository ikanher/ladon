"""A report must not replace an external Lean input after source observation."""
from __future__ import annotations

import json

import pytest

from ladon.proof_search_cli import proof_search_main


@pytest.mark.parametrize("protected", [
    "External.lean", "Init.olean", "Init.olean.server", "Init.olean.private",
    "Init.ir", "Init.ir.sig", "lean", "lake", "diagnostic.txt",
])
def test_report_rejects_external_input_collision_before_execution(tmp_path, capsys, protected):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Owner.lean").write_text("example : True := by\n  skip\n")
    destination = tmp_path / protected
    destination.write_text("retained input bytes")
    common = [
        "--repo-root", str(repo), "--module", "Owner", "--format", "json",
        "--lean-path", str(tmp_path / "lean"), "--lake-path", str(tmp_path / "lake"),
        "--output", str(destination),
    ]
    if protected == "diagnostic.txt":
        selection = ["diagnostic", "--diagnostic-file", str(destination)]
    else:
        selection = ["capture", "--source", "Owner.lean", "--line", "2", "--column", "6"]
    code = proof_search_main(["goal", *selection, *common])
    streams = capsys.readouterr()
    assert code == 2
    assert streams.out == ""
    assert json.loads(streams.err)["diagnostic"]["code"] == "source-report-destination"
    assert destination.read_text() == "retained input bytes"
