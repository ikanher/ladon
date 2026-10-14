"""Closed object maps name binders or declared representation functions."""

import copy

from ladon.correspondence_interpretation import closed


def _validate_representation_map(mapped):
    closed(mapped, {"symbol", "args"}, "representation map")
    if (not isinstance(mapped["symbol"], str) or not mapped["symbol"]
            or not isinstance(mapped["args"], list) or len(mapped["args"]) > 64
            or any(not isinstance(arg, str) or not arg for arg in mapped["args"])):
        raise ValueError("representation map requires a declared symbol and binder identities")


def _validate_object_entry(key, mapped):
    if not isinstance(key, str) or not key:
        raise ValueError("invalid formal object identity")
    if isinstance(mapped, str) and mapped:
        return
    _validate_representation_map(mapped)


def validate_object_map(value):
    if not isinstance(value, dict) or len(value) > 4096:
        raise ValueError("object map must be a bounded object")
    entries = value
    if "profile" in value and "entries" in value:
        closed(value, {"profile", "entries"}, "identity map")
        if value["profile"] != "local-identity-v1" or not isinstance(value["entries"], dict):
            raise ValueError("unsupported local object map profile")
        entries = value["entries"]
        if len(entries) > 4096:
            raise ValueError("object map exceeds identity bound")
    for key, mapped in entries.items():
        _validate_object_entry(key, mapped)
    return copy.deepcopy(value)


def map_references(mapped):
    return [mapped] if isinstance(mapped, str) else mapped["args"]


def mapped_expression(mapped, scope, symbols):
    if isinstance(mapped, str):
        return scope[mapped]
    if mapped["symbol"] not in symbols:
        raise ValueError("representation function requires an explicit symbol declaration")
    row = symbols[mapped["symbol"]]
    name = f"(_root_.{row['leanName']} : {row['leanType']})"
    return "(" + " ".join([name, *(scope[arg] for arg in mapped["args"])]) + ")"
