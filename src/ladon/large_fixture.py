"""Deterministic target-neutral Lean fixture generation for scale gates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


LARGE_FIXTURE_SCHEMA = "ladon-large-lean-fixture-v1"
GENERATOR_VERSION = "ladon-large-fixture-generator-v1"


@dataclass(frozen=True)
class LargeFixtureManifest:
    """Versioned cardinalities and seed for one generated Lean repository."""

    module_count: int
    source_line_count: int
    declaration_count: int
    generated_module_count: int
    facade_import_count: int
    seed: int = 1729
    schema: str = LARGE_FIXTURE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LARGE_FIXTURE_SCHEMA:
            raise ValueError(f"unsupported large fixture schema: {self.schema}")
        if self.module_count < 3:
            raise ValueError("large fixture requires at least three modules")
        if self.source_line_count < self.module_count:
            raise ValueError("source lines must cover every generated module")
        if self.declaration_count < 0:
            raise ValueError("declaration count must be non-negative")
        if not 0 <= self.generated_module_count < self.module_count:
            raise ValueError("generated module count must fit the inventory")
        if not 1 <= self.facade_import_count < self.module_count:
            raise ValueError("facade import count must fit the inventory")
        minimum = self.declaration_count + self.module_count
        if self.source_line_count < minimum:
            raise ValueError(
                "source lines must cover declarations and one line per module"
            )

    @classmethod
    def from_path(cls, path: Path) -> LargeFixtureManifest:
        """Load and validate a tracked fixture manifest."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("large fixture manifest must be a JSON object")
        return cls(
            schema=str(payload.get("schema", "")),
            module_count=int(payload["moduleCount"]),
            source_line_count=int(payload["sourceLineCount"]),
            declaration_count=int(payload["declarationCount"]),
            generated_module_count=int(payload["generatedModuleCount"]),
            facade_import_count=int(payload["facadeImportCount"]),
            seed=int(payload["seed"]),
        )

    def scaled(
        self,
        *,
        module_count: int,
        source_line_count: int,
        declaration_count: int,
        generated_module_count: int,
        facade_import_count: int,
    ) -> LargeFixtureManifest:
        """Return a smaller deterministic manifest for focused tests."""

        return replace(
            self,
            module_count=module_count,
            source_line_count=source_line_count,
            declaration_count=declaration_count,
            generated_module_count=generated_module_count,
            facade_import_count=facade_import_count,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the stable manifest shape included in generated evidence."""

        return {
            "schema": self.schema,
            "generatorVersion": GENERATOR_VERSION,
            "moduleCount": self.module_count,
            "sourceLineCount": self.source_line_count,
            "declarationCount": self.declaration_count,
            "generatedModuleCount": self.generated_module_count,
            "facadeImportCount": self.facade_import_count,
            "seed": self.seed,
        }


def generate_large_fixture(
    destination: Path,
    manifest: LargeFixtureManifest,
) -> dict[str, Any]:
    """Generate one deterministic Lean repository and return its inventory."""

    destination.mkdir(parents=True, exist_ok=True)
    module_names = fixture_module_names(manifest)
    declaration_budgets = distributed_counts(
        manifest.declaration_count,
        manifest.module_count - 1,
    )
    line_budgets = fixture_line_budgets(
        module_names,
        declaration_budgets=declaration_budgets,
        source_line_count=manifest.source_line_count,
        facade_import_count=manifest.facade_import_count,
    )
    hashes: dict[str, str] = {}
    for index, module in enumerate(module_names):
        declarations = 0 if index == 0 else declaration_budgets[index - 1]
        lines = fixture_module_lines(
            module_names,
            index=index,
            line_budget=line_budgets[index],
            declaration_budget=declarations,
            facade_import_count=manifest.facade_import_count,
            seed=manifest.seed,
        )
        path = destination / module_path(module)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
        hashes[path.relative_to(destination).as_posix()] = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()
    inventory = generated_inventory(manifest, hashes)
    destination.joinpath("ladon-large-fixture.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return inventory


def fixture_line_budgets(
    modules: tuple[str, ...],
    *,
    declaration_budgets: tuple[int, ...],
    source_line_count: int,
    facade_import_count: int,
) -> tuple[int, ...]:
    """Reserve each module's imports/declarations before distributing filler."""

    minimums = tuple(
        len(fixture_header(modules, index, facade_import_count))
        + (0 if index == 0 else declaration_budgets[index - 1])
        for index in range(len(modules))
    )
    required = sum(minimums)
    if required > source_line_count:
        raise ValueError(
            "source-line budget cannot cover fixture imports and declarations"
        )
    filler = distributed_counts(
        source_line_count - required,
        len(modules),
    )
    return tuple(
        minimum + extra
        for minimum, extra in zip(minimums, filler)
    )


def fixture_module_names(manifest: LargeFixtureManifest) -> tuple[str, ...]:
    """Return stable facade, core, generated, deep, and owner module names."""

    names = ["Fixture", "Fixture.Core"]
    generated = min(
        manifest.generated_module_count,
        manifest.module_count - len(names),
    )
    names.extend(
        f"Fixture.Generated.Row{index:05d}"
        for index in range(generated)
    )
    remaining = manifest.module_count - len(names)
    deep = min(100, remaining // 5)
    names.extend(
        f"Fixture.Deep.Level1.Level2.Module{index:05d}"
        for index in range(deep)
    )
    names.extend(
        f"Fixture.Owner.Module{index:05d}"
        for index in range(manifest.module_count - len(names))
    )
    return tuple(names)


def fixture_module_lines(
    modules: tuple[str, ...],
    *,
    index: int,
    line_budget: int,
    declaration_budget: int,
    facade_import_count: int,
    seed: int,
) -> list[str]:
    """Build exactly one module's assigned line budget."""

    lines = fixture_header(modules, index, facade_import_count)
    lines.extend(
        f"def value_{index:05d}_{offset:05d} : Nat := {seed + index + offset}"
        for offset in range(declaration_budget)
    )
    if len(lines) > line_budget:
        raise ValueError(
            f"line budget {line_budget} is too small for module {modules[index]}"
        )
    lines.extend(
        f"-- deterministic filler {seed}:{index}:{offset}"
        for offset in range(line_budget - len(lines))
    )
    return lines


def fixture_header(
    modules: tuple[str, ...],
    index: int,
    facade_import_count: int,
) -> list[str]:
    """Return imports and generated provenance for one fixture module."""

    if index == 0:
        return [
            f"import {module}"
            for module in modules[1:1 + facade_import_count]
        ]
    lines = ["import Fixture.Core"] if index > 1 else ["-- shared core owner"]
    if ".Generated." in modules[index]:
        lines.append("-- Code generated by ladon large fixture generator; DO NOT EDIT.")
    return lines


def module_path(module: str) -> Path:
    """Map a conventional Lean module name to its repository-relative path."""

    return Path(*module.split(".")).with_suffix(".lean")


def distributed_counts(total: int, buckets: int) -> tuple[int, ...]:
    """Distribute an exact non-negative total deterministically."""

    quotient, remainder = divmod(total, buckets)
    return tuple(
        quotient + int(index < remainder)
        for index in range(buckets)
    )


def generated_inventory(
    manifest: LargeFixtureManifest,
    hashes: dict[str, str],
) -> dict[str, Any]:
    """Return deterministic generation evidence without host-specific paths."""

    digest_input = "\n".join(
        f"{path}\0{digest}"
        for path, digest in sorted(hashes.items())
    )
    return {
        **manifest.to_dict(),
        "contentFingerprint": hashlib.sha256(
            digest_input.encode("utf-8")
        ).hexdigest(),
        "files": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(hashes.items())
        ],
    }
