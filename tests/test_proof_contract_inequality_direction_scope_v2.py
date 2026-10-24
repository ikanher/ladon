"""Early native rejections retain the selected inequality probe scope."""

from ladon._proof_contract_probe_pair import unsupported_result


def test_early_rejection_uses_the_inequality_direction_v2_scope():
    template = {
        "familyId": "inequality-direction",
        "version": "inequality-direction-v2",
        "direction": "right-to-left",
        "kind": "counterexample",
    }
    result = unsupported_result(template, "different-application-context", "test")
    assert result["status"] == "unsupported"
    assert result["scope"] == "closed-nat-zero-inequality-direction-v2"
    assert result["goals"] == []
