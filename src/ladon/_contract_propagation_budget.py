"""Conservative incremental accounting for every retained output collection.

Counting streams JSON chunks; it never constructs the encoded result to learn
whether it fits. Route reservations include both wire appearances of a witness.
"""

import hashlib
import json

_ENCODER = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def encoded_size(value, limit):
    size = 0
    for chunk in _ENCODER.iterencode(value):
        size += len(chunk.encode())
        if size > limit:
            return size
    return size


def fingerprint(value):
    digest = hashlib.sha256()
    for chunk in _ENCODER.iterencode(value):
        digest.update(chunk.encode())
    return digest.digest()


class OutputBudget:
    """Reserve an upper bound before retaining any new output-bearing object."""

    def __init__(self, limit):
        self.limit, self.used, self.exhausted = limit, 0, False

    def admits(self, value):
        """Reject an oversized candidate before a transfer copies its record."""
        if encoded_size(value, self.limit - self.used) > self.limit - self.used:
            self.exhausted = True
        return not self.exhausted

    def reserve(self, value, *, copies=1, overhead=1):
        if self.exhausted:
            return False
        remaining = self.limit - self.used
        size = copies * encoded_size(value, remaining) + overhead
        if size > remaining:
            self.exhausted = True
            return False
        self.used += size
        return True


class BudgetRows(list):
    """Deduplicate diagnostics and prune receipts within the shared byte budget."""

    def __init__(self, budget):
        super().__init__()
        self.budget, self.seen = budget, set()

    def append(self, value):
        if self.budget.exhausted:
            return
        identity = fingerprint(value)
        if identity in self.seen:
            return
        if self.budget.reserve(value, copies=2):
            self.seen.add(identity)
            super().append(value)

    def extend(self, values):
        for value in values:
            self.append(value)
            if self.budget.exhausted:
                break
