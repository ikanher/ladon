"""Immutable prose contract snapshots made independently of a formal match."""

import hashlib
import json
import math
from copy import deepcopy

from ladon.correspondence_interpretation import validate_interpretation
from ladon.proof_contract_artifacts import source_contract_artifact
from ladon.proof_contract_payloads import closed, identifier, rows
from ladon.proof_contracts import validate_contract
from ladon.proofir_correspondence import interpretation_artifacts
from ladon.proofir_v3 import validate_envelope_batch

SCHEMA = "ladon-contract-production-v1"


def _origin_pointer(record, pointer):
    identifier(pointer, "feature origin pointer")
    parts = pointer.split("/")
    if parts[:2] != ["", "formula"] or len(parts) > 64:
        raise ValueError("feature origin pointer must refer to the original formula")
    current = record
    for part in parts[1:]:
        token = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list) and token.isdecimal():
            index = int(token)
            if index >= len(current):
                raise ValueError("feature origin pointer is outside the interpretation")
            current = current[index]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise ValueError("feature origin pointer is outside the interpretation")


def _origins(record, origins):
    closed(origins, {"regularity", "constantDependencies", "witnessDependencies"},
           "feature origins")
    for pointers in origins.values():
        rows(pointers, "feature origin pointers", minimum=1)
        if len(pointers) > 16:
            raise ValueError("feature origin pointer count exceeds 16")
        for pointer in pointers:
            _origin_pointer(record, pointer)
    return deepcopy(origins)


def feature_residuals(record):
    """Retain unsupported fields instead of silently using empty requirements."""
    result = []
    for name, feature in record["features"].items():
        values = feature if isinstance(feature, list) else [feature]
        for index, value in enumerate(values):
            if value["state"] != "known":
                result.append({"code": value["state"] + "-feature",
                               "message": value["reason"], "feature": f"{name}:{index}"})
    return result


def produce_prose_contract(root, interpretation, contract, feature_origins, *,
                           alternative_id, environment_ref, author="caller"):
    """Source validation preserves attribution; it does not certify prose meaning."""
    reading = validate_interpretation(interpretation, root)
    checked = validate_contract(contract)
    identifier(alternative_id, "alternative ID")
    identifier(author, "author label")
    origins = _origins(reading, feature_origins)
    sources = list(interpretation_artifacts(reading, environment_ref, source_root=root))
    map_artifact = sources[0]
    source_refs = [{"artifactRef": map_artifact["artifactId"], "kind": "source-map",
                    "localId": map_artifact["payload"]["sourceMapId"]}]
    remaining = feature_residuals(checked)
    contract_artifact = source_contract_artifact(
        checked, contract_id="contract:" + alternative_id, environment_ref=environment_ref,
        source_map_refs=source_refs, residuals=remaining,
    )
    artifacts = [*sources, contract_artifact]
    validate_envelope_batch(artifacts)
    result = {
        "schema": SCHEMA, "channel": "prose", "status": "authored", "phase": "pre-match",
        "fidelity": "attributed-unreviewed", "author": author,
        "alternativeId": alternative_id, "interpretation": reading, "contract": checked,
        "featureOrigins": origins, "source": deepcopy(reading["source"]),
        "coverage": {"statementFeatures": "partial" if remaining else "authored",
                     "providers": "not-extracted", "proofBody": "not-extracted"},
        "residuals": remaining, "artifacts": artifacts,
    }
    result["snapshotId"] = snapshot_identity(result)
    return result


def snapshot_identity(snapshot):
    value = {k: v for k, v in snapshot.items() if k != "snapshotId"}
    # Process observations include elapsed seconds and tuple commands. They are
    # ordinary JSON snapshots, outside the native artifact scalar profile.
    value = _snapshot_json(value)
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > 32 * 1024**2:
        raise ValueError("contract snapshot exceeds 32 MiB")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _snapshot_json(value, depth=0):
    if depth > 256:
        raise ValueError("contract snapshot exceeds nesting bound")
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("snapshot keys must be strings")
        return {key: _snapshot_json(child, depth + 1) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_snapshot_json(child, depth + 1) for child in value]
    return _snapshot_scalar(value)


def _snapshot_scalar(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("snapshot contains a non-JSON value")


def verify_prose_snapshot(snapshot, root):
    if (snapshot.get("schema") != SCHEMA or snapshot.get("channel") != "prose"
            or snapshot.get("snapshotId") != snapshot_identity(snapshot)):
        raise ValueError("invalid or altered prose contract snapshot")
    expected = produce_prose_contract(
        root, snapshot["interpretation"], snapshot["contract"], snapshot["featureOrigins"],
        alternative_id=snapshot["alternativeId"],
        environment_ref=snapshot["artifacts"][0]["environmentRef"], author=snapshot["author"],
    )
    if expected != snapshot:
        raise ValueError("prose contract snapshot differs from its source-bound reproduction")
    return deepcopy(snapshot)


def observation_from_prose_snapshot(snapshot, root):
    """Prepare the ordinary independent review workflow for one frozen reading."""
    frozen = verify_prose_snapshot(snapshot, root)
    assertion = json.dumps(
        {key: frozen[key] for key in ("interpretation", "contract", "featureOrigins")},
        sort_keys=True, separators=(",", ":"),
    )
    return {
        "schema": "ladon-investigation-observation-v1",
        "id": "fidelity:" + frozen["alternativeId"],
        "source": deepcopy(frozen["source"]), "author": frozen["author"],
        "assertion": assertion,
        "comparison": "Assess whether the interpretation represents the quoted prose.",
        "evidence": "Frozen pre-match source snapshot " + frozen["snapshotId"],
        "formalSources": [],
        "dependencies": "No formal counterpart is asserted by this fidelity review.",
    }
