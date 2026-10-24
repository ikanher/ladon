"""Canonical identities, closed references and propagation result helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from ladon._proofir_derivation_core import _Graph, _key
from ladon.proof_contract_rules import PROFILE_DIGEST


def _canonical(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


class _UniqueRows(list):
    """Keep repeated residual/pending rows bounded by their exact identities."""

    def __init__(self):
        super().__init__()
        self._seen: set[bytes] = set()

    def append(self, value):
        identity = _canonical(value)
        if identity not in self._seen:
            self._seen.add(identity)
            super().append(value)


def _plain(value: Any) -> Any:
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _external(artifact: dict[str, Any]) -> dict[str, str]:
    payload = artifact["payload"]
    return {
        "artifactRef": artifact["artifactId"],
        "kind": "contract",
        "localId": payload["contractId"],
    }


def _object(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must contain exactly {sorted(keys)}")


def _identifier(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 512
        or len(value.encode()) > 512
    ):
        raise ValueError(f"{label} must be a bounded nonempty string")


def _local_ref(
    value: Any, subjects: frozenset[tuple[str, str]], kinds: set[str], label: str
) -> None:
    _object(value, {"kind", "localId"}, label)
    _identifier(value["kind"], label + ".kind")
    _identifier(value["localId"], label + ".localId")
    if value["kind"] not in kinds or _key(value) not in subjects:
        raise ValueError(f"{label} is not an owned reference of an admitted kind")


def _ref_list(
    value: Any,
    subjects: frozenset[tuple[str, str]],
    kinds: set[str],
    label: str,
    *,
    nonempty: bool = False,
) -> None:
    if not isinstance(value, list) or len(value) > 4096 or (nonempty and not value):
        raise ValueError(
            f"{label} must be a bounded list" + (" with at least one entry" if nonempty else "")
        )
    seen = set()
    for index, row in enumerate(value):
        _local_ref(row, subjects, kinds, f"{label}[{index}]")
        key = _key(row)
        if key in seen:
            raise ValueError(f"{label} must not contain duplicate references")
        seen.add(key)


def _deadline(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("deadlineUtc must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("deadlineUtc must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("deadlineUtc must include a timezone")
    return parsed.astimezone(UTC)


def _deadline_reached(deadline: datetime | None) -> bool:
    return deadline is not None and datetime.now(UTC) >= deadline


def _input_context(
    graph: _Graph,
    contracts: dict,
    bindings: dict,
    interfaces: dict,
    scopes: dict,
    caps: dict,
    deadline: datetime | None,
) -> dict[str, Any]:
    wrapper_material = {
        "bindings": sorted(bindings.values(), key=lambda row: _key(row["stepRef"])),
        "interfaces": sorted(interfaces.values(), key=lambda row: row["interfaceId"]),
        "scopes": sorted((row for values in scopes.values() for row in values), key=_canonical),
    }
    bounds_value = dict(caps)
    if deadline is not None:
        bounds_value["deadlineUtc"] = deadline.isoformat().replace("+00:00", "Z")
    return {
        "profileDigest": PROFILE_DIGEST,
        "derivationArtifactId": graph.artifact_id,
        "contractArtifactIds": sorted(artifact_id for artifact_id, _ in contracts),
        "wrapperDigest": "sha256:" + hashlib.sha256(_canonical(wrapper_material)).hexdigest(),
        "bounds": bounds_value,
    }


def _partial_result(
    goal_ref: dict[str, str], code: str, count: int, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    residual = {"code": code, "observed": count}
    result = {
        "schema": "ladon-contract-propagation-v1",
        "status": "partial",
        "complete": False,
        "goalRef": _plain(goal_ref),
        "frontiers": [],
        "prunings": [],
        "residuals": [residual],
        "coverage": {
            "counts": {"references": count, "steps": 0, "combinations": 0},
            "pending": [residual],
        },
        "witnesses": [],
        "authority": "conditional-profile",
        "profileDigest": PROFILE_DIGEST,
        "analysisInputDigest": "sha256:"
        + hashlib.sha256(_canonical(context or {"profileDigest": PROFILE_DIGEST})).hexdigest(),
        "mathematicalFalsity": "not-established",
        "limitations": ["source-contract-binding-unchecked"],
    }
    result["analysisId"] = "sha256:" + hashlib.sha256(_canonical(result)).hexdigest()
    return result
