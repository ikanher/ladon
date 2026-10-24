"""The documented native propagation fixture runs through ordinary commands."""

import json
from pathlib import Path

from test_proof_contract_cli import invoke


def test_documented_native_example_propagates_and_replays(tmp_path):
    fixture = Path(__file__).parent / "fixtures/proof_contract_propagation"
    # Missing or stale example artifacts fail before any product invocation.
    assert json.loads((fixture / "request.json").read_text())["goalRef"]["kind"] == "statement"
    output = tmp_path / "analysis.json"
    result = invoke("propagate", "--derivation", fixture / "graph.json",
                    "--contract", fixture / "contract.json", "--request", fixture / "request.json",
                    "--analysis-id", "analysis:example", "--output", output)
    assert result.returncode == 0, result.stdout + result.stderr
    inspected = invoke("inspect", "--input", output, "--context", fixture / "context.json")
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    analysis = json.loads(inspected.stdout)
    assert analysis["payload"]["result"]["complete"] is True
    assert analysis["payload"]["result"]["authority"] == "conditional-profile"
