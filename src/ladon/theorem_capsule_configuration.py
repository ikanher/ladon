"""Static configuration evidence and unsupported capsule boundaries."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, Iterable, Mapping

from ladon.theorem_capsule_inventory import CapsuleSource
from ladon.theorem_capsule_models import CapsuleOperationalError, sha256_bytes


CONFIGURATION_NAMES = (
    "lean-toolchain",
    "lakefile.toml",
    "lakefile.lean",
    "lake-manifest.json",
)
NATIVE_FACET_KEYS = {
    "extern_lib",
    "lean_exe",
    "moreLinkArgs",
    "weakLinkArgs",
}


def configuration_files(repo_root: Path) -> tuple[dict[str, Any], ...]:
    """Capture exact supported toolchain, Lake, and lock bytes."""

    rows = []
    for name in CONFIGURATION_NAMES:
        path = repo_root / name
        if not path.is_file():
            continue
        content = path.read_bytes()
        rows.append(
            {
                "path": name,
                "role": configuration_role(name),
                "sha256": sha256_bytes(content),
                "bytes": len(content),
            }
        )
    names = {row["path"] for row in rows}
    if "lean-toolchain" not in names:
        raise CapsuleOperationalError(
            "pinned lean-toolchain disappeared during planning"
        )
    if not names.intersection({"lakefile.toml", "lakefile.lean"}):
        raise CapsuleOperationalError(
            "Lake configuration disappeared during planning"
        )
    return tuple(rows)


def configuration_role(name: str) -> str:
    """Return the manifest role for one recognized configuration path."""

    return {
        "lean-toolchain": "toolchain",
        "lakefile.toml": "lake_configuration",
        "lakefile.lean": "lake_configuration",
        "lake-manifest.json": "lake_lock",
    }[name]


def verify_configuration_files(
    repo_root: Path,
    configuration: Iterable[Mapping[str, Any]],
) -> None:
    """Reject configuration drift across the planning observation window."""

    for row in configuration:
        path = repo_root / str(row["path"])
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise CapsuleOperationalError(
                f"planning configuration disappeared: {row['path']}"
            ) from exc
        if sha256_bytes(content) != row.get("sha256"):
            raise CapsuleOperationalError(
                f"planning configuration drifted: {row['path']}"
            )


def unsupported_facets(
    repo_root: Path,
    configuration: Iterable[Mapping[str, Any]],
    sources: Iterable[CapsuleSource],
) -> tuple[dict[str, Any], ...]:
    """Classify observable build inputs outside the v1 package boundary."""

    configuration_rows = tuple(configuration)
    source_rows = tuple(sources)
    unsupported = [
        *lake_configuration_facets(repo_root, configuration_rows),
        *unsupported_lock_facets(repo_root, source_rows),
        *linked_input_facets(repo_root, configuration_rows, source_rows),
    ]
    return tuple(
        sorted(
            unsupported,
            key=lambda row: (str(row["kind"]), str(row["path"])),
        )
    )


def lake_configuration_facets(
    repo_root: Path,
    configuration: tuple[Mapping[str, Any], ...],
) -> list[dict[str, Any]]:
    """Return custom/native Lake facets visible without executing Lake DSL."""

    unsupported: list[dict[str, Any]] = []
    names = {str(row["path"]) for row in configuration}
    if "lakefile.lean" in names:
        unsupported.append(
            {
                "kind": "custom_lakefile_lean",
                "path": "lakefile.lean",
                "reason": "v1 does not execute custom Lake DSL to discover hidden inputs",
            }
        )
    toml_path = repo_root / "lakefile.toml"
    if toml_path.is_file() and toml_has_native_facets(toml_path):
        unsupported.append(
            {
                "kind": "native_or_custom_lake_facet",
                "path": "lakefile.toml",
                "reason": "v1 packages Lean sources and locked dependencies only",
            }
        )
    return unsupported


def linked_input_facets(
    repo_root: Path,
    configuration: tuple[Mapping[str, Any], ...],
    sources: tuple[CapsuleSource, ...],
) -> list[dict[str, Any]]:
    """Reject link-mediated source or configuration ownership."""

    rows = [
        {
            "kind": "configuration_symlink",
            "path": str(row["path"]),
            "reason": "v1 does not materialize linked build configuration",
        }
        for row in configuration
        if (repo_root / str(row["path"])).is_symlink()
    ]
    rows.extend(
        {
            "kind": "source_symlink",
            "path": source.path,
            "reason": "v1 does not materialize linked Lean source inputs",
        }
        for source in sources
        if (repo_root / source.path).is_symlink()
    )
    return rows


def toml_has_native_facets(path: Path) -> bool:
    """Conservatively find native/custom keys anywhere in Lake TOML."""

    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise CapsuleOperationalError(
            f"Lake TOML is unreadable: {path}: {exc}"
        ) from exc
    return mapping_tree_has_key(payload, NATIVE_FACET_KEYS)


def mapping_tree_has_key(value: Any, keys: set[str]) -> bool:
    """Search nested TOML mappings/lists for one unsupported key."""

    if isinstance(value, Mapping):
        return any(
            key in keys or mapping_tree_has_key(child, keys)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(mapping_tree_has_key(child, keys) for child in value)
    return False


def unsupported_lock_facets(
    repo_root: Path,
    sources: tuple[CapsuleSource, ...],
) -> list[dict[str, Any]]:
    """Require a pinned git lock for every observed external import frontier."""

    manifest_path = repo_root / "lake-manifest.json"
    if external_imports(sources) and not manifest_path.is_file():
        return [
            {
                "kind": "missing_external_lock",
                "path": "lake-manifest.json",
                "reason": "external imports require pinned Lake package evidence",
            }
        ]
    if not manifest_path.is_file():
        return []
    return [
        facet
        for package in load_manifest_packages(manifest_path)
        if (facet := unsupported_package_facet(package)) is not None
    ]


def external_imports(sources: tuple[CapsuleSource, ...]) -> set[str]:
    """Return imports outside the selected repository and toolchain frontiers."""

    repository_modules = {source.module for source in sources}
    return {
        imported
        for source in sources
        for imported in source.imports
        if imported not in repository_modules and not is_toolchain_module(imported)
    }


def load_manifest_packages(path: Path) -> tuple[Mapping[str, Any], ...]:
    """Load structurally valid Lake manifest package rows."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleOperationalError(
            f"Lake manifest is unreadable: {path}: {exc}"
        ) from exc
    packages = payload.get("packages", []) if isinstance(payload, Mapping) else []
    if not isinstance(packages, list) or any(
        not isinstance(package, Mapping) for package in packages
    ):
        raise CapsuleOperationalError("Lake manifest packages are malformed")
    return tuple(packages)


