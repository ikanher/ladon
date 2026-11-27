"""Bounded, independently replayed feasibility of one compiled theorem's premises."""

from __future__ import annotations

import argparse
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.cli_execution import EXIT_INVOCATION, EXIT_OPERATIONAL, EXIT_SUCCESS
from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    sanitize_execution_environment,
    verify_toolchain_identities,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_inventory import _inventory, _resolve_one_compiled_module
from ladon.source_association_io import (
    _MODULE,
    MAX_MODULES,
    _AssociationError,
    _file_identity,
    _strict_json,
)
from ladon.source_goal_completion import ALLOWED_AXIOMS

WORKER = resources.files("ladon").joinpath("lean", "ladon_theorem_feasibility_helper.lean")
FRAME = "LADON_FEASIBILITY "
OUTPUT_BYTES = 8 * 1024**2
CERTIFICATE_BYTES = 8 * 1024**2
OPERATIONAL_STOPS = {
    "binder-limit",
    "premise-unfold-limit",
    "dependency-limit",
    "auxiliary-limit",
    "projection-depth-limit",
    "derived-fact-limit",
    "inference-limit",
    "kernel-resource-limit",
    "kernel-rejected-certificate",
}


class FeasibilityError(RuntimeError):
    """A failed execution or evidence binding."""

    def __init__(self, reason: str, diagnostic: str = "") -> None:
        super().__init__(diagnostic or reason)
        self.reason = reason


def check_theorem_feasibility(
    args: argparse.Namespace,
    *,
    max_rss_bytes: int,
) -> tuple[int, dict[str, Any]]:
    root = Path(args.repo_root).resolve()
    result: dict[str, Any] = {
        "schema": "ladon-theorem-feasibility-v1",
        "declaration": args.theorem,
        "module": args.module,
        "repoRoot": str(root),
        "scope": "compiled-declaration-premises",
        "replay": {"status": "not-run"},
        "trust": {"accepted": None},
        "limits": {
            "secondsPerProcess": args.timeout,
            "rssBytes": max_rss_bytes,
            "outputBytes": OUTPUT_BYTES,
            "certificateBytes": CERTIFICATE_BYTES,
            "binders": args.max_binders,
            "headReductionsPerBinder": 64,
            "dependencies": args.max_dependencies,
            "projectionDepth": args.max_projection_depth,
            "derivedFacts": args.max_derived_facts,
            "inferences": args.max_inferences,
            "leanHeartbeats": 2000,
            "auxiliaryDeclarations": 1024,
        },
    }
    if (
        (args.lean_path is None) != (args.lake_path is None)
        or not args.theorem
        or not _MODULE.fullmatch(args.module)
    ):
        result.update(status="invalid-selection", reason="invalid-selection-options")
        return EXIT_INVOCATION, result

    runner = FeasibilityRunner(args, root, max_rss_bytes)
    try:
        return runner.check(result)
    except (FeasibilityError, _AssociationError, LeanToolchainError, OSError, ValueError) as exc:
        if result["replay"]["status"] == "started":
            result["replay"] = {"status": "failed"}
        result.update(status="unresolved", reason=_error_reason(exc), diagnostic=str(exc))
        return EXIT_OPERATIONAL, result


def _error_reason(exc: Exception) -> str:
    if isinstance(exc, FeasibilityError):
        return exc.reason
    if isinstance(exc, _AssociationError):
        return exc.code
    return "execution-or-input-error"


