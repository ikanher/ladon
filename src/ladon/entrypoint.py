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
    invalid = any(
        arg not in {"--json", "--repo-root"}
        and not arg.startswith("--repo-root=")
        and (index == 0 or arguments[index - 1] != "--repo-root")
        for index, arg in enumerate(arguments)
    )
    if invalid:
        print("ladon doctor: supported options are --json and --repo-root PATH", file=sys.stderr)
        return 2
    repo_root = Path(".")
    for index, arg in enumerate(arguments):
        if arg.startswith("--repo-root="):
            repo_root = Path(arg.split("=", 1)[1])
        elif arg == "--repo-root" and index + 1 < len(arguments):
            repo_root = Path(arguments[index + 1])
    repo_root = repo_root.resolve()
    pin = repo_root / "lean-toolchain"
    try:
        version = metadata.version("ladon")
    except metadata.PackageNotFoundError:
        version = "source-tree"
    payload = {
        "schema": "ladon-doctor-result-v1",
        "status": "available",
        "installed": {"version": version, "python": platform.python_version(), "executable": sys.executable},
        "repository": {
            "root": str(repo_root),
            "toolchainPin": pin.read_text(encoding="utf-8").strip() if pin.is_file() else None,
            "toolchainPinDigest": "sha256:" + hashlib.sha256(pin.read_bytes()).hexdigest() if pin.is_file() else None,
        },
        "posture": {"targetExecution": "not-run", "network": "not-assessed", "environment": "sanitized-by-worker"},
        "readiness": {"repositoryPinPresent": pin.is_file(), "preflight": "not-run"},
        "nonclaims": ["Doctor does not execute Lean, Lake, repository code, or target analysis."],
    }
    if "--json" in arguments:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Ladon {version}; Python {platform.python_version()}; pin={'present' if pin.is_file() else 'missing'}")
    return 0


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
