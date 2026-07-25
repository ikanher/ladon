"""Validation primitives shared by runset models and manifest parsing."""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


ENTRY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SUPPORTED_BACKENDS = frozenset({"text", "lean"})
SUPPORTED_PROJECTIONS = frozenset({"summary", "review", "full"})
SUPPORTED_SCOPE_KINDS = frozenset(
    {"owner", "closure", "namespace", "multi-root", "changed-set", "inventory"}
)
SCOPE_KEYS = frozenset(
    {
        "kind",
        "roots",
        "changedPaths",
        "changedManifest",
        "maxModules",
        "maxContextModules",
        "leanBatchSize",
        "resolvedPaths",
    }
)
PATH_OPTION_KEYS = frozenset(
    {
        "architecturePolicy",
        "sourcePatternPolicy",
        "moduleSystemWitness",
        "importDietWitness",
        "proofXray",
        "generatedFamilyPolicy",
        "leanCacheDir",
    }
)
PATH_LIST_OPTION_KEYS = frozenset({"docFiles", "packetDirs"})
OPTION_KEYS = frozenset(
    {
        "build",
        "buildTimeout",
        "leanExtractionScope",
        "leanCacheDir",
        "leanBatchSize",
        "leanTimeout",
        "failOn",
        "docFiles",
        "packetDirs",
        "architecturePolicy",
        "sourcePatternPolicy",
        "moduleSystemWitness",
        "importDietWitness",
        "proofXray",
        "generatedFamilyPolicy",
        "packetProfile",
    }
)
RUNSET_KEYS = frozenset(
    {
        "artifactKind",
        "schemaVersion",
        "name",
        "repository",
        "policy",
        "resources",
        "metadata",
        "entries",
    }
)
ENTRY_KEYS = frozenset(
    {
        "id",
        "root",
        "scope",
        "backend",
        "projection",
        "output",
        "required",
        "reportVersion",
        "options",
        "dependsOn",
    }
)
POLICY_KEYS = frozenset(
    {
        "concurrency",
        "stopOnRequiredFailure",
        "continueOnAdvisoryFailure",
    }
)
RESOURCE_KEYS = frozenset(
    {"overallTimeoutSeconds", "maxRssMiB", "maxReportBytes"}
)


class RunsetManifestError(ValueError):
    """Raised when a complete runset cannot pass invocation preflight."""


def require_sha256(value: str, label: str) -> None:
    """Require a complete, labeled lowercase SHA-256 digest."""

    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a complete sha256 digest")


def require_portable_relative_path(value: str, label: str) -> None:
    """Reject absolute, escaping, platform-specific, and sibling paths."""

    if not value or "\\" in value or "\x00" in value:
        raise RunsetManifestError(f"{label} must be a portable relative path")
    path = PurePosixPath(value)
    parts = path.parts
    if (
        path.is_absolute()
        or value.startswith("~")
        or re.match(r"^[A-Za-z]:", value)
        or any(part in {"", ".."} for part in parts)
    ):
        raise RunsetManifestError(f"{label} must not escape its portable root")


def validate_scope(identifier: str, scope: Mapping[str, Any]) -> None:
    """Validate generic scope structure and every scope-owned path."""

    row = copy_json_mapping(scope, f"entry {identifier} scope")
    require_allowed_keys(row, SCOPE_KEYS, f"entry {identifier} scope")
    kind = row.get("kind")
    if kind not in SUPPORTED_SCOPE_KINDS:
        raise RunsetManifestError(
            f"entry {identifier} has unsupported scope.kind {kind!r}"
        )
    _validate_scope_lists(identifier, row)
    _validate_scope_limits(identifier, row)
    changed_manifest = row.get("changedManifest")
    if changed_manifest is not None:
        if not isinstance(changed_manifest, str):
            raise RunsetManifestError(
                f"entry {identifier} changedManifest must be a path"
            )
        require_portable_relative_path(
            changed_manifest,
            f"entry {identifier} changedManifest",
        )


