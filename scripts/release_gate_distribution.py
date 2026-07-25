"""Constrained package build, archive, install, and smoke primitives."""

from __future__ import annotations

import json
import os
import sys
import tarfile
import tomllib
import zipfile
from collections.abc import Mapping, Sequence
from email.parser import BytesParser
from pathlib import Path

from release_gate_runtime import run_checked, uv_executable
from release_gate_types import (
    DistributionArtifacts,
    GateError,
    InstalledEnvironment,
)


def build_distributions(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> DistributionArtifacts:
    """Build one constrained sdist and wheel outside the candidate."""

    output = runtime_root / "dist"
    run_checked(
        [
            uv_executable(),
            "build",
            "--force-pep517",
            "--build-constraints",
            str(candidate_root / "build-constraints.txt"),
            "--out-dir",
            str(output),
            "--clear",
            ".",
        ],
        cwd=candidate_root,
        environment=environment,
    )
    sdists = sorted(output.glob("*.tar.gz"))
    wheels = sorted(output.glob("*.whl"))
    if len(sdists) != 1 or len(wheels) != 1:
        raise GateError(
            f"expected one sdist and one wheel, found {len(sdists)} and {len(wheels)}"
        )
    artifacts = DistributionArtifacts(sdist=sdists[0], wheel=wheels[0])
    validate_distribution_metadata(candidate_root, artifacts)
    return artifacts


def project_metadata(candidate_root: Path) -> dict[str, object]:
    """Return the PEP 621 project table for a candidate."""

    document = tomllib.loads(
        (candidate_root / "pyproject.toml").read_text(encoding="utf-8")
    )
    project = document.get("project")
    if not isinstance(project, dict):
        raise GateError("pyproject.toml has no [project] table")
    return project


def wheel_metadata(artifacts: DistributionArtifacts) -> Mapping[str, str]:
    """Parse the wheel's core metadata."""

    with zipfile.ZipFile(artifacts.wheel) as wheel:
        corrupt = wheel.testzip()
        if corrupt is not None:
            raise GateError(f"wheel has a corrupt member: {corrupt}")
        metadata_names = [
            name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise GateError("wheel must contain exactly one METADATA file")
        return BytesParser().parsebytes(wheel.read(metadata_names[0]))


def validate_distribution_metadata(
    candidate_root: Path,
    artifacts: DistributionArtifacts,
) -> None:
    """Validate archive integrity and core metadata against pyproject."""

    project = project_metadata(candidate_root)
    metadata = wheel_metadata(artifacts)
    expected = {
        "Name": str(project["name"]),
        "Version": str(project["version"]),
    }
    mismatches = {
        key: {"expected": value, "actual": metadata.get(key)}
        for key, value in expected.items()
        if metadata.get(key) != value
    }
    expected_python = str(project["requires-python"]).replace(" ", "")
    actual_python = str(metadata.get("Requires-Python", "")).replace(" ", "")
    if actual_python != expected_python:
        mismatches["Requires-Python"] = {
            "expected": project["requires-python"],
            "actual": metadata.get("Requires-Python"),
        }
    if mismatches:
        raise GateError(f"wheel metadata mismatch: {json.dumps(mismatches)}")
    require_archive_members(artifacts)


def require_archive_members(artifacts: DistributionArtifacts) -> None:
    """Require package metadata and the Lean helper in both archive types."""

    with zipfile.ZipFile(artifacts.wheel) as wheel:
        wheel_names = set(wheel.namelist())
    if "ladon/lean/ladon_parser_helper.lean" not in wheel_names:
        raise GateError("wheel omits packaged Lean helper")
    with tarfile.open(artifacts.sdist) as sdist:
        sdist_names = set(sdist.getnames())
    required_suffixes = (
        "/pyproject.toml",
        "/README.md",
        "/src/ladon/lean/ladon_parser_helper.lean",
    )
    missing = [
        suffix
        for suffix in required_suffixes
        if not any(name.endswith(suffix) for name in sdist_names)
    ]
    if missing:
        raise GateError(f"sdist omits required members: {', '.join(missing)}")


def parse_package_resource(value: str) -> tuple[str, str]:
    """Parse ``package:relative/path`` and reject traversal."""

    package, separator, relative = value.partition(":")
    relative_path = Path(relative)
    if (
        not separator
        or not package
        or not relative
        or relative_path.is_absolute()
        or ".." in relative_path.parts
    ):
        raise GateError(
            f"invalid package resource {value!r}; expected package:relative/path"
        )
    return package, relative_path.as_posix()


def assert_resource_in_artifacts(
    resource: str,
    artifacts: DistributionArtifacts,
) -> None:
    """Require one logical resource in the sdist and wheel."""

    package, relative = parse_package_resource(resource)
    package_path = package.replace(".", "/")
    wheel_member = f"{package_path}/{relative}"
    with zipfile.ZipFile(artifacts.wheel) as wheel:
        if wheel_member not in wheel.namelist():
            raise GateError(f"wheel omits requested package resource: {resource}")
    sdist_suffix = f"/src/{package_path}/{relative}"
    with tarfile.open(artifacts.sdist) as sdist:
        if not any(name.endswith(sdist_suffix) for name in sdist.getnames()):
            raise GateError(f"sdist omits requested package resource: {resource}")


def virtual_environment_paths(root: Path) -> InstalledEnvironment:
    """Return platform-aware paths for one uv-created virtual environment."""

    scripts = root / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    return InstalledEnvironment(root=root, python=python, scripts=scripts)


def install_wheel(
    artifacts: DistributionArtifacts,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> InstalledEnvironment:
    """Install a wheel into a fresh, outside-repository virtual environment."""

    installed = virtual_environment_paths(runtime_root / "installed")
    uv = uv_executable()
    run_checked(
        [uv, "venv", "--python", sys.executable, str(installed.root)],
        cwd=runtime_root,
        environment=environment,
    )
    run_checked(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(installed.python),
            str(artifacts.wheel),
        ],
        cwd=runtime_root,
        environment=environment,
    )
    run_checked(
        [uv, "pip", "check", "--python", str(installed.python)],
        cwd=runtime_root,
        environment=environment,
    )
    return installed


def assert_installed_resource(
    installed: InstalledEnvironment,
    resource: str,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Require one package resource through importlib.resources after install."""

    package, relative = parse_package_resource(resource)
    code = (
        "from importlib import resources; import sys; "
        "path = resources.files(sys.argv[1]).joinpath(sys.argv[2]); "
        "assert path.is_file(), path; print(path)"
    )
    run_checked(
        [str(installed.python), "-c", code, package, relative],
        cwd=runtime_root,
        environment=environment,
    )


def project_scripts(candidate_root: Path) -> tuple[str, ...]:
    """Return every declared console script in stable order."""

    project = project_metadata(candidate_root)
    scripts = project.get("scripts")
    if not isinstance(scripts, dict) or not scripts:
        raise GateError("project declares no console scripts")
    return tuple(sorted(str(name) for name in scripts))


def executable_path(installed: InstalledEnvironment, name: str) -> Path:
    """Return one platform-aware console-script executable."""

    suffix = ".exe" if os.name == "nt" else ""
    return installed.scripts / f"{name}{suffix}"


def assert_installed_import_origin(
    installed: InstalledEnvironment,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Require Ladon and its Lean helper to resolve inside the isolated venv."""

    code = "\n".join(
        [
            "from importlib import resources",
            "from pathlib import Path",
            "import json",
            "import ladon",
            "import sys",
            "origin = Path(ladon.__file__).resolve()",
            "prefix = Path(sys.prefix).resolve()",
            "helper = resources.files('ladon').joinpath('lean', 'ladon_parser_helper.lean')",
            "assert origin.is_relative_to(prefix), (origin, prefix)",
            "assert helper.is_file(), helper",
            "print(json.dumps({'origin': str(origin), 'helper': str(helper)}))",
        ]
    )
    run_checked(
        [str(installed.python), "-c", code],
        cwd=runtime_root,
        environment=environment,
    )


def assert_console_script_help(
    candidate_root: Path,
    installed: InstalledEnvironment,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Run every declared installed console script's help path."""

    for name in project_scripts(candidate_root):
        executable = executable_path(installed, name)
        if not executable.is_file():
            raise GateError(f"installed console script is absent: {name}")
        run_checked(
            [str(executable), "--help"],
            cwd=runtime_root,
            environment=environment,
            capture_output=True,
        )


def assert_installed_process_contracts(
    candidate_root: Path,
    installed: InstalledEnvironment,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Run the complete installed CLI pytest contract against the wheel."""

    contract = candidate_root / "tests" / "test_installed_cli_contract.py"
    if not contract.is_file():
        raise GateError("candidate omits tests/test_installed_cli_contract.py")
    install_locked_test_runner(
        candidate_root,
        installed,
        runtime_root,
        environment,
    )
    analyzer = executable_path(installed, "ladon")
    bridge = executable_path(installed, "ladon-proofir-bridge")
    contract_environment = dict(environment)
    contract_environment.pop("PYTHONHOME", None)
    contract_environment.pop("PYTHONPATH", None)
    contract_environment.update(
        {
            "LADON_CONSOLE": str(analyzer),
            "LADON_PROOFIR_BRIDGE_CONSOLE": str(bridge),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    run_checked(
        [
            str(installed.python),
            "-m",
            "pytest",
            "-q",
            "--rootdir",
            str(candidate_root),
            str(contract),
        ],
        cwd=runtime_root,
        environment=contract_environment,
    )


def install_locked_test_runner(
    candidate_root: Path,
    installed: InstalledEnvironment,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Install the candidate's locked dev tools without reinstalling Ladon."""

    requirements = runtime_root / "locked-test-requirements.txt"
    uv = uv_executable()
    run_checked(
        [
            uv,
            "export",
            "--locked",
            "--only-group",
            "dev",
            "--no-emit-project",
            "--output-file",
            str(requirements),
        ],
        cwd=candidate_root,
        environment=environment,
    )
    run_checked(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(installed.python),
            "--require-hashes",
            "--requirements",
            str(requirements),
        ],
        cwd=runtime_root,
        environment=environment,
    )


def assert_portable_fixture_analysis(
    candidate_root: Path,
    installed: InstalledEnvironment,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Run the installed ordinary CLI against a tracked text-only fixture."""

    fixture = candidate_root / "tests" / "fixtures" / "tiny_lean"
    report = runtime_root / "installed-report.json"
    executable = executable_path(installed, "ladon")
    run_checked(
        [
            str(executable),
            "--repo-root",
            str(fixture),
            "--root",
            "Tiny.lean",
            "--output-json",
            str(report),
        ],
        cwd=runtime_root,
        environment=environment,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {})
    if metadata.get("analysis_root_module") != "Tiny":
        raise GateError("installed fixture analysis did not report root module Tiny")


def run_installed_distribution_checks(
    candidate_root: Path,
    artifacts: DistributionArtifacts,
    runtime_root: Path,
    environment: Mapping[str, str],
    resources: Sequence[str] = (),
) -> InstalledEnvironment:
    """Install and verify metadata, entrypoints, assets, and portable analysis."""

    for resource in resources:
        assert_resource_in_artifacts(resource, artifacts)
    installed = install_wheel(artifacts, runtime_root, environment)
    assert_installed_import_origin(installed, runtime_root, environment)
    assert_console_script_help(
        candidate_root,
        installed,
        runtime_root,
        environment,
    )
    assert_installed_process_contracts(
        candidate_root,
        installed,
        runtime_root,
        environment,
    )
    assert_portable_fixture_analysis(
        candidate_root,
        installed,
        runtime_root,
        environment,
    )
    for resource in resources:
        assert_installed_resource(installed, resource, runtime_root, environment)
    return installed
