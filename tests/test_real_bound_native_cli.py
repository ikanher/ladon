"""Native Real production never accepts assertions or saved successes as plans."""

import json

from ladon.proof_contract_cli import contract_main


def test_native_plan_cli_rejects_claim(tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_text('{"derivativeAdmission":"checked"}')
    status = contract_main(["plan-real-bound", "--input", str(source), "--root", str(tmp_path)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


def test_native_production_rejects_saved_receipt(tmp_path, capsys):
    source = tmp_path / "input.json"
    terms = tmp_path / "terms.json"
    source.write_text('{"status":"admitted","authority":"fresh-lean-check"}')
    terms.write_text('{"predicate-admission":"by trivial","scalar-semantics":"by trivial"}')
    status = contract_main(["admit-real-bound", "--input", str(source), "--proofs", str(terms),
                            "--root", str(tmp_path)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
