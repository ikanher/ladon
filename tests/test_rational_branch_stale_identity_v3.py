"""Same-name branch and context edits must invalidate accepted branch checks."""
from __future__ import annotations

import copy

import pytest
from test_rational_branch_receipts_v3 import (
    _assert_no_support,
    _branch,
    _goal,
    _plan,
    _replay_hook,
    _terms,
    request,
)

from ladon.proof_contract_rational_probes import check_rational_branch_probe


@pytest.mark.parametrize("changed_field", ["branch", "baseGoal"])
def test_same_display_names_cannot_reuse_positive_receipt_after_semantic_change(
    monkeypatch, changed_field
):
    original = request()
    old_plan = _plan(monkeypatch, original)
    calls = _replay_hook(monkeypatch)
    accepted = check_rational_branch_probe(
        original, old_plan["planId"], _terms(old_plan)
    )
    assert accepted["status"] == "checked-rational-branch", accepted
    old_cache = accepted["cache"]
    replay_count = len(calls)

    changed = copy.deepcopy(original)
    if changed_field == "branch":
        # Keep the finding and constraint display IDs fixed; change only its rule.
        changed["branch"] = _branch("gt")
        assert changed["branch"]["originalFinding"]["id"] == (
            original["branch"]["originalFinding"]["id"]
        )
        assert changed["branch"]["constraints"][0]["id"] == (
            original["branch"]["constraints"][0]["id"]
        )
    else:
        # Keep variable names fixed; change the formal context's conclusion.
        changed["baseGoal"] = _goal("gt")
        assert changed["baseGoal"]["variables"] == original["baseGoal"]["variables"]

    regenerated = _plan(monkeypatch, changed)
    assert regenerated["planId"] != old_plan["planId"]
    stale = check_rational_branch_probe(
        changed,
        old_plan["planId"],
        _terms(old_plan),
        cached_result=old_cache,
    )
    assert stale["status"] in {"rejected", "stale-input"}
    assert stale["reason"] == "plan-id-mismatch"
    _assert_no_support(stale)
    # The stale identity is rejected before any old cached evidence can skip replay.
    assert len(calls) == replay_count
