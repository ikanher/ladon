"""Registered semantic transfers over exact scoped interfaces."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ladon._proofir_derivation_core import _Graph, _key
from ladon.proof_contracts import validate_contract

_INTERFACE_TRANSFER_KEYS = (
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
)


def _transfer(
    step: dict[str, Any],
    binding: dict[str, Any],
    combo: tuple[dict[str, Any], ...],
    interfaces: dict[str, dict[str, Any]],
    graph: _Graph,
    residuals: list[dict[str, Any]],
) -> dict[str, Any] | None:
    rule = binding.get("ruleId")
    parameters = binding.get("parameters", {})
    output_interface = interfaces.get(binding.get("outputInterfaceId"))
    if output_interface is None:
        residuals.append({"code": "missing-output-interface", "stepRef": step["stepRef"]})
        return None
    if output_interface.get("operatorId") != output_interface.get("objectId"):
        residuals.append({"code": "invalid-output-interface", "stepRef": step["stepRef"]})
        return None
    prepared = _prepare_inputs(step, combo, interfaces, residuals)
    if prepared is None:
        return None
    inputs, input_interfaces = prepared
    handler = {
        "identity": _identity,
        "weaken-loss": _weakening,
        "compose": _compose,
        "combine-estimates": _estimates,
    }.get(rule)
    if handler is None:
        residuals.append({"code": "unsupported-rule", "stepRef": step["stepRef"], "ruleId": rule})
        return None
    output = handler(inputs, input_interfaces, output_interface, parameters, step, residuals)
    if output is None:
        return None
    if rule in {"identity", "weaken-loss"}:
        output = _output_record(output, output_interface)
    return validate_contract(output)


def _route_evidence(binding, combo, interfaces):
    refs = list(binding["evidenceRefs"])
    for value in binding["parameters"].values():
        if isinstance(value, list):
            refs.extend(value)
    output = interfaces[binding["outputInterfaceId"]]
    refs.extend(output["evidenceRefs"])
    for item in combo:
        refs.extend(interfaces[item["routeWitness"]["interfaceId"]]["evidenceRefs"])
    unique = {_key(row): row for row in refs}
    return [unique[key] for key in sorted(unique)]


def _same_transfer_interface(left, right):
    return all(left.get(key) == right.get(key) for key in _INTERFACE_TRANSFER_KEYS)


def _input_interface_matches(interface, record):
    return (
        interface.get("endpointId") == record["endpointId"]
        and interface.get("operatorId") == record["context"]["objectId"]
        and interface.get("domainId") == record["context"]["domainId"]
        and interface.get("representationId") == record["context"]["representationId"]
        and interface.get("inputScaleId") == record["context"]["scaleId"]
        and interface.get("conclusionId") == record["conclusionId"]
    )


def _has_explicit_anchor(record):
    return "binderId" in record["features"]["constantDependencies"]


def _known(record):
    features = record["features"]
    return (
        features["regularity"]["state"] == "known"
        and features["constantDependencies"]["state"] == "known"
        and all(row["state"] == "known" for row in features["witnessDependencies"])
    )


def _output_record(source, interface):
    output = deepcopy(source)
    output["endpointId"] = interface["endpointId"]
    output["context"] = {
        "objectId": interface["objectId"],
        "domainId": interface["domainId"],
        "scaleId": interface["inputScaleId"],
        "representationId": interface["representationId"],
    }
    output["conclusionId"] = interface["conclusionId"]
    output["features"]["regularity"]["scaleId"] = interface["inputScaleId"]
    return output


def _union_permissions(output, inputs):
    features = output["features"]
    constant = features["constantDependencies"]
    permissions = [
        set(row["features"]["constantDependencies"]["allowedBinderIds"]) for row in inputs
    ]
    constant["allowedBinderIds"] = sorted(set.union(*permissions))
    witness_rows = {row["binderId"]: row for row in features["witnessDependencies"]}
    for binder, target in witness_rows.items():
        sets = [
            set(
                next(
                    row
                    for row in item["features"]["witnessDependencies"]
                    if row["binderId"] == binder
                )["allowedBinderIds"]
            )
            for item in inputs
        ]
        target["allowedBinderIds"] = sorted(set.union(*sets))


def _identity(inputs, input_interfaces, output_interface, parameters, step, residuals):
    if not _same_transfer_interface(input_interfaces[0], output_interface):
        residuals.append({"code": "incompatible-identity-interface", "stepRef": step["stepRef"]})
        return None
    output = deepcopy(inputs[0])
    return output


def _weakening(inputs, input_interfaces, output_interface, parameters, step, residuals):
    if not _same_transfer_interface(input_interfaces[0], output_interface):
        residuals.append({"code": "incompatible-weakening-interface", "stepRef": step["stepRef"]})
        return None
    old = inputs[0]["features"]["regularity"]
    target = parameters.get("targetOffset")
    nesting = parameters.get("nestednessRefs")
    if (
        old["state"] != "known"
        or isinstance(target, bool)
        or (not isinstance(target, int))
        or (target < old["offset"])
        or (not nesting)
    ):
        residuals.append(
            {"code": "unsupported-weakening-side-condition", "stepRef": step["stepRef"]}
        )
        return None
    output = deepcopy(inputs[0])
    output["features"]["regularity"]["offset"] = target
    return output


def _compose(inputs, input_interfaces, output_interface, parameters, step, residuals):
    left, right = inputs
    left_interface, right_interface = input_interfaces
    if parameters.get("compositeOperatorId") != output_interface.get("operatorId"):
        residuals.append({"code": "unsupported-compose-side-condition", "stepRef": step["stepRef"]})
        return None
    if not _compose_interfaces(left_interface, right_interface, output_interface):
        residuals.append({"code": "incompatible-compose-interface", "stepRef": step["stepRef"]})
        return None
    if any(_has_explicit_anchor(record) for record in inputs):
        residuals.append(
            {"code": "unsupported-anchored-choice-transport", "stepRef": step["stepRef"]}
        )
        return None
    if not _known(left) or not _known(right):
        residuals.append({"code": "unknown-contract-feature", "stepRef": step["stepRef"]})
        return None
    output = _output_record(left, output_interface)
    output["features"]["regularity"]["offset"] = (
        left["features"]["regularity"]["offset"] + right["features"]["regularity"]["offset"]
    )
    _union_permissions(output, [left, right])
    return output


def _estimates(inputs, input_interfaces, output_interface, parameters, step, residuals):
    left, right = inputs
    params_ok = all(
        parameters.get(key) for key in ("leftEmbeddingRefs", "rightEmbeddingRefs", "nestednessRefs")
    )
    if not params_ok or not all(map(_known, inputs)):
        residuals.append(
            {"code": "unsupported-estimate-combination-side-condition", "stepRef": step["stepRef"]}
        )
        return None
    gates = ("endpointId", "context", "telescope", "assumptions", "conclusionId")
    if any(left[key] != right[key] for key in gates):
        residuals.append({"code": "incompatible-contract-scope", "stepRef": step["stepRef"]})
        return None
    if any(_has_explicit_anchor(record) for record in inputs):
        residuals.append(
            {"code": "unsupported-anchored-choice-transport", "stepRef": step["stepRef"]}
        )
        return None
    if not all(_same_transfer_interface(item, output_interface) for item in input_interfaces):
        residuals.append(
            {"code": "unsupported-estimate-scope-transport", "stepRef": step["stepRef"]}
        )
        return None
    output = _output_record(left, output_interface)
    output["features"]["regularity"]["offset"] = max(
        left["features"]["regularity"]["offset"], right["features"]["regularity"]["offset"]
    )
    _union_permissions(output, [left, right])
    return output


def _prepare_inputs(step, combo, interfaces, residuals):
    if not _premise_scopes(step, combo, residuals):
        return None
    inputs = [row["contractRecord"] for row in combo]
    if not _shared_scope(inputs):
        residuals.append({"code": "incompatible-contract-scope", "stepRef": step["stepRef"]})
        return None
    input_interfaces = []
    for ordinal, record in enumerate(inputs):
        interface = interfaces.get(combo[ordinal]["routeWitness"].get("interfaceId"))
        if interface is None or not _input_interface_matches(interface, record):
            residuals.append(
                {
                    "code": "missing-input-interface",
                    "stepRef": step["stepRef"],
                    "premiseOrdinal": ordinal,
                }
            )
            return None
        input_interfaces.append(interface)
    return inputs, input_interfaces


def _compose_interfaces(left, right, output):
    intermediate = ("TypeId", "ScaleId", "NormId")
    if not all(left["output" + key] == right["input" + key] for key in intermediate):
        return False
    outer = {"input" + key: left["input" + key] for key in intermediate}
    outer.update({"output" + key: right["output" + key] for key in intermediate})
    outer.update({key: left[key] for key in ("domainId", "representationId")})
    return all(output[key] == value for key, value in outer.items())


def _shared_scope(inputs):
    if not inputs:
        return False
    keys = ("telescope", "assumptions")
    return all(record[key] == inputs[0][key] for record in inputs for key in keys)


def _premise_scopes(step, combo, residuals):
    substitutions = [row["termRef"] for row in step["substitutions"]]
    for ordinal, item in enumerate(combo):
        witness = item["routeWitness"]
        code = None
        if witness["localContextRef"] != step["localContextRef"]:
            code = "incompatible-local-context"
        inherited = witness["substitutionRefs"]
        if inherited and inherited != substitutions:
            code = "incompatible-substitution"
        if code:
            residuals.append({"code": code, "stepRef": step["stepRef"], "premiseOrdinal": ordinal})
            return False
    return True
