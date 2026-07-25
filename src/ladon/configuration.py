"""Pre-analysis validation for Ladon-owned policy configuration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from ladon.analysis.population_calibration import (
    PolicyValidationError,
    parse_generated_family_policy,
)


ARCHITECTURE_POLICY_CANDIDATES = (
    ".ladon/architecture-policy.json",
    "ladon.architecture.json",
    "ladon-architecture-policy.json",
)
SOURCE_PATTERN_POLICY_CANDIDATES = (
    ".ladon/source-pattern-policy.json",
    ".ladon/source-patterns.json",
    "ladon.source-patterns.json",
    "ladon-source-pattern-policy.json",
)
GENERATED_FAMILY_POLICY_CANDIDATES = (
    ".ladon/generated-family-policy.json",
    ".ladon/generated-families.json",
    "ladon-generated-family-policy.json",
)
ARCHITECTURE_RULE_KINDS = {
    "forbid_imports",
    "forbid_direct_imports",
    "forbid_transitive_imports",
}


class ConfigurationError(ValueError):
    """A readable Ladon policy violates its invocation-time schema."""


def validate_policy_configuration(
    repo_root: Path,
    *,
    architecture_policy: Path | None,
    source_pattern_policy: Path | None,
    generated_family_policy: Path | None = None,
) -> None:
    """Validate explicit or discovered Ladon-owned policy documents."""

    resolve_policy_configuration(
        repo_root,
        architecture_policy=architecture_policy,
        source_pattern_policy=source_pattern_policy,
        generated_family_policy=generated_family_policy,
    )


def resolve_policy_configuration(
    repo_root: Path,
    *,
    architecture_policy: Path | None = None,
    source_pattern_policy: Path | None = None,
    generated_family_policy: Path | None = None,
    architecture_inline: Mapping[str, Any] | None = None,
    source_pattern_inline: Mapping[str, Any] | None = None,
    generated_family_inline: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve and fingerprint policy inputs without running analysis."""

    return {
        "architecture": resolved_policy_identity(
            repo_root,
            explicit=architecture_policy,
            inline=architecture_inline,
            candidates=ARCHITECTURE_POLICY_CANDIDATES,
            label="architecture policy",
            validator=validate_architecture_policy,
        ),
        "generatedFamily": resolved_policy_identity(
            repo_root,
            explicit=generated_family_policy,
            inline=generated_family_inline,
            candidates=GENERATED_FAMILY_POLICY_CANDIDATES,
            label="generated-family policy",
            validator=validate_generated_family_policy,
        ),
        "sourcePattern": resolved_policy_identity(
            repo_root,
            explicit=source_pattern_policy,
            inline=source_pattern_inline,
            candidates=SOURCE_PATTERN_POLICY_CANDIDATES,
            label="source-pattern policy",
            validator=validate_source_pattern_policy,
        ),
    }


def policy_fingerprint_options(
    policies: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Return stable policy identities suitable for source-index validity."""

    return {
        "policies": {
            name: {
                "status": row.get("status"),
                "sha256": row.get("sha256"),
            }
            for name, row in sorted(policies.items())
        }
    }


def resolved_policy_identity(
    repo_root: Path,
    *,
    explicit: Path | None,
    inline: Mapping[str, Any] | None,
    candidates: tuple[str, ...],
    label: str,
    validator: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    """Return one validated policy identity without embedding policy content."""

    selected = None if inline is not None else selected_policy_path(
        repo_root,
        explicit,
        candidates,
    )
    source = (
        "inline"
        if inline is not None
        else "explicit"
        if explicit is not None
        else "discovered"
        if selected is not None
        else "none"
    )
    if inline is None and selected is None:
        return {
            "status": "absent",
            "source": source,
            "path": None,
            "schema": None,
            "sha256": None,
        }
    payload = (
        dict(inline)
        if inline is not None
        else load_policy_object(selected, label)
    )
    try:
        validator(payload)
    except (ConfigurationError, PolicyValidationError) as exc:
        location = f" {selected}" if selected is not None else ""
        raise ConfigurationError(f"{label}{location}: {exc}") from exc
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "status": "selected",
        "source": source,
        "path": policy_display_path(repo_root, selected),
        "schema": payload.get("schema"),
        "sha256": f"sha256:{hashlib.sha256(encoded).hexdigest()}",
    }


def load_policy_object(path: Path | None, label: str) -> dict[str, Any]:
    """Load one selected policy object with an actionable parse error."""

    if path is None:
        raise ConfigurationError(f"{label} path is absent")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"{label} {path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError(f"{label} {path} must be a JSON object")
    return payload


def policy_display_path(repo_root: Path, path: Path | None) -> str | None:
    """Prefer a portable repository-relative spelling for selected policies."""

    if path is None:
        return None
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def validate_generated_family_policy(payload: dict[str, Any]) -> None:
    """Validate one generated-family policy through its owning parser."""

    parse_generated_family_policy(payload)


def selected_policy_path(
    repo_root: Path,
    explicit: Path | None,
    candidates: tuple[str, ...],
) -> Path | None:
    """Return an explicit path or the first repo-local policy candidate."""

    if explicit is not None:
        if not explicit.is_file():
            raise OSError(f"Ladon policy file does not exist: {explicit}")
        return explicit
    return next(
        (
            repo_root / candidate
            for candidate in candidates
            if (repo_root / candidate).is_file()
        ),
        None,
    )


def validate_architecture_policy(payload: dict[str, Any]) -> None:
    """Check the supported architecture-policy container and rule shapes."""

    groups = payload.get("groups")
    rules = payload.get("rules")
    if not isinstance(groups, dict) or not groups:
        raise ConfigurationError("groups must be a non-empty object")
    if not isinstance(rules, list):
        raise ConfigurationError("rules must be an array")
    for index, rule in enumerate(rules):
        validate_architecture_rule(rule, index)


def validate_architecture_rule(rule: Any, index: int) -> None:
    """Validate one architecture rule before normalization could drop it."""

    if not isinstance(rule, dict):
        raise ConfigurationError(f"rules[{index}] must be an object")
    if rule.get("kind") not in ARCHITECTURE_RULE_KINDS:
        raise ConfigurationError(f"rules[{index}].kind is unsupported")
    if not group_selector(rule, "from", "fromGroups"):
        raise ConfigurationError(f"rules[{index}] needs a non-empty from selector")
    if not group_selector(rule, "to", "toGroups"):
        raise ConfigurationError(f"rules[{index}] needs a non-empty to selector")


def group_selector(rule: dict[str, Any], primary: str, alias: str) -> bool:
    """Whether an architecture rule contains a non-empty group selector."""

    value = rule.get(primary, rule.get(alias))
    if isinstance(value, str):
        return bool(value)
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item
        for item in value
    )


def validate_source_pattern_policy(payload: dict[str, Any]) -> None:
    """Check the supported source-pattern policy container and row shapes."""

    patterns = payload.get("patterns")
    if not isinstance(patterns, list):
        raise ConfigurationError("patterns must be an array")
    for index, pattern in enumerate(patterns):
        if not isinstance(pattern, dict):
            raise ConfigurationError(f"patterns[{index}] must be an object")
        if not str(pattern.get("id", "")):
            raise ConfigurationError(f"patterns[{index}].id must be non-empty")
        if not str(pattern.get("pattern", "")):
            raise ConfigurationError(
                f"patterns[{index}].pattern must be non-empty"
            )
