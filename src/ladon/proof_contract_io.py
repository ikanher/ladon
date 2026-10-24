"""Admit the entire raw native input budget before decoding any JSON object."""

import json

from ladon.investigation import _pairs


def load_bounded_plans(paths, *, max_bytes):
    """Read at most one byte beyond a shared cap, including files that grow."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= 32 * 1024**2:
        raise ValueError("invalid aggregate JSON byte bound")
    if not isinstance(paths, (list, tuple)) or len(paths) > 4098:
        raise ValueError("aggregate JSON file count exceeds limit")
    raw, remaining = [], max_bytes
    for path in paths:
        with path.open("rb") as stream:
            data = stream.read(remaining + 1)
        remaining -= len(data)
        if remaining < 0:
            raise ValueError("aggregate raw JSON input exceeds byte limit")
        raw.append(data)
    return [_decode(data) for data in raw]


def _nonfinite(_value):
    raise ValueError("nonfinite JSON input is unsupported")


def _decode(data):
    try:
        result = json.loads(data, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    except (UnicodeDecodeError, RecursionError) as error:
        raise ValueError("native input must be bounded UTF-8 JSON") from error
    if not isinstance(result, dict):
        raise TypeError("native input must be a JSON object")
    return result
