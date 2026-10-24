"""Closed, bounded propagation wrapper validation."""

from __future__ import annotations

from ladon._contract_propagation_common import (
    _canonical,
    _identifier,
    _local_ref,
    _object,
    _plain,
    _ref_list,
)
from ladon._proofir_derivation_core import _key

INTERFACE_FIELDS = {
    "interfaceId",
    "endpointId",
    "operatorId",
    "objectId",
    "domainId",
    "representationId",
    "inputTypeId",
    "outputTypeId",
    "inputScaleId",
    "outputScaleId",
    "inputNormId",
    "outputNormId",
    "conclusionId",
    "evidenceRefs",
}
RULE_PARAMETERS = {
    "identity": set(),
    "weaken-loss": {"targetOffset", "nestednessRefs"},
    "compose": {"compositeOperatorId"},
    "combine-estimates": {"leftEmbeddingRefs", "rightEmbeddingRefs", "nestednessRefs"},
    "combine-requirements": set(),
}


def _interface(raw, index, subjects, contracts, by_interface, contract_interfaces):
    row = raw
    if not isinstance(row, dict):
        raise TypeError("endpoint interface must be an object")
    allowed = INTERFACE_FIELDS | ({"contractRef"} if "contractRef" in row else set())
    _object(row, allowed, f"endpoint_interfaces[{index}]")
    for key in INTERFACE_FIELDS - {"evidenceRefs"}:
        _identifier(row[key], f"endpoint_interfaces[{index}].{key}")
    if row["interfaceId"] in by_interface:
        raise ValueError("interfaceId values must be unique")
    _ref_list(
        row["evidenceRefs"],
        subjects,
        {"check-run"},
        f"endpoint_interfaces[{index}].evidenceRefs",
        nonempty=True,
    )
    if "contractRef" in row:
        _object(
            row["contractRef"],
            {"artifactRef", "kind", "localId"},
            f"endpoint_interfaces[{index}].contractRef",
        )
        _identifier(row["contractRef"]["artifactRef"], "contractRef.artifactRef")
        if row["contractRef"]["kind"] != "contract":
            raise ValueError("interface contractRef.kind must be contract")
        _identifier(row["contractRef"]["localId"], "contractRef.localId")
        if (row["contractRef"]["artifactRef"], row["contractRef"]["localId"]) not in contracts:
            raise ValueError("interface contractRef does not identify an input contract")
        external_key = (row["contractRef"]["artifactRef"], row["contractRef"]["localId"])
        if external_key in contract_interfaces:
            raise ValueError("each source contract identity must have one input interface")
        contract_interfaces.add(external_key)
    if row["operatorId"] != row["objectId"]:
        raise ValueError("interface operatorId must equal objectId")
    return _plain(row)


def _binding(raw, index, subjects, graph_steps, by_interface, by_step):
    row = raw
    _object(
        row,
        {
            "stepRef",
            "ruleRef",
            "profileDigest",
            "ruleId",
            "arity",
            "outputInterfaceId",
            "parameters",
            "evidenceRefs",
        },
        f"rule_bindings[{index}]",
    )
    _local_ref(row["stepRef"], subjects, {"derivation-step"}, f"rule_bindings[{index}].stepRef")
    _local_ref(row["ruleRef"], subjects, {"declaration"}, f"rule_bindings[{index}].ruleRef")
    if row["stepRef"] != _plain(graph_steps.get(_key(row["stepRef"]), {}).get("stepRef")) or row[
        "ruleRef"
    ] != _plain(graph_steps.get(_key(row["stepRef"]), {}).get("ruleRef")):
        raise ValueError("rule binding must match an exact derivation application")
    _identifier(row["profileDigest"], "rule binding profileDigest")
    _identifier(row["ruleId"], "rule binding ruleId")
    if type(row["arity"]) is not int or row["arity"] < 0:
        raise ValueError("rule binding arity must be a nonnegative integer")
    _identifier(row["outputInterfaceId"], "rule binding outputInterfaceId")
    if row["outputInterfaceId"] not in by_interface:
        raise ValueError("rule binding output interface is missing")
    _parameters(row, index, subjects)
    _ref_list(
        row["evidenceRefs"],
        subjects,
        {"check-run"},
        f"rule_bindings[{index}].evidenceRefs",
        nonempty=True,
    )
    step = graph_steps[_key(row["stepRef"])]
    if _key(step["checkRunRef"]) not in {_key(ref) for ref in row["evidenceRefs"]}:
        raise ValueError("rule binding evidence must include the exact step check run")
    key = _key(row["stepRef"])
    if key in by_step:
        raise ValueError("rule bindings must not duplicate step identity")
    return _plain(row)


