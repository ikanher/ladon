"""Root-selected independent M1 lowering regression (board #62/#64)."""

def test_quantifier_order_is_semantic_and_not_normalized_away():
    from ladon.correspondence_interpretation import lower_formula

    symbols = {}
    x_then_y = {"tag": "forall", "binder": {"id": "x", "name": "x", "domain": "ℝ"},
                "body": {"tag": "exists", "binder": {"id": "y", "name": "y", "domain": "ℝ"},
                         "body": {"tag": "eq", "left": {"tag": "var", "id": "x"},
                                  "right": {"tag": "var", "id": "y"}}}}
    y_then_x = {"tag": "exists", "binder": {"id": "y", "name": "y", "domain": "ℝ"},
                "body": {"tag": "forall", "binder": {"id": "x", "name": "x", "domain": "ℝ"},
                         "body": {"tag": "eq", "left": {"tag": "var", "id": "x"},
                                  "right": {"tag": "var", "id": "y"}}}}
    assert lower_formula(x_then_y, symbols) != lower_formula(y_then_x, symbols)

