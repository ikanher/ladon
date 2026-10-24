"""Context boundary for the exact Nat inequality-direction profile."""

from __future__ import annotations

import copy

import pytest

from ladon._proof_contract_probe_inequality_contracts import _context_error


@pytest.fixture
def nat_order_contract():
    return {
        "context": {
            "objectId": "object:nat-order",
            "domainId": "domain:Nat",
            "scaleId": "scale:none",
            "representationId": "representation:original",
        }
    }


def test_registered_nat_order_context_is_accepted(nat_order_contract):
    assert _context_error(nat_order_contract) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("objectId", "object:custom-order"),
        ("domainId", "domain:Int"),
        ("scaleId", "scale:custom"),
        ("representationId", "representation:custom"),
    ],
)
def test_noncanonical_order_context_is_rejected(nat_order_contract, field, value):
    contract = copy.deepcopy(nat_order_contract)
    contract["context"][field] = value
    error = _context_error(contract)
    assert error is not None
    assert error["code"] == "unsupported-inequality-direction"


def test_same_custom_order_context_is_rejected_by_the_probe_planner(tmp_path):
    from test_proof_contract_inequality_direction_contract_v2 import (
        TEMPLATE,
        _pair,
        _template_result,
    )

    data = _pair(tmp_path, context_ids=("object:custom-order", "object:custom-order"))
    assert _template_result(data, TEMPLATE)["status"] == "unsupported"
