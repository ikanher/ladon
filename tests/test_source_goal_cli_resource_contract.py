"""Unsupported execution bounds are invocation errors before binary resolution."""
from __future__ import annotations

import json

import pytest

from ladon.proof_search_cli import proof_search_main


@pytest.mark.parametrize(("option", "value"), [
    ("--timeout-seconds", "601"), ("--max-output-mib", "65"),
    ("--max-rss-mib", "65537"), ("--timeout-seconds", "nan"),
    ("--timeout-seconds", "inf"), ("--max-rss-mib", "0"),
])
def test_resource_arguments_use_the_api_supported_range(tmp_path, capsys, option, value):
    (tmp_path / "Owner.lean").write_text("example : True := by\n  skip\n")
    code = proof_search_main([
        "goal", "capture", "--repo-root", str(tmp_path), "--source", "Owner.lean",
        "--module", "Owner", "--line", "2", "--column", "6",
        "--lean-path", "/absent/lean", "--lake-path", "/absent/lake", option, value,
    ])
    output = capsys.readouterr()
    assert code == 2
    assert output.out == ""
    assert json.loads(output.err)["diagnostic"]["code"] == "invalid-goal-bounds"
