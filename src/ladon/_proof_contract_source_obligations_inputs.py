"""Bounded ownership preflight without expanding shared data or large strings."""

from dataclasses import fields
from pathlib import Path

from ladon._contract_propagation_input_budget import _InputBytes
from ladon.proof_contract_obligations import BackwardTransformRequest


class _SourceInputBytes(_InputBytes):
    def visit(self, value, depth=0):
        if depth > 128:
            raise ValueError("source-bound request nesting exceeds 128 levels")
        if isinstance(value, BackwardTransformRequest):
            value = {field.name: getattr(value, field.name) for field in fields(value)}
        elif isinstance(value, Path):
            value = str(value)
        super().visit(value, depth)


def bounded_json_size(value, maximum):
    counter = _SourceInputBytes(maximum)
    counter.visit(value)
    return counter.size
