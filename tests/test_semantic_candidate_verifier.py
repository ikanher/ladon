from __future__ import annotations

import pytest

from ladon.semantic_candidate_verifier import PatternRequest, verify_candidates


def test_candidate_batch_preserves_matches_residuals_and_stale_rows() -> None:
    request = PatternRequest("req", "Main", "Nat → Nat")
    rows = verify_candidates(request, [
        {"name": "exact", "type": "Nat → Nat"},
        {"name": "residual", "type": "Nat → Bool"},
        {"name": "old", "type": "Nat → Nat", "stale": True},
    ])
    assert [row.status for row in rows] == ["matched", "residual", "stale"]
    assert rows[0].match_kind == "exact"
    assert rows[1].residual_goals == ("Nat → Nat",)


def test_candidate_limits_and_request_validation() -> None:
    with pytest.raises(ValueError):
        PatternRequest("", "Main", "Nat")
    request = PatternRequest("req", "Main", "Nat", max_candidates=1)
    assert len(verify_candidates(request, [{"name": "a", "type": "Nat"}, {"name": "b", "type": "Nat"}])) == 1


def test_wildcard_matching_is_explicitly_labelled() -> None:
    row = verify_candidates(PatternRequest("req", "Main", "Nat → _"), [{"name": "f", "type": "Nat → Bool"}])[0]
    assert row.status == "matched"
    assert row.match_kind == "wildcard"
