"""Lightweight installed entrypoint with lazy command-family imports."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch proof-search without importing the general analyzer first."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "doctor":
        return doctor_main(arguments[1:])
    if arguments and arguments[0] == "proof-search":
        from ladon.proof_search_cli import proof_search_main

        return proof_search_main(arguments[1:])
    if arguments and arguments[0] == "proofir":
        from ladon.proofir_v3_cli import proofir_v3_main

        return proofir_v3_main(arguments[1:])
    from ladon.cli import main as analyzer_main

    return analyzer_main(arguments)


def doctor_main(arguments: Sequence[str]) -> int:
    """Emit read-only installation and bounded repository readiness data."""
    if not _doctor_arguments_valid(arguments):
        print("ladon doctor: supported options are --json and --repo-root PATH", file=sys.stderr)
        return 2
    repo_root = _doctor_repo_root(arguments)
    payload = _doctor_payload(repo_root)
    if "--json" in arguments:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"Ladon {payload['installed']['version']}; Python {payload['installed']['python']}; pin={'present' if payload['readiness']['repositoryPinPresent'] else 'missing'}"
        )
    return 0


def _doctor_arguments_valid(arguments: Sequence[str]) -> bool:
    seen_root = False
    index = 0
    while index < len(arguments):
        arg = arguments[index]
        if arg == "--json":
            index += 1
            continue
        if arg.startswith("--repo-root="):
            if seen_root or not arg.split("=", 1)[1]:
                return False
            seen_root = True
            index += 1
            continue
        if arg == "--repo-root":
            if seen_root or index + 1 >= len(arguments) or arguments[index + 1].startswith("-"):
                return False
            seen_root = True
            index += 2
            continue
        return False
    return True


def _doctor_repo_root(arguments: Sequence[str]) -> Path:
    for index, arg in enumerate(arguments):
        if arg.startswith("--repo-root="):
            return Path(arg.split("=", 1)[1]).resolve()
        if arg == "--repo-root" and index + 1 < len(arguments):
            return Path(arguments[index + 1]).resolve()
    return Path.cwd()


def _doctor_payload(repo_root: Path) -> dict[str, object]:
    pin = repo_root / "lean-toolchain"
    try:
        version = metadata.version("ladon")
    except metadata.PackageNotFoundError:
        version = "source-tree"
    return {
        "schema": "ladon-doctor-result-v1",
        "status": "available",
        "installed": {
            "version": version,
            "python": platform.python_version(),
            "executable": sys.executable,
        },
        "repository": {
            "root": str(repo_root),
            "toolchainPin": pin.read_text(encoding="utf-8").strip() if pin.is_file() else None,
            "toolchainPinDigest": "sha256:" + hashlib.sha256(pin.read_bytes()).hexdigest()
            if pin.is_file()
            else None,
        },
        "posture": {
            "targetExecution": "not-run",
            "targetTrustRequirement": "trusted-repository-only",
            "initializerIsolation": "absent",
            "network": "not-assessed",
            "environment": "sanitized-by-worker",
        },
        "readiness": {"repositoryPinPresent": pin.is_file(), "preflight": "not-run"},
        "nonclaims": [
            "Doctor does not execute Lean, Lake, repository code, or target analysis.",
            "Lean-backed authority is not claimed for adversarial target repositories because target initializers are not isolated.",
        ],
    }


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