def _validate_scope_lists(identifier: str, scope: Mapping[str, Any]) -> None:
    for key in ("roots", "changedPaths", "resolvedPaths"):
        if key not in scope:
            continue
        values = string_tuple(scope[key], f"entry {identifier} scope.{key}")
        if len(set(values)) != len(values):
            raise RunsetManifestError(
                f"entry {identifier} scope.{key} contains duplicates"
            )
        if key in {"changedPaths", "resolvedPaths"}:
            for value in values:
                require_portable_relative_path(
                    value,
                    f"entry {identifier} scope.{key} path",
                )


def _validate_scope_limits(
    identifier: str,
    scope: Mapping[str, Any],
) -> None:
    for key in ("maxModules", "maxContextModules"):
        if key not in scope:
            continue
        value = required_integer(scope[key], f"entry {identifier} scope.{key}")
        if value <= 0:
            raise RunsetManifestError(
                f"entry {identifier} scope.{key} must be positive"
            )
    if "leanBatchSize" in scope:
        value = required_integer(
            scope["leanBatchSize"],
            f"entry {identifier} scope.leanBatchSize",
        )
        if value < 2:
            raise RunsetManifestError(
                f"entry {identifier} scope.leanBatchSize must be at least 2"
            )


def validate_portable_options(
    identifier: str,
    options: Mapping[str, Any],
) -> None:
    """Require only documented ordinary CLI options and portable paths."""

    require_allowed_keys(
        options,
        OPTION_KEYS,
        f"entry {identifier} options",
    )
    _validate_scalar_options(identifier, options)
    _validate_path_options(identifier, options)
    _validate_path_list_options(identifier, options)


def _validate_path_options(
    identifier: str,
    options: Mapping[str, Any],
) -> None:
    for key in PATH_OPTION_KEYS:
        value = options.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise RunsetManifestError(
                f"entry {identifier} option {key} must be a path"
            )
        require_portable_relative_path(
            value,
            f"entry {identifier} option {key}",
        )


def _validate_path_list_options(
    identifier: str,
    options: Mapping[str, Any],
) -> None:
    for key in PATH_LIST_OPTION_KEYS:
        if key not in options:
            continue
        values = string_tuple(
            options[key],
            f"entry {identifier} option {key}",
        )
        for value in values:
            require_portable_relative_path(
                value,
                f"entry {identifier} option {key}",
            )


def _validate_scalar_options(
    identifier: str,
    options: Mapping[str, Any],
) -> None:
    prefix = f"entry {identifier} option"
    if "build" in options:
        required_boolean(options["build"], f"{prefix} build")
    for key in ("buildTimeout", "leanTimeout"):
        if key in options:
            value = optional_number(options[key], f"{prefix} {key}")
            positive_optional_number(value, f"{prefix} {key}")
    _validate_lean_batch_size(options, prefix)
    _validate_enum_option(
        options,
        "leanExtractionScope",
        {"root", "inventory"},
        prefix,
    )
    _validate_enum_option(
        options,
        "packetProfile",
        {"generic", "review_packet", "witness_bundle", "release_bundle"},
        prefix,
    )
    if "failOn" in options:
        string_tuple(options["failOn"], f"{prefix} failOn")


def _validate_lean_batch_size(
    options: Mapping[str, Any],
    prefix: str,
) -> None:
    if "leanBatchSize" not in options:
        return
    value = required_integer(
        options["leanBatchSize"],
        f"{prefix} leanBatchSize",
    )
    if value < 2:
        raise RunsetManifestError(
            f"{prefix} leanBatchSize must be at least 2"
        )


def _validate_enum_option(
    options: Mapping[str, Any],
    key: str,
    allowed: set[str],
    prefix: str,
) -> None:
    if key in options and options[key] not in allowed:
        raise RunsetManifestError(
            f"{prefix} {key} must be one of {sorted(allowed)}"
        )


def validate_entry_collection(entries: Sequence[Any]) -> None:
    """Require unique identities/outputs and a complete acyclic dependency DAG."""

    identifiers = [entry.identifier for entry in entries]
    if len(set(identifiers)) != len(identifiers):
        raise RunsetManifestError("runset entry ids must be unique")
    outputs = [entry.output for entry in entries]
    if len(set(outputs)) != len(outputs):
        raise RunsetManifestError("runset entry outputs must be unique")
    _validate_dependencies(entries, set(identifiers))
    require_acyclic(entries)


