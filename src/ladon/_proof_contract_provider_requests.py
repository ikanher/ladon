"""Pure construction of exact, not-yet-dispatched provider slice requests."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import PurePosixPath

from ladon._proof_contract_obligation_check_inputs import (
    _requirements_for_demand,
    _selected_identity,
)
from ladon.proofir_v3 import canonical_bytes, validate_envelope

_MAX_INPUT_BYTES = 8 * 1024**2
_MAX_TIMEOUT = 30
_MAX_RSS_BYTES = 12 * 1024**3
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_LEAN_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")


def _digest(value):
    return "sha256:" + hashlib.sha256(
        canonical_bytes(value, max_bytes=_MAX_INPUT_BYTES)
    ).hexdigest()


def _validate_arguments(analysis, context, route, demand, requirement, deadline, limits):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    if _planned_input_size([analysis, context, route, demand, requirement, deadline, limits]) > _MAX_INPUT_BYTES:
        raise ValueError('aggregate provider request inputs exceed 8 MiB')
    if not all(isinstance(value, dict) for value in (analysis, context, route, demand, requirement)):
        raise TypeError("analysis, context, route, demand, and requirement must be objects")
    if not isinstance(context.get("artifacts"), list) or len(context["artifacts"]) > 4096:
        raise ValueError("context artifacts must be a bounded list")
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("deadline must be finite")
    if not isinstance(limits, dict) or set(limits) != {
        "timeout_seconds", "max_output_bytes", "max_rss_bytes"
    }:
        raise ValueError("provider request limits have an invalid schema")
    _validate_limits(limits)

    desired, reading = _analysis_inputs(analysis)
    _validate_members(analysis, route, demand, requirement)
    return analysis, desired, reading


def _validate_limits(limits):
    if (
        type(limits["timeout_seconds"]) not in (int, float)
        or not math.isfinite(limits["timeout_seconds"])
        or not 0 < limits["timeout_seconds"] <= _MAX_TIMEOUT
        or type(limits["max_output_bytes"]) is not int
        or not 1 <= limits["max_output_bytes"] <= _MAX_INPUT_BYTES
        or type(limits["max_rss_bytes"]) is not int
        or not 1 <= limits["max_rss_bytes"] <= _MAX_RSS_BYTES
    ):
        raise ValueError("provider request limits exceed the fixed profile")



def _analysis_inputs(analysis):
    checked_analysis = validate_envelope(analysis, max_bytes=_MAX_INPUT_BYTES).to_dict()
    if checked_analysis != analysis or analysis.get("artifactKind") != "proofir.contract-analysis":
        raise ValueError("analysis artifact is not an exact validated native owner")
    payload = analysis.get("payload")
    if not isinstance(payload, dict) or payload.get("stage") != "obligations":
        raise ValueError("analysis artifact is not an obligations result")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("schema") != "ladon-contract-obligation-planner-v2":
        raise ValueError("provider expansion requires planner-v2")
    desired = payload.get('request', {}).get('desiredContract')
    reading = payload.get('request', {}).get('desiredReadingIdentity')
    if not isinstance(desired, dict) or not isinstance(reading, dict):
        raise TypeError('native desired contract and reading identity are required')
    return desired, reading


def _validate_members(analysis, route, demand, requirement):
    result = analysis['payload']['result']

    _unique_member(route, result.get('routeComparisons'), 'route')
    _unique_member(demand, route.get('obligationBundle', {}).get('demands'), 'demand')
    requirements = route.get('backwardRequirements')
    _unique_member(requirement, requirements, 'requirement')
    matches = _requirements_for_demand(requirements, demand)
    if not matches or sum(row == requirement for _, row in matches) != 1:
        raise ValueError("requirement does not bind to the native demand")
    if route.get("routeId") != demand.get("routeId", route.get("routeId")):
        raise ValueError("demand route identity differs from its owner")
    if requirement.get("parentWitnessRef") != demand.get("witnessRef"):
        raise ValueError("requirement witness differs from the native demand")


def _unique_member(value, rows, label):
    if not isinstance(rows, list) or rows.count(value) != 1:
        raise ValueError(label+' is not a unique member of its native owner')


def _source_selection(analysis, context, requirement):
    ref = requirement.get('forwardContractRef')
    if not isinstance(ref, dict) or ref.get('kind') != 'contract':
        return None, 'selected forward contract reference is unavailable'
    if analysis['payload'].get('contractRefs', []).count(ref) != 1:
        return None, 'forward contract is not uniquely owned by analysis'
    contract = _exact_owner(context['artifacts'], ref, 'proofir.contract', analysis['environmentRef'])
    if contract is None or contract['payload']['contractId'] != ref.get('localId'):
        return None, 'forward contract owner is unavailable'
    refs = contract['payload'].get('sourceMapRefs', [])
    if not refs:
        return None, 'forward contract has no source-map owner'
    candidates = []
    for source_ref in refs:
        found = _source_map_candidates(context['artifacts'], source_ref, analysis['environmentRef'])
        if found is None:
            return None, 'source-map reference or owner is unavailable'
        candidates.extend(found)
    if len(candidates) != 1:
        return None, 'no unique producer-declaration anchor is owned by the forward contract'
    return candidates[0], None


def _exact_owner(artifacts, ref, kind, environment):
    rows = [row for row in artifacts if row.get('artifactId') == ref.get('artifactRef')
            and row.get('artifactKind') == kind]
    if len(rows) != 1:
        return None
    try:
        owner = validate_envelope(rows[0], max_bytes=_MAX_INPUT_BYTES).to_dict()
    except (TypeError, ValueError):
        return None
    if owner != rows[0] or owner.get('environmentRef') != environment:
        return None
    subject = {'kind': ref['kind'], 'localId': ref['localId']}
    return owner if subject in owner['subjectRefs'] else None


def _source_map_candidates(artifacts, ref, environment):
    if not isinstance(ref, dict) or set(ref) != {'artifactRef', 'kind', 'localId'}:
        return None
    if ref['kind'] != 'source-map':
        return None
    source_map = _exact_owner(artifacts, ref, 'proofir.source-map', environment)
    if source_map is None or source_map['payload']['sourceMapId'] != ref['localId']:
        return None
    candidates = []
    for anchor in source_map['payload']['anchors']:
        if _valid_anchor(anchor, source_map['subjectRefs']):
            candidates.append({'availability': 'available',
                'sourcePath': anchor['sourcePath'], 'module': anchor['module'],
                'declaration': anchor['declName'], 'contentDigest': anchor['contentDigest'],
                'anchor': copy.deepcopy(anchor), 'sourceMapRef': copy.deepcopy(ref)})
    return candidates


def _valid_anchor(anchor, subjects):
    subject = anchor.get('subjectRef')
    expected = {'kind': 'declaration', 'localId': anchor.get('declName')}
    return (anchor.get('matchMethod') == 'producer-declaration' and subject == expected
            and subject in subjects and _valid_anchor_names(anchor)
            and _valid_position(anchor.get('start')) and _valid_position(anchor.get('end')))


def _valid_anchor_names(anchor):
    values = [anchor.get('module'), anchor.get('declName')]
    if any(not isinstance(value, str) or not _LEAN_NAME.fullmatch(value) for value in values):
        return False
    path, digest = anchor.get('sourcePath'), anchor.get('contentDigest')
    return (isinstance(path, str) and _valid_source_path(path)
            and isinstance(digest, str) and _SHA256.fullmatch(digest) is not None)


def _valid_position(value):
    return (
        isinstance(value, dict)
        and type(value.get("byte")) is int and value["byte"] >= 0
        and type(value.get("line")) is int and value["line"] >= 1
        and type(value.get("column")) is int and value["column"] >= 1
    )


def _valid_source_path(value):
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value and bool(path.parts)


def make_provider_slice_request(analysis, context, route, demand, requirement, deadline, limits):
    """Retain a native provider demand and its unique, verified source anchor."""
    analysis, desired, reading = _validate_arguments(
        analysis, context, route, demand, requirement, deadline, limits
    )
    try:
        owned_demand = copy.deepcopy(demand)
        incoming = copy.deepcopy(demand.get("incomingOccurrences"))
        identity = _selected_identity(route, requirement)
        binding = {
            "analysisArtifactRef": analysis["artifactId"],
            "demand": owned_demand,
            "demandDigest": _digest(owned_demand),
            "incomingOccurrences": incoming,
            "selectedIdentity": identity,
            "desiredReadingIdentity": copy.deepcopy(reading),
            "desiredContractDigest": _digest(desired),
        }
        source_selection, reason = _source_selection(analysis, context, requirement)
        request = {
            "schema": "ladon-provider-slice-request-v1",
            "status": "not-dispatched",
            "obligation": demand["demandId"],
            "routeId": route["routeId"],
            "sourceRef": copy.deepcopy(requirement["parentWitnessRef"]),
            "contractRef": copy.deepcopy(requirement["forwardContractRef"]),
            "bounds": copy.deepcopy(limits),
            "deadlineMonotonic": float(deadline),
            "goalOrigin": "requested-original-provider-source",
            "binding": binding,
            "sourceSelection": source_selection,
            "diagnostic": None if reason is None else {
                "code": "source-anchor-unavailable", "message": reason[:500],
            },
        }
        encoded = json.dumps(
            request, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > _MAX_INPUT_BYTES:
            raise ValueError("provider slice request exceeds the 8 MiB bound")
        return request
    except RecursionError as error:
        raise ValueError("provider slice request exceeds nesting bounds") from error
