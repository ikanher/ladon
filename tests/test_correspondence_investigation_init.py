"""Portable CLI acceptance tests for the v3 plan selector.

These exercise only init and JSON publication. They never invoke Lean or claim
that any mathematical statement has been checked.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[1]


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CHECKOUT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", "investigation", *args],
        cwd=CHECKOUT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_legacy_initialization(tmp_path, root, source):
    v1 = tmp_path / "v1.json"
    result = invoke("init", "--text", str(source), "--root", str(root), "--output", str(v1))
    assert result.returncode == 0, result.stderr + result.stdout
    plan1 = json.loads(v1.read_text(encoding="utf-8"))
    assert plan1["version"] == 1
    assert plan1["claims"] == []
    assert plan1["scope"]["path"] == "note.md"

    v2 = tmp_path / "v2.json"
    result = invoke(
        "init", "--text", str(source), "--root", str(root), "--output", str(v2), "--derivations"
    )
    assert result.returncode == 0, result.stderr + result.stdout
    plan2 = json.loads(v2.read_text(encoding="utf-8"))
    assert plan2["version"] == 2
    assert plan2["claims"] == []
    assert plan2["scope"] == plan1["scope"]

    return plan1


def test_correspondence_flag_selects_v3_without_changing_v1_or_v2(tmp_path: Path) -> None:
    root = tmp_path / "sources"
    root.mkdir()
    source = root / "note.md"
    source.write_text("A source statement.\n", encoding="utf-8")

    plan1 = _assert_legacy_initialization(tmp_path, root, source)

    v3 = tmp_path / "v3.json"
    result = invoke(
        "init", "--text", str(source), "--root", str(root), "--output", str(v3), "--correspondence"
    )
    assert result.returncode == 0, result.stderr + result.stdout
    plan3 = json.loads(v3.read_text(encoding="utf-8"))
    assert plan3["version"] == 3
    assert plan3["scope"] == plan1["scope"]
    assert plan3["units"] == plan1["units"]
    assert plan3["claims"] == []
    assert plan3["correspondenceBundles"] == []
    assert plan3["responses"] == []
    assert plan3["reconciliations"] == []


def test_correspondence_and_derivations_cannot_be_combined(tmp_path: Path) -> None:
    root = tmp_path / "sources"
    root.mkdir()
    source = root / "note.md"
    source.write_text("A source statement.\n", encoding="utf-8")
    correspondence = tmp_path / "correspondence.json"
    v2 = tmp_path / "v2.json"
    for option, destination in (("--correspondence", correspondence), ("--derivations", v2)):
        result = invoke(
            "init", "--text", str(source), "--root", str(root), "--output", str(destination), option
        )
        assert result.returncode == 0, result.stderr + result.stdout

    output = tmp_path / "combined.json"
    result = invoke(
        "init", "--text", str(source), "--root", str(root), "--output", str(output),
        "--correspondence", "--derivations",
    )
    assert result.returncode != 0
    assert not output.exists()
