"""Explicit semantic adapter registry with deterministic policy validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AdapterRule:
    rule_id: str
    source: str
    authority: str
    direction: str
    declaration: str
    input_shape: str
    output_shape: str
    side_conditions: tuple[str, ...] = ()
    cost: int = 1
    precedence: int = 0

    def __post_init__(self) -> None:
        if not self.rule_id or self.authority not in {"registered", "verified"} or self.direction not in {"forward", "reverse"}:
            raise ValueError("invalid adapter rule identity or enum")
        if self.cost < 0 or self.precedence < 0 or any("{" in item or "}" in item for item in self.side_conditions):
            raise ValueError("invalid adapter cost, precedence, or unbounded side condition")


BUILTIN_RULES = (
    AdapterRule("eq-symmetry", "Eq", "registered", "reverse", "Eq.symm", "Eq", "Eq", precedence=10),
    AdapterRule("iff-symmetry", "Iff", "registered", "reverse", "Iff.symm", "Iff", "Iff", precedence=20),
    AdapterRule("coercion-projection", "coercion", "registered", "forward", "Coe.coe", "coercion", "value", precedence=30),
)


def validate_registry(rules: Iterable[AdapterRule]) -> tuple[AdapterRule, ...]:
    ordered = tuple(rules)
    seen: set[str] = set()
    for rule in ordered:
        if rule.rule_id in seen:
            raise ValueError(f"duplicate adapter rule {rule.rule_id}")
        seen.add(rule.rule_id)
    precedence: dict[int, str] = {}
    for rule in ordered:
        if rule.precedence in precedence and precedence[rule.precedence] != rule.rule_id:
            raise ValueError("equal-precedence adapter conflict")
        precedence[rule.precedence] = rule.rule_id
    return tuple(sorted(ordered, key=lambda rule: (rule.precedence, rule.cost, rule.rule_id)))


def registry_fingerprint(rules: Iterable[AdapterRule]) -> str:
    payload = [rule.__dict__ for rule in validate_registry(rules)]
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def resolve_adapters(rules: Iterable[AdapterRule], *, source_shape: str, target_shape: str, direction: str = "forward") -> list[dict[str, Any]]:
    selected = [rule for rule in validate_registry(rules) if rule.direction == direction and rule.input_shape == source_shape and rule.output_shape == target_shape]
    return [{"ruleId": rule.rule_id, "declaration": rule.declaration, "authority": rule.authority, "cost": rule.cost, "sideConditions": list(rule.side_conditions), "verification": "not_requested"} for rule in selected]


__all__ = ["AdapterRule", "BUILTIN_RULES", "validate_registry", "registry_fingerprint", "resolve_adapters"]
