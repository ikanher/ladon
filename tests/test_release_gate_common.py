from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

from release_gate_candidate import (
    collection_comparison_root,
    materialize_candidate,
)
from release_gate_distribution import parse_package_resource
from release_gate_runtime import (
    absolute_maintainer_paths,
    assert_lock_unchanged,
    prepare_candidate_lean_fixture,
    pytest_node_ids,
    sanitized_environment,
)
from release_gate_types import GateError


def load_common():
    return SimpleNamespace(
        GateError=GateError,
        absolute_maintainer_paths=absolute_maintainer_paths,
        assert_lock_unchanged=assert_lock_unchanged,
        collection_comparison_root=collection_comparison_root,
        materialize_candidate=materialize_candidate,
        parse_package_resource=parse_package_resource,
        pytest_node_ids=pytest_node_ids,
        sanitized_environment=sanitized_environment,
    )


def test_clean_candidate_prepares_only_its_own_pinned_lean_fixture(tmp_path, monkeypatch) -> None:
    import release_gate_runtime

    fixture = tmp_path / "tests" / "fixtures" / "lean_integration"
    fixture.mkdir(parents=True)
    (fixture / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    calls = []
    environment = {"PATH": "/selected-toolchain"}
    monkeypatch.setattr(release_gate_runtime.shutil, "which", lambda name, path: "/selected-toolchain/lake")
    monkeypatch.setattr(release_gate_runtime, "run_checked", lambda command, **kwargs: calls.append((command, kwargs)))
    prepare_candidate_lean_fixture(tmp_path, environment)
    assert calls == [(["/selected-toolchain/lake", "build"], {"cwd": fixture, "environment": environment})]


def test_clean_candidate_without_lake_keeps_python_only_gate(tmp_path, monkeypatch) -> None:
    import release_gate_runtime

    monkeypatch.setattr(release_gate_runtime.shutil, "which", lambda name, path: None)
    prepare_candidate_lean_fixture(tmp_path, {"PATH": "/without-lean"})
    assert not list(tmp_path.iterdir())


def test_sanitized_home_retains_explicit_rust_toolchain_and_cache(tmp_path, monkeypatch) -> None:
    from release_gate_runtime import preserve_rust_toolchain_locations

    original_home = tmp_path / "original-home"
    original_home.mkdir()
    for directory in (".cargo", ".rustup"):
        (original_home / directory).mkdir()
    environment = {"HOME": str(tmp_path / "isolated-home")}
    preserve_rust_toolchain_locations({"HOME": str(original_home)}, environment)
    assert environment == {
        "HOME": str(tmp_path / "isolated-home"),
        "CARGO_HOME": str(original_home / ".cargo"),
        "RUSTUP_HOME": str(original_home / ".rustup"),
    }
    preserve_rust_toolchain_locations({"RUSTUP_HOME": "/configured-rust", "CARGO_HOME": "/configured-cargo"}, environment)
    assert environment["RUSTUP_HOME"] == "/configured-rust"
    assert environment["CARGO_HOME"] == "/configured-cargo"


def initialize_candidate_repo(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    for directory in ("scripts", "src", "tests"):
        (repository / directory).mkdir()
        (repository / directory / "tracked.txt").write_text(
            f"{directory}\n",
            encoding="utf-8",
        )
    for name in ("README.md", "build-constraints.txt", "pyproject.toml", "uv.lock"):
        (repository / name).write_text(f"{name}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Gate Test",
            "-c",
            "user.email=gate@example.invalid",
            "commit",
            "-qm",
            "candidate",
        ],
        cwd=repository,
        check=True,
    )
    return repository


def test_materialize_worktree_uses_current_tracked_contents(tmp_path: Path) -> None:
    common = load_common()
    repository = initialize_candidate_repo(tmp_path)
    tracked = repository / "src" / "tracked.txt"
    tracked.write_text("modified\n", encoding="utf-8")

    with common.materialize_candidate("worktree", repository) as candidate:
        assert candidate.kind == "worktree"
        assert (candidate.root / "src" / "tracked.txt").read_text(
            encoding="utf-8"
        ) == "modified\n"
        assert candidate.root.parent != repository


def test_worktree_rejects_untracked_required_input(tmp_path: Path) -> None:
    common = load_common()
    repository = initialize_candidate_repo(tmp_path)
    (repository / "tests" / "test_hidden.py").write_text(
        "def test_hidden(): pass\n",
        encoding="utf-8",
    )

    with pytest.raises(
        common.GateError, match="untracked required candidate inputs"
    ), common.materialize_candidate("worktree", repository):
            pass


@pytest.mark.parametrize('relative', [
    'skills/ladon/SKILL.md', 'docs/hidden.md', 'src/ladon/schemas/hidden.json',
    'scripts/hidden_helper.py', 'tests/fixtures/hidden.json',
], ids=['skill', 'documentation', 'schema', 'helper', 'fixture'])
def test_worktree_rejects_every_maintained_input_root(tmp_path: Path, relative: str) -> None:
    repository = initialize_candidate_repo(tmp_path)
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('required input\n')
    with pytest.raises(GateError, match='untracked required candidate inputs'), materialize_candidate('worktree', repository):
        pass


def test_treeish_rejects_dirty_stale_head(tmp_path: Path) -> None:
    common = load_common()
    repository = initialize_candidate_repo(tmp_path)
    (repository / "README.md").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(common.GateError, match="stale HEAD"), common.materialize_candidate(
        "HEAD", repository
    ):
            pass


def test_treeish_materializes_clean_commit(tmp_path: Path) -> None:
    common = load_common()
    repository = initialize_candidate_repo(tmp_path)

    with common.materialize_candidate("HEAD", repository) as candidate:
        assert candidate.kind == "treeish"
        assert (candidate.root / "README.md").read_text(encoding="utf-8") == (
            "README.md\n"
        )


def test_directory_candidate_omits_local_state(tmp_path: Path) -> None:
    common = load_common()
    repository = initialize_candidate_repo(tmp_path)
    (repository / "temp").mkdir()
    (repository / "temp" / "local.txt").write_text("local\n", encoding="utf-8")
    (repository / ".codex").mkdir()
    (repository / ".codex" / "host.txt").write_text("host\n", encoding="utf-8")
    (repository / "tests" / ".lake").mkdir()
    (repository / "tests" / ".lake" / "stale.olean").write_text(
        "stale\n",
        encoding="utf-8",
    )

    with common.materialize_candidate(str(repository), repository) as candidate:
        assert candidate.kind == "directory"
        assert not (candidate.root / "temp").exists()
        assert not (candidate.root / ".codex").exists()
        assert not (candidate.root / "tests" / ".lake").exists()


def test_collection_comparison_root_follows_explicit_candidate_kind(
    tmp_path: Path,
) -> None:
    common = load_common()
    repository = tmp_path / "repository"
    directory = tmp_path / "selected"
    repository.mkdir()
    directory.mkdir()

    assert common.collection_comparison_root(
        "worktree",
        repository,
        "worktree",
    ) == repository.resolve()
    assert common.collection_comparison_root(
        str(directory),
        repository,
        "directory",
    ) == directory.resolve()
    assert common.collection_comparison_root(
        "HEAD~1",
        repository,
        "treeish",
    ) is None


@pytest.mark.parametrize(
    ("candidate_kind", "candidate_name", "comparison_name"),
    [
        ("worktree", "worktree", "live"),
        ("directory", "selected", "selected"),
        ("treeish", "HEAD~1", None),
    ],
)
def test_clean_collection_parity_uses_only_selected_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    candidate_kind: str,
    candidate_name: str,
    comparison_name: str | None,
) -> None:
    import clean_checkout_gate

    source_root = tmp_path / "live"
    selected = source_root / "selected"
    materialized = tmp_path / "materialized"
    source_root.mkdir()
    selected.mkdir()
    materialized.mkdir()
    candidate = str(selected) if candidate_kind == "directory" else candidate_name
    source_calls: list[Path] = []
    candidate_calls: list[Path] = []
    parity_calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def collect_source(path: Path) -> tuple[str, ...]:
        source_calls.append(path)
        return ("tests/test_selected.py::test_selected",)

    def collect_candidate(path: Path, _environment) -> tuple[str, ...]:
        candidate_calls.append(path)
        return ("tests/test_selected.py::test_selected",)

    monkeypatch.setattr(clean_checkout_gate, "collect_live_node_ids", collect_source)
    monkeypatch.setattr(
        clean_checkout_gate,
        "collect_candidate_node_ids",
        collect_candidate,
    )
    monkeypatch.setattr(
        clean_checkout_gate,
        "assert_collection_parity",
        lambda left, right: parity_calls.append((left, right)),
    )

    clean_checkout_gate.assert_selected_collection_parity(
        candidate,
        source_root,
        candidate_kind,
        materialized,
        {"CI": "1"},
    )

    assert candidate_calls == [materialized]
    expected_root = {
        "live": source_root.resolve(),
        "selected": selected.resolve(),
        None: None,
    }[comparison_name]
    assert source_calls == ([] if expected_root is None else [expected_root])
    assert len(parity_calls) == (0 if expected_root is None else 1)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "ladon:lean/ladon_parser_helper.lean",
            ("ladon", "lean/ladon_parser_helper.lean"),
        ),
        ("ladon.schemas:v2.json", ("ladon.schemas", "v2.json")),
    ],
)
def test_parse_package_resource(value: str, expected: tuple[str, str]) -> None:
    common = load_common()

    assert common.parse_package_resource(value) == expected


