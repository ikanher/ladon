"""Bounded native attachment projection for attributed investigation observations."""

import copy

from ladon.correspondence_interpretation import closed
from ladon.proofir_v3 import validate_envelope_batch

ATTACHMENT_KEYS = {"artifact", "context"}


def validate_contract_analysis(value, expected_finding_id):
    closed(value, ATTACHMENT_KEYS, "contract analysis attachment")
    context = value["context"]
    closed(context, {"artifacts"}, "contract analysis context")
    artifacts = context["artifacts"]
    if type(artifacts) is not list:
        raise TypeError("contract analysis context artifacts must be an array")
    target = value["artifact"]
    if not isinstance(target, dict) or target.get("artifactKind") != "proofir.contract-analysis":
        raise ValueError("contract analysis artifact has the wrong kind")
    validate_envelope_batch([*copy.deepcopy(artifacts), copy.deepcopy(target)])
    payload = target.get("payload", {})
    if (payload.get("stage") == "rational-branch-check"
            and payload.get("result", {}).get("originalFindingId") != expected_finding_id):
        raise ValueError("checked rational branch is attached to a different finding identity")
    return copy.deepcopy(value)


def contract_dimensions(attachment, responses):
    from ladon.investigation_observations import review_relation

    return {
        "sourceFidelity": review_relation(responses, "sourceFidelity"),
        "extractionCompleteness": "not-established",
        "routeSupport": "not-established",
        "mathematicalFalsity": "not-established",
        "methodCorrespondence": review_relation(responses, "method"),
        "exploredPopulation": {
            "coverage": copy.deepcopy(attachment["artifact"]["coverage"]),
            "authority": "declared-child-coverage-only",
        },
    }


def project_contract_finding(finding, record, responses):
    attachment = record["contractAnalysis"]
    finding.update({
        "projectionSchema": "ladon-investigation-contract-finding-v1",
        "contractAnalysis": copy.deepcopy(attachment),
        "contractDimensions": contract_dimensions(attachment, responses),
        "formalSources": copy.deepcopy(record["formalSources"]),
    })
    return finding