@dataclass(frozen=True)
class FeasibilityRunner:
    args: argparse.Namespace
    root: Path
    max_rss_bytes: int

    def process(self, command: Sequence[str], environment: Mapping[str, str]) -> str:
        outcome = run_bounded_target_process(
            command,
            cwd=self.root,
            env=environment,
            timeout_seconds=self.args.timeout,
            max_output_bytes=OUTPUT_BYTES,
            max_rss_bytes=self.max_rss_bytes,
        )
        if outcome.succeeded:
            return outcome.stdout
        if outcome.timed_out:
            raise FeasibilityError("timeout")
        if outcome.memory_limited:
            raise FeasibilityError("rss-limit")
        if outcome.output_limited:
            raise FeasibilityError("output-limit")
        diagnostic = (outcome.stderr.strip() or outcome.stdout.strip())[:2000]
        raise FeasibilityError("lean-execution-failed", diagnostic)

    def check(self, result: dict) -> tuple[int, dict]:
        args = self.args
        prefix = Path(
            self.process(
                [str(args.lean_path or "lean"), "--print-prefix"], sanitize_execution_environment()
            ).strip()
        )
        if not prefix.is_absolute():
            raise FeasibilityError("invalid-lean-sysroot")
        context = resolve_toolchain_context(
            self.root,
            lean_path=args.lean_path or prefix / "bin" / "lean",
            lake_path=args.lake_path or prefix / "bin" / "lake",
        )
        execution = prepare_direct_lean_execution(self.root, args.module, context)
        result["toolchain"] = {
            "release": context.lean_release,
            "commit": context.lean_commit,
            "pinDigest": context.pin_digest,
            "leanIdentity": context.lean_identity,
        }

        with tempfile.TemporaryDirectory(prefix="ladon-feasibility-") as private:
            worker = Path(private) / "FeasibilityWorker.lean"
            worker.write_bytes(WORKER.read_bytes())
            certificate = Path(private) / "certificate.olean"

            def run(mode: str) -> dict:
                stdout = self.process(
                    [
                        *execution.command,
                        "--run",
                        str(worker),
                        mode,
                        args.module,
                        args.theorem,
                        str(certificate),
                        str(args.max_binders),
                        str(args.max_dependencies),
                        str(args.max_projection_depth),
                        str(args.max_derived_facts),
                        str(args.max_inferences),
                    ],
                    execution.environment,
                )
                return _read_frame(stdout, args.module, args.theorem)

            inspected = run("inspect")
            if inspected["status"] == "invalid-selection":
                result.update(status="invalid-selection", reason="exact-owned-theorem-required")
                return EXIT_INVOCATION, result
            if inspected["status"] != "selected":
                raise FeasibilityError("invalid-worker-response")
            files = _resolve_modules(
                inspected.get("compiledModules"),
                args.module,
                (*execution.library_roots, prefix / "lib" / "lean"),
            )
            inputs = CompiledInputs.observe(files)
            code, assessed = _check_certificate(run, inspected, certificate, result)
            verify_toolchain_identities(context)
            inputs.verify()
            assessed["compiledInputs"] = {
                **inputs.inventory,
                "ownerDigest": inputs.digests[args.module],
            }
            return code, assessed


def _check_certificate(
    run: Callable[[str], dict],
    inspected: dict,
    certificate: Path,
    result: dict,
) -> tuple[int, dict]:
    proposal = run("prove")
    _verify_modules(inspected, proposal)
    result["premises"] = proposal.get("premises")
    if proposal["status"] == "unresolved":
        return _unresolved(result, _string_field(proposal, "reason"))
    if proposal["status"] != "produced":
        raise FeasibilityError("invalid-worker-response")
    if certificate.stat().st_size > CERTIFICATE_BYTES:
        raise FeasibilityError("certificate-limit")
    certificate_digest, _ = _file_identity(certificate)
    result.update(route=_string_field(proposal, "route"), replay={"status": "started"})
    replayed = run("replay")
    if _file_identity(certificate)[0] != certificate_digest:
        raise FeasibilityError("certificate-changed")
    _verify_modules(inspected, replayed)
    # Keep the verdict private until the caller re-verifies the compiled inputs.
    return _finish_replay(result.copy(), replayed, certificate_digest)


@dataclass(frozen=True)
class CompiledInputs:
    files: dict[str, Path]
    digests: dict[str, str]
    inventory: dict
    metadata: tuple

    @classmethod
    def observe(cls, files: dict[str, Path]) -> CompiledInputs:
        metadata = _inputs_metadata(files)
        digests = {name: _file_identity(path)[0] for name, path in sorted(files.items())}
        inventory = _inventory(files, _inventory_input(digests))
        if _inputs_metadata(files) != metadata:
            raise FeasibilityError("compiled-inputs-changed")
        return cls(files, digests, inventory, metadata)

    def verify(self) -> None:
        if (
            _inventory(self.files, _inventory_input(self.digests)) != self.inventory
            or _inputs_metadata(self.files) != self.metadata
        ):
            raise FeasibilityError("compiled-inputs-changed")


def _inventory_input(digests: dict[str, str]) -> dict:
    return {
        "payload": {
            "compiledModules": [
                {"module": name, "digest": digest} for name, digest in digests.items()
            ]
        }
    }


def _inputs_metadata(files: dict[str, Path]) -> tuple:
    # File identities also detect a concurrent replacement with identical bytes.
    identities = []
    for path in files.values():
        for candidate in (
            path,
            Path(f"{path}.server"),
            Path(f"{path}.private"),
            path.with_suffix(".ir"),
            path.with_suffix(".ir.sig"),
        ):
            try:
                info = candidate.stat(follow_symlinks=False)
            except FileNotFoundError:
                identities.append(None)
            else:
                identities.append(
                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                )
    return tuple(identities)


