"""Installed help stays compact by default and discovers the live command tree."""

from __future__ import annotations

import subprocess
import sys

import pytest

from ladon.entrypoint import main


@pytest.mark.parametrize("arguments", [["-h"], ["--help"]])
def test_compact_help_prioritizes_reuse_and_points_to_full_catalog(arguments, capsys):
    assert main(arguments) == 0
    captured = capsys.readouterr()
    assert not captured.err
    assert "proof-search search type-text" in captured.out
    assert "proof-search discover" in captured.out
    assert "ladon -h --verbose" in captured.out
    assert "ladon proof-search discover --help" in captured.out
    assert "Type-text search is lexical" in captured.out
    assert "investigation contract" not in captured.out
    assert len(captured.out.splitlines()) <= 40


@pytest.mark.parametrize(
    "arguments",
    [["-h", "--verbose"], ["--verbose", "-h"], ["--help", "--verbose"], ["--verbose", "--help"]],
)
def test_verbose_help_includes_nested_commands_and_analyzer_options(arguments, capsys):
    assert main(arguments) == 0
    captured = capsys.readouterr()
    assert not captured.err
    for command in (
        "proof-search index prune",
        "proof-search goal complete",
        "proof-search proof slice",
        "proof-search discover",
        "investigation contract produce",
        "investigation contract review-probe",
        "investigation interpret",
        "theorem lineage",
        "proofir canonicalize",
        "result validate",
        "runset",
        "preview",
        "inspect",
        "findings",
        "atlas",
        "query",
        "diff",
        "cards",
        "workflow",
        "version",
        "doctor",
    ):
        assert f"  {command}" in captured.out
    assert "--max-modules" in captured.out
    assert "--repo-root" in captured.out
    assert "Analyzer options:" in captured.out


def test_verbose_catalog_tracks_parser_additions(monkeypatch, capsys):
    import ladon.proof_search_cli as proof_search

    original = proof_search.build_proof_search_parser

    def extended_parser():
        import argparse

        parser = original()
        operations = next(
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        )
        operations.add_parser("catalog-regression", help="Newly registered command.")
        return parser

    monkeypatch.setattr(proof_search, "build_proof_search_parser", extended_parser)
    assert main(["-h", "--verbose"]) == 0
    assert "proof-search catalog-regression  Newly registered command." in capsys.readouterr().out


def test_nested_help_keeps_command_specific_options(capsys):
    with pytest.raises(SystemExit) as result:
        main(["proof-search", "discover", "--help"])
    assert result.value.code == 0
    output = capsys.readouterr().out
    assert "--goal" in output
    assert "--local" in output
    assert "Common commands" not in output


@pytest.mark.parametrize("command", ["version", "doctor"])
@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_diagnostic_command_help_does_not_run_diagnostics(command, flag, monkeypatch, capsys):
    from ladon import entrypoint

    def unexpected_execution(*args, **kwargs):
        pytest.fail("Help must not execute diagnostics")

    monkeypatch.setattr(entrypoint, "version_main", unexpected_execution)
    monkeypatch.setattr(entrypoint, "doctor_main", unexpected_execution)
    assert main([command, flag]) == 0
    assert f"usage: ladon {command}" in capsys.readouterr().out


@pytest.mark.parametrize("arguments", [["--verbose"], ["--verbose", "--unknown"]])
def test_verbose_is_not_an_analysis_mode(arguments, capsys):
    with pytest.raises(SystemExit) as result:
        main(arguments)
    assert result.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize("arguments", [["-h"], ["-h", "--verbose"]])
def test_help_works_in_empty_directory_without_creating_analysis_files(arguments, tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", *arguments],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("usage: ladon")
    assert not result.stderr
    assert not list(tmp_path.iterdir())


def test_compact_help_does_not_import_the_analyzer():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from ladon.entrypoint import main; main(['-h']); "
                "assert 'ladon.cli' not in sys.modules; "
                "assert 'ladon.proof_search_cli' not in sys.modules"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
