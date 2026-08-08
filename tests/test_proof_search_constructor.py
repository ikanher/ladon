from __future__ import annotations

from ladon.proof_search_constructor import ConstructorRequest, constructor_coverage


def test_constructor_coverage_keeps_field_order_and_leakage_classes() -> None:
    result = constructor_coverage(ConstructorRequest("Record"), [
        {"name": "value", "type": "Nat", "supplied": True, "equivalentInput": "binder.x"},
        {"name": "proof", "type": "value > 0", "projectionDependency": "Record.value"},
        {"name": "alias", "type": "Nat", "aliasProjection": "Record.value"},
    ])
    assert [row["field"] for row in result["fields"]] == ["value", "proof", "alias"]
    assert [row["leakage"]["class"] for row in result["fields"]] == ["equivalent_field_input", "direct_projection_dependency", "alias_projection_dependency"]


def test_constructor_unavailable_field_is_explicit() -> None:
    result = constructor_coverage(ConstructorRequest("Record"), [{"name": "x", "unavailable": True}])
    assert result["fields"][0]["classification"] == "unavailable"
