from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

from lean_integration_gate import (  # noqa: E402
    assert_declaration_evidence,
    json_strings,
)


def test_reference_fixture_pins_a_finite_lean_toolchain() -> None:
    fixture = REPO_ROOT / "tests" / "fixtures" / "lean_integration"

    assert fixture.joinpath("lean-toolchain").read_text(encoding="utf-8") == (
        "leanprover/lean4:v4.32.1\n"
    )
    assert "[[lean_lib]]" in fixture.joinpath("lakefile.toml").read_text(
        encoding="utf-8"
    )
    assert "fixtureIdentity" in fixture.joinpath("LadonFixture.lean").read_text(
        encoding="utf-8"
    )


def test_json_strings_walks_nested_report_data() -> None:
    payload = {"phase": {"rows": [{"declaration": "Fixture.value"}]}}

    assert list(json_strings(payload)) == ["Fixture.value"]


def test_declaration_evidence_requires_expected_fixture_name(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "declarations": [
                    {"name": "LadonFixture.fixtureIdentity"},
                ]
            }
        ),
        encoding="utf-8",
    )

    assert_declaration_evidence(report)


def test_lean_gate_requires_explicit_candidate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/lean_integration_gate.py", "--required"],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "--candidate" in result.stderr
