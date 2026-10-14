"""Scoped, attributed interpretations; lowering is not certification of prose intent."""

from __future__ import annotations

import copy
import re
from pathlib import Path

from ladon.investigation import SourceReader

LOWERING_PROFILE = "typed-operators-v2"
LEGACY_PROFILE = "untyped-operators-v1"

MAX_NODES = 4096
MAX_DEPTH = 64
MAX_TEXT = 1024 * 1024
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")
# Types are authored Lean presentations, subsequently elaborated in the pinned
# environment. This lexical gate prevents command injection, not type checking.
_TYPE = re.compile(r"[A-Za-z_0-9. ()→∀ℝℕℤαβγ,:<>≤=∧]+\Z")


class UnsupportedInterpretation(ValueError):
    """A retained opaque source expression cannot be lowered by this fragment."""


def closed(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} requires exactly {sorted(keys)}")


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > MAX_TEXT:
        raise ValueError(f"invalid bounded {label}")
    return value


def lean_type(value):
    text(value, "Lean type")
    if not _TYPE.fullmatch(value) or any(word in value.split() for word in ("by", "where")):
        raise UnsupportedInterpretation("domain outside the bounded type presentation fragment")
    return value


def validate_symbols(symbols):
    if not isinstance(symbols, dict) or len(symbols) > MAX_NODES:
        raise ValueError("symbols must be a bounded object")
    for key, row in symbols.items():
        if not _NAME.fullmatch(key):
            raise ValueError("invalid symbol identity")
        closed(row, {"leanName", "leanType"}, "symbol")
        if not isinstance(row["leanName"], str) or not _NAME.fullmatch(row["leanName"]):
            raise ValueError("symbol must name an ordinary Lean declaration")
        lean_type(row["leanType"])


def _collect_binder_identity(node, identities):
    if node.get("tag") not in {"forall", "exists"}:
        return
    binder = node.get("binder")
    if isinstance(binder, dict) and isinstance(binder.get("id"), str):
        identities.add(binder["id"])


def _child_nodes(node, depth):
    children = []
    for key, value in node.items():
        if key == "binder":
            continue
        if isinstance(value, dict):
            children.append((value, depth + 1))
        elif isinstance(value, list):
            children.extend((item, depth + 1) for item in value)
    return children


def binder_identities(formula):
    """Collect domain-reference identities without losing lexical visibility."""
    identities, todo, visited = set(), [(formula, 0)], 0
    while todo:
        node, depth = todo.pop()
        visited += 1
        if visited > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("interpretation exceeds node/depth bounds")
        if isinstance(node, dict):
            _collect_binder_identity(node, identities)
            todo.extend(_child_nodes(node, depth))
    return identities


