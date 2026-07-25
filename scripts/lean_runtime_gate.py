#!/usr/bin/env python3
"""Run non-skippable real-Lean root and batch extraction acceptance."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

from release_gate_runtime import run_checked, uv_executable
from release_gate_types import GateError


def build_parser() -> argparse.ArgumentParser:
    """Build the required/optional toolchain policy interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--required",
        action="store_true",
        help="Fail instead of skipping when Elan, Lake, or Lean is unavailable.",
    )
    return parser


def project_root() -> Path:
    """Return the repository containing this gate."""

    return Path(__file__).resolve().parents[1]


def fixture_root() -> Path:
    """Return the tracked pinned-toolchain integration fixture."""

    return project_root() / "tests" / "fixtures" / "lean_integration"


def require_executable(name: str, required: bool) -> str | None:
    """Resolve an executable or apply the explicit optional policy."""

    executable = shutil.which(name)
    if executable is None and required:
        raise GateError(f"required executable is unavailable: {name}")
    return executable


def provision_reference_toolchain(
    fixture: Path,
    environment: Mapping[str, str],
    *,
    required: bool,
) -> bool:
    """Provision and verify the exact tracked Lean toolchain."""

    elan = require_executable("elan", required)
    lake = require_executable("lake", required)
    if elan is None or lake is None:
        return False
    toolchain = fixture.joinpath("lean-toolchain").read_text(encoding="utf-8").strip()
    installed = run_checked(
        [elan, "toolchain", "list"],
        cwd=fixture,
        environment=environment,
        capture_output=True,
    ).stdout
    if not toolchain_is_installed(toolchain, installed):
        run_checked(
            [elan, "toolchain", "install", toolchain],
            cwd=fixture,
            environment=environment,
        )
    version = run_checked(
        [lake, "--version"],
        cwd=fixture,
        environment=environment,
        capture_output=True,
    ).stdout
    expected = toolchain.rsplit(":v", maxsplit=1)[-1]
    if expected not in version:
        raise GateError(
            f"fixture selected unexpected Lean version: expected {expected}, got {version.strip()}"
        )
    return True


def toolchain_is_installed(toolchain: str, listing: str) -> bool:
    """Recognize Elan's optional ``(default)`` and ``(override)`` suffixes."""

    return toolchain in {
        line.split(maxsplit=1)[0]
        for line in listing.splitlines()
        if line.strip()
    }


def run_ladon_report(
    fixture: Path,
    output: Path,
    *,
    scope: str,
    environment: Mapping[str, str],
) -> dict:
    """Run one locked worktree CLI extraction and return its report."""

    run_checked(
        [
            uv_executable(),
            "run",
            "--locked",
            "ladon",
            "--repo-root",
            str(fixture),
            "--root",
            "LadonFixture",
            "--extraction-backend",
            "lean",
            "--lean-extraction-scope",
            scope,
            "--format",
            "json",
            "--output",
            str(output),
        ],
        cwd=project_root(),
        environment=environment,
    )
    return json.loads(output.read_text(encoding="utf-8"))


def assert_root_report(payload: Mapping[str, object]) -> None:
    """Require declaration and runtime evidence from one-module scope."""

    if "LadonFixture.fixtureIdentity" not in set(json_strings(payload)):
        raise GateError("root Lean extraction omitted fixtureIdentity declaration")
    runtime = lean_runtime_data(payload)
    if runtime.get("requested") != 1 or runtime.get("completed") != 1:
        raise GateError(f"root runtime counts are invalid: {runtime}")


def assert_inventory_report(payload: Mapping[str, object]) -> None:
    """Require one genuinely amortized multi-module helper batch."""

    runtime = lean_runtime_data(payload)
    requested = int(runtime.get("requested", 0))
    invocations = phase_counter(payload, "helper_invocations")
    if requested < 3:
        raise GateError(f"inventory fixture did not expose multiple modules: {runtime}")
    if invocations >= requested:
        raise GateError(
            f"inventory extraction was not amortized: {invocations} helpers for "
            f"{requested} modules"
        )
    if runtime.get("completed") != requested or runtime.get("failed") != 0:
        raise GateError(f"inventory runtime did not complete cleanly: {runtime}")


def lean_runtime_data(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Return the report-v2 Lean phase owner payload."""

    phases = payload.get("phases")
    if not isinstance(phases, Mapping):
        raise GateError("report omits phase envelopes")
    phase = phases.get("lean_extraction")
    if not isinstance(phase, Mapping):
        raise GateError("report omits lean_extraction phase")
    data = phase.get("data")
    if not isinstance(data, Mapping):
        raise GateError("lean_extraction phase omits runtime data")
    return data


def phase_counter(
    payload: Mapping[str, object],
    name: str,
) -> int:
    """Read one integer Lean phase counter."""

    phase = payload["phases"]["lean_extraction"]  # type: ignore[index]
    counters = phase["counters"]  # type: ignore[index]
    return int(counters[name])  # type: ignore[index]


def json_strings(value: object) -> Iterator[str]:
    """Yield strings nested anywhere in JSON-like report data."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from json_strings(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            yield from json_strings(nested)


def run_gate(required: bool) -> None:
    """Provision, build, and exercise root plus inventory extraction."""

    root = fixture_root()
    environment = dict(os.environ)
    if not provision_reference_toolchain(root, environment, required=required):
        print("lean runtime gate: SKIP: reference toolchain is unavailable")
        return
    lake = require_executable("lake", required=True)
    assert lake is not None
    run_checked([lake, "build"], cwd=root, environment=environment)
    with tempfile.TemporaryDirectory(prefix="ladon-lean-runtime-") as temporary:
        runtime = Path(temporary)
        root_payload = run_ladon_report(
            root,
            runtime / "root.json",
            scope="root",
            environment=environment,
        )
        inventory_payload = run_ladon_report(
            root,
            runtime / "inventory.json",
            scope="inventory",
            environment=environment,
        )
        assert_root_report(root_payload)
        assert_inventory_report(inventory_payload)


def main(argv: list[str] | None = None) -> int:
    """Run the gate with a stable PASS/FAIL/SKIP protocol."""

    args = build_parser().parse_args(argv)
    try:
        run_gate(args.required)
    except GateError as exc:
        print(f"lean runtime gate: FAIL: {exc}")
        return 1
    print("lean runtime gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
