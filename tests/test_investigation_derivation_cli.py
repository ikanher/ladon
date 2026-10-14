"""The installed CLI must expose v2 plans without changing the default v1 path."""

import json
import subprocess
import sys


def test_public_derivation_initialization(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("For positive x and y, multiply the inequality by y.\n")
    plan = tmp_path / "plan.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "investigation",
            "init",
            "--text",
            str(source),
            "--root",
            str(tmp_path),
            "--output",
            str(plan),
            "--derivations",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(plan.read_text())["version"] == 2
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "investigation",
            "finish",
            "--plan",
            str(plan),
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["schema"] == "ladon-investigation-status-v2"
