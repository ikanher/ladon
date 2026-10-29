"""Generic syntax controls: these do not establish predicate or Real-law admission."""

from copy import deepcopy

import pytest


def const(name):
    return {"const": name, "levels": []}


def app(name, *args):
    term = const(name) if isinstance(name, str) else name
    for arg in args:
        term = {"app": [term, arg]}
    return term


def var(name):
    return {"variable": name}


def bind(name, domain, body, kind="forallE"):
    return {kind: {"name": name, "type": domain, "body": body, "binderInfo": "explicit"}}


def resolve(value, scope=()):
    if isinstance(value, list):
        return [resolve(item, scope) for item in value]
    if not isinstance(value, dict):
        return value
    if "variable" in value:
        return {"bvar": list(reversed(scope)).index(value["variable"])}
    if set(value) & {"forallE", "lam"}:
        kind = next(iter(value))
        row = value[kind]
        return {kind: {**row, "type": resolve(row["type"], scope),
                       "body": resolve(row["body"], (*scope, row["name"]))}}
    return {key: resolve(child, scope) for key, child in value.items()}


def nonnegative(name):
    zero = app("OfNat.ofNat", const("Real"), {"nat": 0}, const("zeroInstance"))
    return app("LE.le", const("Real"), const("orderInstance"), zero, var(name))


def plus(left, right):
    instance = app("instHAdd", const("Nat"), const("instAddNat"))
    return app("HAdd.hAdd", const("Nat"), const("Nat"), const("Nat"), instance, left, right)


def input_binders(result):
    for name, domain in reversed([("f", const("Function")), ("S", const("Domain")),
                                  ("C", const("Real"))]):
        result = bind(name, domain, result)
    return result


def estimate(*, loss=7, predicate="CoefficientEnvelope", operator="Transform",
             late_constant=False, guard_k=True, guard_c=True, symbolic=False,
             other_set=False, other_parameter=False):
    order = plus(var("n"), var("l") if symbolic else {"nat": loss})
    pred = app(predicate, var("T"))
    source = app(pred, var("f"), var("S"), order, var("C"))
    product = app("HMul.hMul", const("Real"), const("Real"), const("Real"),
                  const("multiplyInstance"), var("K"), var("C"))
    output_pred = app(predicate, const("OtherParameter")) if other_parameter else pred
    result = app(output_pred, app(operator, var("f")),
                 const("OtherSet") if other_set else var("S"), var("n"), product)
    result = bind("h", source, result)
    if guard_c:
        result = bind("hC", nonnegative("C"), result)
    result = bind("smooth", app("Regular", var("f")), result)
    if not late_constant:
        result = input_binders(result)
    if guard_k:
        result = app("And", nonnegative("K"), result)
    result = app("Exists", const("Real"), bind("K", const("Real"), result, "lam"))
    if late_constant:
        result = input_binders(result)
    if symbolic:
        result = bind("l", const("Nat"), result)
    return resolve(bind("T", {"sort": "1"}, bind("n", const("Nat"), result)))


def observe(expression):
    from ladon.real_bound_shape import observe_bound_shape

    return observe_bound_shape(expression)


@pytest.mark.parametrize("loss", [0, 4, 7])
@pytest.mark.parametrize("predicate,operator", [("CoefficientEnvelope", "Transform"),
                                               ("Unrelated.Prefix", "Unrelated.Map")])
def test_arbitrary_names_and_losses_are_observations_only(loss, predicate, operator):
    result = observe(estimate(loss=loss, predicate=predicate, operator=operator))
    shape = result["candidate"]
    assert shape["loss"] == loss
    assert shape["input"]["predicate"]["app"][0] == const(predicate)
    assert shape["operator"] == const(operator)
    assert result["admission"] == "unresolved"
    assert {r["code"] for r in result["residuals"]} >= {"predicate-admission-unchecked"}
    assert shape["constant"]["permittedBinderIds"] == ["b0", "b1"]
    assert shape["roles"]["constant"] == "b2"
    assert shape["guards"]["constantNonnegative"]["originPath"].startswith("/normalizedTypeExpr")
    assert any(row["type"].get("app", [{}])[0] == const("Regular")
               for row in shape["telescope"])


def test_late_constant_preserves_larger_scope_without_uniformity_claim():
    early = observe(estimate())["candidate"]
    late = observe(estimate(late_constant=True))["candidate"]
    assert len(early["constant"]["permittedBinderIds"]) == 2
    assert len(late["constant"]["permittedBinderIds"]) == 5
    assert late["roles"]["function"] in late["constant"]["permittedBinderIds"]
    assert late["roles"]["set"] in late["constant"]["permittedBinderIds"]


@pytest.mark.parametrize("changes", [{"guard_k": False}, {"guard_c": False},
                                     {"symbolic": True}, {"other_set": True},
                                     {"other_parameter": True}])
def test_unhandled_or_mismatched_shape_cannot_supply_candidate(changes):
    result = observe(estimate(**changes))
    assert result["candidate"] is None
    assert result["admission"] == "unresolved"
    assert result["residuals"]


@pytest.mark.parametrize("connective", ["Not", "Or"])
def test_estimates_under_other_polarity_or_alternatives_are_not_mined(connective):
    expression = app(connective, estimate(), const("False"))
    assert observe(expression)["candidate"] is None


def test_scoped_terms_preserve_nested_binders_and_do_not_capture_outer_variables():
    source = estimate()
    outer = source["forallE"]
    domain = bind("z", const("Nat"), {"bvar": 1})
    outer["body"]["forallE"]["type"] = domain
    assert observe(source)["candidate"] is None  # order is no longer Nat
    assert source["forallE"]["body"]["forallE"]["type"] == domain


def test_bound_observation_never_passes_as_old_semantic_contract():
    from ladon.proof_contracts import compare_contracts, validate_contract

    result = observe(estimate())
    with pytest.raises(ValueError):
        validate_contract(result["candidate"])
    with pytest.raises(ValueError):
        compare_contracts(result["candidate"], result["candidate"])


def test_input_is_unchanged_and_mutable_result_is_detached():
    source = estimate()
    frozen = deepcopy(source)
    result = observe(source)
    result["candidate"]["telescope"][0]["type"]["sort"] = "changed"
    assert source == frozen


def test_expression_depth_and_invalid_bound_reference_are_bounded_residuals():
    deep = const("terminal")
    for _ in range(140):
        deep = app("wrap", deep)
    assert observe(deep)["residuals"][0]["code"] == "expression-depth-limit"
    source = estimate()
    source["forallE"]["type"] = {"bvar": 99}
    assert observe(source)["candidate"] is None
