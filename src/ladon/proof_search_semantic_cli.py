"""CLI transport helpers for compact semantic results and evidence expansion."""

from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.execution_posture import (
    ISOLATION_UNAVAILABLE,
    TargetIsolationUnavailable,
    require_target_execution_policy,
)
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

SEMANTIC_TEXT_SCHEMAS = frozenset({
    "ladon-semantic-candidate-check-result-v1",
    "ladon-verified-discovery-result-v1",
    "ladon-semantic-candidate-projection-v1",
    "ladon-verified-discovery-projection-v1",
})


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


def add_target_execution_options(parser: argparse.ArgumentParser) -> None:
    """Allow callers to require isolation before Lean-backed work begins."""

    parser.add_argument(
        "--require-isolation",
        action="store_true",
        help="Require target initializer isolation; fails closed when unavailable.",
    )


def enforce_semantic_execution_policy(args: argparse.Namespace) -> None:
    """Translate the shared execution policy into the stable CLI diagnostic."""

    try:
        require_target_execution_policy(
            require_isolation=getattr(args, "require_isolation", False)
        )
    except TargetIsolationUnavailable as error:
        raise ProofSearchIndexError(
            str(error),
            exit_class="operational",
            code=ISOLATION_UNAVAILABLE,
            remediation="Inspect the policy with 'ladon doctor --json --require-isolation'.",
        ) from error


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
        "evidenceReceipt": _stored_artifact_receipt(artifact, registry),
        "registry": registry.inspect(),
    }


def _stored_artifact_receipt(
    artifact: Mapping[str, Any], registry: SemanticEvidenceRegistry,
) -> Mapping[str, Any] | None:
    """Keep canonical historical bytes intact and attribute the current read."""

    try:
        environments = []
        observation = artifact.get('extensions', {}).get('ladon.process-observation/v1', {})
        if observation.get('evidenceReceipt') is not None:
            environments = [registry.resolve_environment(str(artifact['environmentRef']))]
        return stored_check_receipt(artifact, environment_artifacts=environments)
    except (ValueError, ProofIRV3Error, SemanticEvidenceRegistryError, sqlite3.Error) as error:
        raise ProofSearchIndexError(
            str(error), exit_class="operational", code="invalid-stored-evidence-receipt",
        ) from error


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


def render_semantic_candidates(
    candidates: list[Any], *, include_projected_evidence: bool = False,
) -> list[str]:
    """Render projected candidate evidence for text-mode semantic output."""

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
        if include_projected_evidence:
            if check.get("applicationObservationVersion") == 4:
                lines.extend(_render_v4_application_observation(check))
            else:
                lines.extend(_render_residual_propositions(check))
            lines.extend(_render_expansion_references(check))
        lines.extend(_render_observation_receipt(check))
        scratch = check.get("scratch")
        if isinstance(scratch, Mapping):
            lines.append(f"  scratch: {scratch.get('status', 'unknown')}")
            if include_projected_evidence:
                lines.extend(_render_expansion_references(scratch))
            lines.extend(_render_observation_receipt(scratch))
    return lines


def _render_residual_propositions(check: Mapping[str, Any]) -> list[str]:
    """Show observed propositions, without inventing missing projection detail."""

    rows = check.get("residualPremises")
    if not isinstance(rows, list):
        return ["  remaining goals: unavailable in this view; expand check evidence"]
    lines = []
    for row in rows:
        proposition = row.get("typeDisplay") if isinstance(row, Mapping) else None
        if isinstance(proposition, str) and proposition:
            lines.append(f"  remaining goal: {proposition}")
        else:
            lines.append("  remaining goal: unavailable in this view; expand check evidence")
    return lines


def _render_v4_application_observation(check: Mapping[str, Any]) -> list[str]:
    lines = _render_selected_declaration(check)
    residuals = check.get("residualPremises")
    contexts = check.get("residualContexts")
    residuals = residuals if isinstance(residuals, list) else []
    contexts = contexts if isinstance(contexts, list) else []
    if len(contexts) != len(residuals):
        lines.append("  residual local contexts: incomplete in this view; expand check evidence")
    for ordinal, expression in enumerate(residuals[:4]):
        proposition = expression.get("typeDisplay") if isinstance(expression, Mapping) else None
        lines.append(f"  remaining goal {ordinal}: {_application_text_fragment(proposition, 512)}")
        row = contexts[ordinal] if ordinal < len(contexts) else None
        if not isinstance(row, Mapping):
            lines.append(f"    residual context {ordinal}: unavailable in this view")
            continue
        lines.extend(_render_residual_local_context(row, ordinal))
    if len(residuals) > 4:
        lines.append(f"  remaining goal/context omission: {len(residuals) - 4} more; expand check evidence")
    return lines


