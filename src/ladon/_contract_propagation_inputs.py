"""Input admission and hard resource limits before graph traversal."""

from ladon._contract_propagation_common import _deadline
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import validate_envelope

LIMITS = {
    "maxDepth": 64,
    "maxFrontierContractsPerStatement": 128,
    "maxCombinationsPerStep": 4096,
    "maxEvaluatedSteps": 8192,
    "maxTotalCombinations": 16384,
    "maxGraphReferences": 4096,
    "maxWitnessCandidates": 256,
    "maxOutputBytes": 8 * 1024 * 1024,
}


def read_bounds(bounds):
    if bounds is None:
        return dict(LIMITS), None
    if not isinstance(bounds, dict):
        raise TypeError("bounds must be an object")
    caps, deadline = dict(LIMITS), None
    for key, value in bounds.items():
        if key == "deadlineUtc":
            deadline = _deadline(value)
        else:
            _bound(key, value)
            caps[key] = value
    return caps, deadline


def _bound(key, value):
    if key not in LIMITS or type(value) is not int:
        raise ValueError("invalid propagation bound")
    minimum = 1024 if key == "maxOutputBytes" else 1
    if not minimum <= value <= LIMITS[key]:
        raise ValueError("invalid propagation bound")


def read_contracts(artifacts, environment):
    if not isinstance(artifacts, list) or len(artifacts) > 4096:
        raise ValueError("contract_artifacts must be a bounded list")
    contracts = {}
    for artifact in artifacts:
        checked = validate_envelope(artifact).to_dict()
        if checked["artifactKind"] != "proofir.contract":
            raise ValueError("contract input must be proofir.contract")
        if checked["environmentRef"] != environment:
            raise ValueError("contract artifact environment mismatch")
        payload = checked["payload"]
        if payload["profileDigest"] != PROFILE_DIGEST:
            raise ValueError("contract profile digest mismatch")
        key = (checked["artifactId"], payload["contractId"])
        if key in contracts:
            raise ValueError("contract artifacts must not duplicate exact artifact identity")
        contracts[key] = checked
    return contracts


def reference_count(graph, contracts, bindings, interfaces, scopes):
    attached = sum(len(row["subjectRefs"]) for row in contracts.values())
    rules = sum(
        2 + len(row["evidenceRefs"]) + _parameter_refs(row["parameters"])
        for row in bindings.values()
    )
    endpoints = sum(
        len(row["evidenceRefs"]) + int("contractRef" in row) for row in interfaces.values()
    )
    scoped = sum(
        3 + len(row["substitutionRefs"]) + len(row["evidenceRefs"])
        for rows in scopes.values()
        for row in rows
    )
    return (
        len(graph.subjects) + _step_occurrences(graph.steps) + attached + rules + endpoints + scoped
    )


def _parameter_refs(parameters):
    return sum(len(value) for value in parameters.values() if isinstance(value, list))


def preflight_size(derivation, contracts, bindings, interfaces, scopes):
    """Inspect collection lengths before native copying and wrapper snapshots."""
    references = _subject_count(derivation) + _graph_occurrences(derivation)
    if not isinstance(contracts, list) or len(contracts) > 4096:
        raise ValueError("contract_artifacts must be a bounded list")
    for row in contracts:
        references += _subject_count(row)
        if references > LIMITS["maxGraphReferences"]:
            return references
    for rows in (bindings, interfaces, scopes):
        references += _wrapper_size(rows)
    return references


def _subject_count(artifact):
    from collections.abc import Mapping

    if not isinstance(artifact, Mapping):
        artifact = getattr(artifact, "payload", None)
    if not isinstance(artifact, Mapping):
        raise TypeError("artifact must be a native envelope")
    return len(artifact.get("subjectRefs", ()))


def _wrapper_size(rows):
    if not isinstance(rows, (list, tuple)):
        raise TypeError("wrapper collection must be a list")
    size = len(rows)
    if size > LIMITS["maxGraphReferences"]:
        return size
    for row in rows:
        size += _wrapper_row_size(row)
        if size > LIMITS["maxGraphReferences"]:
            return size
    return size


def _wrapper_row_size(row):
    if not isinstance(row, dict):
        raise TypeError("wrapper must be an object")
    keys = ("evidenceRefs", "substitutionRefs", "objectMap", "binderMap")
    size = sum(len(row[key]) for key in keys if isinstance(row.get(key), list))
    parameters = row.get("parameters", {})
    if isinstance(parameters, dict):
        size += _parameter_refs(parameters)
    return size


def _graph_occurrences(artifact):
    from collections.abc import Mapping

    if not isinstance(artifact, Mapping):
        artifact = artifact.payload
    payload = artifact.get("payload", {})
    if not isinstance(payload, Mapping):
        raise TypeError("artifact payload must be an object")
    return _step_occurrences(payload.get("steps", ()))


def _step_occurrences(steps):
    count = 0
    for step in steps:
        count += 4 + len(step.get("premiseRefs", ())) + len(step.get("substitutions", ()))
        if count > LIMITS["maxGraphReferences"]:
            return count
    return count
