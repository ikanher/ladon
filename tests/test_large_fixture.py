from __future__ import annotations

import json
from pathlib import Path

from ladon.extraction import discover_modules
from ladon.large_fixture import (
    LargeFixtureManifest,
    distributed_counts,
    fixture_line_budgets,
    generate_large_fixture,
)

MANIFEST = (
    Path(__file__).parent
    / "fixtures"
    / "large_inventory"
    / "manifest-v1.json"
)


def test_required_manifest_preregisters_large_repository_contract() -> None:
    manifest = LargeFixtureManifest.from_path(MANIFEST)

    assert manifest.module_count >= 2600
    assert manifest.source_line_count >= 1_500_000
    assert manifest.declaration_count >= 100_000


def test_small_fixture_generation_is_deterministic_and_discoverable(
    tmp_path: Path,
) -> None:
    manifest = LargeFixtureManifest.from_path(MANIFEST).scaled(
        module_count=12,
        source_line_count=240,
        declaration_count=60,
        generated_module_count=4,
        facade_import_count=5,
    )
    first = tmp_path / "first"
    second = tmp_path / "second"

    left = generate_large_fixture(first, manifest)
    right = generate_large_fixture(second, manifest)
    discovery = discover_modules(first, "Fixture")

    assert left == right
    assert left["moduleCount"] == 12
    assert len(left["files"]) == 12
    assert len(discovery.modules) == 12
    assert sum(module.line_count for module in discovery.modules.values()) == 240
    assert sum(len(module.declarations) for module in discovery.modules.values()) == 60
    assert json.loads(
        first.joinpath("ladon-large-fixture.json").read_text(encoding="utf-8")
    ) == left


def test_distributed_counts_preserve_exact_total() -> None:
    counts = distributed_counts(17, 5)

    assert counts == (4, 4, 3, 3, 3)
    assert sum(counts) == 17


def test_line_budgets_reserve_a_broad_facade_before_filler() -> None:
    modules = ("Fixture", "Fixture.Core", "Fixture.Owner")
    budgets = fixture_line_budgets(
        modules,
        declaration_budgets=(2, 2),
        source_line_count=20,
        facade_import_count=2,
    )

    assert budgets[0] >= 2
    assert budgets[1] >= 3
    assert budgets[2] >= 3
    assert sum(budgets) == 20
