from __future__ import annotations

from ladon.proof_difference import DifferenceRequest, analyze_difference


def test_difference_and_route_card_are_deterministic() -> None:
    exact = analyze_difference(DifferenceRequest("P", "P", module="Main"))
    mismatch = analyze_difference(DifferenceRequest("P", "Q", module="Main"))
    assert exact["classification"] == "applicable"
    assert mismatch["classification"] == "not-applicable"
    assert exact["routeCard"]["identity"] != mismatch["routeCard"]["identity"]


def test_casefold_difference_is_not_silently_accepted() -> None:
    result = analyze_difference(DifferenceRequest("Nat", "nat"))
    assert result["classification"] == "representation-boundary"
    assert result["routeCard"]["accepted"] is False
