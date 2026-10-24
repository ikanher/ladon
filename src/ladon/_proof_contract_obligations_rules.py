"""Admitted rule checks and finite backward choices."""
from ladon.proof_contract_rules import PROFILE, PROFILE_DIGEST

from ._proof_contract_obligations_validation import _MAX_CHOICES, _bounded_ref_list, _identifier


def _preflight_rule_values(evidence, parameters, choices):
    rule_id = evidence["ruleId"]
    known = {"identity", "weaken-loss", "compose", "combine-estimates"}
    if rule_id not in known:
        if parameters or choices:
            raise ValueError("unsupported rules cannot supply parameters or choices")
        return
    _validate_rule_parameters(rule_id, parameters)
    _validate_choices(rule_id, choices)


def _dispatch_residual(desired, evidence, premises, output, parameters, choices):
    rule_id = evidence["ruleId"]
    supported = {"identity", "weaken-loss", "compose", "combine-estimates"}
    if rule_id not in supported:
        return {"code": "unsupported-rule", "ruleId": rule_id}
    if evidence["ruleDeclaration"] != PROFILE["rules"].get(rule_id):
        return {"code": "rule-declaration-mismatch", "ruleId": rule_id}
    if evidence["profileDigest"] != PROFILE_DIGEST:
        return {"code": "rule-profile-mismatch", "ruleId": rule_id}
    arity = 1 if rule_id in {"identity", "weaken-loss"} else 2
    if len(premises) != arity:
        return {"code": "premise-arity-mismatch", "ruleId": rule_id}
    if not _desired_matches(desired, output):
        return {"code": "desired-output-interface-mismatch"}
    return _interface_residual(rule_id, desired, premises, output, parameters)


def _interface_residual(rule_id, desired, premises, output, parameters):
    if rule_id in {"identity", "weaken-loss"}:
        return _single_interface_residual(rule_id, premises[0], output)
    if rule_id == "combine-estimates":
        return _combine_interface_residual(premises, output)
    return _compose_residual(desired, premises, output, parameters)


def _single_interface_residual(rule_id, premise, output):
    if _same_interface(premise, output):
        return None
    code = "incompatible-identity-interface" if rule_id == "identity" else "incompatible-weakening-interface"
    return {"code": code}


def _combine_interface_residual(premises, output):
    if _same_interface(premises[0], premises[1]) and _same_interface(premises[0], output):
        return None
    return {"code": "unsupported-estimate-scope-transport"}


def _compose_residual(desired, premises, output, parameters):
    mismatch = _compose_check(desired, premises[0], premises[1], output, parameters)
    if mismatch:
        return mismatch
    constant = desired["features"]["constantDependencies"]
    if "binderId" in constant:
        return {"code": "unsupported-anchored-choice-transport"}
    if not _all_known(desired):
        return {"code": "unknown-contract-feature"}
    return None

def _validate_rule_parameters(rule_id, parameters):
    expected = {
        "identity": set(),
        "weaken-loss": {"targetOffset", "nestednessRefs"},
        "compose": {"compositeOperatorId"},
        "combine-estimates": {"leftEmbeddingRefs", "rightEmbeddingRefs", "nestednessRefs"},
    }[rule_id]
    if set(parameters) != expected:
        raise ValueError("rule parameters have invalid or missing keys")
    for key, value in parameters.items():
        if key.endswith("Refs"):
            _bounded_ref_list(value, "parameters." + key, nonempty=True)
    if rule_id == "weaken-loss":
        _validate_weakening_parameters(parameters)
    if rule_id == "compose":
        _identifier(parameters["compositeOperatorId"], "compositeOperatorId")


def _validate_weakening_parameters(parameters):
    target = parameters["targetOffset"]
    if type(target) is not int or not 0 <= target <= 2**53 - 1:
        raise ValueError("targetOffset must be a supported natural")

def _validate_choices(rule_id, choices):
    expected = {"identity": set(), "weaken-loss": {"weakenLossOffsets"},
                "compose": {"lossSplits"}, "combine-estimates": set()}[rule_id]
    if set(choices) != expected:
        raise ValueError("transform choices have invalid or missing keys")
    if rule_id == "weaken-loss":
        _validate_offsets(choices["weakenLossOffsets"])
    if rule_id == "compose":
        _validate_splits(choices["lossSplits"])


