from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.theorem_capsule_models import (
    CapsuleInvocationError,
    CapsuleOperationalError,
    TheoremPlan,
)
from ladon.theorem_capsule_planning import (
    plan_theorem_capsule,
    semantic_components,
)
from ladon.theorem_cli import theorem_main

FIXTURE = Path(__file__).parent / "fixtures" / "theorem_capsule"


@pytest.fixture
def compiled_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    result = subprocess.run(
        ["lake", "build"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(result.stderr or result.stdout)
    return root


def test_plan_is_exact_complete_and_deterministic(
    compiled_repository: Path,
) -> None:
    first = plan_theorem_capsule(
        compiled_repository,
        "CapsuleFixture.chosen",
    )
    second = plan_theorem_capsule(
        compiled_repository,
        "CapsuleFixture.chosen",
    )

    assert first.to_bytes() == second.to_bytes()
    assert first.eligible is True
    assert first.target["module"] == "CapsuleFixture"
    assert first.target["path"] == "CapsuleFixture.lean"
    assert_plan_graphs(first)
    assert_plan_inputs(first)

    loaded = TheoremPlan.from_payload(json.loads(first.to_bytes()))
    assert loaded.identity == first.identity


def assert_plan_graphs(plan: TheoremPlan) -> None:
    semantic = plan.payload["semanticGraph"]
    build = plan.payload["buildGraph"]

    assert semantic["status"] == "complete"
    assert semantic["nodeCount"] > 64
    assert semantic["stronglyConnectedComponents"]
    assert any(node["compilerGenerated"] for node in semantic["nodes"])
    assert build["moduleDagFingerprint"].startswith("sha256:")
    assert {row["module"] for row in build["modules"]} == {
        "CapsuleFixture",
        "CapsuleFixture.Base",
        "CapsuleFixture.Large",
    }


def assert_plan_inputs(plan: TheoremPlan) -> None:
    assert plan.repository["sourceInventoryFingerprint"].startswith("sha256:")
    assert {row["role"] for row in plan.files} == {
        "target_prefix",
        "module_import",
    }


def test_semantic_cycles_are_condensed_deterministically() -> None:
    nodes = [{"name": "Cycle.a"}, {"name": "Cycle.b"}]
    edges = [
        {"source": "Cycle.a", "target": "Cycle.b"},
        {"source": "Cycle.b", "target": "Cycle.a"},
    ]

    assert semantic_components(nodes, edges) == (
        {
            "component": ("Cycle.a", "Cycle.b"),
            "members": ["Cycle.a", "Cycle.b"],
            "cyclic": True,
        },
    )


def test_plan_prefix_ends_before_later_theorem(
    compiled_repository: Path,
) -> None:
    plan = plan_theorem_capsule(
        compiled_repository,
        "CapsuleFixture.chosen",
    )
    source = (compiled_repository / "CapsuleFixture.lean").read_bytes()
    prefix = source[: int(plan.target["prefixEndOffset"])]

    assert b"local notation" in prefix
    assert b"theorem chosen" in prefix
    assert b"theorem later" not in prefix


def test_plan_rejects_short_and_wrong_kind_names(
    compiled_repository: Path,
) -> None:
    with pytest.raises(CapsuleInvocationError, match="fully qualified"):
        plan_theorem_capsule(compiled_repository, "chosen")
    with pytest.raises(CapsuleInvocationError, match="extractable theorem"):
        plan_theorem_capsule(compiled_repository, "CapsuleFixture.base")


def test_plan_rejects_ambiguous_exact_lexical_candidates(
    compiled_repository: Path,
) -> None:
    duplicate = compiled_repository / "CapsuleFixture" / "Duplicate.lean"
    duplicate.write_text(
        "namespace CapsuleFixture\n"
        "theorem chosen : True := by trivial\n"
        "end CapsuleFixture\n",
        encoding="utf-8",
    )

    with pytest.raises(CapsuleInvocationError, match="ambiguous lexical"):
        plan_theorem_capsule(compiled_repository, "CapsuleFixture.chosen")


def test_plan_process_tree_rss_limit_fails_closed(
    compiled_repository: Path,
) -> None:
    if not Path("/proc").is_dir():
        pytest.skip("RSS enforcement needs /proc")

    with pytest.raises(CapsuleOperationalError, match="RSS limit"):
        plan_theorem_capsule(
            compiled_repository,
            "CapsuleFixture.chosen",
            max_rss_bytes=1024 * 1024,
        )


def test_plan_marks_native_lake_facets_ineligible(
    compiled_repository: Path,
) -> None:
    lakefile = compiled_repository / "lakefile.toml"
    lakefile.write_text(
        lakefile.read_text(encoding="utf-8")
        + '\nmoreLinkArgs = ["-unsupported-native-link"]\n',
        encoding="utf-8",
    )

    plan = plan_theorem_capsule(
        compiled_repository,
        "CapsuleFixture.chosen",
    )

    assert plan.eligible is False
    assert {
        row["kind"] for row in plan.payload["unsupportedFacets"]
    } == {"native_or_custom_lake_facet"}


def test_plan_cli_emits_one_json_document(
    compiled_repository: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = theorem_main(
        [
            "plan",
            "CapsuleFixture.chosen",
            "--repo-root",
            str(compiled_repository),
            "--format",
            "json",
            "--output",
            "-",
        ]
    )
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    assert json.loads(captured.out)["target"]["name"] == "CapsuleFixture.chosen"


def test_plan_cli_rejects_output_inside_target_without_writing(
    compiled_repository: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = compiled_repository / "plan.json"

    status = theorem_main(
        [
            "plan",
            "CapsuleFixture.chosen",
            "--repo-root",
            str(compiled_repository),
            "--output",
            str(output),
        ]
    )

    assert status != 0
    assert output.exists() is False
    assert "outside" in capsys.readouterr().err


def test_theorem_help_is_caller_neutral(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        theorem_main(["--help"])
    output = capsys.readouterr().out

    assert exit_info.value.code == 0
    assert "plan" in output
    assert "materialize" in output
    assert "replay" in output
    assert "LLM" not in output
