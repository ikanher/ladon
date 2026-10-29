"""Closed wire shapes for extracted observations; freshness requires re-extraction."""

import json

from ladon._expr_graph_protocol import validate_structural_text
from ladon.correspondence_interpretation import closed, text
from ladon.proof_slice_limits import validate_max_nodes
from ladon.scoped_slice import (
    premise_rows,
    profile_is_scoped,
    provider_frontiers,
    validate_provider_rows,
)
from ladon.slice_application_validation import validate_application_arguments

SLICE_KEYS = {
    "schema",
    "complete",
    "status",
    "nodes",
    "frontiers",
    "processReceipts",
    "selection",
    "source",
    "environment",
    "helper",
    "limits",
    "compiledInventory",
    "localContext",
    "observation",
    "sliceId",
}
EXPRESSION_KEYS = {"display", "structural"}
LOCAL_KEYS = {"name", "localId", "isProp", "binderInfo", "type", "letValue"}
ARGUMENT_KEYS = {"index", "expression", "type", "isProp", "binderInfo"}
APPLICATION_KEYS = {
    "occurrence",
    "application",
    "applicationType",
    "arguments",
    "closedApplicationTypeText",
    "closedApplicationProofText",
    "closedApplicationTypeStructural",
    "closedApplicationProofStructural",
}


def _expression(row):
    closed(row, EXPRESSION_KEYS, "observed expression")
    if not isinstance(row["display"], str):
        raise TypeError("expression presentation must be text")
    if len(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode()) > 1024**2:
        raise ValueError("serialized expression exceeds 1 MiB")
    validate_structural_text(row["structural"])


def _locals(rows, *, declaration=False):
    for row in rows:
        keys = (
            (LOCAL_KEYS - {"letValue"}) | {"isImplementationDetail"} if declaration else LOCAL_KEYS
        )
        closed(row, keys, "formal local")
        _expression(row["type"])
        if row.get("letValue") is not None:
            _expression(row["letValue"])
        if type(row["isProp"]) is not bool:
            raise TypeError("formal local isProp must be boolean")


def _arguments(rows):
    for i, row in enumerate(rows):
        closed(row, ARGUMENT_KEYS, "instantiated argument")
        if row["index"] != i or type(row["isProp"]) is not bool:
            raise ValueError("arguments require exact ordered occurrences and proposition flags")
        _expression(row["expression"])
        _expression(row["type"])


def _observations(frame, *, scoped=False, transported=False):
    closed(
        frame,
        {
            "protocol",
            "declaration",
            "declarationType",
            "declarationBinders",
            "proofLocalsAndLets",
            "sourceAttribution",
            "applicationHead",
            "applications",
            "importedModules",
        },
        "Lean application observation",
    )
    _expression(frame["declarationType"])
    _locals(frame["declarationBinders"], declaration=True)
    _locals(frame["proofLocalsAndLets"])
    closed(frame["sourceAttribution"], {"scope", "range"}, "declaration attribution")
    for i, row in enumerate(frame["applications"]):
        keys = APPLICATION_KEYS | {"localContext", "providerObservations", "scopePath", "nestedLocalIds"} if scoped else APPLICATION_KEYS
        if transported:
            keys = keys | {"transport"}
        closed(row, keys, "observed application")
        if transported:
            _transport(row["transport"], row)
        if row["occurrence"] != i:
            raise ValueError("observation occurrence order changed")
        _arguments(row["arguments"])
        _expression(row["application"])
        _expression(row["applicationType"])
        validate_application_arguments(row, frame["applicationHead"])
        validate_structural_text(row["closedApplicationTypeStructural"])
        validate_structural_text(row["closedApplicationProofStructural"])
        if scoped:
            _locals(row["localContext"])
            validate_provider_rows(row, _expression)


