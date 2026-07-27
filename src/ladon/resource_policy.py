"""Explicit repository policy for finite lexical resource review.

The policy remains a navigation threshold, not a runtime measurement.  It is
carried by the existing source-pattern policy so its canonical digest already
participates in analysis and source-index fingerprints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ladon.lexical_occurrences import RESOURCE_OPTIONS


RESOURCE_THRESHOLDS_KEY = "resourceThresholds"
_RESOURCE_THRESHOLD_KEYS = frozenset({"id", "option", "minimumValue"})


class ResourceThresholdPolicyError(ValueError):
    """One explicit finite-resource threshold has an invalid shape."""


@dataclass(frozen=True)
class ResourceThreshold:
    """One exact option and inclusive finite-value review threshold."""

    identifier: str
    option: str
    minimum_value: int

    def to_dict(self) -> dict[str, Any]:
        """Return the normalized fingerprint and report representation."""

        return {
            "id": self.identifier,
            "option": self.option,
            "minimumValue": self.minimum_value,
        }


def normalize_resource_thresholds(
    policy: Mapping[str, Any] | None,
) -> tuple[ResourceThreshold, ...]:
    """Validate and normalize optional finite resource-review thresholds."""

    if policy is None or RESOURCE_THRESHOLDS_KEY not in policy:
        return ()
    raw = policy.get(RESOURCE_THRESHOLDS_KEY)
    if not isinstance(raw, list):
        raise ResourceThresholdPolicyError(
            f"{RESOURCE_THRESHOLDS_KEY} must be an array"
        )
    thresholds = tuple(
        _resource_threshold(row, index) for index, row in enumerate(raw)
    )
    identifiers = [row.identifier for row in thresholds]
    if len(set(identifiers)) != len(identifiers):
        raise ResourceThresholdPolicyError(
            f"{RESOURCE_THRESHOLDS_KEY} ids must be unique"
        )
    return tuple(
        sorted(
            thresholds,
            key=lambda row: (row.option, row.minimum_value, row.identifier),
        )
    )


def matching_resource_threshold(
    resource: Mapping[str, Any],
    thresholds: Sequence[ResourceThreshold],
) -> ResourceThreshold | None:
    """Return the strongest explicit threshold matching one finite row."""

    if resource.get("normalizedMeaning") != "finite":
        return None
    numeric_value = resource.get("numericValue")
    if (
        not isinstance(numeric_value, int)
        or isinstance(numeric_value, bool)
        or numeric_value < 0
    ):
        return None
    option = resource.get("option")
    matches = [
        row
        for row in thresholds
        if row.option == option and numeric_value >= row.minimum_value
    ]
    return min(
        matches,
        key=lambda row: (-row.minimum_value, row.identifier),
        default=None,
    )


def _resource_threshold(value: Any, index: int) -> ResourceThreshold:
    label = f"{RESOURCE_THRESHOLDS_KEY}[{index}]"
    if not isinstance(value, Mapping):
        raise ResourceThresholdPolicyError(f"{label} must be an object")
    _validate_threshold_keys(value, label)
    return ResourceThreshold(
        _threshold_identifier(value.get("id"), label),
        _threshold_option(value.get("option"), label),
        _threshold_minimum(value.get("minimumValue"), label),
    )


def _validate_threshold_keys(
    value: Mapping[str, Any],
    label: str,
) -> None:
    unknown = sorted(set(value) - _RESOURCE_THRESHOLD_KEYS)
    missing = sorted(_RESOURCE_THRESHOLD_KEYS - set(value))
    if unknown or missing:
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unknown:
            details.append(f"unknown={','.join(unknown)}")
        raise ResourceThresholdPolicyError(f"{label} has {' '.join(details)}")


def _threshold_identifier(value: Any, label: str) -> str:
    identifier = value
    if not isinstance(identifier, str) or not identifier:
        raise ResourceThresholdPolicyError(f"{label}.id must be non-empty")
    return identifier


def _threshold_option(value: Any, label: str) -> str:
    option = value
    if option not in RESOURCE_OPTIONS:
        supported = ", ".join(sorted(RESOURCE_OPTIONS))
        raise ResourceThresholdPolicyError(
            f"{label}.option must be one of: {supported}"
        )
    return str(option)


def _threshold_minimum(value: Any, label: str) -> int:
    minimum_value = value
    if (
        not isinstance(minimum_value, int)
        or isinstance(minimum_value, bool)
        or minimum_value <= 0
    ):
        raise ResourceThresholdPolicyError(
            f"{label}.minimumValue must be a positive integer"
        )
    return minimum_value


__all__ = [
    "RESOURCE_THRESHOLDS_KEY",
    "ResourceThreshold",
    "ResourceThresholdPolicyError",
    "matching_resource_threshold",
    "normalize_resource_thresholds",
]
