"""The ordinary producer CLI handles formal statements and unsupported features."""

import json
from copy import deepcopy
from pathlib import Path

from test_proof_contract_cli import invoke

ROOT = Path(__file__).resolve().parent / "fixtures/proof_contract_production"


def _assert_supported_snapshot(produced, destination):
    assert produced.returncode == 0, produced.stdout + produced.stderr
    snapshot = json.loads(destination.read_text())
    assert snapshot["status"] == "extracted"
    assert snapshot["fidelity"] == "attributed-unreviewed"
    return snapshot


def _assert_inspection_matches(inspected, snapshot):
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    assert json.loads(inspected.stdout) == snapshot


def _assert_unsupported_result(unsupported):
    assert unsupported.returncode == 0, unsupported.stdout + unsupported.stderr
    result = json.loads(unsupported.stdout)
    assert result["status"] == "unsupported"
    assert result["contract"] is None
    assert result["residuals"]
    assert result["coverage"]["statementFeatures"] == "unsupported"


def test_formal_cli_snapshot_inspection_and_unsupported_diagnostics(tmp_path):
    destination = tmp_path / "formal.json"
    produced = invoke("produce", "--channel", "formal", "--root", ROOT,
                      "--file", "ProducerCases.lean", "--module", "ProducerCases",
                      "--declaration", "ProducerCases.supported_base", "--output", destination)
    snapshot = _assert_supported_snapshot(produced, destination)
    inspected = invoke("inspect", "--root", ROOT, "--input", destination)
    _assert_inspection_matches(inspected, snapshot)
    unsupported = invoke("produce", "--channel", "formal", "--root", ROOT,
                         "--file", "ProducerCases.lean", "--module", "ProducerCases",
                         "--declaration", "ProducerCases.unsupported_membership")
    _assert_unsupported_result(unsupported)


def test_formal_cli_rejects_rehashed_stale_environment(tmp_path):
    from ladon.proof_contract_formal import produce_formal_snapshot
    from ladon.proof_contract_source import snapshot_identity

    frozen = produce_formal_snapshot(ROOT, "ProducerCases.lean", "ProducerCases",
                                     "ProducerCases.supported_base")
    altered = deepcopy(frozen)
    altered["environment"] = "sha256:" + "0" * 64
    altered["snapshotId"] = snapshot_identity(altered)
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(altered))
    result = invoke("inspect", "--root", ROOT, "--input", path)
    assert result.returncode == 2
    assert "stale" in result.stdout


def test_memory_failure_is_nonzero_and_keeps_stop_instruction(tmp_path, monkeypatch, capsys):
    from ladon import proof_contract_cli
    from ladon.resource_limits import memory_limit_message

    limited = {"channel": "formal", "status": "unavailable", "contract": None,
               "residuals": [{"code": "lean-memory-limit", "feature": "statement",
                   "message": memory_limit_message(12 * 1024**3, 13 * 1024**3)}]}
    monkeypatch.setattr(proof_contract_cli, "_produce", lambda _args: limited)
    status = proof_contract_cli.contract_main(["produce", "--channel", "formal",
                                               "--root", str(tmp_path)])
    assert status != 0
    observed = json.loads(capsys.readouterr().out)
    assert observed == limited
    assert "Stop progress and report back to user:" in observed["residuals"][0]["message"]