@pytest.mark.parametrize(
    "value",
    ["ladon", ":file.json", "ladon:", "ladon:/absolute", "ladon:../escape"],
)
def test_parse_package_resource_rejects_invalid_values(value: str) -> None:
    common = load_common()

    with pytest.raises(common.GateError, match="invalid package resource"):
        common.parse_package_resource(value)


def test_absolute_path_audit_is_scoped_to_required_surfaces(tmp_path: Path) -> None:
    common = load_common()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs" / "REQUIRED.md").write_text(
        "Run /home/carol/ladon/check.py\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "installed.py").write_text(
        'ROOT = "/home/alice/project"\n',
        encoding="utf-8",
    )
    (tmp_path / "tests" / "fixture.py").write_text(
        'ROOT = "/home/bob/fixture"\n',
        encoding="utf-8",
    )

    findings = common.absolute_maintainer_paths(tmp_path)

    assert len(findings) == 2
    assert findings[0].startswith("docs/REQUIRED.md:1:")
    assert findings[1].startswith("src/installed.py:1:")


def test_sanitized_environment_removes_python_and_virtualenv_state(
    monkeypatch, tmp_path: Path
) -> None:
    common = load_common()
    monkeypatch.setenv("PYTHONPATH", "/host/python")
    monkeypatch.setenv("VIRTUAL_ENV", "/host/venv")
    candidate = tmp_path / "candidate"
    candidate.mkdir()

    environment = common.sanitized_environment(tmp_path / "runtime", candidate)

    assert "PYTHONPATH" not in environment
    assert "VIRTUAL_ENV" not in environment
    assert environment["HOME"].startswith(str(tmp_path / "runtime"))
    assert environment["UV_PROJECT_ENVIRONMENT"].startswith(
        str(tmp_path / "runtime")
    )


