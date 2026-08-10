from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.semantic_candidate_worker import SemanticCandidateRequest

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lean_integration"


@pytest.mark.parametrize(
    ("module", "goal", "candidate"),
    [
        ("Main\n#eval 1", "True", "Main.value"),
        ("Main", "True", "Main.value\nexact injected"),
        ("Main", "True := by trivial\n#check False", "Main.value"),
    ],
)
def test_generated_probe_rejects_command_injection(
    tmp_path: Path, module: str, goal: str, candidate: str
) -> None:
    with pytest.raises(ValueError):
        SemanticCandidateRequest(tmp_path, module, goal, candidate)


def test_python_boundary_defers_name_grammar_to_lean(tmp_path: Path) -> None:
    request = SemanticCandidateRequest(
        tmp_path, "Main", "True", "Main.value+1"
    )
    assert request.candidate == "Main.value+1"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_lean_name_parser_rejects_non_identifier_candidate() -> None:
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
            "True",
            "--candidate",
            "And.intro+True",
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
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "rejected"
    assert payload["diagnostic"]["code"] == "checker-rejected"
    assert "invalid Lean name" in payload["diagnostic"]["message"]


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_real_check_claims_elaborator_route_not_kernel_theorem_truth() -> None:
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
    guarantee = payload["artifacts"][1]["payload"]["guarantee"]
    assert guarantee["authorityBasis"] == "elaborator-check"
    assert guarantee["scope"] == "route"
    assert "residual premises" in guarantee["statement"]
