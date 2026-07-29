"""Installed-distribution contract for the caller-neutral theorem CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ladon.installed_contract import invoke


def test_installed_theorem_capsule_help_is_caller_neutral() -> None:
    result = invoke(analyzer_command(), "theorem", "--help")

    assert result.returncode == 0
    assert result.stderr == ""
    assert all(
        command in result.stdout
        for command in ("plan", "materialize", "replay", "extract")
    )
    assert "LLM" not in result.stdout


def analyzer_command() -> list[str]:
    """Return the installed analyzer selected by distribution smoke."""

    return [
        os.environ.get(
            "LADON_CONSOLE",
            str(Path(sys.executable).with_name("ladon")),
        )
    ]
