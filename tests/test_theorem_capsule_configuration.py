from __future__ import annotations

import json
from pathlib import Path

from ladon.theorem_capsule_configuration import (
    locked_package_rows,
    unsupported_lock_facets,
)
from ladon.theorem_capsule_inventory import CapsuleSource


def test_git_package_lock_is_retained_for_external_frontier(
    tmp_path: Path,
) -> None:
    write_manifest(
        tmp_path,
        {
            "name": "external",
            "type": "git",
            "url": "https://example.invalid/external",
            "rev": "0123456789abcdef",
            "inputRev": "main",
        },
    )
    sources = (
        CapsuleSource(
            module="Fixture",
            path="Fixture.lean",
            content=b"import External\n",
            imports=("External",),
        ),
    )

    assert unsupported_lock_facets(tmp_path, sources) == []
    assert locked_package_rows(tmp_path) == (
        {
            "name": "external",
            "type": "git",
            "url": "https://example.invalid/external",
            "revision": "0123456789abcdef",
            "inputRevision": "main",
            "lockEvidence": "lake-manifest.json",
        },
    )


def test_path_package_is_an_explicit_unsupported_facet(
    tmp_path: Path,
) -> None:
    write_manifest(
        tmp_path,
        {
            "name": "local-input",
            "type": "path",
            "dir": "../local-input",
        },
    )

    facets = unsupported_lock_facets(tmp_path, ())

    assert facets[0]["kind"] == "external_path_dependency"
    assert facets[0]["path"] == "lake-manifest.json"


def write_manifest(root: Path, package: dict) -> None:
    (root / "lake-manifest.json").write_text(
        json.dumps({"version": "1.1.0", "packages": [package]}),
        encoding="utf-8",
    )
