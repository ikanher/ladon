"""Source association setup for exact source-to-compiled observations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.source_association_io import (
    MAX_MODULES,
    MAX_SETUP_BYTES,
    _AssociationError,
    _read_regular,
    _safe_repo_file,
    _strict_json,
)


def _load_setup(root: Path, relative: str | None, module: str) -> tuple[bytes | None, dict[str, Any] | None]:
    if relative is None:
        return None, None
    path = _safe_repo_file(root, relative)
    raw = _read_regular(path, MAX_SETUP_BYTES)
    value = _strict_json(raw)
    _validate_setup_shape(value)
    _validate_setup_identity(value, module)
    options = _validated_setup_options(value.get("options", {}))
    _validate_import_arts(value.get("importArts", {}))
    _reject_setup_plugins(value)
    normalized = _normalized_setup(value, module, options)
    return raw, normalized


def _validate_setup_shape(value: Any) -> None:
    fields = {"name", "package", "options", "isModule", "importArts", "plugins", "dynlibs"}
    if not isinstance(value, dict) or set(value) - fields:
        raise _AssociationError("unavailable", "unsupported-setup", "setup profile contains unsupported fields")


def _validate_setup_identity(value: Mapping[str, Any], module: str) -> None:
    if value.get("name") != module or value.get("isModule", False) is not False:
        raise _AssociationError("unavailable", "unsupported-setup", "setup name must match the selected non-modular module")
    if "package" in value and (
        not isinstance(value["package"], str)
        or len(value["package"].encode()) > 4096
    ):
        raise _AssociationError("unavailable", "unsupported-setup", "setup package is malformed")


def _validated_setup_options(options: Any) -> dict[str, Any]:
    if not isinstance(options, dict) or len(options) > 4096:
        raise _AssociationError("unavailable", "unsupported-setup", "setup options must be a bounded object")
    for key, item in options.items():
        if not isinstance(key, str) or not key or len(key.encode()) > 4096 or not isinstance(item, (str, bool, int)):
            raise _AssociationError("unavailable", "unsupported-setup", "setup options contain malformed values")

    return options


def _validate_import_arts(import_arts: Any) -> None:
    if not isinstance(import_arts, dict) or len(import_arts) > MAX_MODULES:
        raise _AssociationError("unavailable", "unsupported-setup", "setup importArts must be a bounded object")
    for key, groups in import_arts.items():
        if (
            not isinstance(key, str)
            or not key
            or not _valid_import_art_paths(groups)
        ):
            raise _AssociationError("unavailable", "unsupported-setup", "setup importArts are malformed")


def _reject_setup_plugins(value: Mapping[str, Any]) -> None:
    for field in ("plugins", "dynlibs"):
        if value.get(field, []) != []:
            raise _AssociationError("unavailable", "unsupported-setup", f"setup {field} are unsupported")


def _normalized_setup(value: Mapping[str, Any], module: str, options: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "name": module,
        "options": options,
        "isModule": False,
        "importArts": {},
        "plugins": [],
        "dynlibs": [],
    }
    if "package" in value:
        normalized["package"] = value["package"]
    return normalized


def _valid_import_art_paths(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value)
    return (
        isinstance(value, list)
        and len(value) <= 4
        and all(
            isinstance(group, list)
            and len(group) <= 4
            and all(isinstance(path, str) and bool(path) for path in group)
            for group in value
        )
    )