def _resolve_modules(rows, owner: str, roots: tuple[Path, ...]) -> dict[str, Path]:
    if not isinstance(rows, list) or not 0 < len(rows) <= MAX_MODULES:
        raise FeasibilityError("compiled-module-bound")
    roots = tuple(dict.fromkeys(path.resolve() for path in roots))
    files = {}
    for row in rows:
        module, reported = _compiled_row(row)
        path = _resolve_one_compiled_module(module, roots)
        if module in files or reported.resolve(strict=True) != path:
            raise FeasibilityError("compiled-module-resolution")
        files[module] = path
    if owner not in files:
        raise FeasibilityError("compiled-owner-missing")
    return files


def _compiled_row(row: object) -> tuple[str, Path]:
    if not isinstance(row, dict):
        raise FeasibilityError("invalid-worker-response")
    module, path = row.get("module"), row.get("path")
    if not isinstance(module, str) or not isinstance(path, str):
        raise FeasibilityError("invalid-worker-response")
    return module, Path(path)


def _read_frame(stdout: str, module: str, declaration: str) -> dict:
    frames = [line.removeprefix(FRAME) for line in stdout.splitlines() if line.startswith(FRAME)]
    if len(frames) != 1:
        raise FeasibilityError("invalid-worker-response")
    frame = _strict_json(frames[0])
    if (
        not isinstance(frame, dict)
        or (frame.get("module"), frame.get("declaration")) != (module, declaration)
        or not isinstance(frame.get("status"), str)
    ):
        raise FeasibilityError("invalid-worker-response")
    return frame


def _string_field(frame: dict, key: str) -> str:
    value = frame.get(key)
    if not isinstance(value, str):
        raise FeasibilityError("invalid-worker-response")
    return value


def _verify_modules(inspected: dict, frame: dict) -> None:
    if inspected["compiledModules"] != frame.get("compiledModules"):
        raise FeasibilityError("compiled-import-closure-changed")


def _unresolved(result: dict, reason: str) -> tuple[int, dict]:
    result.update(status="unresolved", reason=reason)
    return (EXIT_OPERATIONAL if reason in OPERATIONAL_STOPS else EXIT_SUCCESS), result


def _finish_replay(result: dict, replayed: dict, digest: str) -> tuple[int, dict]:
    if replayed["status"] == "rejected":
        result["replay"] = {"status": "rejected", "certificateDigest": digest}
        return _unresolved(result, _string_field(replayed, "reason"))
    if replayed["status"] != "replayed":
        raise FeasibilityError("invalid-worker-response")
    axioms = replayed.get("axioms")
    if not isinstance(axioms, list) or any(not isinstance(name, str) for name in axioms):
        raise FeasibilityError("invalid-worker-response")
    trusted = set(axioms).issubset(ALLOWED_AXIOMS)
    result["replay"] = {"status": "accepted", "certificateDigest": digest}
    result["trust"] = {
        "policy": "lean-standard-no-placeholders-v1",
        "coverage": "complete",
        "accepted": trusted,
        "observedAxioms": axioms,
    }
    if not trusted:
        return _unresolved(result, "forbidden-axiom")
    result.update(status="inconsistent", reason="declared-premises-uninhabitable")
    return EXIT_SUCCESS, result


def render_feasibility(result: dict) -> str:
    lines = [
        f"Feasibility of {result['declaration']} in {result['module']}: {result['status']}",
        f"Reason: {result['reason']}",
    ]
    if result.get("premises") is not None:
        lines.append(f"Premises: {result['premises']}")
    if "compiledInputs" in result:
        lines.append(f"Compiled inputs: {result['compiledInputs']['snapshotDigest']}")
    if result.get("route"):
        lines.append(f"Refutation route: {result['route']}")
    lines.append(f"Independent replay: {result['replay']['status']}")
    trust = result["trust"]
    if trust["accepted"] is not None:
        status = "accepted" if trust["accepted"] else "rejected"
        lines.append(f"Trust: {status} ({', '.join(trust['observedAxioms']) or 'no axioms'})")
    if result.get("diagnostic"):
        lines.append(result["diagnostic"])
    limits = result["limits"]
    lines.append(
        f"Limits: {limits['secondsPerProcess']} s per process, {limits['rssBytes']} RSS bytes, "
        f"{limits['binders']} binders, {limits['dependencies']} dependencies, "
        f"projection depth {limits['projectionDepth']}, {limits['derivedFacts']} derived facts, "
        f"{limits['inferences']} inference attempts"
    )
    return "\n".join(lines) + "\n"
