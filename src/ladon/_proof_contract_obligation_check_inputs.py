"""Closed bounded input ownership and exact native-plan reconstruction."""
from __future__ import annotations

import json
import math

from .proof_contract_source_obligations import _plain

MAX_BYTES = 8 * 1024**2
MAX_MESSAGE = 500
_REQUEST_KEYS = {"repoRoot", "analysisArtifact", "context", "sourceBindings",
                 "outputDir", "deadlineMonotonic", "limits", "maxCheckAttempts"}
_BINDING_KEYS = {"parentSnapshot", "parentReadingId", "providers"}
_PROVIDER_KEYS = {"contractRef", "providerSnapshot", "providerReadingId", "terms"}


def _validate_and_own(request):
    if not isinstance(request, dict) or set(request) != _REQUEST_KEYS:
        raise ValueError("source-check request must use the closed schema")
    from ladon._proof_contract_planned_source_inputs import _planned_input_size

    if _planned_input_size(request) > MAX_BYTES:
        raise ValueError("source-check input exceeds 8 MiB")
    owned = _plain(request)
    # _plain owns and canonicalizes Path/dataclass values; JSON round-tripping
    # then detaches nested caller-owned dicts and enforces finite JSON scalars.
    owned = json.loads(json.dumps(owned, ensure_ascii=False, allow_nan=False))
    _validate_context(owned["context"])
    _validate_bounds(owned)
    _validate_bindings(owned["sourceBindings"])
    return owned



def _validate_bounds(owned):
    from ladon.proof_contract_source_obligations import _limits

    if not isinstance(owned["deadlineMonotonic"], (int, float)) or not math.isfinite(owned["deadlineMonotonic"]):
        raise ValueError("deadlineMonotonic must be finite")
    if type(owned["maxCheckAttempts"]) is not int or not 1 <= owned["maxCheckAttempts"] <= 64:
        raise ValueError("maxCheckAttempts must be between 1 and 64")
    limits = owned["limits"]
    if not isinstance(limits, dict) or set(limits) != {"timeout_seconds", "max_output_bytes", "max_rss_bytes"}:
        raise ValueError("limits schema is invalid")
    if limits["max_output_bytes"] > MAX_BYTES or limits["max_rss_bytes"] > 12 * 1024**3:
        raise ValueError("source-check bounds exceed the fixed profile")
    owned["limits"] = _limits(limits)



def _validate_bindings(bindings):
    if not isinstance(bindings, dict) or set(bindings) != _BINDING_KEYS:
        raise ValueError("sourceBindings schema is invalid")
    if not isinstance(bindings["providers"], list) or len(bindings["providers"]) > 4096:
        raise ValueError("provider list exceeds its bound")
    for provider in bindings["providers"]:
        _validate_provider(provider)



def _validate_provider(provider):
    if not isinstance(provider, dict) or set(provider) != _PROVIDER_KEYS:
        raise ValueError("provider binding schema is invalid")
    if not isinstance(provider["terms"], list) or len(provider["terms"]) > 64:
        raise ValueError("provider term list exceeds its bound")
    if any(not isinstance(term, str) or len(term.encode("utf-8")) > 65536 for term in provider["terms"]):
        raise ValueError("provider term is invalid or too large")



def _validate_context(context):
    if not isinstance(context, dict) or set(context) != {"artifacts"}:
        raise ValueError("context must contain only the native artifact list")
    if not isinstance(context["artifacts"], list) or len(context["artifacts"]) > 4096:
        raise ValueError("native artifact list exceeds its bound")



def _validation_plan(checked, context):
    """Reconstruct the request from validated refs; return historical result."""
    from ladon.proof_contract_obligation_artifacts import request_from_payload

    artifact = checked["result"]
    payload = artifact.get("payload") if isinstance(artifact, dict) else None
    if not isinstance(payload, dict) or payload.get("stage") != "obligations":
        raise ValueError("native validation did not return an obligations artifact")
    by_id = {row["artifactId"]: row for row in context["artifacts"]}
    goal_ref = payload.get("derivationGoalRef", {})
    graph = by_id.get(goal_ref.get("artifactRef"))
    contract_rows = payload.get("contractRefs")
    if graph is None or not isinstance(contract_rows, list):
        raise ValueError("validated artifact references are incomplete")
    contracts = [by_id[ref["artifactRef"]] for ref in contract_rows]
    plan_request = request_from_payload(graph, contracts, payload["request"])
    historical = payload.get("result")
    if not isinstance(historical, dict) or historical.get("schema") != "ladon-contract-obligation-planner-v2":
        raise ValueError("source checks require a planner-v2 historical result")
    return plan_request, historical



def _provider_index(providers):
    result = {}
    for provider in providers:
        key = _ref_key(provider.get("contractRef"))
        if key is None or key in result:
            raise ValueError("provider contract references must be present and unique")
        result[key] = provider
    return result



def _requirements_for_demand(requirements, demand):
    from ladon._contract_propagation_budget import fingerprint
    witness = demand.get("witnessRef")
    digest = demand.get("outputContractDigest")
    matches = []
    for index, row in enumerate(requirements):
        if row.get("parentWitnessRef") != witness:
            continue
        if "sha256:" + fingerprint(row.get("contractRecord")).hex() != digest:
            continue
        matches.append((index, row))
    return matches



def _selected_identity(route, row):
    fields = ("stepRef", "witnessRef", "branchRef", "branchIndex", "premiseOrdinal",
              "forwardContractRef", "statementRef", "parentWitnessRef", "interfaceId")
    return {"routeId": route["routeId"], **{key: row[key] for key in fields}}



def _verify_parent_identity(plan_request, reading_id):
    identity = plan_request.desired_reading_identity
    if identity.get("readingId") != reading_id:
        raise ValueError("parent reading does not match native desired identity")



def _ref_key(value):
    if not isinstance(value, dict):
        return None
    return (value.get("artifactRef"), value.get("kind"), value.get("localId"))
