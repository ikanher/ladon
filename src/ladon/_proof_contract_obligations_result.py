"""Bounded result construction for backward templates."""
from copy import deepcopy

from ladon._contract_propagation_budget import encoded_size, fingerprint
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proof_contracts import validate_contract


def _base_result(desired, evidence):
    return {
        "schema": "ladon-proof-contract-backward-transform-v1",
        "status": "residual",
        "branches": [],
        "residuals": [],
        "authority": "conditional-template",
        "checkerAuthority": "none",
        "mathematicalFalsity": "not-established",
        "necessity": "not-claimed",
        "profileDigest": PROFILE_DIGEST,
        "ruleId": evidence["ruleId"],
        "ruleDeclaration": evidence["ruleDeclaration"],
        "attributionStatus": evidence["attributionStatus"],
        "desiredContractDigest": _digest(desired),
        "ruleRef": evidence["ruleRef"],
        "evidenceRefs": list(evidence["evidenceRefs"]),
        "limitations": ["source-binding-unchecked", "evidence-binding-unchecked"],
    }


def _digest(value):
    return "sha256:" + fingerprint(value).hex()




def _make_branch(spec):
    rows = []
    for ordinal, interface in enumerate(spec["premises"]):
        record = deepcopy(spec["desired"])
        record["endpointId"] = interface["endpointId"]
        record["context"] = {
            "objectId": interface["objectId"], "domainId": interface["domainId"],
            "scaleId": interface["inputScaleId"], "representationId": interface["representationId"],
        }
        record["conclusionId"] = interface["conclusionId"]
        record["features"]["regularity"]["scaleId"] = interface["inputScaleId"]
        offsets = spec["offsets"]
        if offsets is not None:
            record["features"]["regularity"]["offset"] = offsets[ordinal]
        record = validate_contract(record)
        rows.append({
            "premiseOrdinal": ordinal,
            "interfaceId": interface["interfaceId"],
            "contractRecord": record,
        })
    return {"requirements": rows}


def _finish(result, max_output):
    result["resultDigest"] = "sha256:" + "0" * 64
    if encoded_size(result, max_output) > max_output:
        raise ValueError("result exceeds maxOutputBytes")
    result.pop("resultDigest")
    result["resultDigest"] = _digest(result)
    return result