def validate_slice_shape(value):
    """Reject unknown fields and malformed expressions without granting authority."""
    closed(value, SLICE_KEYS, "extracted application slice")
    closed(
        value["selection"],
        {"sourceFile", "module", "declaration", "application", "occurrence"},
        "selection",
    )
    closed(
        value["source"], {"path", "sha256", "attribution", "module", "declaration"}, "formal source"
    )
    closed(value["helper"], {"sha256", "profile"}, "extraction helper")
    closed(
        value["limits"],
        {"secondsPerProcess", "rssBytes", "outputBytes", "nodes", "depth"},
        "limits",
    )
    validate_max_nodes(value["limits"]["nodes"])
    inventory = value["compiledInventory"]
    closed(
        inventory,
        {
            "moduleCount",
            "primaryBytes",
            "primaryDigest",
            "sidecarCount",
            "sidecarBytes",
            "sidecarSnapshotDigest",
            "snapshotDigest",
            "modules",
        },
        "compiled inventory",
    )
    for row in inventory["modules"]:
        closed(row, {"module", "digest"}, "compiled module")
    _locals(value["localContext"])
    scoped = profile_is_scoped(value)
    _observations(value["observation"], scoped=scoped,
                  transported=value["helper"]["profile"] == "scoped-identity-transport-v2")
    if len(value["nodes"]) != 1:
        raise ValueError("selected-application profile requires exactly one selected node")
    node = value["nodes"][0]
    closed(
        node,
        {
            "id",
            "kind",
            "declaration",
            "arguments",
            "premises",
            "type",
            "expression",
            "closedType",
            "closedProof",
        },
        "selected application",
    )
    _arguments(node["arguments"])
    _expression(node["type"])
    _expression(node["expression"])
    for row in node["premises"]:
        keys = {"occurrence", "proposition", "provider", "providerStatus"}
        if scoped:
            keys.add("providerObservation")
        closed(row, keys, "premise occurrence")
        _expression(row["proposition"])
        _expression(row["provider"])
    _check_consistency(value)


def _check_consistency(value):
    frame, selection, node = value["observation"], value["selection"], value["nodes"][0]
    selected = frame["applications"][selection["occurrence"]]
    closed(value["source"]["attribution"], {"scope", "range"}, "source attribution")
    scoped = profile_is_scoped(value)
    expected = premise_rows(selected, scoped=scoped)
    comparisons = [
        (value["localContext"], selected["localContext"] if scoped else frame["proofLocalsAndLets"]),
        (value["source"]["attribution"], frame["sourceAttribution"]),
        (value["source"]["path"], selection["sourceFile"]),
        (value["source"]["module"], selection["module"]),
        (value["source"]["declaration"], selection["declaration"]),
        (frame["declaration"], selection["declaration"]),
        (node["declaration"], frame["applicationHead"]),
        (node["arguments"], selected["arguments"]),
        (node["expression"], selected["application"]),
        (node["type"], selected["applicationType"]),
        (node["closedProof"], selected["closedApplicationProofText"]),
        (node["closedType"], selected["closedApplicationTypeText"]),
        (node["premises"], expected),
        (
            value["frontiers"],
            provider_frontiers(expected, scoped=scoped),
        ),
        (value["compiledInventory"]["moduleCount"], len(value["compiledInventory"]["modules"])),
    ]
    if any(left != right for left, right in comparisons):
        raise ValueError("slice projections disagree with their bound application observation")
    recorded = [row["module"] for row in value["compiledInventory"]["modules"]]
    if len(set(recorded)) != len(recorded) or set(recorded) != set(frame["importedModules"]):
        raise ValueError("compiled inventory does not cover loaded modules exactly once")


def _transport(value, original):
    closed(value, {"profile", "localContext", "application", "applicationType", "arguments",
                   "closedType", "closedProof"}, "identity transport")
    if value["profile"] != "fvar-substitution-v1":
        raise ValueError("unsupported identity transport profile")
    text(value["closedType"], "transport closed type")
    text(value["closedProof"], "transport closed proof")
    locals_ = value["localContext"]
    if len(locals_) != len(original["localContext"]):
        raise ValueError("transport context must preserve every ordered local")
    identities = set()
    for i, (row, source) in enumerate(zip(locals_, original["localContext"], strict=True)):
        _transport_local(row, source, i, identities)
    _expression(value["application"])
    _expression(value["applicationType"])
    _arguments(value["arguments"])
    if [a["isProp"] for a in value["arguments"]] != [a["isProp"] for a in original["arguments"]]:
        raise ValueError("transport lost an application premise")


def _transport_local(row, source, index, identities):
    closed(row, LOCAL_KEYS | {"originalLocalId"}, "transported local")
    prefix = f"ladonFormal{index}"
    if (row["originalLocalId"] != source["localId"]
            or not row["name"].startswith(prefix)
            or set(row["name"][len(prefix):]) - {"_"}
            or row["localId"] in identities or row["isProp"] != source["isProp"]
            or row["binderInfo"] != source["binderInfo"]):
        raise ValueError("identity transport local mapping changed")
    identities.add(row["localId"])
    _locals([{k: v for k, v in row.items() if k != "originalLocalId"}])