def _validate_dependencies(entries: Sequence[Any], known: set[str]) -> None:
    for entry in entries:
        unknown = set(entry.depends_on) - known
        if unknown:
            raise RunsetManifestError(
                f"entry {entry.identifier} has unknown dependencies "
                f"{sorted(unknown)}"
            )
        if entry.identifier in entry.depends_on:
            raise RunsetManifestError(
                f"entry {entry.identifier} cannot depend on itself"
            )


def require_acyclic(entries: Sequence[Any]) -> None:
    """Reject cycles while allowing stable forward dependency references."""

    dependencies = {entry.identifier: entry.depends_on for entry in entries}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise RunsetManifestError("runset entry dependencies contain a cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in dependencies[identifier]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in dependencies:
        visit(identifier)


def copy_json_mapping(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    """Copy one mapping through JSON and reject nonportable value types."""

    if not isinstance(value, Mapping):
        raise RunsetManifestError(f"{label} must be a JSON object")
    try:
        copied = json.loads(json.dumps(value, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise RunsetManifestError(f"{label} is not JSON-compatible: {exc}") from exc
    if not isinstance(copied, dict):
        raise RunsetManifestError(f"{label} must be a JSON object")
    return copied


def optional_mapping(value: Any, label: str) -> dict[str, Any]:
    """Require and detach a JSON object."""

    if not isinstance(value, Mapping):
        raise RunsetManifestError(f"{label} must be a JSON object")
    return copy_json_mapping(value, label)


def require_keys(
    row: Mapping[str, Any],
    required: set[str],
    label: str,
) -> None:
    """Require every named manifest key."""

    missing = required - set(row)
    if missing:
        raise RunsetManifestError(f"{label} is missing keys {sorted(missing)}")


def require_allowed_keys(
    row: Mapping[str, Any],
    allowed: frozenset[str],
    label: str,
) -> None:
    """Reject unknown fields rather than silently changing fingerprints."""

    unknown = set(row) - allowed
    if unknown:
        raise RunsetManifestError(f"{label} has unknown keys {sorted(unknown)}")


def required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RunsetManifestError(f"{label} must be a non-empty string")
    return value


def required_boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise RunsetManifestError(f"{label} must be a boolean")
    return value


def required_integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RunsetManifestError(f"{label} must be an integer")
    return value


def optional_integer(value: Any, label: str) -> int | None:
    if value is None:
        return None
    return required_integer(value, label)


def optional_number(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RunsetManifestError(f"{label} must be a number")
    return float(value)


def positive_optional_integer(value: int | None, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RunsetManifestError(f"{label} must be a positive integer")


def positive_optional_number(value: float | None, label: str) -> None:
    if value is None:
        return
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value <= 0
    ):
        raise RunsetManifestError(f"{label} must be a positive number")


def string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise RunsetManifestError(f"{label} must be an array of non-empty strings")
    return tuple(value)


def require_optional_sha256(value: str | None, label: str) -> None:
    if value is not None:
        require_sha256(value, label)


def nonnegative_integer_mapping(
    values: Mapping[str, int],
    label: str,
) -> None:
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in values.values()
    ):
        raise ValueError(f"{label} values must be non-negative integers")


def validate_diagnostics(rows: Sequence[Mapping[str, Any]]) -> None:
    """Require schema-valid structured diagnostics at the bundle boundary."""

    for row in rows:
        copied = copy_json_mapping(row, "bundle diagnostic")
        if not isinstance(copied.get("id"), str) or not copied["id"]:
            raise ValueError("bundle diagnostic id must be non-empty")
        if copied.get("severity") not in {"info", "warning", "error"}:
            raise ValueError("bundle diagnostic severity is unsupported")
        if not isinstance(copied.get("message"), str):
            raise ValueError("bundle diagnostic message must be text")
