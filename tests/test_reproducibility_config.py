from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]


def check_ignore(tmp_path: Path, path: str) -> bool:
    repository = tmp_path / "ignore-policy"
    repository.mkdir(exist_ok=True)
    (repository / ".gitignore").write_text(
        (REPO_ROOT / ".gitignore").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=repository,
        check=False,
    )
    assert result.returncode in {0, 1}
    return result.returncode == 0


def test_ignore_policy_keeps_project_metadata_trackable(tmp_path: Path) -> None:
    assert not check_ignore(tmp_path, ".github/workflows/ci.yml")
    assert not check_ignore(tmp_path, "uv.lock")
    assert not check_ignore(tmp_path, ".python-version")
    assert not check_ignore(
        tmp_path,
        "openspec/changes/ladon-clean-checkout-and-ci/.openspec.yaml"
    )


def test_ignore_policy_excludes_only_named_local_artifacts(tmp_path: Path) -> None:
    assert check_ignore(tmp_path, ".venv/lib/python/site.py")
    assert check_ignore(tmp_path, "src/ladon/__pycache__/cli.cpython-311.pyc")
    assert check_ignore(tmp_path, "dist/ladon.whl")
    assert check_ignore(tmp_path, "temp/local-report.json")
    assert check_ignore(tmp_path, ".codex/skills/host-owned/SKILL.md")


def test_pytest_discovery_is_explicit_and_excludes_fixture_data() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_options = project["tool"]["pytest"]["ini_options"]

    assert pytest_options["testpaths"] == ["tests"]
    assert pytest_options["python_files"] == ["test_*.py"]
    assert set(pytest_options["norecursedirs"]) >= {
        ".codex",
        "temp",
        "tests/fixtures",
    }


def test_maintained_collection_is_nonempty_and_excludes_inert_fixture_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "tests/test_reproducibility_config.py" in result.stdout
    assert "tests/fixtures/" not in result.stdout


def test_supported_python_metadata_is_a_finite_two_minor_set() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    assert project["requires-python"] == ">=3.11,<3.13"
    python_classifiers = {
        value
        for value in project["classifiers"]
        if value.startswith("Programming Language :: Python :: 3.")
    }
    assert python_classifiers == {
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    }


def test_required_ci_matches_support_and_gate_contracts() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    required = (
        'python-version: ["3.11", "3.12"]',
        "scripts/clean_checkout_gate.py --candidate HEAD",
        "scripts/installed_distribution_smoke.py",
        "scripts/lean_integration_gate.py",
        "--required",
        "openspec validate --all --strict --no-interactive",
        "scripts/ladon_openspec_backlog.py",
        "scripts/ladon_openspec_hygiene.py",
    )
    assert all(marker in workflow for marker in required)

    normalized = workflow.lower().replace("use-mathlib-cache: false", "")
    forbidden = (
        'python-version: "3.13"',
        "publish",
        "/home/",
        "matrix-factorization",
        "mathlib",
        "quux",
    )
    assert all(marker not in normalized for marker in forbidden)


def test_isolated_build_backend_is_exactly_constrained() -> None:
    constraints = (REPO_ROOT / "build-constraints.txt").read_text(encoding="utf-8")

    assert constraints.splitlines()[-1] == "uv_build==0.10.2"


def test_reproducibility_document_records_external_boundaries() -> None:
    text = (REPO_ROOT / "docs" / "REPRODUCIBILITY.md").read_text(encoding="utf-8")

    assert ".codex/**" in text
    assert "tests/fixtures/**" in text
    assert "temp/**" in text
    assert "Quux, matrix-factorization, mathlib" in text
    assert "publication blocked—no license granted" in text
