"""The binding commands reject caller claims before entering a Lean worker."""

import json

from ladon.proof_contract_cli import contract_main


def test_binding_plan_cli_rejects_unchecked_observation(tmp_path, capsys):
    path = tmp_path / "request.json"
    measure = tmp_path / "measure.json"
    path.write_text(json.dumps({"admitted": True}))
    measure.write_text('{"declaration":"Other.sample","arguments":[]}')
    status = contract_main(["plan-bound-prefix", "--root", str(tmp_path), "--input", str(path),
                            "--measure", str(measure)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


def test_binding_check_cli_rejects_saved_acceptance(tmp_path, capsys):
    path = tmp_path / "plan.json"
    proof = tmp_path / "proof.json"
    path.write_text('{"predicateAdmission":"checked"}')
    proof.write_text('{"term":"by trivial"}')
    status = contract_main(["check-bound-prefix", "--root", str(tmp_path), "--input", str(path),
                            "--proof", str(proof)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
