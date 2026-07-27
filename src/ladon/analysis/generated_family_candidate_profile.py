"""Strict profiles for advisory generated-family candidate detection.

The built-in profile is immutable.  Alternative profiles are accepted only as
explicit, complete JSON documents whose schema and profile identity are
separate from the built-in predicate identity.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ladon.lexical_command_skeleton import COMMAND_SKELETON_VERSION


CANDIDATE_PROFILE_SCHEMA = "ladon-generated-family-candidate-profile-v1"
BUILTIN_PROFILE_VERSION = "generic-numbered-family-v1"
GROUPING_VERSION = "parent-final-segment-decimal-suffix-v1"
GROUPING_SUFFIX_WIDTH_VERSION = (
    "parent-final-segment-decimal-suffix-width-v1"
)
SUPPORTED_GROUPING_VERSIONS = (
    GROUPING_VERSION,
    GROUPING_SUFFIX_WIDTH_VERSION,
)
DECLARATION_STEM_VERSION = "declaration-stem-v1"
SUPPORTED_LEXICAL_FEATURES = (
    DECLARATION_STEM_VERSION,
    COMMAND_SKELETON_VERSION,
)
FEATURE_KEY_PROJECTION_VERSION = (
    "strongest-feature-keys-per-kind-version-v1"
)
FEATURE_KEY_LIMIT = 12
PROFILE_VERSION_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*-v[1-9][0-9]*$")

_DOCUMENT_KEYS = frozenset(
    {
        "schema",
        "profileVersion",
        "grouping",
        "clauses",
        "normalizers",
        "representatives",
    }
)
_GROUPING_KEYS = frozenset({"version"})
_CLAUSE_KEYS = frozenset(
    {
        "minimumMembers",
        "minimumDensity",
        "directInternalImportMemberCoverage",
        "lexicalMemberCoverage",
        "lexicalFeatures",
    }
)
_RATIO_KEYS = frozenset({"numerator", "denominator"})
_NORMALIZER_KEYS = frozenset({"declarationStem", "commandSkeleton"})
_REPRESENTATIVE_KEYS = frozenset({"limit"})


class CandidateProfileError(ValueError):
    """Raised when a candidate profile is ambiguous or unsupported."""


@dataclass(frozen=True)
class CandidateRatio:
    """One exact inclusive lower-bound ratio."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if not _positive_int(self.numerator):
            raise CandidateProfileError("ratio numerator must be positive")
        if not _positive_int(self.denominator):
            raise CandidateProfileError("ratio denominator must be positive")
        if self.numerator > self.denominator:
            raise CandidateProfileError("ratio cannot exceed one")

    def to_dict(self) -> dict[str, int]:
        """Return an exact JSON-compatible fraction."""

        return {
            "numerator": self.numerator,
            "denominator": self.denominator,
        }

    def required_count(self, population: int) -> int:
        """Return the least count satisfying this ratio for `population`."""

        if not isinstance(population, int) or isinstance(population, bool):
            raise CandidateProfileError("ratio population must be an integer")
        if population < 0:
            raise CandidateProfileError("ratio population cannot be negative")
        return (population * self.numerator + self.denominator - 1) // self.denominator

    def satisfied_by(self, count: int, population: int) -> bool:
        """Evaluate this ratio without floating-point rounding."""

        if count < 0 or population < 0 or count > population:
            raise CandidateProfileError("ratio operands are inconsistent")
        return count * self.denominator >= population * self.numerator


