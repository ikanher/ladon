from __future__ import annotations

import json
import subprocess
import sys


def test_public_command_does_not_finish_while_source_work_remains(tmp_path):
    text = tmp_path / "exposition.txt"
    text.write_text("First assertion.\nSecond assertion.\n")
    plan = tmp_path / "investigation.json"
    base = [sys.executable, "-m", "ladon.entrypoint", "investigation"]
    initialized = subprocess.run(base + ["init", "--text", str(text), "--root", str(tmp_path),
        "--output", str(plan), "--minutes", "90", "--unit-lines", "1"],
        capture_output=True, text=True, check=False)
    assert initialized.returncode == 0, initialized.stderr
    original = plan.read_bytes()
    finished = subprocess.run(base + ["finish", "--plan", str(plan), "--root", str(tmp_path)],
        capture_output=True, text=True, check=False)
    assert finished.returncode == 2, finished.stderr
    report = json.loads(finished.stdout)
    assert report["status"] == "continue"
    assert report["mayFinalize"] is False
    assert len(report["next"]) == 2
    assert plan.read_bytes() == original
    overwritten = subprocess.run(base + ["init", "--text", str(text), "--root", str(tmp_path),
        "--output", str(plan)], capture_output=True, text=True, check=False)
    assert overwritten.returncode == 2
    assert plan.read_bytes() == original
