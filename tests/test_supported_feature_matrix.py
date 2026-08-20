from __future__ import annotations

import importlib.util
from pathlib import Path


def _generator():
    path = Path(__file__).parents[1] / "scripts/generate_supported_feature_matrix.py"
    spec = importlib.util.spec_from_file_location("supported_feature_matrix", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_matrix_has_exactly_three_core_workflows_and_collectable_nodes() -> None:
    generator = _generator()
    core = [feature for feature in generator.FEATURES if feature["tier"] == "core"]
    assert [feature["id"] for feature in core] == [
        "architecture-review",
        "semantic-declaration-search",
        "evidence-and-lineage-inspection",
    ]
    root = Path(__file__).parents[1]
    for feature in generator.FEATURES:
        assert feature["readiness"] in {"experimental", "contract-supported", "externally-evaluated", "release-qualified"}
        assert feature["tests"]
        for node in feature["tests"]:
            relative, test_name = node.split("::", 1)
            source = root.joinpath(relative).read_text(encoding="utf-8")
            assert f"def {test_name}(" in source


def test_committed_matrix_matches_generator() -> None:
    generator = _generator()
    root = Path(__file__).parents[1]
    assert (root / "docs/SUPPORTED_FEATURE_MATRIX.json").read_text(
        encoding="utf-8"
    ) == generator.render_json()
    assert (root / "docs/SUPPORTED_FEATURE_MATRIX.md").read_text(
        encoding="utf-8"
    ) == generator.render_markdown()
