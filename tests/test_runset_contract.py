from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ladon.runset_contract import (
    RunsetManifestError,
    load_bundle_schema,
    load_runset_manifest,
    load_runset_schema,
    load_runset_state_schema,
    parse_runset_manifest,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "runsets"
MANIFEST_PATH = FIXTURE_ROOT / "manifest-v1.json"


def validator(schema: dict) -> Draft202012Validator:
    """Return a checked draft-2020 validator."""

    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_tracked_generic_manifest_is_normalized_and_schema_valid() -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)

    validator(load_runset_schema()).validate(manifest.to_payload())

    assert manifest.fingerprint.startswith("sha256:")
    assert [entry.identifier for entry in manifest.execution_order] == [
        "core",
        "helper",
        "facade",
    ]
    assert manifest.to_payload() == load_runset_manifest(MANIFEST_PATH).to_payload()


def test_same_root_with_distinct_scope_has_distinct_run_identity() -> None:
    payload = load_runset_manifest(MANIFEST_PATH).to_payload()
    second = deepcopy(payload["entries"][0])
    second["id"] = "core-closure"
    second["scope"] = {"kind": "closure", "roots": ["Fixture.Core"]}
    second["output"] = "reports/core-closure.json"
    payload["entries"].append(second)

    manifest = parse_runset_manifest(payload)

    assert manifest.entries[0].root == manifest.entries[-1].root
    assert manifest.entries[0].run_identity != manifest.entries[-1].run_identity


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda payload: payload.update(schemaVersion=2),
            "supported major is 1",
        ),
        (
            lambda payload: payload["entries"][0].update(
                output="/home/maintainer/report.json"
            ),
            "portable",
        ),
        (
            lambda payload: payload["entries"][0]["options"].update(
                architecturePolicy="../sibling/private-policy.json"
            ),
            "portable",
        ),
        (
            lambda payload: payload["entries"][0].update(
                unexpectedCallerDefault=True
            ),
            "unknown keys",
        ),
    ],
)
def test_manifest_preflight_rejects_unknown_major_and_nonportable_input(
    mutation,
    match: str,
) -> None:
    payload = load_runset_manifest(MANIFEST_PATH).to_payload()
    mutation(payload)

    with pytest.raises(RunsetManifestError, match=match):
        parse_runset_manifest(payload)


def test_complete_manifest_rejects_duplicate_outputs_and_dependency_cycles() -> None:
    duplicate = load_runset_manifest(MANIFEST_PATH).to_payload()
    duplicate["entries"][1]["output"] = duplicate["entries"][0]["output"]
    with pytest.raises(RunsetManifestError, match="outputs must be unique"):
        parse_runset_manifest(duplicate)

    cycle = load_runset_manifest(MANIFEST_PATH).to_payload()
    cycle["entries"][0]["dependsOn"] = ["facade"]
    with pytest.raises(RunsetManifestError, match="contain a cycle"):
        parse_runset_manifest(cycle)


def test_all_runset_schemas_are_packaged_draft_2020_documents() -> None:
    for schema in (
        load_runset_schema(),
        load_bundle_schema(),
        load_runset_state_schema(),
    ):
        Draft202012Validator.check_schema(schema)
