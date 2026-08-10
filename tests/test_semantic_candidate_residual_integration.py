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


def _assert_residual_check_subjects(check: dict[str, object]) -> None:
    results = check["payload"]["results"]  # type: ignore[index]
    assert results[0]["subjectRef"]["kind"] == "candidate-application"
    assert results[0]["result"] == "accepted"
    assert results[1]["subjectRef"]["kind"] == "statement"
    assert results[1]["result"] == "unchecked"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_lean_application_emits_substitutions_residuals_and_context() -> None:
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
            "True ∧ True",
            "--candidate",
            "And.intro",
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
    payload = json.loads(completed.stdout)
    assert payload["status"] == "applicable-with-residuals"
    assert [row["artifactKind"] for row in payload["artifacts"]] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.attempt-log",
    ]
    validate_envelope_batch(payload["artifacts"])
    attempt = payload["artifacts"][2]
    _assert_residual_check_subjects(payload["artifacts"][1])
    assert len(attempt["payload"]["summary"]["residualPremiseRefs"]) == 2
    assert len(attempt["payload"]["attempts"][0]["substitutions"]) == 4
    context = attempt["extensions"]["ladon.lean-attempt-context/v1"]
    assert context["localContextRef"]["kind"] == "local-context"
    assert attempt["payload"]["summary"]["outcome"] == "incomplete"
    assert attempt["limitations"][0]["id"] == "application-has-residual-premises"
