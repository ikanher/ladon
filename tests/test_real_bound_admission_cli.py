"""Public law planning/checking preserves the unresolved contract boundary."""

import json

from ladon.proof_contract_cli import contract_main


def test_new_plan_command_rejects_injected_acceptance(tmp_path, capsys):
    path = tmp_path / "request.json"
    path.write_text(json.dumps({"admitted": True}))
    status = contract_main(["plan-prefix-admission", "--root", str(tmp_path), "--input", str(path)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


def test_new_check_command_rejects_foreign_plan_without_worker(tmp_path, capsys):
    path = tmp_path / "plan.json"
    terms = tmp_path / "terms.json"
    path.write_text(json.dumps({"admission": "checked"}))
    terms.write_text("{}")
    status = contract_main(["check-prefix-laws", "--root", str(tmp_path),
                            "--input", str(path), "--terms", str(terms)])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
