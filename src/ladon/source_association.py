"""Source association for exact source-to-compiled observations."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ladon.lean_toolchain import LeanToolchainContext
from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.proofir_v3 import (
    ProofIRV3Error,
    canonical_bytes,
    validate_envelope_batch,
)
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.source_association_environment import (
    _repo_root,
    _select_subject,
    _validate_toolchain,
    _verify_toolchain,
)
from ladon.source_association_evidence import (
    _anchor_from_ilean,
    _bounded_status,
    _make_source_map,
    _resource_result,
    _result,
)
from ladon.source_association_inventory import _inventory, _recorded_module, _resolve_compiled_files
from ladon.source_association_io import (
    _MODULE,
    MAX_EVIDENCE_FILE_BYTES,
    _AssociationError,
    _check_unchanged,
    _digest,
    _file_identity,
    _ProcessRunner,
    _read_regular,
    _reject_unsupported_output_sidecars,
    _safe_repo_file,
    _source_path,
)
from ladon.source_association_setup import _load_setup


@dataclass(frozen=True)
class SourceAssociationRequest:
    """Inputs for one explicit source-to-compiled coherence observation."""

    repo_root: Path
    module: str
    source_path: str
    candidate: str
    subject_artifact_id: str
    toolchain: LeanToolchainContext
    setup_path: str | None = None
    timeout_seconds: float = 120
    max_output_bytes: int = 8 * 1024 * 1024
    max_rss_bytes: int = 32 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        _validate_limits(self)


def capture_source_association(
    request: SourceAssociationRequest,
    artifacts: Sequence[Mapping[str, Any]],
    *,
    process_runner: _ProcessRunner = run_bounded_target_process,
) -> dict[str, Any]:
    """Observe fresh compilation parity and emit one canonical source map."""

    source_info: dict[str, Any] = {}
    compiled_info: dict[str, Any] = {}
    resource: dict[str, Any] = {
        "timeoutMilliseconds": int(request.timeout_seconds * 1000),
        "maxOutputBytes": request.max_output_bytes,
        "maxRssBytes": request.max_rss_bytes,
    }
    try:
        _validate_limits(request)
        root = _repo_root(request)
        owner, environment, declaration = _select_subject(
            request, artifacts
        )
        _validate_toolchain(request.toolchain, environment)
        _recorded_module(environment, request.module)
        source_path = _source_path(root, request.source_path, request.module)
        source_bytes = _read_regular(source_path, MAX_EVIDENCE_FILE_BYTES)
        source_digest = _digest(source_bytes)
        source_info = {"path": request.source_path, "digest": source_digest}
        setup_bytes, normalized_setup = _load_setup(
            root, request.setup_path, request.module
        )
        setup_digest = _digest(setup_bytes) if setup_bytes is not None else None
        normalized_setup_digest = (
            _digest(canonical_bytes(normalized_setup))
            if normalized_setup is not None
            else None
        )
        compiled_files = _resolve_compiled_files(request.toolchain, environment)
        compiled_before = _inventory(compiled_files, environment)
        compiled_info = {
            "recordedModules": len(compiled_files),
            "before": compiled_before,
        }
        _verify_toolchain(request.toolchain)
        process, fresh_olean_digest, fresh_olean_size, fresh_ilean = _compile(
            request,
            root,
            source_path,
            source_bytes,
            normalized_setup,
            process_runner,
            resource,
        )
        resource.update(_resource_result(process))
        _require_successful_process(process)
        compiled_after = _verify_unchanged_inputs(
            request, root, source_path, source_digest, setup_digest,
            compiled_files, compiled_before, environment,
        )
        compiled_info["after"] = compiled_after
        module_digest = fresh_olean_digest
        expected_digest = _recorded_module(environment, request.module)["digest"]
        if module_digest != expected_digest:
            raise _AssociationError(
                "stale", "compiled-module-mismatch", "fresh module bytes differ from the selected environment"
            )
        ilean_bytes = fresh_ilean
        ilean_digest = _digest(ilean_bytes)
        anchor = _anchor_from_ilean(
            ilean_bytes,
            request.module,
            request.candidate,
            source_bytes,
            request.source_path,
            owner,
            declaration,
        )
        process_observation = {
            "schema": "ladon-source-association-observation-v1",
            "operation": "source-compiled-coherence",
            "sourceDigest": source_digest,
            "sourcePath": request.source_path,
            "stdinDigest": source_digest,
            "setupDigest": setup_digest,
            "normalizedSetupDigest": normalized_setup_digest,
            "freshCompiledModuleDigest": module_digest,
            "freshCompiledModuleBytes": fresh_olean_size,
            "recordedCompiledModuleDigest": expected_digest,
            "freshIleanDigest": ilean_digest,
            "leanExecutableDigest": request.toolchain.lean_identity,
            "leanVersion": request.toolchain.lean_release,
            "captureContextIdentity": request.toolchain.context_identity,
            "captureSourceTreeIdentity": request.toolchain.source_tree_identity,
            "compiledInputSnapshotDigest": compiled_after["snapshotDigest"],
            "compiledInputSnapshotBeforeDigest": compiled_before["snapshotDigest"],
            "compiledInputModuleCount": compiled_after["moduleCount"],
            "compiledInputBytes": compiled_after["primaryBytes"],
            "compiledSidecarSnapshotDigest": compiled_after["sidecarSnapshotDigest"],
            "compiledSidecarCount": compiled_after["sidecarCount"],
            "compiledSidecarBytes": compiled_after["sidecarBytes"],
            "resources": resource,
            "resourceScope": "compiler-process-tree",
            "checking": "not-assessed",
            "correspondence": "not-assessed",
            "sourceFreshness": "not-assessed",
        }
        source_map = _make_source_map(
            owner,
            declaration,
            request.module,
            anchor,
            source_digest,
            process_observation,
        )
        validate_envelope_batch([*[dict(a) for a in artifacts], source_map])
        return _result(
            "associated",
            source_info,
            compiled_info,
            resource,
            [source_map],
            None,
            None,
        )
    except _AssociationError as exc:
        return _result(
            exc.status, source_info, compiled_info, resource, [], exc.code, str(exc)
        )
    except (OSError, ValueError, ProofIRV3Error, json.JSONDecodeError) as exc:
        return _result(
            "unavailable",
            source_info,
            compiled_info,
            resource,
            [],
            "input-unavailable",
            str(exc),
        )


def _validate_limits(request: SourceAssociationRequest) -> None:
    validate_semantic_bounds(request.timeout_seconds, request.max_output_bytes, request.max_rss_bytes)
    if not _MODULE.fullmatch(request.module) or not _MODULE.fullmatch(request.candidate):
        raise _AssociationError("failed", "invalid-identity", "module and candidate must be qualified Lean names")


def _require_successful_process(process: ProcessResult) -> None:
    bounded_status = _bounded_status(process)
    if bounded_status:
        raise _AssociationError(
            bounded_status,
            "bounded-process",
            "Lean source compilation reached a configured process bound",
        )
    if not process.succeeded:
        raise _AssociationError("failed", "lean-compile-failed", "Lean source compilation failed")


def _verify_unchanged_inputs(
    request: SourceAssociationRequest,
    root: Path,
    source_path: Path,
    source_digest: str,
    setup_digest: str | None,
    compiled_files: Mapping[str, Path],
    compiled_before: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    _check_unchanged(source_path, source_digest, "source")
    _verify_setup_unchanged(request, root, setup_digest)
    _verify_toolchain(request.toolchain)
    compiled_after = _inventory(compiled_files, environment)
    if compiled_before != compiled_after:
        raise _AssociationError("stale", "compiled-input-changed", "recorded compiled inputs changed during compilation")
    return compiled_after


def _verify_setup_unchanged(
    request: SourceAssociationRequest,
    root: Path,
    setup_digest: str | None,
) -> None:
    if request.setup_path is None:
        return
    setup_path = _safe_repo_file(root, request.setup_path)
    _check_unchanged(setup_path, setup_digest or "", "setup")


def _compile(request: SourceAssociationRequest, root: Path, source: Path, source_bytes: bytes,
             setup: dict[str, Any] | None, process_runner: _ProcessRunner, resources: dict[str, Any]) -> tuple[ProcessResult, str, int, bytes]:
    relative = PurePosixPath(request.source_path)
    root_parts = relative.parts[: -(len(request.module.split(".")))]
    lean_root = root.joinpath(*root_parts).resolve()
    with tempfile.TemporaryDirectory(prefix="ladon-source-association-") as directory:
        scratch = Path(directory)
        output = scratch / "Owner.olean"
        ilean = scratch / "Owner.ilean"
        command = [str(request.toolchain.lean_path), "--stdin", f"--root={lean_root}", "-o", str(output), "-i", str(ilean)]
        if setup is not None:
            setup_file = scratch / "setup.json"
            setup_file.write_text(json.dumps(setup, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            command.extend(("--setup", str(setup_file)))
        command.append(str(source))
        process = process_runner(
            command,
            cwd=root,
            env=request.toolchain.environment,
            input_bytes=source_bytes,
            timeout_seconds=request.timeout_seconds,
            max_output_bytes=request.max_output_bytes,
            max_rss_bytes=request.max_rss_bytes,
        )
        resources.update(_resource_result(process))
        if process.succeeded:
            _reject_unsupported_output_sidecars(output)
            olean_digest, olean_size = _file_identity(output)
            return (
                process,
                olean_digest,
                olean_size,
                _read_regular(ilean, MAX_EVIDENCE_FILE_BYTES),
            )
        return process, "", 0, b""

