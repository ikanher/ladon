"""Validate only the finite shape vocabulary of the bundled result-v1 schema.

This is an internal contract interpreter, not a general JSON Schema validator.
The packaged schema owns shape bounds; semantic references and review currency
are checked separately. Development tests compare shape behavior with jsonschema.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from importlib.resources import files
from typing import Any

from ladon.result_manifest_io import ResultManifestError


def manifest_schema() -> dict[str, Any]:
    """Load the packaged schema without a network or source-checkout dependency."""

    path = files("ladon.schemas").joinpath("ladon-result-manifest-v1.schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_shape(value: Any) -> None:
    """Validate the closed v1 schema with bounded schema-directed traversal."""

    schema = manifest_schema()
    validate_document_shape(value, schema)


def validate_document_shape(value: Any, schema: dict) -> None:
    """Validate a packaged schema using this owner's finite vocabulary."""
    _node(value, schema, schema["$defs"], "$")


def _node(value: Any, spec: dict, definitions: dict, path: str) -> None:
    if "$ref" in spec:
        spec = definitions[spec["$ref"].removeprefix("#/$defs/")]
    validators = {"object": _object, "array": _array, "string": _string, "integer": _integer}
    validators[spec["type"]](value, spec, definitions, path)
    if "const" in spec and value != spec["const"]:
        raise ResultManifestError(f"{path}: unsupported schema version")
    if "enum" in spec and value not in spec["enum"]:
        raise ResultManifestError(f"{path}: unsupported value")


def _integer(value: Any, spec: dict, _definitions: dict, path: str) -> None:
    if type(value) is not int or not spec['minimum'] <= value <= spec['maximum']:
        raise ResultManifestError(f'{path}: integer limit violated')


def _object(value: Any, spec: dict, definitions: dict, path: str) -> None:
    if not isinstance(value, dict):
        raise ResultManifestError(f"{path}: expected object")
    properties = spec["properties"]
    if set(value) - set(properties):
        raise ResultManifestError(f"{path}: unknown fields")
    if set(spec["required"]) - set(value):
        raise ResultManifestError(f"{path}: missing required fields")
    for key, child in value.items():
        _node(child, properties[key], definitions, f"{path}.{key}")


def _array(value: Any, spec: dict, definitions: dict, path: str) -> None:
    if not isinstance(value, list):
        raise ResultManifestError(f"{path}: expected array")
    if not spec["minItems"] <= len(value) <= spec["maxItems"]:
        raise ResultManifestError(f"{path}: collection limit violated")
    for index, child in enumerate(value):
        _node(child, spec["items"], definitions, f"{path}[{index}]")
    if spec.get("uniqueItems") and len(set(value)) != len(value):
        raise ResultManifestError(f"{path}: duplicate array member")


def _string(value: Any, spec: dict, _definitions: dict, path: str) -> None:
    if not isinstance(value, str):
        raise ResultManifestError(f"{path}: expected string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ResultManifestError(f"{path}: invalid Unicode") from exc
    if not spec.get("minLength", 0) <= len(value) <= spec.get("maxLength", 65536):
        raise ResultManifestError(f"{path}: text length limit violated")
    if size > spec.get("x-maxUtf8Bytes", 65536):
        raise ResultManifestError(f"{path}: UTF-8 byte limit violated")
    _string_format(value, spec, path)


def _string_format(value: str, spec: dict, path: str) -> None:
    if "pattern" in spec and re.fullmatch(spec["pattern"], value) is None:
        raise ResultManifestError(f"{path}: invalid string format")
    if spec.get("format") == "date-time":
        _timestamp(value, path)


def _timestamp(value: str, path: str) -> None:
    pattern = r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})"
    try:
        if re.fullmatch(pattern, value) is None:
            raise ValueError("timestamp must include a timezone")
        datetime.fromisoformat(value.upper())
    except ValueError as exc:
        raise ResultManifestError(f"{path}: invalid timestamp") from exc
