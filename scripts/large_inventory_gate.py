#!/usr/bin/env python3
"""Measure Ladon's installed CLI against the portable large Lean fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from typing import Any, Mapping, TextIO

import jsonschema

from release_gate_candidate import materialize_candidate
from release_gate_distribution import (
    build_distributions,
    executable_path,
    install_wheel,
    project_metadata,
)
from release_gate_runtime import (
    assert_lock_unchanged,
    assert_no_absolute_maintainer_paths,
    lock_digest,
    run_checked,
    runtime_directory,
    sanitized_environment,
)
from release_gate_types import GateError

from ladon.large_inventory_gate import (
    REQUIRED_SAMPLE_COUNT,
    LargeInventoryGateError,
    run_large_inventory_measurements,
)


MANIFEST_PATH = Path("tests/fixtures/large_inventory/manifest-v1.json")
REPORT_SCHEMA_PATH = Path("src/ladon/schemas/ladon-report-v3.schema.json")


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit installed-candidate gate interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--samples",
        type=sample_count,
        default=REQUIRED_SAMPLE_COUNT,
        help="Cold and warm samples; the contract minimum is three of each.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help=(
            "Exit nonzero unless all contracts pass on the exact Ubuntu "
            "24.04 x86-64 four-core reference matrix cell."
        ),
    )
    parser.add_argument(
        "--output",
        help="Optional JSON artifact path; stdout is used when omitted.",
    )
    return parser


def sample_count(raw: str) -> int:
    """Parse the normative minimum sample count."""

    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("sample count must be an integer") from exc
    if value < REQUIRED_SAMPLE_COUNT:
        raise argparse.ArgumentTypeError(
            f"sample count must be at least {REQUIRED_SAMPLE_COUNT}"
        )
    return value


def project_root() -> Path:
    """Return the checkout containing this gate script."""

    return Path(__file__).resolve().parents[1]


def run_gate(candidate: str, *, samples: int) -> dict[str, Any]:
    """Build, install, generate, and measure one explicit candidate."""

    with materialize_candidate(candidate, project_root()) as materialized:
        with runtime_directory("ladon-large-inventory-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            expected_lock = lock_digest(materialized.root)
            assert_no_absolute_maintainer_paths(materialized.root)
            artifacts = build_distributions(
                materialized.root,
                runtime_root,
                environment,
            )
            installed = install_wheel(artifacts, runtime_root, environment)
            fixture_root = runtime_root / "fixture"
            inventory = generate_installed_fixture(
                installed.python,
                materialized.root / MANIFEST_PATH,
                fixture_root,
                runtime_root,
                environment,
            )
            candidate_identity = build_candidate_identity(
                candidate,
                materialized.kind,
                materialized.root,
                artifacts.wheel,
                installed.python,
            )
            fixture_identity = build_fixture_identity(
                materialized.root / MANIFEST_PATH,
                inventory,
            )
            result = run_large_inventory_measurements(
                analyzer=executable_path(installed, "ladon"),
                fixture_root=fixture_root,
                runtime_root=runtime_root,
                environment=environment,
                candidate_identity=candidate_identity,
                fixture_identity=fixture_identity,
                sample_count=samples,
                report_validator=report_validator(materialized.root),
            )
            assert_lock_unchanged(materialized.root, expected_lock)
            return result


def generate_installed_fixture(
    installed_python: Path,
    manifest: Path,
    destination: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    """Generate through the selected wheel rather than the live source package."""

    program = "\n".join(
        [
            "import json",
            "import sys",
            "from pathlib import Path",
            "from ladon.large_fixture import LargeFixtureManifest, generate_large_fixture",
            "manifest = LargeFixtureManifest.from_path(Path(sys.argv[1]))",
            "result = generate_large_fixture(Path(sys.argv[2]), manifest)",
            "print(json.dumps(result, sort_keys=True, separators=(',', ':')))",
        ]
    )
    completed = run_checked(
        [
            str(installed_python),
            "-c",
            program,
            str(manifest),
            str(destination),
        ],
        cwd=runtime_root,
        environment=environment,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise GateError("installed fixture generator returned a non-object")
    return payload


def build_candidate_identity(
    selector: str,
    kind: str,
    candidate_root: Path,
    wheel: Path,
    installed_python: Path,
) -> dict[str, Any]:
    """Identify the exact source, wheel, and Python matrix cell."""

    metadata = project_metadata(candidate_root)
    wheel_digest = file_sha256(wheel)
    return {
        "id": f"sha256:{wheel_digest}",
        "selector": selector,
        "selectionKind": kind,
        "sourceFingerprint": directory_fingerprint(candidate_root),
        "wheelSha256": wheel_digest,
        "projectName": metadata["name"],
        "projectVersion": metadata["version"],
        "requiresPython": metadata["requires-python"],
        "supportedPythonMinors": supported_python_minors(metadata),
        "installedPython": installed_python_version(installed_python),
    }


def build_fixture_identity(
    manifest_path: Path,
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    """Return fixture identity without embedding all 2,600 file rows."""

    fingerprint = str(inventory.get("contentFingerprint", ""))
    if not fingerprint:
        raise GateError("generated fixture omitted its content fingerprint")
    return {
        "id": f"sha256:{fingerprint}",
        "manifestSha256": file_sha256(manifest_path),
        "schema": inventory.get("schema"),
        "generatorVersion": inventory.get("generatorVersion"),
        "contentFingerprint": fingerprint,
        "moduleCount": inventory.get("moduleCount"),
        "sourceLineCount": inventory.get("sourceLineCount"),
        "declarationCount": inventory.get("declarationCount"),
        "generatedModuleCount": inventory.get("generatedModuleCount"),
        "facadeImportCount": inventory.get("facadeImportCount"),
        "seed": inventory.get("seed"),
    }


def report_validator(candidate_root: Path):
    """Return a validator backed by the selected candidate's v3 schema."""

    schema = json.loads(
        (candidate_root / REPORT_SCHEMA_PATH).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    return validator.validate


def supported_python_minors(metadata: Mapping[str, Any]) -> list[str]:
    """Read declared Python minors from stable packaging classifiers."""

    prefix = "Programming Language :: Python :: "
    return sorted(
        {
            classifier.removeprefix(prefix)
            for classifier in metadata.get("classifiers", [])
            if isinstance(classifier, str)
            and classifier.startswith(prefix)
            and classifier.removeprefix(prefix).count(".") == 1
        }
    )


def installed_python_version(installed_python: Path) -> str:
    """Return the exact isolated interpreter version."""

    result = run_checked(
        [str(installed_python), "--version"],
        cwd=installed_python.parent,
        environment=os.environ,
        capture_output=True,
    )
    return (result.stdout or result.stderr).strip()


def directory_fingerprint(root: Path) -> str:
    """Hash candidate-relative names, kinds, and bytes deterministically."""

    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            _update_digest(digest, relative, f"link:{os.readlink(path)}".encode())
        elif path.is_file():
            _update_digest(digest, relative, path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _update_digest(
    digest: Any,
    relative: str,
    content: bytes,
) -> None:
    digest.update(relative.encode("utf-8"))
    digest.update(b"\0")
    digest.update(hashlib.sha256(content).digest())
    digest.update(b"\0")


def file_sha256(path: Path) -> str:
    """Return a lowercase SHA-256 hex digest."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit_result(result: Mapping[str, Any], output: str | None) -> None:
    """Write one deterministic result artifact and compact status summary."""

    content = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, destination)
        print(f"large-inventory results: {destination}")
    else:
        print(content, end="")
    print_summary(result, stream=sys.stdout if output else sys.stderr)


def print_summary(
    result: Mapping[str, Any],
    *,
    stream: TextIO = sys.stdout,
) -> None:
    """Print status without collapsing individual metrics into a score."""

    failed = result.get("failures", [])
    reference = result["environment"]["matchesReferenceJob"]
    print(
        "large-inventory summary: "
        f"passed={result['passed']}; "
        f"reference-job={reference}; "
        f"failed-contracts={len(failed)}",
        file=stream,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the gate while preserving machine-only stdout when requested."""

    args = build_parser().parse_args(argv)
    try:
        log_context = (
            nullcontext()
            if args.output
            else redirect_stdout(sys.stderr)
        )
        with log_context:
            result = run_gate(args.candidate, samples=args.samples)
        emit_result(result, args.output)
    except (
        GateError,
        LargeInventoryGateError,
        json.JSONDecodeError,
        jsonschema.ValidationError,
        OSError,
        ValueError,
    ) as exc:
        print(f"large-inventory gate: FAIL: {exc}", file=sys.stderr)
        return 1
    if args.required and not result["referencePassed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
