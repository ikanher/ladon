"""Bounded canonical JSON history transport for ProofIR-native envelopes."""

from __future__ import annotations

import hashlib
import json
import math
import re

from ladon.proofir_v3 import (
    MAX_ARTIFACT_BYTES,
    SAFE_INTEGER_MAX,
    SAFE_INTEGER_MIN,
    canonical_bytes,
)
from ladon.proof_contract_worker import _ensure_json_depth, _unique_json_object

SCHEMA = 'ladon-prose-history-chunks-v1'
CHUNK_BYTES = 65_536
MAX_HISTORY_BYTES = 8 * 1024 * 1024
MAX_CHUNKS = 128
MAX_JSON_DEPTH = 272
_DIGEST = re.compile(r'^sha256:[0-9a-f]{64}$')
_KEYS = {'schema', 'digest', 'byteLength', 'chunks'}


def encode_history(value: dict) -> dict:
    """Encode a JSON object as a closed, size-bounded ASCII chunk envelope."""
    if not isinstance(value, dict):
        raise TypeError('history root must be an object')
    _validate_json_value(value)
    try:
        raw = json.dumps(
            value, ensure_ascii=True, sort_keys=True,
            separators=(',', ':'), allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError('history is not canonical JSON data') from exc
    encoded_raw = raw.encode('ascii')
    if not encoded_raw or len(encoded_raw) > MAX_HISTORY_BYTES:
        raise ValueError('history exceeds its byte bound')
    chunks = [
        encoded_raw[offset:offset + CHUNK_BYTES].decode('ascii')
        for offset in range(0, len(encoded_raw), CHUNK_BYTES)
    ]
    if len(chunks) > MAX_CHUNKS:
        raise ValueError('history exceeds its chunk bound')
    result = {
        'schema': SCHEMA,
        'digest': 'sha256:' + hashlib.sha256(encoded_raw).hexdigest(),
        'byteLength': len(encoded_raw),
        'chunks': chunks,
    }
    # The enclosing native artifact escapes chunk strings; check its real size.
    canonical_bytes(result, max_bytes=MAX_ARTIFACT_BYTES)
    return result


def decode_history(encoded: dict) -> dict:
    """Validate the exact transport shape and reconstruct its canonical object."""
    if not isinstance(encoded, dict) or set(encoded) != _KEYS:
        raise ValueError('history transport has an invalid shape')
    if encoded['schema'] != SCHEMA:
        raise ValueError('unsupported history transport schema')
    digest = encoded['digest']
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise ValueError('invalid history digest')
    byte_length = encoded['byteLength']
    if type(byte_length) is not int or not 0 < byte_length <= MAX_HISTORY_BYTES:
        raise ValueError('invalid history byte length')
    chunks = encoded['chunks']
    if not isinstance(chunks, list) or not 0 < len(chunks) <= MAX_CHUNKS:
        raise ValueError('invalid history chunk list')
    if not all(isinstance(chunk, str) for chunk in chunks):
        raise ValueError('history chunks must be strings')
    if any(not chunk or len(chunk) > CHUNK_BYTES or not chunk.isascii() for chunk in chunks):
        raise ValueError('history chunk violates its size or encoding bound')
    if any(len(chunk) != CHUNK_BYTES for chunk in chunks[:-1]):
        raise ValueError('nonfinal history chunks must have the fixed size')
    actual_length = sum(map(len, chunks))
    if actual_length != byte_length:
        raise ValueError('history chunk length mismatch')
    raw = ''.join(chunks)
    raw_bytes = raw.encode('ascii')
    if 'sha256:' + hashlib.sha256(raw_bytes).hexdigest() != digest:
        raise ValueError('history digest mismatch')
    try:
        _ensure_json_depth(raw, MAX_JSON_DEPTH)
        value = json.loads(
            raw,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, TypeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError('history is not valid unambiguous JSON') from exc
    if not isinstance(value, dict):
        raise ValueError('history root must be an object')
    _validate_json_value(value)
    if _canonical_text(value) != raw:
        raise ValueError('history is not canonically serialized')
    # Also reject transport objects too large for one current native artifact.
    canonical_bytes(encoded, max_bytes=MAX_ARTIFACT_BYTES)
    return value


def _canonical_text(value: dict) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True,
            separators=(',', ':'), allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError('history is not canonical JSON data') from exc


def _reject_constant(value: str):
    raise ValueError(f'nonfinite JSON number {value!r} is forbidden')


def _validate_json_value(root: dict) -> None:
    """Iteratively constrain values before recursive stdlib JSON encoding."""
    stack = [(root, 0, False)]
    active = set()
    while stack:
        value, depth, exiting = stack.pop()
        if exiting:
            active.remove(id(value))
            continue
        if depth > MAX_JSON_DEPTH:
            raise ValueError('history exceeds its JSON depth bound')
        if isinstance(value, dict):
            identity = id(value)
            if identity in active:
                raise ValueError('history contains a cycle')
            active.add(identity)
            stack.append((value, depth, True))
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError('history object keys must be strings')
                stack.append((child, depth + 1, False))
        elif isinstance(value, list):
            identity = id(value)
            if identity in active:
                raise ValueError('history contains a cycle')
            active.add(identity)
            stack.append((value, depth, True))
            stack.extend((child, depth + 1, False) for child in value)
        elif value is None or isinstance(value, (str, bool)):
            continue
        elif type(value) is int:
            if not SAFE_INTEGER_MIN <= value <= SAFE_INTEGER_MAX:
                raise ValueError('history integer exceeds the canonical safe range')
        elif type(value) is float:
            if not math.isfinite(value):
                raise ValueError('history contains a nonfinite number')
        else:
            raise ValueError('history contains a non-JSON value')
