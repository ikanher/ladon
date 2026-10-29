"""Bounded syntax utilities; these do not interpret an observed predicate."""

from ladon.proof_contract_expressions import _app_parts, _const_name, _Unsupported

MAX_DEPTH = 128
MAX_NODES = 100_000
MAX_BINDERS = 64


def unsupported(message, feature="statement", code="unsupported-bound-shape"):
    raise _Unsupported(code, message, feature)


def check_tree(expression):
    stack = [(expression, 0)]
    count = 0
    while stack:
        value, depth = stack.pop()
        count += 1
        if count > MAX_NODES:
            unsupported("Expression exceeds the node limit", code="expression-node-limit")
        if depth > MAX_DEPTH:
            unsupported("Expression exceeds the depth limit", code="expression-depth-limit")
        if isinstance(value, dict):
            stack.extend((child, depth + 1) for child in value.values())
        elif isinstance(value, list):
            stack.extend((child, depth + 1) for child in value)


def scoped(value, scope, local_depth=0):
    """Resolve outer de Bruijn references without capturing inner binders."""
    if isinstance(value, list):
        return [scoped(child, scope, local_depth) for child in value]
    if not isinstance(value, dict):
        return value
    if "bvar" in value:
        return _scoped_bvar(value["bvar"], scope, local_depth)
    for kind in ("forallE", "lam", "letE"):
        if kind in value:
            return {kind: {
                key: scoped(child, scope, local_depth + (key == "body"))
                for key, child in value[kind].items()
            }}
    return {key: scoped(child, scope, local_depth) for key, child in value.items()}


def _scoped_bvar(index, scope, local_depth):
    if type(index) is not int or not 0 <= index < local_depth + len(scope):
        unsupported("Invalid bound variable reference", code="invalid-bound-reference")
    if index < local_depth:
        return {"bvar": index}
    return {"binderId": scope[-(index - local_depth) - 1]}


def application(expression, count, label):
    head, args = _app_parts(expression)
    if not isinstance(head, dict) or len(args) < count:
        unsupported(f"Unrecognized {label} application", label)
    prefix = expression
    for _ in range(count):
        prefix = prefix["app"][0]
    return prefix, args[-count:]


def direct_binder(expression, telescope, *, type_name=None):
    if not isinstance(expression, dict) or set(expression) != {"binderId"}:
        unsupported("Expected a direct typed binder")
    binder_id = expression["binderId"]
    row = next((row for row in telescope if row["binderId"] == binder_id), None)
    if row is None or (type_name and _const_name(row["type"]) != type_name):
        unsupported("Binder has an unsupported type")
    return binder_id


def is_nonnegative(expression, binder_id):
    head, args = _app_parts(expression)
    if _const_name(head) != "LE.le" or len(args) != 4:
        return False
    if _const_name(args[0]) != "Real" or args[-1] != {"binderId": binder_id}:
        return False
    zero_head, zero_args = _app_parts(args[-2])
    return (_const_name(zero_head) == "OfNat.ofNat" and len(zero_args) == 3
            and _const_name(zero_args[0]) == "Real" and zero_args[1] == {"nat": 0})
