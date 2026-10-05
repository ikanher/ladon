from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.cli_execution import EXIT_INVOCATION, EXIT_OPERATIONAL
from ladon.entrypoint import main
from ladon.result_manifest_io import MAX_RESULT_BYTES, ResultManifestError, load_result_manifest

FIXTURE = Path(__file__).parent / "fixtures" / "result_manifest" / "finite-map.json"


def forbidden(*_args, **_kwargs):
    raise AssertionError("offline result validation attempted external activity")


def test_cli_is_offline_and_json_text_preserve_same_evidence(monkeypatch, capsys) -> None:
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    assert main(["result", "validate", str(FIXTURE)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert len(captured.out.encode()) <= MAX_RESULT_BYTES
    assert main(["result", "validate", str(FIXTURE), "--format", "text"]) == 0
    text = capsys.readouterr().out
    decoded = {key: json.loads(value) for key, value in (line.split(": ", 1) for line in text.splitlines())}
    assert decoded == payload


def test_general_cli_also_dispatches_result(capsys) -> None:
    from ladon.cli import main as general_main

    assert general_main(["result", "validate", str(FIXTURE)]) == 0
    assert json.loads(capsys.readouterr().out)["validationScope"] == "offline-manifest-integrity"


@pytest.mark.parametrize("arguments", [["result"], ["result", "inspect"], ["result", "validate"]])
def test_bad_invocations_have_structured_stderr(arguments, capsys) -> None:
    assert main(arguments) == EXIT_INVOCATION
    output = capsys.readouterr()
    assert output.out == ""
    assert json.loads(output.err)["exitClass"] == "invocation"


def test_missing_input_is_operational_failure(tmp_path: Path, capsys) -> None:
    assert main(["result", "validate", str(tmp_path / "missing.json")]) == EXIT_OPERATIONAL
    output = capsys.readouterr()
    assert output.out == ""
    assert json.loads(output.err)["diagnostic"]["code"] == "manifest-unreadable"


def test_invalid_manifest_has_no_success_output(tmp_path: Path, capsys) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema":"first","schema":"second"}')
    assert main(["result", "validate", str(path)]) == EXIT_INVOCATION
    output = capsys.readouterr()
    assert output.out == ""
    assert json.loads(output.err)["diagnostic"]["code"] == "manifest-invalid"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX regular-file guard")
def test_fifo_is_rejected_without_waiting_for_writer(tmp_path: Path) -> None:
    path = tmp_path / "input.fifo"
    os.mkfifo(path)
    with pytest.raises(ResultManifestError, match="regular file"):
        load_result_manifest(path)


def test_console_entrypoint_outside_checkout(tmp_path: Path) -> None:
    console = os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))
    result = subprocess.run(
        [console, "result", "validate", str(FIXTURE.resolve())],
        cwd=tmp_path, capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["canonicalResolution"]["status"] == "not-assessed"
