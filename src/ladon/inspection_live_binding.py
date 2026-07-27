"""Live repository configuration rebinding for source-index inspection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    CandidateProfile,
    load_explicit_candidate_profile,
)
from ladon.configuration import (
    policy_display_path,
    resolve_policy_configuration,
)


_FILE_POLICY_NAMES = frozenset(
    {"architecture", "generatedFamily", "sourcePattern"}
)
_CANDIDATE_PROFILE_NAME = "generatedFamilyCandidateProfile"
_SUPPORTED_POLICY_NAMES = _FILE_POLICY_NAMES | {_CANDIDATE_PROFILE_NAME}


class LiveInspectionBindingError(ValueError):
    """Recorded configuration cannot be safely rebound to a live checkout."""


def live_source_index_options(
    recorded_options: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    """Re-resolve the policy identities represented by source-index options."""

    raw_policies = recorded_options.get("policies")
    if raw_policies is None:
        return dict(recorded_options)
    if not isinstance(raw_policies, Mapping):
        raise LiveInspectionBindingError(
            "recorded source-index policies are malformed"
        )
    recorded = _recorded_policy_rows(raw_policies)
    unknown = sorted(set(recorded) - _SUPPORTED_POLICY_NAMES)
    if unknown:
        raise LiveInspectionBindingError(
            "recorded source-index policies cannot be rebound: "
            + ", ".join(unknown)
        )
    resolved = _resolved_file_policy_identities(repo_root, recorded)
    if _CANDIDATE_PROFILE_NAME in recorded:
        resolved[_CANDIDATE_PROFILE_NAME] = _candidate_profile_identity(
            repo_root,
            recorded[_CANDIDATE_PROFILE_NAME],
        )
    shaped = {
        name: _recorded_identity_shape(resolved[name], row)
        for name, row in sorted(recorded.items())
    }
    return {**dict(recorded_options), "policies": shaped}


def _recorded_policy_rows(
    raw_policies: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    rows: dict[str, Mapping[str, Any]] = {}
    for name, value in raw_policies.items():
        if not isinstance(name, str) or not isinstance(value, Mapping):
            raise LiveInspectionBindingError(
                "recorded source-index policy identity is malformed"
            )
        rows[name] = value
    return rows


def _resolved_file_policy_identities(
    repo_root: Path,
    recorded: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    resolved = resolve_policy_configuration(
        repo_root,
        architecture_policy=_explicit_policy_path(
            repo_root,
            recorded.get("architecture"),
            "architecture policy",
        ),
        source_pattern_policy=_explicit_policy_path(
            repo_root,
            recorded.get("sourcePattern"),
            "source-pattern policy",
        ),
        generated_family_policy=_explicit_policy_path(
            repo_root,
            recorded.get("generatedFamily"),
            "generated-family policy",
        ),
    )
    return {
        name: resolved[name]
        for name in _FILE_POLICY_NAMES
        if name in recorded
    }


def _explicit_policy_path(
    repo_root: Path,
    recorded: Mapping[str, Any] | None,
    label: str,
) -> Path | None:
    if recorded is None:
        return None
    source = recorded.get("source")
    if source == "inline":
        raise LiveInspectionBindingError(
            f"{label} used inline configuration that --repo-root cannot rebind"
        )
    if source in {None, "none", "discovered"}:
        return None
    if source != "explicit":
        raise LiveInspectionBindingError(
            f"{label} has unsupported recorded source {source!r}"
        )
    return _repository_policy_path(repo_root, recorded.get("path"), label)


def _candidate_profile_identity(
    repo_root: Path,
    recorded: Mapping[str, Any],
) -> dict[str, Any]:
    source = recorded.get("source")
    if source == "inline":
        raise LiveInspectionBindingError(
            "generated-family candidate profile used inline configuration "
            "that --repo-root cannot rebind"
        )
    if source == "explicit":
        path = _repository_policy_path(
            repo_root,
            recorded.get("path"),
            "generated-family candidate profile",
        )
        profile = load_explicit_candidate_profile(path)
        return _profile_identity(profile, source="explicit", path=path, repo_root=repo_root)
    if source not in {None, "built_in"}:
        raise LiveInspectionBindingError(
            "generated-family candidate profile has unsupported recorded "
            f"source {source!r}"
        )
    return _profile_identity(
        BUILTIN_CANDIDATE_PROFILE,
        source="built_in",
        path=None,
        repo_root=repo_root,
    )


def _profile_identity(
    profile: CandidateProfile,
    *,
    source: str,
    path: Path | None,
    repo_root: Path,
) -> dict[str, Any]:
    return {
        "status": "selected",
        "source": source,
        "path": policy_display_path(repo_root, path),
        "schema": profile.schema,
        "profileVersion": profile.profile_version,
        "sha256": profile.digest,
    }


def _repository_policy_path(
    repo_root: Path,
    value: Any,
    label: str,
) -> Path:
    if not isinstance(value, str) or not value:
        raise LiveInspectionBindingError(f"{label} path is missing")
    root = repo_root.resolve()
    raw = Path(value)
    selected = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        selected.relative_to(root)
    except ValueError as exc:
        raise LiveInspectionBindingError(
            f"{label} path is outside the live repository"
        ) from exc
    return selected


def _recorded_identity_shape(
    current: Mapping[str, Any],
    recorded: Mapping[str, Any],
) -> dict[str, Any]:
    return {key: current.get(key) for key in recorded}


__all__ = [
    "LiveInspectionBindingError",
    "live_source_index_options",
]
