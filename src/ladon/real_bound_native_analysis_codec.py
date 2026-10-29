"""Lossless process-receipt transport inside the integer-only native profile."""

import math

from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_ARTIFACT_BYTES, canonical_bytes

_TAG = "$realBoundFloat"


def _map(value, *, decode=False):
    if isinstance(value, float):
        if decode or not math.isfinite(value):
            raise ValueError("Real replay requires finite encoded receipt scalars")
        return {_TAG: value.hex()}
    if isinstance(value, dict):
        if _TAG in value:
            return _decode_float(value, decode)
        return {key: _map(item, decode=decode) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_map(item, decode=decode) for item in value]
    return value


def _decode_float(value, decode):
    if not decode or set(value) != {_TAG} or not isinstance(value[_TAG], str):
        raise ValueError("invalid Real receipt scalar encoding")
    try:
        number = float.fromhex(value[_TAG])
    except (ValueError, OverflowError) as error:
        raise ValueError("invalid Real receipt scalar value") from error
    if not math.isfinite(number) or number.hex() != value[_TAG]:
        raise ValueError("noncanonical Real receipt scalar encoding")
    return number


def encode_replay(productions, run):
    replay = _map({"productions": productions, "relationRun": run})
    for production in replay["productions"]:
        production["snapshotId"] = snapshot_identity(production)
    canonical_bytes(replay, max_bytes=MAX_ARTIFACT_BYTES)
    return replay


def decode_replay(replay):
    canonical_bytes(replay, max_bytes=MAX_ARTIFACT_BYTES)
    if not isinstance(replay, dict) or set(replay) != {"productions", "relationRun"}:
        raise ValueError("invalid Real comparison replay object")
    productions = replay["productions"]
    if not isinstance(productions, list) or len(productions) != 2:
        raise ValueError("Real comparison requires two ordered replay productions")
    for production in productions:
        if (not isinstance(production, dict) or production.get("authority") != "none"
                or production.get("snapshotId") != snapshot_identity(production)):
            raise ValueError("invalid historical Real production identity or authority")
    decoded = _map(replay, decode=True)
    for production in decoded["productions"]:
        production["snapshotId"] = snapshot_identity(production)
    return decoded["productions"], decoded["relationRun"]
