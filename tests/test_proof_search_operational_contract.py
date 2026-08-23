from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon import proof_search_cli
from ladon.lean_toolchain import LeanToolchainError


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
    expected = {
        "exitClass": exit_class,
        "exitCode": exit_code,
        "operation": "index.status",
        "schema": "ladon-proof-search-terminal-v1",
        "status": status,
    }
    if exit_class == "operational":
        expected["diagnostic"] = {
            "code": "operational-failure",
            "message": "fixture I/O failure",
        }
    assert terminal == expected
    assert output.read_text(encoding="utf-8") == "prior-result\n"


def test_checker_preflight_retains_actionable_toolchain_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_toolchain(*_args: object, **_kwargs: object) -> object:
        raise LeanToolchainError("lake configuration failed: missing manifest")

    monkeypatch.setattr(proof_search_cli, "resolve_toolchain_context", fail_toolchain)
    status = proof_search_cli.proof_search_main(
        [
            "check",
            "candidate",
            "--repo-root",
            str(tmp_path),
            "--module",
            "Main",
            "--goal",
            "True",
            "--candidate",
            "True.intro",
            "--progress",
        ]
    )
    assert status == 1
    records = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    assert records[0]["status"] == "started"
    terminal = records[-1]
    assert terminal["exitClass"] == "operational"
    assert terminal["diagnostic"] == {
        "code": "toolchain-unavailable",
        "message": "lake configuration failed: missing manifest",
        "remediation": "Run 'ladon doctor --json' and correct the reported Lean/Lake posture.",
    }


@pytest.mark.parametrize(
    ("result_status", "exit_code", "progress_status"),
    [
        ("rejected", 0, "completed"),
        ("failed-checker", 1, "failed"),
        ("timeout", 1, "failed"),
    ],
)
def test_checker_payload_controls_process_and_progress_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    result_status: str,
    exit_code: int,
    progress_status: str,
) -> None:
    monkeypatch.setattr(
        proof_search_cli,
        "_dispatch",
        lambda _args: {"schema": "fixture", "status": result_status},
    )

    status = proof_search_cli.proof_search_main(
        [
            "check",
            "candidate",
            "--repo-root",
            str(tmp_path),
            "--module",
            "Main",
            "--goal",
            "True",
            "--candidate",
            "True.intro",
            "--format",
            "json",
            "--output",
            "-",
            "--progress",
        ]
    )

    streams = capsys.readouterr()
    assert status == exit_code
    assert json.loads(streams.out)["status"] == result_status
    progress = [json.loads(line) for line in streams.err.splitlines()]
    assert progress[-1]["status"] == progress_status
    assert progress[-1]["resultStatus"] == result_status
    assert progress[-1]["exitCode"] == exit_code


def test_discovery_operational_candidate_fails_process_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        proof_search_cli,
        "_dispatch",
        lambda _args: {
            "schema": "fixture",
            "status": "partial",
            "candidates": [
                {"name": "Main.good", "check": {"status": "accepted"}},
                {"name": "Main.failed", "check": {"status": "failed-checker"}},
            ],
        },
    )

    status = proof_search_cli.proof_search_main(
        [
            "discover",
            "--repo-root",
            str(tmp_path),
            "--module",
            "Main",
            "--goal",
            "True",
            "--candidate",
            "Main.good",
            "--format",
            "json",
            "--output",
            "-",
        ]
    )

    assert status == 1
    assert json.loads(capsys.readouterr().out)["status"] == "partial"