def _render_selected_declaration(check) -> list[str]:
    selected = check.get("selectedDeclaration")
    lines: list[str] = []
    if isinstance(selected, Mapping):
        lines.append(f"  selected declaration type: {_application_text_fragment(selected.get('typeDisplay'), 1024)}")
        binders = selected.get("binders")
        if isinstance(binders, list):
            kinds = [_application_text_fragment(row.get("binderInfo"), 32) for row in binders[:8] if isinstance(row, Mapping)]
            lines.append("  selected declaration binder kinds: " + (", ".join(kinds) if kinds else "none observed"))
            if len(binders) > 8:
                lines.append(f"  declaration binder omission: {len(binders) - 8} more; expand check evidence")
    return lines


def _render_residual_local_context(row, ordinal) -> list[str]:
    lines = []
    locals_ = row.get("localContext")
    lines.append(f"    residual context {ordinal} ({_application_text_fragment(row.get('goalId'), 128)}):")
    if not isinstance(locals_, list):
        lines.append("      local declarations unavailable in this view")
        return lines
    for local in locals_[:6]:
        if isinstance(local, Mapping):
            name = str(local.get("userName", "_"))[:96]
            type_text = str(local.get("typeDisplay", ""))[:256]
            lines.append(f"      {name} : {type_text}")
    if len(locals_) > 6:
        lines.append(f"      local declaration omission: {len(locals_) - 6} more; expand check evidence")
    return lines


def _application_text_fragment(value, limit) -> str:
    if not isinstance(value, str):
        return "unavailable in this view"
    if len(value) <= limit:
        return value
    return value[:limit] + f" [text omission: {len(value) - limit} chars; expand check evidence]"


def _render_expansion_references(check: Mapping[str, Any]) -> list[str]:
    """Expose supplied registry references without revalidating their contents."""

    return [
        f"  evidence expansion {key}: {_compact_json(check[key])}"
        for key in ("environmentRef", "checkRunRef")
        if check.get(key) is not None
    ]


def render_semantic_omissions(payload: Mapping[str, Any]) -> list[str]:
    """Expose the projection's bounded omission ledger and its population count."""

    lines: list[str] = []
    omissions = payload.get("omissions")
    if isinstance(omissions, list):
        lines.extend(f"omission: {_compact_json(row)}" for row in omissions)
    coverage = payload.get("coverage")
    population = coverage.get("omissionPopulation") if isinstance(coverage, Mapping) else None
    if isinstance(population, Mapping):
        lines.append(f"omissionPopulation: {_compact_json(population)}")
    if payload.get("requiresAuditExpansion"):
        lines.append("detail unavailable: this projection requires audit evidence expansion")
    return lines


def _compact_json(value: Any) -> str:
    """Serialize projected values without mutating or ASCII-escaping them."""

    import json

    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _render_observation_receipt(check: Mapping[str, Any]) -> list[str]:
    """Keep the exact receipt identities and every axis visible in text cards."""

    receipt = check.get("evidenceReceipt")
    if isinstance(receipt, Mapping):
        from ladon.evidence_receipt_readers import receipt_text_lines

        return receipt_text_lines(receipt)
    authority = check.get("authority")
    if not isinstance(authority, Mapping):
        return []
    lines = [f"evidenceReceipt: {check.get('receiptIdentity')}"]
    if check.get("sourceReceiptIdentity") is not None:
        lines.append(f"sourceReceipt: {check['sourceReceiptIdentity']}")
    lines.append("evidence dimensions: " + ", ".join(
        f"{field}={authority.get(field)}" for field in (
            "executionBinding", "observationState", "operationOutcome", "sourceFreshness",
            "environmentMatch", "authorityBasis", "analysisCompleteness",
        )
    ))
    if check.get("executionBindingLimitation") is not None:
        lines.append(f"execution binding limitation: {check['executionBindingLimitation']}")
    return lines


__all__ = [
    "SEMANTIC_TEXT_SCHEMAS",
    "add_semantic_output_options",
    "add_semantic_registry_options",
    "add_target_execution_options",
    "deliver_semantic_payload",
    "dispatch_semantic_evidence",
    "enforce_semantic_execution_policy",
    "render_semantic_candidates",
    "render_semantic_omissions",
]
