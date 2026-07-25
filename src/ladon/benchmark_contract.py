"""Versioned manifest and promotion policy for portable Ladon benchmarks."""

from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


BENCHMARK_ARTIFACT_KIND = "ladon_signal_benchmark_manifest"
BENCHMARK_SCHEMA_VERSION = 1
FORBIDDEN_CALLER_OPTIONS = frozenset(
    {
        "--agent-only",
        "--benchmark-threshold",
        "--llm",
        "--model-only",
        "--prompt-only",
    }
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"^/(?:home|Users)/"),
    re.compile(r"^[A-Za-z]:[\\/]+Users[\\/]+"),
)
OPTIONAL_LIVE_NAMES = frozenset({"quux", "matrix-factorization", "mathlib"})


class BenchmarkContractError(ValueError):
    """Raised when a benchmark manifest violates the portable contract."""


def load_benchmark_manifest(path: Path) -> dict[str, Any]:
    """Load and validate one benchmark manifest object."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BenchmarkContractError("benchmark manifest must be a JSON object")
    validate_manifest_contract(payload)
    return payload


def load_benchmark_manifest_schema() -> dict[str, Any]:
    """Load the packaged benchmark-manifest schema."""

    text = (
        resources.files("ladon")
        .joinpath("schemas", "ladon-benchmark-manifest-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise BenchmarkContractError("packaged benchmark schema must be an object")
    return payload


def validate_manifest_contract(manifest: Mapping[str, Any]) -> None:
    """Validate portable fields not conveniently expressed in JSON Schema."""

    require_manifest_identity(manifest)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise BenchmarkContractError("benchmark manifest must declare cases")
    identifiers: set[str] = set()
    for case in cases:
        validate_case(case, identifiers)
    validate_optional_live_runs(manifest.get("optionalLiveRuns", []))


def require_manifest_identity(manifest: Mapping[str, Any]) -> None:
    """Require the supported manifest kind and schema version."""

    if manifest.get("artifactKind") != BENCHMARK_ARTIFACT_KIND:
        raise BenchmarkContractError("unsupported benchmark artifactKind")
    if manifest.get("schemaVersion") != BENCHMARK_SCHEMA_VERSION:
        raise BenchmarkContractError("unsupported benchmark schemaVersion")


def validate_case(case: Any, identifiers: set[str]) -> None:
    """Validate one case's identity and ordinary-CLI command."""

    if not isinstance(case, Mapping):
        raise BenchmarkContractError("benchmark cases must be objects")
    identifier = str(case.get("id", ""))
    if not identifier or identifier in identifiers:
        raise BenchmarkContractError(f"missing or duplicate benchmark case id: {identifier!r}")
    identifiers.add(identifier)
    command = case.get("command")
    if not isinstance(command, list) or command[:1] != ["ladon"]:
        raise BenchmarkContractError(f"{identifier}: command must invoke installed ladon")
    validate_command(identifier, command, required=bool(case.get("required")))


def validate_command(
    identifier: str,
    command: Iterable[Any],
    *,
    required: bool,
) -> None:
    """Reject alternate analysis controls and nonportable required paths."""

    tokens = tuple(str(token) for token in command)
    forbidden = sorted(FORBIDDEN_CALLER_OPTIONS.intersection(tokens))
    if forbidden:
        raise BenchmarkContractError(
            f"{identifier}: caller-specific or alternate-threshold option: {forbidden[0]}"
        )
    if required:
        invalid = next((token for token in tokens if nonportable_required_token(token)), None)
        if invalid is not None:
            raise BenchmarkContractError(
                f"{identifier}: nonportable required command token: {invalid}"
            )


def nonportable_required_token(token: str) -> bool:
    """Return whether one required command token depends on local/external state."""

    normalized = token.replace("\\", "/")
    if any(pattern.search(token) for pattern in LOCAL_PATH_PATTERNS):
        return True
    if normalized.startswith("../") or "/../" in normalized:
        return True
    path_parts = {part.lower() for part in PurePosixPath(normalized).parts}
    return bool(path_parts.intersection(OPTIONAL_LIVE_NAMES))


def validate_optional_live_runs(raw: Any) -> None:
    """Require live-repository evidence to be explicit and non-blocking."""

    if not isinstance(raw, list):
        raise BenchmarkContractError("optionalLiveRuns must be a list")
    for row in raw:
        if not isinstance(row, Mapping) or row.get("blocking") is not False:
            raise BenchmarkContractError("optional live runs must be non-blocking")
        if row.get("id") not in OPTIONAL_LIVE_NAMES:
            raise BenchmarkContractError("unsupported optional live-run id")


def promotion_readiness(labels: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return readiness rows for every explicitly named promotion family."""

    grouped: dict[str, set[str]] = {}
    for label in labels:
        family = str(label.get("promotionFamily", ""))
        if family:
            grouped.setdefault(family, set()).add(str(label.get("class", "")))
    required = {"positive", "intentional_negative", "boundary"}
    return [
        {
            "promotionFamily": family,
            "classes": sorted(classes),
            "missingClasses": sorted(required - classes),
            "ready": required <= classes,
        }
        for family, classes in sorted(grouped.items())
    ]
