from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon import proofir_v3_cli


def test_artifact_cli_interruption_is_one_versioned_terminal_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    source = tmp_path / "artifact.json"
    source.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        proofir_v3_cli, "validate_envelope", lambda _value: _interrupt()
    )

    assert proofir_v3_cli.proofir_v3_main(["validate", str(source)]) == 130
    streams = capsys.readouterr()
    assert streams.out == ""
    assert streams.err.count("\n") == 1
    assert json.loads(streams.err) == {
        "exitClass": "interrupted",
        "exitCode": 130,
        "operation": "validate",
        "schema": "ladon-proofir-terminal-v1",
        "status": "interrupted",
    }


def test_artifact_cli_operational_failure_is_json(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.json"
    assert proofir_v3_cli.proofir_v3_main(["inspect", str(missing)]) == 1
    streams = capsys.readouterr()
    assert streams.out == ""
    assert streams.err.count("\n") == 1
    terminal = json.loads(streams.err)
    assert terminal["schema"] == "ladon-proofir-terminal-v1"
    assert terminal["exitClass"] == "operational"
    assert terminal["exitCode"] == 1
    assert terminal["operation"] == "inspect"
    assert terminal["status"] == "failed"
    assert terminal["diagnostic"]["code"] == "operational-failure"


def test_artifact_cli_parser_failure_returns_instead_of_exiting(capsys) -> None:
    assert proofir_v3_cli.proofir_v3_main(["validate"]) == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    assert streams.err.count("\n") == 1
    terminal = json.loads(streams.err)
    assert terminal["schema"] == "ladon-proofir-terminal-v1"
    assert terminal["exitClass"] == "invocation"
    assert terminal["operation"] == "validate"


def _interrupt() -> None:
    raise KeyboardInterrupt
