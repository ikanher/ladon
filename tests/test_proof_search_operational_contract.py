from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon import proof_search_cli


def _arguments(tmp_path: Path, output: Path) -> list[str]:
    return [
        "index",
        "status",
        "--repo-root",
        str(tmp_path),
        "--format",
        "json",
        "--output",
        str(output),
    ]


@pytest.mark.parametrize(
    ("failure", "exit_code", "exit_class", "status"),
    [
        (KeyboardInterrupt(), 130, "interrupted", "interrupted"),
        (OSError("fixture I/O failure"), 1, "operational", "failed"),
    ],
)
def test_terminal_failure_is_one_json_record_and_preserves_prior_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: BaseException,
    exit_code: int,
    exit_class: str,
    status: str,
) -> None:
    output = tmp_path / "result.json"
    output.write_text("prior-result\n", encoding="utf-8")

    def fail_dispatch(_args: object) -> object:
        raise failure

    monkeypatch.setattr(proof_search_cli, "_dispatch", fail_dispatch)

    assert proof_search_cli.proof_search_main(_arguments(tmp_path, output)) == exit_code
    streams = capsys.readouterr()
    assert streams.out == ""
    terminal = json.loads(streams.err)
    assert streams.err.count("\n") == 1
    assert terminal == {
        "exitClass": exit_class,
        "exitCode": exit_code,
        "operation": "index.status",
        "schema": "ladon-proof-search-terminal-v1",
        "status": status,
    }
    assert output.read_text(encoding="utf-8") == "prior-result\n"
