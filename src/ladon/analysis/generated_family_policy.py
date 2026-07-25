"""Validation and canonicalization for project-generated family policy."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


LEGACY_GENERATED_FAMILY_POLICY_SCHEMA = "ladon-generated-family-policy-v1"
GENERATED_FAMILY_POLICY_SCHEMA = "ladon-generated-family-policy-v2"
SUPPORTED_GENERATED_FAMILY_POLICY_SCHEMAS = (
    LEGACY_GENERATED_FAMILY_POLICY_SCHEMA,
    GENERATED_FAMILY_POLICY_SCHEMA,
)
GENERATED_FAMILY_REVIEW_METRICS = (
    "memberCount",
    "sourceSizeBytes",
    "declarationCount",
    "importRelationshipCount",
)
_FAMILY_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class PolicyValidationError(ValueError):
    """A generated-family policy is not safe to apply."""


@dataclass(frozen=True)
class FamilyProvenance:
    """Optional policy-quoted generator, manifest, and source metadata."""

    generator_name: str | None = None
    generator_version: str | None = None
    manifest_identity: str | None = None
    manifest_path: str | None = None
    source_path: str | None = None
    source_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the normalized policy provenance shape."""

        return {
            "generator": {
                "name": self.generator_name,
                "version": self.generator_version,
            },
            "manifest": {
                "identity": self.manifest_identity,
                "path": self.manifest_path,
            },
            "source": {
                "path": self.source_path,
                "line": self.source_line,
            },
        }


@dataclass(frozen=True)
class FamilyReviewThreshold:
    """One policy-selected aggregate metric and inclusive review boundary."""

    metric: str
    at_least: int

    def to_dict(self) -> dict[str, Any]:
        """Return the portable threshold shape quoted by reports."""

        return {"metric": self.metric, "atLeast": self.at_least}


