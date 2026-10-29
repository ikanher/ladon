"""Explicit node budgets reach Lean, bind identity, and survive replay."""

import copy
import json
from pathlib import Path

import pytest

from ladon.correspondence_cli import proof_slice_main
from ladon.proof_slice import extract_proof_slice, slice_identity
from ladon.proof_slice_validation import validate_slice_shape

FIXTURE = Path(__file__).parent / "fixtures/correspondence_m1"


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "12", 1_048_577])
def test_api_rejects_invalid_budget_before_setup(value):
    with pytest.raises(ValueError, match="node budget"):
        extract_proof_slice(
            Path("/nonexistent-ladon-budget-test"), "Proof.lean", "Proof",
            "Correspondence.term", "bridge", max_nodes=value,
        )


@pytest.mark.parametrize("value", ["0", "-1", "1048577"])
def test_cli_rejects_invalid_budget(value, capsys):
    status = proof_slice_main([
        "--repo", str(FIXTURE), "--source", "Proof.lean", "--module", "Proof",
        "--declaration", "Correspondence.term", "--application", "bridge",
        "--max-nodes", value,
    ])
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


@pytest.mark.parametrize("scoped", [False, True])
def test_cli_low_budget_fails_and_explicit_high_budget_extracts(scoped, tmp_path):
    args = [
        "--repo", str(FIXTURE), "--source", "Proof.lean", "--module", "Proof",
        "--declaration", "Correspondence.term", "--application", "bridge",
    ] + (["--scoped"] if scoped else [])
    for budget, status in [(1, 2), (131_072, 0)]:
        output = tmp_path / f"slice-{budget}.json"
        assert proof_slice_main(args + ["--max-nodes", str(budget),
                                       "--output", str(output)]) == status
        result = json.loads(output.read_text())
        assert result["limits"]["nodes"] == budget
        assert result["complete"] is (status == 0)
        if status:
            assert "expression node count exceeds 1" in result["processReceipts"][-1]["stdout"]
        else:
            validate_slice_shape(result)
            assert result["sliceId"] == slice_identity(result)
            altered = copy.deepcopy(result)
            altered["limits"]["nodes"] += 1
            assert slice_identity(altered) != result["sliceId"]
            for invalid in [0, True, 1_048_577]:
                altered["limits"]["nodes"] = invalid
                with pytest.raises(ValueError, match="node budget"):
                    validate_slice_shape(altered)


def test_correspondence_replays_custom_budget(monkeypatch):
    from ladon import correspondence_check as check

    actual = extract_proof_slice(
        FIXTURE, "Proof.lean", "Proof", "Correspondence.term", "bridge",
        max_nodes=37_000, scoped=True,
    )
    record = json.loads((FIXTURE / "positive.json").read_text())
    plan = check.prepare_correspondence(record, actual, {"n": "n"})
    budgets = []
    original = check.extract_proof_slice

    def record_replay(*args, **kwargs):
        budgets.append(kwargs["max_nodes"])
        return original(*args, **kwargs)

    monkeypatch.setattr(check, "extract_proof_slice", record_replay)
    result = check.check_correspondence(plan, [], FIXTURE)
    assert result["conditionalValidity"] == "supported"
    assert budgets == [37_000, 37_000]