def lower_domain(domain, scope, identities):
    """Resolve whole qualified identities and prevent generated-name capture."""
    domain = lean_type(domain)
    if "∀" in domain or ":" in domain:
        raise UnsupportedInterpretation("domain binders outside the scoped type fragment")

    def replace(match):
        token = match[0]
        if token in identities and token not in scope:
            raise ValueError("domain identity outside lexical scope")
        if token in scope:
            return scope[token]
        if re.fullmatch(r"v[0-9]+|ladonNL[0-9]+_*", token):
            return "_root_." + token
        return token

    return re.sub(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*", replace, domain)


def lower_formula(formula, symbols, *, _scope=None, _profile=LOWERING_PROFILE):
    """Lower in lexical scope, preserving binder order and dependent domains.

    Binder identity is scoped; display names have no semantic role. Domains can
    refer to earlier identities, never to later binders or escaped witnesses.
    Opaque nodes are retained by validation but cannot become checked formulas.
    """
    if _profile not in {LOWERING_PROFILE, LEGACY_PROFILE}:
        raise ValueError("unsupported lowering profile")
    validate_symbols(symbols)
    identities = binder_identities(formula) | set(_scope or {})
    seen = set(_scope or {})
    count = 0

    def visit(node, scope, depth):
        nonlocal count
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("interpretation exceeds node/depth bounds")
        if not isinstance(node, dict):
            raise TypeError("formula node must be an object")
        tag = node.get("tag")
        if tag == "opaque":
            closed(node, {"tag", "text", "reason"}, "opaque expression")
            text(node["text"], "opaque text")
            text(node["reason"], "opaque reason")
            raise UnsupportedInterpretation(node["reason"])
        if tag == "var":
            closed(node, {"tag", "id"}, "variable")
            if node["id"] not in scope:
                raise ValueError("unbound or escaped variable")
            return scope[node["id"]]
        if tag == "const":
            closed(node, {"tag", "name"}, "constant")
            name = text(node["name"], "constant")
            if re.fullmatch(r"[0-9]{1,20}", name) or name in {"True", "False"}:
                return name
            if _profile == LOWERING_PROFILE and re.fullmatch(r"-[0-9]{1,20}", name):
                return f"({name})"
            if name not in symbols:
                raise ValueError("constant requires an explicit symbol mapping")
            row = symbols[name]
            name = "_root_." + row["leanName"]
            return f"({name} : {row['leanType']})" if _profile == LOWERING_PROFILE else name
        if tag == "app":
            closed(node, {"tag", "symbol", "args"}, "application")
            if node["symbol"] not in symbols or not isinstance(node["args"], list):
                raise ValueError("application requires declared symbol and ordered arguments")
            args = [visit(x, scope, depth + 1) for x in node["args"]]
            row = symbols[node["symbol"]]
            operator = "_root_." + row["leanName"]
            if _profile == LOWERING_PROFILE:
                if "∀" in row["leanType"] or ":" in row["leanType"]:
                    raise UnsupportedInterpretation("dependent operator signatures require a supported instantiated type")
                operator = f"({operator} : {row['leanType']})"
            return "(" + " ".join([operator, *args]) + ")"
        if tag in {"forall", "exists"}:
            closed(node, {"tag", "binder", "body"}, "quantifier")
            binder = node["binder"]
            closed(binder, {"id", "name", "domain"}, "binder")
            identity = text(binder["id"], "binder identity")
            text(binder["name"], "binder display name")
            if not _NAME.fullmatch(identity) or identity in seen:
                raise ValueError("duplicate or invalid scoped binder identity")
            domain = lower_domain(binder["domain"], scope, identities)
            name = f"v{len(seen)}"
            seen.add(identity)
            body = visit(node["body"], {**scope, identity: name}, depth + 1)
            return f"({'∀' if tag == 'forall' else '∃'} ({name} : {domain}), {body})"
        if tag in {"eq", "lt", "le"}:
            closed(node, {"tag", "left", "right"}, "relation")
            left = visit(node["left"], scope, depth + 1)
            right = visit(node["right"], scope, depth + 1)
            op = {"eq": "=", "lt": "<", "le": "≤"}[tag]
            return f"({left} {op} {right})"
        if tag == "implies":
            closed(node, {"tag", "premise", "conclusion"}, "implication")
            return f"({visit(node['premise'], scope, depth + 1)} → {visit(node['conclusion'], scope, depth + 1)})"
        if tag == "and":
            closed(node, {"tag", "items"}, "conjunction")
            if not isinstance(node["items"], list) or not node["items"]:
                raise ValueError("conjunction requires ordered nonempty operands")
            return "(" + " ∧ ".join(visit(x, scope, depth + 1) for x in node["items"]) + ")"
        if tag == "not":
            closed(node, {"tag", "body"}, "negation")
            return f"(¬ {visit(node['body'], scope, depth + 1)})"
        raise ValueError("unknown structured expression tag")

    return visit(formula, _scope or {}, 0)


def validate_interpretation(record, source_root: Path | None, *, _profile=LOWERING_PROFILE):
    closed(record, {"id", "source", "formula", "symbols"}, "interpretation")
    text(record["id"], "interpretation identity")
    source = record["source"]
    closed(source, {"path", "startLine", "endLine", "quote", "sha256"}, "source")
    text(source["path"], "source path")
    text(source["quote"], "source quote")
    if not isinstance(source["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
        raise ValueError("invalid source digest")
    if (
        type(source["startLine"]) is not int
        or type(source["endLine"]) is not int
        or not 1 <= source["startLine"] <= source["endLine"]
    ):
        raise ValueError("invalid source span")
    # Validate the full structure even for opaque formulas, without certifying
    # their meaning. An opaque root is the only supported residual in M1.
    try:
        lower_formula(record["formula"], record["symbols"], _profile=_profile)
    except UnsupportedInterpretation:
        if not isinstance(record["formula"], dict) or record["formula"].get("tag") != "opaque":
            raise
    if source_root is not None:
        SourceReader(source_root).span(source, "quote")
    return copy.deepcopy(record)
