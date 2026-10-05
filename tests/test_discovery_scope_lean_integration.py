from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, timeout=120, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
@pytest.mark.parametrize(("scope", "freshness"), [("repository", "stored"), ("module", "verify")])
def test_console_discovers_and_checks_imported_lemma(
    tmp_path: Path, scope: str, freshness: str,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "lean_integration"
    shutil.copyfile(fixture / "lean-toolchain", repository / "lean-toolchain")
    (repository / "lakefile.toml").write_text(
        'name = "discovery_scope"\nversion = "0.1.0"\n'
        'defaultTargets = ["Main"]\n[[lean_lib]]\nname = "Main"\n'
        '[[lean_lib]]\nname = "Helpers"\n',
        encoding="utf-8",
    )
    (repository / "Helpers.lean").write_text(
        "namespace Helpers\ntheorem useful : True := True.intro\nend Helpers\n",
        encoding="utf-8",
    )
    (repository / "Main.lean").write_text(
        "import Helpers\nnamespace Main\ntheorem localFact : True := True.intro\nend Main\n",
        encoding="utf-8",
    )
    _run(["lake", "build"], repository)
    console = os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))
    common = ["--repo-root", str(repository), "--format", "json"]
    _run([console, "proof-search", "index", "build", *common], tmp_path)
    command = [
        console, "proof-search", "discover", *common,
        "--module", "Main", "--goal", "True", "--pattern", "True",
        "--scope", scope, "--freshness", freshness,
        "--max-candidates", "1", "--scratch-mode", "advisory", "--projection", "audit",
    ]
    if scope == "module":
        command.extend(["--root", "Helpers"])

    result = json.loads(_run(command, tmp_path).stdout)

    assert result["request"]["module"] == "Main"
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["name"] == "Helpers.useful"
    assert candidate["check"]["status"] == "accepted"
    assert candidate["check"]["scratch"]["status"] == "compiled"