@dataclass(frozen=True)
class CandidateProfile:
    """One complete, versioned candidate predicate configuration."""

    profile_version: str
    minimum_members: int
    minimum_density: CandidateRatio
    direct_import_coverage: CandidateRatio
    lexical_coverage: CandidateRatio
    lexical_features: tuple[str, ...]
    representative_limit: int
    grouping_version: str = GROUPING_VERSION
    declaration_stem_version: str = DECLARATION_STEM_VERSION
    command_skeleton_version: str = COMMAND_SKELETON_VERSION
    schema: str = CANDIDATE_PROFILE_SCHEMA

    def __post_init__(self) -> None:
        _validate_profile(self)

    @property
    def digest(self) -> str:
        """Return the digest of the normalized, complete configuration."""

        encoded = json.dumps(
            self.normalized_configuration(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    def normalized_configuration(self) -> dict[str, Any]:
        """Return the strict canonical profile document."""

        return {
            "schema": self.schema,
            "profileVersion": self.profile_version,
            "grouping": {"version": self.grouping_version},
            "clauses": {
                "minimumMembers": self.minimum_members,
                "minimumDensity": self.minimum_density.to_dict(),
                "directInternalImportMemberCoverage": (
                    self.direct_import_coverage.to_dict()
                ),
                "lexicalMemberCoverage": self.lexical_coverage.to_dict(),
                "lexicalFeatures": list(self.lexical_features),
            },
            "normalizers": {
                "declarationStem": self.declaration_stem_version,
                "commandSkeleton": self.command_skeleton_version,
            },
            "representatives": {"limit": self.representative_limit},
        }

    def to_dict(self) -> dict[str, Any]:
        """Return report-facing configuration plus its normalized digest."""

        return {
            **self.normalized_configuration(),
            "profileDigest": self.digest,
        }


def parse_explicit_candidate_profile(
    payload: Mapping[str, Any],
) -> CandidateProfile:
    """Decode one strict non-default candidate profile mapping."""

    row = _mapping(payload, "candidate profile")
    _exact_keys(row, _DOCUMENT_KEYS, "candidate profile")
    if row["schema"] != CANDIDATE_PROFILE_SCHEMA:
        raise CandidateProfileError("candidate profile schema is unsupported")
    profile_version = _profile_version(row["profileVersion"])
    if profile_version == BUILTIN_PROFILE_VERSION:
        raise CandidateProfileError(
            "the built-in profile identity is reserved and cannot be "
            "selected through an explicit profile"
        )
    grouping = _mapping(row["grouping"], "grouping")
    clauses = _mapping(row["clauses"], "clauses")
    normalizers = _mapping(row["normalizers"], "normalizers")
    representatives = _mapping(
        row["representatives"],
        "representatives",
    )
    _exact_keys(grouping, _GROUPING_KEYS, "grouping")
    _exact_keys(clauses, _CLAUSE_KEYS, "clauses")
    _exact_keys(normalizers, _NORMALIZER_KEYS, "normalizers")
    _exact_keys(
        representatives,
        _REPRESENTATIVE_KEYS,
        "representatives",
    )
    return CandidateProfile(
        profile_version=profile_version,
        minimum_members=_required_positive_int(
            clauses["minimumMembers"],
            "clauses.minimumMembers",
        ),
        minimum_density=_ratio(
            clauses["minimumDensity"],
            "clauses.minimumDensity",
        ),
        direct_import_coverage=_ratio(
            clauses["directInternalImportMemberCoverage"],
            "clauses.directInternalImportMemberCoverage",
        ),
        lexical_coverage=_ratio(
            clauses["lexicalMemberCoverage"],
            "clauses.lexicalMemberCoverage",
        ),
        lexical_features=_lexical_features(clauses["lexicalFeatures"]),
        representative_limit=_required_positive_int(
            representatives["limit"],
            "representatives.limit",
        ),
        grouping_version=_required_supported_string(
            grouping["version"],
            SUPPORTED_GROUPING_VERSIONS,
            "grouping.version",
        ),
        declaration_stem_version=_required_exact_string(
            normalizers["declarationStem"],
            DECLARATION_STEM_VERSION,
            "normalizers.declarationStem",
        ),
        command_skeleton_version=_required_exact_string(
            normalizers["commandSkeleton"],
            COMMAND_SKELETON_VERSION,
            "normalizers.commandSkeleton",
        ),
    )


def load_explicit_candidate_profile(path: Path) -> CandidateProfile:
    """Read and decode one strict profile, rejecting duplicate JSON keys."""

    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError) as exc:
        raise CandidateProfileError(
            f"could not read candidate profile {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise CandidateProfileError(
            f"candidate profile is not valid JSON: {exc.msg}"
        ) from exc
    return parse_explicit_candidate_profile(_mapping(raw, "candidate profile"))


def candidate_analysis_fingerprint(
    profile: CandidateProfile,
    *,
    source_index_fingerprint: str,
    scope_fingerprint: str | None,
    policy_digest: str | None,
    internal_inventory_fingerprint: str | None = None,
    completeness_fingerprint: str,
) -> str:
    """Bind candidate results to every owned input and normalizer version."""

    if not source_index_fingerprint:
        raise CandidateProfileError(
            "candidate analysis requires a source-index fingerprint"
        )
    payload = {
        "schema": "ladon-generated-family-candidate-analysis-input-v1",
        "profileDigest": profile.digest,
        "sourceIndexFingerprint": source_index_fingerprint,
        "scopeFingerprint": scope_fingerprint,
        "policyDigest": policy_digest,
        "groupingVersion": profile.grouping_version,
        "declarationStemVersion": profile.declaration_stem_version,
        "commandSkeletonVersion": profile.command_skeleton_version,
        "representativeLimit": profile.representative_limit,
        "featureKeyProjectionVersion": FEATURE_KEY_PROJECTION_VERSION,
        "featureKeyLimitPerKindVersion": FEATURE_KEY_LIMIT,
        "completenessFingerprint": completeness_fingerprint,
    }
    if internal_inventory_fingerprint is not None:
        payload["internalInventoryFingerprint"] = internal_inventory_fingerprint
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_profile(profile: CandidateProfile) -> None:
    if profile.schema != CANDIDATE_PROFILE_SCHEMA:
        raise CandidateProfileError("candidate profile schema is unsupported")
    _profile_version(profile.profile_version)
    _required_positive_int(profile.minimum_members, "minimum_members")
    _required_positive_int(
        profile.representative_limit,
        "representative_limit",
    )
    _validate_profile_versions(profile)
    _validate_profile_features(profile.lexical_features)
    if (
        profile.profile_version == BUILTIN_PROFILE_VERSION
        and _profile_constants(profile) != _builtin_constants()
    ):
        raise CandidateProfileError(
            "generic-numbered-family-v1 has frozen built-in constants"
        )


def _validate_profile_versions(profile: CandidateProfile) -> None:
    if profile.grouping_version not in SUPPORTED_GROUPING_VERSIONS:
        raise CandidateProfileError("candidate grouping version is unsupported")
    if profile.declaration_stem_version != DECLARATION_STEM_VERSION:
        raise CandidateProfileError(
            "declaration-stem normalizer version is unsupported"
        )
    if profile.command_skeleton_version != COMMAND_SKELETON_VERSION:
        raise CandidateProfileError(
            "command-skeleton normalizer version is unsupported"
        )


def _validate_profile_features(features: tuple[str, ...]) -> None:
    if (
        not features
        or len(set(features)) != len(features)
        or any(feature not in SUPPORTED_LEXICAL_FEATURES for feature in features)
    ):
        raise CandidateProfileError(
            "lexical features must be a unique non-empty supported list"
        )


def _profile_constants(profile: CandidateProfile) -> tuple[Any, ...]:
    return (
        profile.minimum_members,
        profile.minimum_density,
        profile.direct_import_coverage,
        profile.lexical_coverage,
        profile.lexical_features,
        profile.representative_limit,
        profile.grouping_version,
        profile.declaration_stem_version,
        profile.command_skeleton_version,
    )


def _builtin_constants() -> tuple[Any, ...]:
    return (
        4,
        CandidateRatio(4, 5),
        CandidateRatio(4, 5),
        CandidateRatio(4, 5),
        SUPPORTED_LEXICAL_FEATURES,
        12,
        GROUPING_VERSION,
        DECLARATION_STEM_VERSION,
        COMMAND_SKELETON_VERSION,
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateProfileError(
                f"candidate profile contains duplicate key {key!r}"
            )
        result[key] = value
    return result


def _mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CandidateProfileError(f"{location} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise CandidateProfileError(f"{location} keys must be strings")
    return value


def _exact_keys(
    row: Mapping[str, Any],
    expected: frozenset[str],
    location: str,
) -> None:
    actual = frozenset(row)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise CandidateProfileError(
            f"{location} keys are invalid; missing={missing}, unknown={unknown}"
        )


def _ratio(value: Any, location: str) -> CandidateRatio:
    row = _mapping(value, location)
    _exact_keys(row, _RATIO_KEYS, location)
    return CandidateRatio(
        _required_positive_int(row["numerator"], f"{location}.numerator"),
        _required_positive_int(
            row["denominator"],
            f"{location}.denominator",
        ),
    )


def _lexical_features(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise CandidateProfileError("clauses.lexicalFeatures must be a non-empty list")
    if any(not isinstance(row, str) for row in value):
        raise CandidateProfileError("clauses.lexicalFeatures values must be strings")
    values = tuple(value)
    if len(values) != len(set(values)):
        raise CandidateProfileError("clauses.lexicalFeatures values must be unique")
    unknown = sorted(set(values) - set(SUPPORTED_LEXICAL_FEATURES))
    if unknown:
        raise CandidateProfileError(f"unsupported lexical feature clauses: {unknown}")
    return tuple(feature for feature in SUPPORTED_LEXICAL_FEATURES if feature in values)


def _profile_version(value: Any) -> str:
    if not isinstance(value, str) or not PROFILE_VERSION_RE.fullmatch(value):
        raise CandidateProfileError(
            "profileVersion must be an explicit lowercase versioned identity"
        )
    return value


def _required_exact_string(
    value: Any,
    expected: str,
    location: str,
) -> str:
    if value != expected:
        raise CandidateProfileError(f"{location} must be {expected!r}")
    return expected


def _required_positive_int(value: Any, location: str) -> int:
    if not _positive_int(value):
        raise CandidateProfileError(f"{location} must be a positive integer")
    return value


def _required_supported_string(
    value: Any,
    supported: tuple[str, ...],
    label: str,
) -> str:
    if not isinstance(value, str) or value not in supported:
        raise CandidateProfileError(f"{label} is unsupported")
    return value


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


BUILTIN_CANDIDATE_PROFILE = CandidateProfile(
    profile_version=BUILTIN_PROFILE_VERSION,
    minimum_members=4,
    minimum_density=CandidateRatio(4, 5),
    direct_import_coverage=CandidateRatio(4, 5),
    lexical_coverage=CandidateRatio(4, 5),
    lexical_features=SUPPORTED_LEXICAL_FEATURES,
    representative_limit=12,
)
