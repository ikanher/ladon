"""Bounded ownership and inherited deadlines for planned source requirements."""
from __future__ import annotations

import time
from dataclasses import fields, is_dataclass
from pathlib import Path

from .proof_contract_source_obligations import MAX_INPUT_BYTES


def _planned_deadline(outer, plan_request):
    from datetime import UTC, datetime
    bounds = plan_request.bounds or {}
    if not isinstance(bounds, dict):
        raise TypeError("planRequest.bounds must be a mapping")
    value = bounds.get("deadlineUtc")
    if value is None:
        return float(outer)
    if not isinstance(value, str):
        raise TypeError("planner deadlineUtc must be a string")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return min(float(outer), time.monotonic() + (parsed.astimezone(UTC)-datetime.now(UTC)).total_seconds())


def _planned_input_size(value):
    from ladon._contract_propagation_input_budget import _InputBytes
    class _Counter(_InputBytes):
        def visit(self, item, depth=0):
            if depth > 128:
                raise ValueError("planned source request exceeds 128 levels of nesting")
            if is_dataclass(item) and not isinstance(item, type):
                item = {field.name: getattr(item, field.name) for field in fields(item)}
            elif isinstance(item, Path):
                item = str(item)
            super().visit(item, depth)
    counter = _Counter(MAX_INPUT_BYTES)
    counter.visit(value)
    return counter.size


