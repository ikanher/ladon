from __future__ import annotations

import ast
from pathlib import Path
import tomllib


def _python_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _dependency_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for row in value for item in _dependency_strings(row)]
    if isinstance(value, dict):
        return [
            item
            for key, row in value.items()
            for item in [str(key), *_dependency_strings(row)]
        ]
    return []


def test_proofir_kernel_has_no_quux_runtime_or_build_dependency() -> None:
    root = Path(__file__).parents[1]
    python_paths = [
        *sorted((root / "src").rglob("*.py")),
        *sorted((root / "tests").rglob("*.py")),
        *sorted((root / "scripts").rglob("*.py")),
    ]
    imported = {
        (path.relative_to(root).as_posix(), module)
        for path in python_paths
        for module in _python_imports(path)
        if module.casefold() == "quux" or module.casefold().startswith("quux.")
    }
    assert imported == set()

    package = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package_contract = {
        "build-system": package.get("build-system", {}),
        "dependencies": package.get("project", {}).get("dependencies", []),
        "optional-dependencies": package.get("project", {}).get(
            "optional-dependencies", {}
        ),
    }
    assert all(
        "quux" not in value.casefold()
        for value in _dependency_strings(package_contract)
    )


def test_rust_core_has_no_quux_manifest_path_or_build_script_dependency() -> None:
    root = Path(__file__).parents[1]
    rust = root / "rust"
    manifests = [*rust.rglob("Cargo.toml"), rust / "Cargo.lock"]
    assert all(
        "quux" not in path.read_text(encoding="utf-8").casefold()
        for path in manifests
        if path.is_file()
    )

    sibling = ".." + "/quux"
    build_sources = [*rust.rglob("build.rs"), *rust.rglob("*.rs")]
    assert all(
        sibling not in path.read_text(encoding="utf-8").casefold()
        for path in build_sources
        if "target" not in path.parts
    )