def _scope(raw, index, subjects, contracts, seen_scopes):
    scope_keys = {
        "contractRef",
        "statementRef",
        "localContextRef",
        "objectMap",
        "binderMap",
        "substitutionRefs",
        "evidenceRefs",
    }
    row = raw
    _object(row, scope_keys, f"scope_bindings[{index}]")
    _local_ref(
        row["statementRef"], subjects, {"statement"}, f"scope_bindings[{index}].statementRef"
    )
    _local_ref(
        row["localContextRef"],
        subjects,
        {"local-context"},
        f"scope_bindings[{index}].localContextRef",
    )
    _object(
        row["contractRef"],
        {"artifactRef", "kind", "localId"},
        f"scope_bindings[{index}].contractRef",
    )
    _identifier(row["contractRef"]["artifactRef"], "scope contractRef.artifactRef")
    _identifier(row["contractRef"]["localId"], "scope contractRef.localId")
    if (
        row["contractRef"]["kind"] != "contract"
        or (row["contractRef"]["artifactRef"], row["contractRef"]["localId"]) not in contracts
    ):
        raise ValueError("scope contractRef must identify an input contract")
    _mapping(row["objectMap"], "Object")
    _mapping(row["binderMap"], "Binder")
    _ref_list(
        row["substitutionRefs"], subjects, {"term"}, f"scope_bindings[{index}].substitutionRefs"
    )
    _ref_list(
        row["evidenceRefs"],
        subjects,
        {"check-run"},
        f"scope_bindings[{index}].evidenceRefs",
        nonempty=True,
    )
    identity = _canonical(row)
    if identity in seen_scopes:
        raise ValueError("scope_bindings must not contain duplicate wrappers")
    seen_scopes.add(identity)
    return _plain(row)


def _validate_inputs(bindings, interfaces, scopes, subjects, contracts, graph):
    for value, limit, types, label in (
        (bindings, 8192, list, "rule_bindings"),
        (interfaces, 4096, list, "endpoint_interfaces"),
        (scopes, 4096, (list, tuple), "scope_bindings"),
    ):
        if not isinstance(value, types) or len(value) > limit:
            raise ValueError(f"{label} must be a bounded list")
    by_interface, contract_interfaces = {}, set()
    for index, raw in enumerate(interfaces):
        row = _interface(raw, index, subjects, contracts, by_interface, contract_interfaces)
        by_interface[row["interfaceId"]] = row
    by_step = {}
    graph_steps = {_key(row["stepRef"]): row for row in graph.steps}
    for index, raw in enumerate(bindings):
        row = _binding(raw, index, subjects, graph_steps, by_interface, by_step)
        by_step[_key(row["stepRef"])] = row
    by_statement, seen_scopes = {}, set()
    for index, raw in enumerate(scopes):
        row = _scope(raw, index, subjects, contracts, seen_scopes)
        by_statement.setdefault(_key(row["statementRef"]), []).append(row)
    return by_step, by_interface, by_statement


def _parameters(row, index, subjects):
    params = row["parameters"]
    expected = RULE_PARAMETERS.get(row["ruleId"])
    if expected is not None:
        if not isinstance(params, dict) or not set(params) <= expected:
            raise ValueError(
                f"rule_bindings[{index}].parameters must contain exactly the required keys"
            )
        for key, value in params.items():
            if key.endswith("Refs"):
                _ref_list(
                    value, subjects, {"check-run"}, f"rule_bindings[{index}].parameters.{key}"
                )
        _parameter_scalars(row["ruleId"], params)
    elif not isinstance(params, dict) or params:
        raise ValueError("unknown rule bindings must not supply parameters")


def _parameter_scalars(rule, params):
    required = {"weaken-loss": "targetOffset", "compose": "compositeOperatorId"}.get(rule)
    if required is not None and required not in params:
        raise ValueError(f"missing required parameter: {required}")
    if rule == "weaken-loss" and (
        type(params["targetOffset"]) is not int or params["targetOffset"] < 0
    ):
        raise ValueError("targetOffset must be a nonnegative integer")
    if rule == "compose":
        _identifier(params["compositeOperatorId"], "compositeOperatorId")


def _mapping(rows, kind):
    source, target = f"from{kind}Id", f"to{kind}Id"
    if not isinstance(rows, list) or len(rows) > 4096:
        raise ValueError(f"{kind}Map must be a bounded list")
    for row in rows:
        _object(row, {source, target}, f"{kind}Map")
        _identifier(row[source], source)
        _identifier(row[target], target)
    if len({row[source] for row in rows}) != len(rows):
        raise ValueError(f"{kind}Map source IDs must be unique")