@dataclass(frozen=True)
class GeneratedFamilyRule:
    """One stable project-generated family policy row."""

    identifier: str
    path_patterns: tuple[str, ...]
    module_patterns: tuple[str, ...]
    provenance: FamilyProvenance
    review_threshold: FamilyReviewThreshold | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the normalized versioned policy row."""

        row = {
            "id": self.identifier,
            "pathPatterns": list(self.path_patterns),
            "modulePatterns": list(self.module_patterns),
            "provenance": self.provenance.to_dict(),
        }
        if self.review_threshold is not None:
            row["reviewThreshold"] = self.review_threshold.to_dict()
        return row


@dataclass(frozen=True)
class GeneratedFamilyPolicy:
    """A validated, normalized generated-family policy."""

    schema: str
    families: tuple[GeneratedFamilyRule, ...]
    digest: str

    def to_dict(self) -> dict[str, Any]:
        """Return policy content with its canonical digest."""

        return {
            "schema": self.schema,
            "policyDigest": self.digest,
            "families": [family.to_dict() for family in self.families],
        }


def parse_generated_family_policy(
    payload: Mapping[str, Any],
) -> GeneratedFamilyPolicy:
    """Validate and normalize a versioned repository-neutral policy."""

    _reject_unknown_keys(payload, {"schema", "families"}, "policy")
    schema = payload.get("schema")
    if schema not in SUPPORTED_GENERATED_FAMILY_POLICY_SCHEMAS:
        raise PolicyValidationError(
            f"unsupported generated-family policy schema {schema!r}; "
            f"expected one of {SUPPORTED_GENERATED_FAMILY_POLICY_SCHEMAS!r}"
        )
    family_payloads = payload.get("families")
    if not isinstance(family_payloads, list):
        raise PolicyValidationError("policy families must be an array")
    families = tuple(
        sorted(
            (
                _parse_family(row, index, schema)
                for index, row in enumerate(family_payloads)
            ),
            key=lambda row: row.identifier,
        )
    )
    _validate_distinct_families(families)
    canonical = {
        "schema": schema,
        "families": [family.to_dict() for family in families],
    }
    return GeneratedFamilyPolicy(
        schema=schema,
        families=families,
        digest=_sha256_json(canonical),
    )


def _parse_family(payload: Any, index: int, schema: str) -> GeneratedFamilyRule:
    """Validate one family row with source-locatable field names."""

    location = f"families[{index}]"
    if not isinstance(payload, Mapping):
        raise PolicyValidationError(f"{location} must be an object")
    _reject_unknown_keys(
        payload,
        {
            "id",
            "pathPatterns",
            "modulePatterns",
            "generator",
            "manifest",
            "source",
            "reviewThreshold",
        },
        location,
    )
    _validate_threshold_schema(payload, location, schema)
    identifier = _family_identifier(payload.get("id"), location)
    path_patterns = _path_patterns(payload.get("pathPatterns", []), location)
    module_patterns = _module_patterns(
        payload.get("modulePatterns", []),
        location,
    )
    if not path_patterns and not module_patterns:
        raise PolicyValidationError(
            f"{location} must define at least one path or module pattern"
        )
    return GeneratedFamilyRule(
        identifier=identifier,
        path_patterns=path_patterns,
        module_patterns=module_patterns,
        provenance=_parse_provenance(payload, location),
        review_threshold=_parse_review_threshold(
            payload.get("reviewThreshold"),
            location,
        ),
    )


def _validate_threshold_schema(
    payload: Mapping[str, Any],
    location: str,
    schema: str,
) -> None:
    """Keep the shipped v1 shape immutable while reading it compatibly."""

    if (
        "reviewThreshold" in payload
        and schema == LEGACY_GENERATED_FAMILY_POLICY_SCHEMA
    ):
        raise PolicyValidationError(
            f"{location}.reviewThreshold requires "
            f"schema {GENERATED_FAMILY_POLICY_SCHEMA!r}"
        )


def _parse_review_threshold(
    value: Any,
    location: str,
) -> FamilyReviewThreshold | None:
    """Validate one optional policy-owned promotion boundary."""

    if value is None:
        return None
    threshold = _optional_mapping(
        value,
        f"{location}.reviewThreshold",
    )
    _reject_unknown_keys(
        threshold,
        {"metric", "atLeast"},
        f"{location}.reviewThreshold",
    )
    metric = threshold.get("metric")
    if metric not in GENERATED_FAMILY_REVIEW_METRICS:
        raise PolicyValidationError(
            f"{location}.reviewThreshold.metric must be one of "
            f"{GENERATED_FAMILY_REVIEW_METRICS!r}"
        )
    at_least = threshold.get("atLeast")
    if not _positive_integer(at_least):
        raise PolicyValidationError(
            f"{location}.reviewThreshold.atLeast must be a positive integer"
        )
    return FamilyReviewThreshold(metric=metric, at_least=at_least)


def _family_identifier(value: Any, location: str) -> str:
    """Require one stable family identifier."""

    if not isinstance(value, str) or not _FAMILY_ID_RE.fullmatch(value):
        raise PolicyValidationError(f"{location}.id is not a stable family identifier")
    return value


def _path_patterns(value: Any, location: str) -> tuple[str, ...]:
    """Normalize repository-relative path selectors."""

    patterns = tuple(
        sorted(
            normalize_relative_path(pattern, f"{location}.pathPatterns")
            for pattern in _string_list(value, location)
        )
    )
    _require_unique_values(patterns, f"{location}.pathPatterns")
    return patterns


def _module_patterns(value: Any, location: str) -> tuple[str, ...]:
    """Normalize Lean module selectors."""

    patterns = tuple(
        sorted(pattern.strip() for pattern in _string_list(value, location))
    )
    _require_unique_values(patterns, f"{location}.modulePatterns")
    return patterns


def _parse_provenance(
    family: Mapping[str, Any],
    location: str,
) -> FamilyProvenance:
    """Validate optional quoted provenance without replaying it."""

    generator_name, generator_version = _parse_generator(
        family.get("generator"),
        location,
    )
    manifest_identity, manifest_path = _parse_manifest(
        family.get("manifest"),
        location,
    )
    source_path, source_line = _parse_source_anchor(
        family.get("source"),
        location,
    )
    return FamilyProvenance(
        generator_name=generator_name,
        generator_version=generator_version,
        manifest_identity=manifest_identity,
        manifest_path=manifest_path,
        source_path=source_path,
        source_line=source_line,
    )


def _parse_generator(
    value: Any,
    location: str,
) -> tuple[str | None, str | None]:
    """Validate optional generator name/version metadata."""

    generator = _optional_mapping(value, f"{location}.generator")
    _reject_unknown_keys(generator, {"name", "version"}, f"{location}.generator")
    name = _optional_string(generator.get("name"), f"{location}.generator.name")
    version = _optional_string(
        generator.get("version"),
        f"{location}.generator.version",
    )
    if version and not name:
        raise PolicyValidationError(
            f"{location}.generator.version requires generator.name"
        )
    return name, version


def _parse_manifest(
    value: Any,
    location: str,
) -> tuple[str | None, str | None]:
    """Validate optional quoted manifest identity/path metadata."""

    manifest = _optional_mapping(value, f"{location}.manifest")
    _reject_unknown_keys(manifest, {"identity", "path"}, f"{location}.manifest")
    identity = _optional_string(
        manifest.get("identity"),
        f"{location}.manifest.identity",
    )
    path = _optional_relative_path(
        manifest.get("path"),
        f"{location}.manifest.path",
    )
    if path and not identity:
        raise PolicyValidationError(
            f"{location}.manifest.path requires manifest.identity"
        )
    return identity, path


def _parse_source_anchor(
    value: Any,
    location: str,
) -> tuple[str | None, int | None]:
    """Validate optional policy source-path/line metadata."""

    source = _optional_mapping(value, f"{location}.source")
    _reject_unknown_keys(source, {"path", "line"}, f"{location}.source")
    path = _optional_relative_path(
        source.get("path"),
        f"{location}.source.path",
    )
    line = source.get("line")
    if line is not None and not _positive_integer(line):
        raise PolicyValidationError(f"{location}.source.line must be a positive integer")
    if line and not path:
        raise PolicyValidationError(f"{location}.source.line requires source.path")
    return path, line


def _positive_integer(value: Any) -> bool:
    """Distinguish positive integers from booleans."""

    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def _validate_distinct_families(
    families: Sequence[GeneratedFamilyRule],
) -> None:
    """Reject duplicate identities and identical cross-family selectors."""

    identifiers: set[str] = set()
    selectors: dict[tuple[str, str], str] = {}
    for family in families:
        if family.identifier in identifiers:
            raise PolicyValidationError(
                f"duplicate generated-family id {family.identifier!r}"
            )
        identifiers.add(family.identifier)
        _register_selectors(selectors, family, "path", family.path_patterns)
        _register_selectors(selectors, family, "module", family.module_patterns)


def _register_selectors(
    selectors: dict[tuple[str, str], str],
    family: GeneratedFamilyRule,
    kind: str,
    patterns: Sequence[str],
) -> None:
    """Register exact selectors and reject cross-family duplication."""

    for pattern in patterns:
        owner = selectors.setdefault((kind, pattern), family.identifier)
        if owner != family.identifier:
            raise PolicyValidationError(
                f"{kind} selector {pattern!r} is assigned to both "
                f"{owner!r} and {family.identifier!r}"
            )


def normalize_relative_path(value: Any, location: str) -> str:
    """Require a non-empty repository-relative POSIX path or glob."""

    if not isinstance(value, str):
        raise PolicyValidationError(f"{location} must contain strings")
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise PolicyValidationError(
            f"{location} must be a repository-relative path or pattern"
        )
    return path.as_posix()


def _optional_relative_path(value: Any, location: str) -> str | None:
    """Normalize one optional repository-relative provenance path."""

    return None if value is None else normalize_relative_path(value, location)


def _optional_mapping(value: Any, location: str) -> Mapping[str, Any]:
    """Normalize omitted metadata to an empty mapping."""

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise PolicyValidationError(f"{location} must be an object")
    return value


def _optional_string(value: Any, location: str) -> str | None:
    """Validate one optional non-empty string."""

    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PolicyValidationError(f"{location} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, location: str) -> tuple[str, ...]:
    """Require an array of non-empty strings."""

    if not isinstance(value, list):
        raise PolicyValidationError(f"{location} patterns must be arrays")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise PolicyValidationError(f"{location} patterns must be non-empty strings")
    return tuple(value)


def _require_unique_values(values: Sequence[str], location: str) -> None:
    """Reject redundant selectors that obscure policy provenance."""

    if len(values) != len(set(values)):
        raise PolicyValidationError(f"{location} contains duplicate selectors")


def _reject_unknown_keys(
    payload: Mapping[str, Any],
    allowed: set[str],
    location: str,
) -> None:
    """Reject misspelled policy fields before classification."""

    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise PolicyValidationError(
            f"{location} contains unsupported fields: {unknown}"
        )


def _sha256_json(payload: Mapping[str, Any]) -> str:
    """Hash normalized JSON with no host-specific formatting."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
