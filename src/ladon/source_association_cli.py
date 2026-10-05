"""CLI adapter for the independent source-association observation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_semantic_cli import enforce_semantic_execution_policy
from ladon.result_evidence_io import load_result_artifacts
from ladon.result_manifest_io import ResultManifestError
from ladon.semantic_candidate_limits import validate_semantic_bounds


def dispatch_source_association(
    args: Any,
    repo_root: Path,
) -> Mapping[str, Any]:
    """Run the source producer using only pinned tools and selected artifacts."""

    enforce_semantic_execution_policy(args)
    try:
        validate_semantic_bounds(args.timeout_seconds, args.max_output_mib * 1024**2,
                                 args.max_rss_mib * 1024**2)
    except (TypeError, ValueError) as error:
        raise ProofSearchIndexError(str(error)) from error
    try:
        root = repo_root.resolve()
        toolchain = resolve_toolchain_context(
            root,
            lake_path=args.lake_path,
            lean_path=args.lean_path,
            selection_mode=args.toolchain_mode,
        )
    except LeanToolchainError as error:
        raise ProofSearchIndexError(
            str(error),
            exit_class="operational",
            code="toolchain-unavailable",
            remediation="Use the repository's pinned Lean release and explicit executable paths.",
        ) from error

    try:
        artifacts = load_result_artifacts(args.artifact)
    except (OSError, ResultManifestError) as error:
        raise ProofSearchIndexError(
            str(error),
            code="canonical-artifact-invalid",
        ) from error

    # Ordinary candidate checking does not load the source-association producer.
    try:
        from ladon.source_association import (
            SourceAssociationRequest,
            capture_source_association,
        )
    except ImportError as error:
        raise ProofSearchIndexError(
            "source association producer is unavailable",
            exit_class="operational",
            code="source-association-unavailable",
        ) from error

    try:
        request = SourceAssociationRequest(
            repo_root=root,
            module=args.module,
            source_path=args.source_path,
            candidate=args.candidate,
            subject_artifact_id=args.subject_artifact,
            toolchain=toolchain,
            setup_path=str(args.setup_path) if args.setup_path is not None else None,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_mib * 1024 * 1024,
            max_rss_bytes=args.max_rss_mib * 1024 * 1024,
        )
        payload = capture_source_association(request, artifacts)
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error
    if not isinstance(payload, Mapping):
        raise ProofSearchIndexError(
            "source association producer returned an invalid result",
            exit_class="operational",
            code="source-association-result-invalid",
        )
    return payload


__all__ = ["dispatch_source_association"]
