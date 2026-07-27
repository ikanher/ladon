from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.configuration import (
    ConfigurationError,
    policy_fingerprint_options,
    resolve_policy_configuration,
    validate_policy_configuration,
)


def test_valid_explicit_policy_configuration(tmp_path: Path) -> None:
    architecture = tmp_path / "architecture.json"
    architecture.write_text(
        json.dumps(
            {
                "groups": {"api": ["Pkg"], "core": ["Pkg.Core"]},
                "rules": [
                    {
                        "kind": "forbid_direct_imports",
                        "from": ["api"],
                        "to": ["core"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    patterns = tmp_path / "patterns.json"
    patterns.write_text(
        json.dumps(
            {
                "patterns": [
                    {"id": "legacy", "pattern": "OldName", "kind": "stale_term"}
                ]
            }
        ),
        encoding="utf-8",
    )

    validate_policy_configuration(
        tmp_path,
        architecture_policy=architecture,
        source_pattern_policy=patterns,
    )


def test_schema_invalid_policy_is_configuration_error(tmp_path: Path) -> None:
    architecture = tmp_path / "architecture.json"
    architecture.write_text(
        '{"groups": [], "rules": "not-an-array"}',
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="groups must be"):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=architecture,
            source_pattern_policy=None,
        )


def test_malformed_json_is_configuration_error(tmp_path: Path) -> None:
    patterns = tmp_path / "patterns.json"
    patterns.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="not valid JSON"):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=None,
            source_pattern_policy=patterns,
        )


def test_missing_explicit_policy_is_operational_input_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(OSError, match="does not exist"):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=tmp_path / "missing.json",
            source_pattern_policy=None,
        )


def test_discovered_policy_is_validated_before_analysis(tmp_path: Path) -> None:
    policy_dir = tmp_path / ".ladon"
    policy_dir.mkdir()
    (policy_dir / "source-pattern-policy.json").write_text(
        '{"patterns": [{"id": "", "pattern": "x"}]}',
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match=r"patterns\[0\]\.id"):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=None,
            source_pattern_policy=None,
        )


def test_generated_policy_is_validated_and_fingerprinted(tmp_path: Path) -> None:
    policy = tmp_path / "generated.json"
    policy.write_text(
        json.dumps(
            {
                "schema": "ladon-generated-family-policy-v1",
                "families": [
                    {
                        "id": "rows",
                        "pathPatterns": ["Pkg/Generated/*.lean"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_policy_configuration(
        tmp_path,
        generated_family_policy=policy,
    )

    generated = resolved["generatedFamily"]
    assert generated["status"] == "selected"
    assert generated["source"] == "explicit"
    assert generated["path"] == "generated.json"
    assert generated["schema"] == "ladon-generated-family-policy-v1"
    assert generated["sha256"].startswith("sha256:")


def test_invalid_generated_policy_fails_preflight(tmp_path: Path) -> None:
    policy = tmp_path / "generated.json"
    policy.write_text(
        '{"schema":"wrong","families":[]}',
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="unsupported generated-family"):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=None,
            source_pattern_policy=None,
            generated_family_policy=policy,
        )


def test_finite_resource_policy_is_normalized_into_fingerprint(
    tmp_path: Path,
) -> None:
    policy = tmp_path / "resource-policy.json"
    policy.write_text(
        json.dumps(
            {
                "patterns": [],
                "resourceThresholds": [
                    {
                        "id": "deep-recursion",
                        "option": "maxRecDepth",
                        "minimumValue": 100,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_policy_configuration(
        tmp_path,
        source_pattern_policy=policy,
    )
    identity = resolved["sourcePattern"]
    fingerprint = policy_fingerprint_options(resolved)

    assert identity["status"] == "selected"
    assert identity["source"] == "explicit"
    assert identity["resourceThresholds"] == [
        {
            "id": "deep-recursion",
            "option": "maxRecDepth",
            "minimumValue": 100,
        }
    ]
    assert fingerprint["policies"]["sourcePattern"] == identity


@pytest.mark.parametrize(
    ("threshold", "message"),
    [
        (
            {
                "id": "zero-depth",
                "option": "maxRecDepth",
                "minimumValue": 0,
            },
            "minimumValue must be a positive integer",
        ),
        (
            {
                "id": "unsupported",
                "option": "timeout",
                "minimumValue": 1,
            },
            "option must be one of",
        ),
    ],
)
def test_invalid_finite_resource_policy_fails_preflight(
    tmp_path: Path,
    threshold: dict,
    message: str,
) -> None:
    policy = tmp_path / "resource-policy.json"
    policy.write_text(
        json.dumps(
            {
                "patterns": [],
                "resourceThresholds": [threshold],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match=message):
        validate_policy_configuration(
            tmp_path,
            architecture_policy=None,
            source_pattern_policy=policy,
        )
