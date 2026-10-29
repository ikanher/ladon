"""Scope and origin regressions beyond the initial simple quantifier layout."""

from test_real_bound_shape import (
    app,
    bind,
    const,
    estimate,
    nonnegative,
    observe,
    plus,
    resolve,
    var,
)


def after_premise():
    source = app("Envelope", var("f"), var("S"), plus(var("n"), {"nat": 4}), var("C"))
    product = app("HMul.hMul", const("Real"), const("Real"), const("Real"),
                  const("multiplyInstance"), var("K"), var("C"))
    conclusion = app("Envelope", app("Transform", var("f")), var("S"), var("n"), product)
    result = app("Exists", const("Real"), bind("K", const("Real"),
                 app("And", nonnegative("K"), conclusion), "lam"))
    result = bind("hJ", source, result)
    result = bind("hC", nonnegative("C"), result)
    for name, domain in reversed([("n", const("Nat")), ("f", const("Function")),
                                  ("S", const("Domain")), ("C", const("Real"))]):
        result = bind(name, domain, result)
    return resolve(result)


def at_pointer(expression, path):
    value = {"normalizedTypeExpr": expression}
    for part in path.lstrip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def test_constant_after_input_premise_has_exact_input_origin_and_permissions():
    expression = after_premise()
    shape = observe(expression)["candidate"]
    source = at_pointer(expression, shape["input"]["originPath"])
    assert "forallE" not in source
    assert shape["roles"]["constant"] == "b6"
    assert shape["constant"]["permittedBinderIds"] == [f"b{i}" for i in range(6)]
    assert shape["loss"] == 4
    assert source["app"][1] == {"bvar": 1}  # C, before adding hJ and K


def test_nested_dependent_type_keeps_inner_and_outer_binders_separate():
    expression = estimate()
    row = expression["forallE"]["body"]["forallE"]["body"]["app"][1]["lam"]
    # The first forall under K's conjunction binds f in scope [T, n, K].
    function_row = row["body"]["app"][1]["forallE"]
    function_row["type"] = bind("x", {"bvar": 2}, {"bvar": 3})
    shape = observe(expression)["candidate"]
    function = next(row for row in shape["telescope"] if row["binderId"] == "b3")
    assert function["type"]["forallE"]["type"] == {"binderId": "b0"}
    assert function["type"]["forallE"]["body"] == {"binderId": "b0"}


def test_outer_telescope_and_total_node_population_have_explicit_limits():
    expression = estimate()
    for index in range(65):
        expression = bind(f"extra{index}", const("Nat"), expression)
    # Depth can be encountered first; either guard stops before candidate publication.
    assert observe(expression)["candidate"] is None
    result = observe({"unrecognized": [0] * 100_001})
    assert result["residuals"][0]["code"] == "expression-node-limit"
