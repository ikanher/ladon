"""Observe typed bound-estimate syntax without admitting mathematical meaning."""

from ladon._real_bound_terms import (
    MAX_BINDERS,
    application,
    check_tree,
    direct_binder,
    is_nonnegative,
    scoped,
    unsupported,
)
from ladon.proof_contract_expressions import (
    _app_argument_path,
    _app_parts,
    _const_name,
    _scale_offset,
    _Unsupported,
)


def observe_bound_shape(expression):
    """Return source shape or a named residual, always with unresolved admission."""
    try:
        check_tree(expression)
        candidate = _candidate(expression)
    except _Unsupported as error:
        return {"candidate": None, "admission": "unresolved", "residuals": [{
            "code": error.code, "message": str(error), "feature": error.feature,
        }]}
    return {"candidate": candidate, "admission": "unresolved", "residuals": [{
        "code": "predicate-admission-unchecked", "feature": "predicate",
        "message": "Observed shape does not establish predicate meaning or Real-bound laws.",
    }]}


def _binder(row, quantifier, scope, telescope, path):
    if len(telescope) >= MAX_BINDERS:
        unsupported("Telescope exceeds the binder limit", code="telescope-limit")
    binder_id = f"b{len(telescope)}"
    telescope.append({"binderId": binder_id, "quantifier": quantifier,
                      "type": scoped(row["type"], scope),
                      "binderInfo": row["binderInfo"], "originPath": path})
    scope.append(binder_id)


def _peel(expression):
    telescope, scope, conjunctions = [], [], []
    path = "/normalizedTypeExpr"
    last_input = None
    while isinstance(expression, dict):
        if "forallE" in expression:
            row = expression["forallE"]
            last_input = (row["type"], list(scope), path + "/forallE/type")
            _binder(row, "forall", scope, telescope, path)
            expression, path = row["body"], path + "/forallE/body"
            continue
        head, args = _app_parts(expression)
        if _const_name(head) == "Exists" and len(args) == 2 and "lam" in args[-1]:
            row = args[-1]["lam"]
            if _const_name(args[0]) != "Real" or _const_name(row["type"]) != "Real":
                unsupported("Existential coefficient must have observed type Real")
            path = _app_argument_path(expression, 1, path) + "/lam"
            _binder(row, "exists", scope, telescope, path)
            expression, path = row["body"], path + "/body"
            continue
        if _const_name(head) == "And" and len(args) == 2:
            conjunctions.append({"expression": scoped(args[0], scope),
                                 "originPath": _app_argument_path(expression, 0, path)})
            path = _app_argument_path(expression, 1, path)
            expression = args[1]
            continue
        break
    return telescope, scope, conjunctions, last_input, expression, path


def _candidate(expression):
    telescope, scope, conjunctions, last_input, body, path = _peel(expression)
    constants = [row for row in telescope if row["quantifier"] == "exists"]
    if len(constants) != 1 or last_input is None or len(conjunctions) != 1:
        unsupported("Expected one existential coefficient and its nonnegative conjunction")
    anchor = constants[0]["binderId"]
    if not is_nonnegative(conjunctions[0]["expression"], anchor):
        unsupported("Missing explicit nonnegative coefficient guard", "constant.guard")
    source = _bound_application(scoped(last_input[0], last_input[1]))
    target = _bound_application(scoped(body, scope))
    roles = _roles(source, target, telescope, anchor)
    _matching_applications(source, target)
    operator, operands = application(target["function"], 1, "operator")
    if operands[0] != source["function"]:
        unsupported("Output operator does not apply to the same input function")
    bound_guard = _guards(target, telescope, roles)
    loss = _literal_loss(last_input, roles["order"])
    return {
        "schema": "ladon-typed-bound-shape-v1", "telescope": telescope, "roles": roles,
        "input": {**source, "originPath": last_input[2]},
        "output": {**target, "originPath": path}, "operator": operator, "loss": loss,
        "constant": {"binderId": anchor, "permittedBinderIds": _permissions(telescope, anchor)},
        "guards": {"constantNonnegative": conjunctions[0], "boundNonnegative": bound_guard},
    }


def _bound_application(expression):
    predicate, args = application(expression, 4, "bound-predicate")
    head, _args = _app_parts(predicate)
    if _const_name(head) in {None, "Not", "Or", "And", "Exists", "Eq", "LE.le"}:
        unsupported("Bound predicate must be a named applied predicate")
    return dict(zip(("function", "set", "order", "bound"), args, strict=True),
                predicate=predicate)


def _roles(source, target, telescope, anchor):
    roles = {"function": direct_binder(source["function"], telescope),
             "set": direct_binder(source["set"], telescope),
             "order": direct_binder(target["order"], telescope, type_name="Nat"),
             "bound": direct_binder(source["bound"], telescope, type_name="Real"),
             "constant": anchor}
    if len(set(roles.values())) != len(roles):
        unsupported("Estimate roles must use distinct binders")
    universals = {row["binderId"] for row in telescope if row["quantifier"] == "forall"}
    if not set(roles.values()) - {anchor} <= universals:
        unsupported("Input roles must be universal binders")
    return roles


def _matching_applications(source, target):
    if source["predicate"] != target["predicate"] or source["set"] != target["set"]:
        unsupported("Predicate parameters and set must match exactly", "predicate")


def _guards(target, telescope, roles):
    head, args = _app_parts(target["bound"])
    if (_const_name(head) != "HMul.hMul" or len(args) != 6
            or any(_const_name(arg) != "Real" for arg in args[:3])
            or args[-2:] != [{"binderId": roles["constant"]}, {"binderId": roles["bound"]}]):
        unsupported("Output bound must retain the observed Real product K*C", "bound")
    matches = [row for row in telescope if row["quantifier"] == "forall"
               and is_nonnegative(row["type"], roles["bound"])]
    if not matches:
        unsupported("Missing explicit nonnegative input-bound guard", "bound.guard")
    return matches[0]["binderId"]


def _literal_loss(last_input, order):
    _predicate, args = application(last_input[0], 4, "bound-predicate")
    scope = [{"kind": "binder", "binderId": binder} for binder in last_input[1]]
    loss = _scale_offset(args[2], order, scope)
    if not 0 <= loss <= 2**53 - 1:
        unsupported("Literal shift exceeds the supported integer range", "loss")
    return loss


def _permissions(telescope, anchor):
    allowed = []
    for row in telescope:
        if row["binderId"] == anchor:
            break
        if row["quantifier"] == "forall":
            allowed.append(row["binderId"])
    return allowed
