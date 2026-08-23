"""CLI transport helpers for compact semantic results and evidence expansion."""

from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.proof_search_index import ProofSearchIndexError
from ladon.proofir_v3 import ProofIRV3Error
from ladon.semantic_evidence_registry import (
    DEFAULT_MAX_DATABASE_BYTES,
    SemanticEvidenceRegistry,
    SemanticEvidenceRegistryError,
    default_semantic_evidence_registry_path,
)
from ladon.semantic_result_delivery import deliver_semantic_result
from ladon.semantic_result_projection import PROJECTION_NAMES, SemanticProjectionError


def add_semantic_output_options(parser: argparse.ArgumentParser, positive_integer: Any) -> None:
    """Add compact/audit selection plus bounded registry options."""

    parser.add_argument(
        "--projection",
        choices=PROJECTION_NAMES,
        default="llm",
        help=(
            "Select compact LLM/review output backed by registered evidence, "
            "or audit for the complete embedded ProofIR payload."
        ),
    )
    add_semantic_registry_options(parser, positive_integer)


def add_semantic_registry_options(
    parser: argparse.ArgumentParser, positive_integer: Any
) -> None:
    """Add the finite external semantic-registry boundary."""

    parser.add_argument(
        "--evidence-store",
        type=Path,
        help="Override the repository-scoped user-cache semantic evidence registry.",
    )
    parser.add_argument(
        "--max-evidence-store-mib",
        type=positive_integer,
        default=DEFAULT_MAX_DATABASE_BYTES // (1024 * 1024),
        help="Maximum semantic evidence registry size in MiB; defaults to 512.",
    )


def deliver_semantic_payload(
    args: argparse.Namespace,
    repo_root: Path,
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Commit evidence before allowing one compact semantic projection to escape."""

    try:
        return deliver_semantic_result(
            payload,
            projection=args.projection,
            repo_root=repo_root,
            registry_path=args.evidence_store,
            max_registry_bytes=args.max_evidence_store_mib * 1024 * 1024,
        )
    except (
        ProofIRV3Error,
        SemanticEvidenceRegistryError,
        SemanticProjectionError,
        sqlite3.Error,
    ) as error:
        raise ProofSearchIndexError(
            str(error),
            exit_class="operational",
            code="semantic-evidence-publication-failed",
            remediation=(
                "Retry with a writable --evidence-store, increase "
                "--max-evidence-store-mib, or request --projection audit."
            ),
        ) from error


def dispatch_semantic_evidence(
    args: argparse.Namespace,
    repo_root: Path,
) -> Mapping[str, Any]:
    """Expand one registry artifact, environment, or typed check reference."""

    path = args.evidence_store or default_semantic_evidence_registry_path(repo_root)
    if not Path(path).is_file():
        raise ProofSearchIndexError(f"semantic evidence registry not found: {path}")
    try:
        registry = SemanticEvidenceRegistry(
            path,
            max_database_bytes=args.max_evidence_store_mib * 1024 * 1024,
        )
        reference, artifact = _resolve_semantic_reference(registry, args)
    except ProofSearchIndexError:
        raise
    except (SemanticEvidenceRegistryError, ValueError, sqlite3.Error) as error:
        raise ProofSearchIndexError(str(error)) from error
    return {
        "schema": "ladon-semantic-evidence-expansion-v1",
        "operation": "semantic-evidence-expansion",
        "status": "available",
        "reference": reference,
        "artifact": artifact,
        "registry": registry.inspect(),
    }


def _resolve_semantic_reference(
    registry: SemanticEvidenceRegistry,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    if args.kind == "semantic-artifact":
        return {"artifactRef": args.name}, registry.resolve_artifact(args.name)
    if args.kind == "semantic-environment":
        return {"environmentRef": args.name}, registry.resolve_environment(args.name)
    if not args.local_id:
        raise ProofSearchIndexError("semantic-check evidence requires --local-id")
    reference = {
        "artifactRef": args.name,
        "kind": "check-run",
        "localId": args.local_id,
    }
    return reference, registry.resolve_typed_ref(reference)["artifact"]


def render_semantic_candidates(candidates: list[Any]) -> list[str]:
    """Render bounded status/application cards for text-mode semantic output."""

    lines: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        check = candidate.get("check")
        check = check if isinstance(check, Mapping) else {}
        name = candidate.get("name") or "<unknown>"
        status = check.get("status", "unknown")
        application = check.get("applicationTerm")
        suffix = f" application={application}" if isinstance(application, str) else ""
        lines.append(f"- {name} [{status}]{suffix}")
    return lines


__all__ = [
    "add_semantic_output_options",
    "add_semantic_registry_options",
    "deliver_semantic_payload",
    "dispatch_semantic_evidence",
    "render_semantic_candidates",
]
