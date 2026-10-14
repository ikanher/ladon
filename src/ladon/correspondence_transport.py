"""Map original observed identities into the compiler-reconstructed context."""

import copy


def _mapped_local(key, originals, explicit, selected):
    matches = [r for r in originals if r["localId" if explicit else "name"] == key]
    if len(matches) != 1:
        raise ValueError("ambiguous or unknown object map reference; use exact local identity")
    row = matches[0]
    if row["isProp"] or row["letValue"] is not None:
        raise ValueError("unknown object map reference or escaped binder")
    if row["localId"] in selected["nestedLocalIds"]:
        raise ValueError("escaped witness: nested scope cannot map to an outer prose object")
    return row


def _resolve_bindings(entries, originals, explicit, selected):
    resolved = {}
    for key, mapped in entries.items():
        row = _mapped_local(key, originals, explicit, selected)
        resolved[row["localId"]] = mapped
    return resolved


def _transported_view(proof_slice, transport):
    view = copy.deepcopy(proof_slice)
    view["localContext"] = [{k: v for k, v in r.items() if k != "originalLocalId"}
                            for r in transport["localContext"]]
    _transport_node(view["nodes"][0], transport)
    return view


def transport_inputs(proof_slice, object_map):
    """Use compiler-reconstructed fvars; original spellings only resolve legacy maps."""
    if proof_slice["helper"]["profile"] != "scoped-identity-transport-v2":
        if "profile" in object_map and "entries" in object_map:
            raise ValueError("identity maps require observed identity transport")
        return proof_slice, object_map
    selected = proof_slice["observation"]["applications"][proof_slice["selection"]["occurrence"]]
    originals = proof_slice["localContext"]
    explicit = "profile" in object_map and "entries" in object_map
    entries = object_map["entries"] if explicit else object_map
    resolved = _resolve_bindings(entries, originals, explicit, selected)
    transport = selected["transport"]
    view = _transported_view(proof_slice, transport)
    bindings = {r["name"]: resolved[r["originalLocalId"]]
                for r in transport["localContext"] if r["originalLocalId"] in resolved}
    return view, bindings


def _transport_node(node, transport):
    node["arguments"] = transport["arguments"]
    node["expression"] = transport["application"]
    node["type"] = transport["applicationType"]
    for premise in node["premises"]:
        argument = transport["arguments"][premise["occurrence"]]
        premise["proposition"] = argument["type"]
        premise["provider"] = argument["expression"]