def unsupported_package_facet(
    package: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Classify one non-git or unpinned Lake manifest package."""

    package_type = str(package.get("type", "unknown"))
    if package_type == "git" and package.get("rev"):
        return None
    name = str(package.get("name", "<unnamed>"))
    return {
        "kind": (
            "external_path_dependency"
            if package_type == "path"
            else "unsupported_lake_dependency"
        ),
        "path": "lake-manifest.json",
        "reason": f"package {name} uses unsupported lock type {package_type}",
    }


def locked_package_rows(repo_root: Path) -> tuple[dict[str, Any], ...]:
    """Return deterministic Lake lock identities without reading package sources."""

    path = repo_root / "lake-manifest.json"
    if not path.is_file():
        return ()
    rows = [
        {
            "name": str(package.get("name", "<unnamed>")),
            "type": str(package.get("type", "unknown")),
            "url": package.get("url"),
            "revision": package.get("rev"),
            "inputRevision": package.get("inputRev"),
            "lockEvidence": "lake-manifest.json",
        }
        for package in load_manifest_packages(path)
    ]
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                str(row["name"]),
                str(row["type"]),
                str(row["revision"]),
            ),
        )
    )


def is_toolchain_module(module: str) -> bool:
    """Return whether a module is supplied by the pinned Lean toolchain."""

    return any(
        module == prefix or module.startswith(f"{prefix}.")
        for prefix in ("Init", "Lean", "Std")
    )


__all__ = [
    "configuration_files",
    "locked_package_rows",
    "unsupported_facets",
    "verify_configuration_files",
]
