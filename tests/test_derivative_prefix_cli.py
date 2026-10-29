"""Public derivative operations reject caller assertions and foreign receipts."""

import json

from ladon.proof_contract_cli import contract_main


def test_derivative_plan_rejects_caller_assertions(tmp_path, capsys):
    path = tmp_path / "observation.json"
    path.write_text('{"isJoint":true,"admitted":true}')
    result = contract_main(["plan-derivative-prefix", "--root", str(tmp_path), "--input", str(path)])
    assert result == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


def test_derivative_check_rejects_receipt_as_plan(tmp_path, capsys):
    path = tmp_path / "receipt.json"
    proof = tmp_path / "proof.json"
    path.write_text('{"derivativeAdmission":"checked"}')
    proof.write_text('{"term":"by trivial"}')
    result = contract_main(["check-derivative-prefix", "--root", str(tmp_path), "--input", str(path),
                            "--proof", str(proof)])
    assert result == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
