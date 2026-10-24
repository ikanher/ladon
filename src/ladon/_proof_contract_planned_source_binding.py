"""Exact native provider artifact and source-map binding."""
from __future__ import annotations

import copy
import hashlib

from .proof_contract_source_obligations import MAX_INPUT_BYTES


def _validate_plan_provider(selected, plan_request, provider, parent, root):
    contract = _exact_provider_contract(selected, plan_request, provider)
    source_maps = _verified_provider_source_maps(contract, provider)
    _verify_provider_anchors(source_maps, provider, root)
    _verify_provider_order(parent, provider)
    _verify_selected_provider_record(selected, provider)


def _exact_provider_contract(selected, plan_request, provider):
    ref = selected["forwardContractRef"]
    if not isinstance(ref, dict) or ref.get("kind") != "contract":
        raise ValueError("selected route leaf is not a source contract")
    request_contract = _unique_contract_artifact(plan_request.contract_artifacts, ref)
    contract = _unique_contract_artifact(provider["artifacts"], ref)
    _compare_provider_contract(contract, request_contract, provider)
    payload = contract["payload"]
    if (ref.get("artifactRef") != contract.get("artifactId")
            or ref.get("localId") != payload.get("contractId")
            or ref.get("kind") != "contract"):
        raise ValueError("forwardContractRef does not identify the exact provider contract")
    return contract


def _unique_contract_artifact(artifacts, ref):
    matches = [row for row in artifacts if row.get("artifactId") == ref.get("artifactRef")
               and row.get("artifactKind") == "proofir.contract"]
    if len(matches) != 1:
        raise ValueError("source contract reference is not unique in artifacts")
    return matches[0]


def _compare_provider_contract(contract, request_contract, provider):
    if contract != request_contract or contract["payload"].get("record") != provider.get("contract"):
        raise ValueError("planned source contract differs from verified provider snapshot")


def _verified_provider_source_maps(contract, provider):
    source_maps = []
    for source_ref in contract["payload"].get("sourceMapRefs", []):
        matches = [row for row in provider["artifacts"]
                   if row.get("artifactId") == source_ref.get("artifactRef")
                   and row.get("artifactKind") == "proofir.source-map"
                   and source_ref.get("kind") == "source-map"
                   and row.get("payload", {}).get("sourceMapId") == source_ref.get("localId")]
        if len(matches) != 1:
            raise ValueError("contract source-map reference is not uniquely verified")
        source_maps.extend(matches)
    if not source_maps:
        raise ValueError("provider contract has no verified source map")
    return source_maps


def _verify_provider_anchors(source_maps, provider, root):
    source, selection = provider["source"], provider["selection"]
    location = provider["observation"]["declarationRange"]
    for source_map in source_maps:
        _verify_one_provider_anchor(source_map, source, selection, location, root)


def _verify_one_provider_anchor(source_map, source, selection, location, root):
    anchors = source_map["payload"].get("anchors", [])
    matching = [anchor for anchor in anchors
                if _anchor_matches_observation(anchor, source, selection, location)]
    if len(matching) != 1:
        raise ValueError("source map anchor does not match verified provider declaration")
    _check_anchor_bytes(matching[0], source, selection, location, root)


def _anchor_matches_observation(anchor, source, selection, location):
    subject = {"kind": "declaration", "localId": selection["declaration"]}
    return (anchor.get("subjectRef") == subject
        and anchor.get("module") == selection["module"]
        and anchor.get("declName") == selection["declaration"]
        and anchor.get("sourcePath") == source["path"]
        and anchor.get("contentDigest") == "sha256:" + source["sha256"]
        and anchor.get("start", {}).get("line") == location["startLine"]
        and anchor.get("start", {}).get("column") == location["startColumn"] + 1
        and anchor.get("end", {}).get("line") == location["endLine"]
        and anchor.get("end", {}).get("column") == location["endColumn"] + 1)


def _check_anchor_bytes(anchor, source, selection, location, root):
    from ladon.proof_contract_formal import _position
    from ladon.source_association_io import _read_regular, _source_path
    source_path = _source_path(root, source["path"], selection["module"])
    raw = _read_regular(source_path, MAX_INPUT_BYTES)
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("provider source changed during source-map binding")
    lines = raw.decode("utf-8").splitlines(keepends=True)
    start = _position(lines, location["startLine"], location["startColumn"])
    end = _position(lines, location["endLine"], location["endColumn"])
    if anchor.get("start") != start or anchor.get("end") != end:
        raise ValueError("source-map anchor byte range differs from observed declaration")


def _verify_provider_order(parent, provider):
    source, selection = provider["source"], provider["selection"]
    if (parent["source"] != source or parent["selection"]["module"] != selection["module"]
            or provider["observation"]["declarationRange"]["endLine"]
            >= parent["observation"]["declarationRange"]["startLine"]):
        raise ValueError("provider is not an earlier declaration in the exact parent source")


def _verify_selected_provider_record(selected, provider):
    record = copy.deepcopy(provider["contract"])
    record["features"]["regularity"]["offset"] = selected["contractRecord"]["features"]["regularity"]["offset"]
    if record != selected["contractRecord"]:
        raise ValueError("selected local record differs from provider contract beyond its offset")


