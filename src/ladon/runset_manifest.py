"""JSON parsing and packaged schemas for versioned generic runsets."""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.runset_models import (
    RunsetEntry,
    RunsetManifest,
    RunsetPolicy,
    RunsetResources,
)
from ladon.runset_validation import (
    ENTRY_KEYS,
    POLICY_KEYS,
    RESOURCE_KEYS,
    RUNSET_KEYS,
    RunsetManifestError,
    copy_json_mapping,
    optional_integer,
    optional_mapping,
    optional_number,
    require_allowed_keys,
    require_keys,
    required_boolean,
    required_integer,
    required_string,
    string_tuple,
)


def parse_runset_manifest(payload: Mapping[str, Any]) -> RunsetManifest:
    """Parse and validate one complete v1 manifest before execution."""

    row = copy_json_mapping(payload, "runset manifest")
    require_allowed_keys(row, RUNSET_KEYS, "runset manifest")
    require_keys(
        row,
        {
            "artifactKind",
            "schemaVersion",
            "name",
            "repository",
            "entries",
        },
        "runset manifest",
    )
    return RunsetManifest(
        name=required_string(row["name"], "runset name"),
        repository=required_string(row["repository"], "runset repository"),
        entries=_parse_entries(row["entries"]),
        policy=_parse_policy(row.get("policy", {})),
        resources=_parse_resources(row.get("resources", {})),
        metadata=optional_mapping(row.get("metadata", {}), "runset metadata"),
        artifact_kind=required_string(
            row["artifactKind"],
            "runset artifactKind",
        ),
        schema_version=required_integer(
            row["schemaVersion"],
            "runset schemaVersion",
        ),
    )


def load_runset_manifest(path: str | Path) -> RunsetManifest:
    """Load a JSON manifest and classify malformed input as invocation error."""

    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunsetManifestError(
            f"cannot load runset manifest {source}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise RunsetManifestError("runset manifest must be a JSON object")
    return parse_runset_manifest(payload)


def load_runset_schema() -> dict[str, Any]:
    """Load the packaged runset-v1 schema."""

    return _load_packaged_schema("ladon-analysis-runset-v1.schema.json")


def load_bundle_schema() -> dict[str, Any]:
    """Load the packaged deterministic bundle-v1 schema."""

    return _load_packaged_schema("ladon-analysis-bundle-v1.schema.json")


def load_runset_state_schema() -> dict[str, Any]:
    """Load the packaged durable-state-v1 schema."""

    return _load_packaged_schema("ladon-analysis-runset-state-v1.schema.json")


def _parse_entries(raw: Any) -> tuple[RunsetEntry, ...]:
    if not isinstance(raw, list) or not raw:
        raise RunsetManifestError("runset entries must be a non-empty array")
    return tuple(_parse_entry(item, index) for index, item in enumerate(raw))


def _parse_entry(raw: Any, index: int) -> RunsetEntry:
    row = optional_mapping(raw, f"runset entry {index}")
    require_allowed_keys(row, ENTRY_KEYS, f"runset entry {index}")
    require_keys(
        row,
        {
            "id",
            "root",
            "scope",
            "backend",
            "projection",
            "output",
            "required",
        },
        f"runset entry {index}",
    )
    identifier = required_string(row["id"], f"runset entry {index} id")
    return RunsetEntry(
        identifier=identifier,
        root=required_string(row["root"], f"entry {identifier} root"),
        scope=optional_mapping(row["scope"], f"entry {identifier} scope"),
        backend=required_string(row["backend"], f"entry {identifier} backend"),
        projection=required_string(
            row["projection"],
            f"entry {identifier} projection",
        ),
        output=required_string(row["output"], f"entry {identifier} output"),
        required=required_boolean(
            row["required"],
            f"entry {identifier} required",
        ),
        report_version=required_string(
            row.get("reportVersion", "v3"),
            f"entry {identifier} reportVersion",
        ),
        options=optional_mapping(
            row.get("options", {}),
            f"entry {identifier} options",
        ),
        depends_on=string_tuple(
            row.get("dependsOn", []),
            f"entry {identifier} dependsOn",
        ),
    )


def _parse_policy(raw: Any) -> RunsetPolicy:
    row = optional_mapping(raw, "runset policy")
    require_allowed_keys(row, POLICY_KEYS, "runset policy")
    return RunsetPolicy(
        stop_on_required_failure=required_boolean(
            row.get("stopOnRequiredFailure", True),
            "policy.stopOnRequiredFailure",
        ),
        continue_on_advisory_failure=required_boolean(
            row.get("continueOnAdvisoryFailure", True),
            "policy.continueOnAdvisoryFailure",
        ),
        concurrency=required_integer(
            row.get("concurrency", 1),
            "policy.concurrency",
        ),
    )


def _parse_resources(raw: Any) -> RunsetResources:
    row = optional_mapping(raw, "runset resources")
    require_allowed_keys(row, RESOURCE_KEYS, "runset resources")
    return RunsetResources(
        overall_timeout_seconds=optional_number(
            row.get("overallTimeoutSeconds"),
            "resources.overallTimeoutSeconds",
        ),
        max_rss_mib=optional_integer(
            row.get("maxRssMiB"),
            "resources.maxRssMiB",
        ),
        max_report_bytes=optional_integer(
            row.get("maxReportBytes"),
            "resources.maxReportBytes",
        ),
    )


def _load_packaged_schema(name: str) -> dict[str, Any]:
    raw = resources.files("ladon").joinpath("schemas", name).read_text(
        encoding="utf-8"
    )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RunsetManifestError(f"packaged schema {name} must be an object")
    return payload