def test_pytest_node_ids_ignore_summary_and_sort() -> None:
    common = load_common()
    output = "tests/test_z.py::test_z\ntests/test_a.py::test_a\n\n2 tests collected in 0.01s"

    assert common.pytest_node_ids(output) == (
        "tests/test_a.py::test_a",
        "tests/test_z.py::test_z",
    )


def test_lock_immutability_failure_names_digest_change(tmp_path: Path) -> None:
    common = load_common()
    lock = tmp_path / "uv.lock"
    lock.write_text("before\n", encoding="utf-8")
    expected = hashlib.sha256(lock.read_bytes()).hexdigest()
    lock.write_text("after\n", encoding="utf-8")

    with pytest.raises(common.GateError, match="uv.lock changed"):
        common.assert_lock_unchanged(tmp_path, expected)


def test_candidate_scripts_require_explicit_candidate() -> None:
    for script in (
        "clean_checkout_gate.py",
        "installed_distribution_smoke.py",
        "lean_integration_gate.py",
    ):
        result = subprocess.run(
            [os.fspath(Path(os.sys.executable)), f"scripts/{script}"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 2
        assert "--candidate" in result.stderr


def test_full_clean_gate_runs_one_installed_resource_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import clean_checkout_gate

    candidate_root = tmp_path / "candidate"
    runtime_root = tmp_path / "runtime"
    candidate_root.mkdir()
    runtime_root.mkdir()
    installed_resources: list[tuple[str, ...]] = []

    def noop(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(clean_checkout_gate, "project_root", lambda: tmp_path)
    monkeypatch.setattr(
        clean_checkout_gate,
        "materialize_candidate",
        lambda *_args: nullcontext(
            SimpleNamespace(root=candidate_root, kind="directory")
        ),
    )
    monkeypatch.setattr(
        clean_checkout_gate,
        "runtime_directory",
        lambda *_args: nullcontext(str(runtime_root)),
    )
    monkeypatch.setattr(clean_checkout_gate, "sanitized_environment", noop)
    monkeypatch.setattr(clean_checkout_gate, "prepare_locked_environment", noop)
    monkeypatch.setattr(clean_checkout_gate, "assert_no_absolute_maintainer_paths", noop)
    monkeypatch.setattr(clean_checkout_gate, "collect_live_node_ids", noop)
    monkeypatch.setattr(clean_checkout_gate, "collect_candidate_node_ids", noop)
    monkeypatch.setattr(clean_checkout_gate, "assert_collection_parity", noop)
    monkeypatch.setattr(clean_checkout_gate, "run_candidate_quality", noop)
    monkeypatch.setattr(clean_checkout_gate, "build_distributions", noop)
    monkeypatch.setattr(clean_checkout_gate, "assert_lock_unchanged", noop)
    monkeypatch.setattr(
        clean_checkout_gate,
        "verify_requested_resources",
        lambda *_args: pytest.fail("full gate must not pre-install requested resources"),
    )
    monkeypatch.setattr(
        clean_checkout_gate,
        "run_installed_distribution_checks",
        lambda *_args: installed_resources.append(tuple(_args[-1])),
    )

    clean_checkout_gate.run_gate(
        str(candidate_root),
        baseline_only=False,
        resources=["ladon:schemas/report.json"],
    )

    assert installed_resources == [("ladon:schemas/report.json",)]


def test_installed_process_contract_runs_full_wheel_suite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import release_gate_distribution

    candidate_root = tmp_path / "candidate"
    contract = candidate_root / "tests" / "test_installed_cli_contract.py"
    contract.parent.mkdir(parents=True)
    contract.write_text("def test_placeholder(): pass\n", encoding="utf-8")
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    scripts = runtime_root / "installed" / "bin"
    installed = SimpleNamespace(
        python=scripts / "python",
        scripts=scripts,
    )
    calls: list[tuple[list[str], Path, dict[str, str]]] = []

    def record(command, *, cwd, environment, **_kwargs):
        calls.append((list(command), cwd, dict(environment)))

    monkeypatch.setattr(release_gate_distribution, "run_checked", record)
    monkeypatch.setattr(
        release_gate_distribution,
        "uv_executable",
        lambda: "/tool/uv",
    )

    release_gate_distribution.assert_installed_process_contracts(
        candidate_root,
        installed,
        runtime_root,
        {
            "PATH": "/usr/bin",
            "PYTHONHOME": "/host/python",
            "PYTHONPATH": "/host/source",
        },
    )

    assert [call[0][1:3] for call in calls[:2]] == [
        ["export", "--locked"],
        ["pip", "install"],
    ]
    command, cwd, environment = calls[-1]
    assert command == [
        str(installed.python),
        "-m",
        "pytest",
        "-q",
        "--rootdir",
        str(candidate_root),
        str(contract),
    ]
    assert cwd == runtime_root
    assert environment["LADON_CONSOLE"] == str(scripts / "ladon")
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert "PYTHONHOME" not in environment
    assert "PYTHONPATH" not in environment
