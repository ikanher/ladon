from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.proofir_v3 import validate_envelope_batch


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lean_integration"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_installed_cli_emits_batch_closed_semantic_evidence() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "check",
            "candidate",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ value : Nat, value = value",
            "--candidate",
            "LadonFixture.fixtureIdentity",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "ladon-semantic-candidate-check-result-v1"
    assert payload["status"] == "accepted"
    assert [row["artifactKind"] for row in payload["artifacts"]] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    validate_envelope_batch(payload["artifacts"])
