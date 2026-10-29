"""Saved production is historical, while replay requires the current source/checker."""

import copy
import json

import pytest
from test_real_bound_native_records import FIXTURE

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_source import snapshot_identity


def saved():
    from ladon.real_bound_native_production import recorded_production

    fixture = json.loads(FIXTURE.read_text())
    terms = {r["goal"]["id"]: r["term"] for r in fixture["check"]["result"]["checks"]}
    return recorded_production(fixture["plan"], terms, fixture["check"], fixture["sourceText"])


def test_saved_success_inspects_as_historical_without_authority():
    from ladon.real_bound_native_production import inspect_real_bound

    result = inspect_real_bound(saved())
    assert result["status"] == "validated-historical"
    assert result["authority"] == "none"
    assert result["paperNormBridge"] == "unresolved"
    assert result["contract"]["loss"] == 0


def test_saved_receipt_does_not_gain_current_identity():
    from ladon.real_bound_native_production import inspect_real_bound

    result = inspect_real_bound(saved())
    assert result["freshCheck"] is False
    assert result["evidenceAuthentication"] == "not-established"


@pytest.mark.parametrize("target", ["source", "record", "receipt", "term"])
def test_rehashed_saved_mutations_fail_deterministic_inspection(target):
    from ladon.real_bound_native_production import inspect_real_bound

    production = copy.deepcopy(saved())
    if target == "source":
        production["sourceText"] += "\n-- changed\n"
    elif target == "record":
        production["artifacts"][-1]["payload"]["record"]["loss"] = 5
    elif target == "term":
        production["request"]["terms"]["scalar-semantics"] = "by trivial"
    else:
        production["check"]["result"]["checks"][1]["evidence"]["completion"]["trust"]["accepted"] = False
    production["snapshotId"] = snapshot_identity(production)
    with pytest.raises(ValueError):
        inspect_real_bound(production)


def test_closed_saved_shape_rejects_claimed_extra_authority():
    from ladon.real_bound_native_production import inspect_real_bound

    production = saved()
    production["nativeProofIsAuthoritative"] = True
    production["snapshotId"] = snapshot_identity(production)
    with pytest.raises(ValueError):
        inspect_real_bound(production)


def test_offline_inspection_and_report_cli_preserve_historical_state(tmp_path, capsys):
    source = tmp_path / "recorded.json"
    source.write_text(json.dumps(saved()))
    for operation in ("inspect-real-bound", "report-real-bound", "inspect"):
        status = contract_main([operation, "--input", str(source)])
        result = json.loads(capsys.readouterr().out)
        assert status == 0
        assert result["status"] == "validated-historical"
        assert result["authority"] == "none"


def test_missing_recorded_goal_receipts_fail_inspection():
    from ladon.real_bound_native_production import inspect_real_bound

    production = saved()
    production["check"]["result"]["checks"][1]["evidence"]["completion"]["processReceipts"] = []
    production["snapshotId"] = snapshot_identity(production)
    with pytest.raises(ValueError):
        inspect_real_bound(production)
