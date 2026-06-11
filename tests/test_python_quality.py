from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ladon.quality import (
    collect_radon_complexity_issues,
    collect_vulture_issues,
    strict_quality_issues,
)


def test_strict_quality_rejects_c_or_worse_complexity(tmp_path: Path) -> None:
    source = tmp_path / "bad_complexity.py"
    source.write_text(
        "\n".join(
            [
                "def bad_complexity(x):",
                *[f"    if x == {index}: return {index}" for index in range(12)],
                "    return -1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    issues = collect_radon_complexity_issues([source])

    assert any(issue.tool == "radon-cc" for issue in issues)
    assert any(issue.rank >= "C" for issue in issues)


def test_strict_quality_rejects_high_confidence_vulture_findings(tmp_path: Path) -> None:
    source = tmp_path / "dead_code.py"
    source.write_text(
        "def reachable_function():\n    return 1\n    print('never')\n",
        encoding="utf-8",
    )

    issues = collect_vulture_issues([source], min_confidence=80)

    assert any(issue.tool == "vulture" for issue in issues)


def test_project_strict_quality_has_no_radon_or_vulture_issues() -> None:
    issues = strict_quality_issues([Path("src"), Path("tests"), Path("scripts")])

    assert issues == []


def test_strict_quality_pytest_gate_is_scoped_to_maintained_tests(
    monkeypatch, tmp_path: Path
) -> None:
    spec = importlib.util.spec_from_file_location(
        "python_quality_script",
        Path(__file__).parents[1] / "scripts" / "python_quality.py",
    )
    assert spec is not None
    assert spec.loader is not None
    python_quality = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(python_quality)

    for directory in ("src", "tests", "scripts"):
        (tmp_path / directory).mkdir()

    commands: list[tuple[str, list[str], Path]] = []
    monkeypatch.setattr(python_quality, "strict_quality_issues", lambda _targets: [])
    monkeypatch.setattr(
        python_quality.compileall, "compile_dir", lambda _path, **_kwargs: True
    )
    monkeypatch.setattr(
        python_quality,
        "run_command",
        lambda label, command, cwd: commands.append((label, command, cwd)) or 0,
    )

    status = python_quality.run_strict(tmp_path, ["src", "tests", "scripts"])

    assert status == 0
    assert commands == [
        ("pytest", [sys.executable, "-m", "pytest", "-q", "tests"], tmp_path)
    ]
