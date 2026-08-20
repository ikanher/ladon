from __future__ import annotations

from ladon.proof_difference import DifferenceRequest, analyze_difference


def test_difference_and_route_card_are_deterministic() -> None:
    exact = analyze_difference(DifferenceRequest("P", "P", module="Main"))
    mismatch = analyze_difference(DifferenceRequest("P", "Q", module="Main"))
    assert exact["classification"] == "exact-rendered-conclusion"
    assert mismatch["classification"] == "no-structural-match"
    assert exact["routeCard"]["accepted"] is False
    assert exact["routeCard"]["identity"] != mismatch["routeCard"]["identity"]


def test_casefold_difference_is_not_silently_accepted() -> None:
    result = analyze_difference(DifferenceRequest("Nat", "nat"))
    assert result["classification"] == "casefold-text-near-match"
    assert result["routeCard"]["accepted"] is False


def test_structural_matching_does_not_use_substring_applicability() -> None:
    result = analyze_difference(DifferenceRequest("Nat", "NotNat"))
    assert result["classification"] == "no-structural-match"


def test_structural_analysis_preserves_all_binders_and_explicit_assumptions() -> None:
    result = analyze_difference(
        DifferenceRequest("True", "Demo.proof", assumptions=("h : x = x",)),
        candidate_signature="(x : Nat) (h : x = x) : True",
    )
    assert result["classification"] == "rendered-conclusion-with-binders"
    assert result["residuals"] == ["x : Nat"]
    assert result["dischargedBinders"] == ["h : x = x"]
