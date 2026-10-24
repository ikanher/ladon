"""Count aggregate JSON input bytes before copying native envelopes.

Strings are encoded in small chunks. Cycles and excessive depth are rejected;
shared acyclic inputs are charged for every appearance in the JSON value.
"""

import json
from collections.abc import Mapping

MAX_INPUT_BYTES = 8 * 1024**2
MAX_INPUT_DEPTH = 256


class _InputBytes:
    def __init__(self, limit):
        self.limit, self.size, self.active = limit, 0, set()

    def string(self, value):
        self.size += 2
        for start in range(0, len(value), 4096):
            if self.size > self.limit:
                break
            chunk = json.dumps(value[start:start + 4096], ensure_ascii=False)
            self.size += len(chunk.encode()) - 2

    def visit(self, value, depth=0):
        if self.size > self.limit:
            return
        if depth > MAX_INPUT_DEPTH:
            raise ValueError("aggregate input exceeds nesting limit")
        if isinstance(value, str):
            self.string(value)
        elif isinstance(value, (Mapping, list, tuple)):
            self.collection(value, depth)
        elif value is None or type(value) in (bool, int, float):
            self.size += len(json.dumps(value, allow_nan=False).encode())
        else:
            payload = getattr(value, "payload", None)
            if not isinstance(payload, Mapping):
                raise TypeError("aggregate input requires JSON values or native envelopes")
            self.visit(payload, depth + 1)

    def collection(self, value, depth):
        identity = id(value)
        if identity in self.active:
            raise ValueError("aggregate input contains a cycle")
        self.active.add(identity)
        self.size += 2 + max(0, len(value) - 1)
        try:
            self.items(value, depth)
        finally:
            self.active.remove(identity)

    def items(self, value, depth):
        values = value.values() if isinstance(value, Mapping) else value
        if isinstance(value, Mapping):
            self.size += len(value)
            for key in value:
                if not isinstance(key, str):
                    raise TypeError("aggregate JSON input keys must be strings")
                self.string(key)
                if self.size > self.limit:
                    return
        for item in values:
            self.visit(item, depth + 1)
            if self.size > self.limit:
                break


def input_bytes_exceeded(values):
    """Return a bounded observed byte count only when the fixed cap is exceeded."""
    counter = _InputBytes(MAX_INPUT_BYTES)
    counter.visit(values)
    return counter.size if counter.size > MAX_INPUT_BYTES else None