def _validate_offsets(offsets):
    if type(offsets) is not list or len(offsets) > _MAX_CHOICES:
        raise ValueError("weaken-loss choices exceed the finite choice cap")
    if any(type(value) is not int or not 0 <= value <= 2**53 - 1 for value in offsets):
        raise ValueError("weaken-loss offsets must be supported naturals")


def _validate_splits(splits):
    if type(splits) is not list or len(splits) > _MAX_CHOICES:
        raise ValueError("compose choices exceed the finite choice cap")
    for split in splits:
        if type(split) is not list or len(split) != 2:
            raise ValueError("each loss split must contain two supported naturals")
        if any(type(value) is not int or not 0 <= value <= 2**53 - 1 for value in split):
            raise ValueError("each loss split must contain two supported naturals")

def _desired_matches(desired, interface):
    return (
        desired["endpointId"] == interface["endpointId"]
        and desired["context"] == {
            "objectId": interface["objectId"],
            "domainId": interface["domainId"],
            "scaleId": interface["inputScaleId"],
            "representationId": interface["representationId"],
        }
        and desired["conclusionId"] == interface["conclusionId"]
        and desired["features"]["regularity"]["scaleId"] == interface["inputScaleId"]
    )


def _same_interface(left, right):
    fields = (
        "endpointId", "operatorId", "objectId", "domainId", "representationId",
        "inputTypeId", "outputTypeId", "inputScaleId", "outputScaleId",
        "inputNormId", "outputNormId", "conclusionId",
    )
    return all(left[key] == right[key] for key in fields)


def _compose_check(desired, left, right, output, parameters):
    typed = ("TypeId", "ScaleId", "NormId")
    if not all(left["output" + key] == right["input" + key] for key in typed):
        return {"code": "incompatible-compose-interface"}
    outer = {"input" + key: left["input" + key] for key in typed}
    outer.update({"output" + key: right["output" + key] for key in typed})
    outer.update({key: left[key] for key in ("domainId", "representationId")})
    if any(output[key] != value for key, value in outer.items()):
        return {"code": "incompatible-compose-interface"}
    if parameters["compositeOperatorId"] != output["operatorId"]:
        return {"code": "incompatible-compose-interface"}
    if not _desired_matches(desired, output):
        return {"code": "desired-output-interface-mismatch"}
    return None


def _all_known(record):
    features = record["features"]
    return (features["regularity"]["state"] == "known"
            and features["constantDependencies"]["state"] == "known"
            and all(row["state"] == "known" for row in features["witnessDependencies"]))


def _branch_specs(rule_id, desired, premises, output, parameters, choices):
    if rule_id == "compose":
        return _compose_specs(desired, premises, choices)
    if rule_id == "weaken-loss":
        return _weakening_specs(desired, premises, parameters, choices)
    if rule_id == "combine-estimates":
        return _combination_specs(desired, premises)
    return [_spec(desired, premises, None)]


def _compose_specs(desired, premises, choices):
    loss = desired["features"]["regularity"]["offset"]
    if type(loss) is not int:
        return {"code": "unknown-contract-feature"}
    splits = choices["lossSplits"]
    if not splits:
        return {"code": "empty-loss-split-choices"}
    if any(sum(split) != loss for split in splits):
        return {"code": "invalid-compose-loss-split"}
    return [_spec(desired, premises, split) for split in splits]


def _weakening_specs(desired, premises, parameters, choices):
    target = desired["features"]["regularity"]["offset"]
    if type(target) is not int or parameters["targetOffset"] != target:
        return {"code": "invalid-weakening-target"}
    offsets = choices["weakenLossOffsets"]
    if not offsets:
        return {"code": "empty-weakening-choices"}
    if any(value > target for value in offsets):
        return {"code": "invalid-weakening-offset"}
    return [_spec(desired, premises, [value]) for value in offsets]


def _combination_specs(desired, premises):
    if not _all_known(desired) or "binderId" in desired["features"]["constantDependencies"]:
        return {"code": "unsupported-estimate-combination-side-condition"}
    return [_spec(desired, premises, None)]

def _spec(desired, premises, offsets):
    return {"desired": desired, "premises": premises, "offsets": offsets}

