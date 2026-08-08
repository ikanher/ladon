from __future__ import annotations

import pytest

from ladon.semantic_adapter_registry import AdapterRule, BUILTIN_RULES, registry_fingerprint, resolve_adapters, validate_registry


def test_builtin_registry_is_valid_and_fingerprint_stable() -> None:
    assert validate_registry(BUILTIN_RULES) == validate_registry(BUILTIN_RULES)
    assert registry_fingerprint(BUILTIN_RULES) == registry_fingerprint(BUILTIN_RULES)
    assert resolve_adapters(BUILTIN_RULES, source_shape="Eq", target_shape="Eq", direction="reverse")[0]["authority"] == "registered"


def test_registry_rejects_duplicates_and_precedence_conflicts() -> None:
    rule = AdapterRule("r", "x", "registered", "forward", "x.rule", "a", "b", precedence=1)
    with pytest.raises(ValueError):
        validate_registry((rule, rule))
    with pytest.raises(ValueError):
        validate_registry((rule, AdapterRule("s", "y", "registered", "forward", "y.rule", "a", "b", precedence=1)))
