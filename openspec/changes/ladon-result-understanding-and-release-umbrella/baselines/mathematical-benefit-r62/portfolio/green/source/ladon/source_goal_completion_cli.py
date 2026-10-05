"""Ordinary captured-goal completion input and mathematical text view."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._source_goal_completion_inputs import own_capture
from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_semantic_cli import enforce_semantic_execution_policy
from ladon.source_association_io import _AssociationError, _read_regular, _strict_json
from ladon.source_goal_capture import MAX_SOURCE_BYTES, RESULT_SCHEMA
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal


def dispatch_completion(args, repo_root):
    capture = _read_capture(args.capture_file)
    enforce_semantic_execution_policy(args)
    try:
        context = resolve_toolchain_context(
            repo_root, lean_path=args.lean_path, lake_path=args.lake_path,
            selection_mode="explicit",
        )
        request = SourceGoalCompletionRequest(
            repo_root=repo_root, capture=capture, term=args.term, toolchain=context,
            timeout_seconds=args.timeout_seconds, max_output_bytes=args.max_output_mib * 1024**2,
            max_rss_bytes=args.max_rss_mib * 1024**2, require_isolation=args.require_isolation,
        )
    except (LeanToolchainError, OSError, TypeError, ValueError) as error:
        raise ProofSearchIndexError(str(error), code="completion-input-or-toolchain") from error
    return complete_source_goal(request)


def _read_capture(path):
    try:
        envelope = _strict_json(_read_regular(path, MAX_SOURCE_BYTES).decode("utf-8"))
        if not isinstance(envelope, dict) or set(envelope) != {
            "schema", "operation", "status", "capture", "diagnostic", "resourceAccounting", "processReceipts",
        }:
            raise ValueError("input must be the complete JSON capture result")
        if (envelope["schema"] != RESULT_SCHEMA or envelope["operation"] != "capture-source-goal"
                or envelope["status"] != "captured" or envelope["diagnostic"] is not None):
            raise ValueError("input must be a successful source capture v1")
        return own_capture(envelope["capture"])
    except (_AssociationError, OSError, UnicodeError, TypeError, ValueError) as error:
        raise ProofSearchIndexError(str(error), code="completion-capture-input") from error


def render_completion_text(payload: Mapping[str, Any]) -> str:
    lines = [f"application outcome: {payload['status']}"]
    application = payload.get("application")
    if application:
        goal = application.get("originalGoal")
        if goal:
            lines.append("original goal: " + goal["typeDisplay"])
        for residual in application["residualGoals"]:
            lines.append("remaining obligation: " + residual["typeDisplay"])
            for local in residual["localContext"]:
                role = "internal implementation detail" if local["implementationDetail"] else "usable premise"
                lines.append(f"  {role}:")
                declaration = f"  {local['userName']} : {local['typeDisplay']}"
                value = local.get("valueDisplay")
                if value:
                    declaration += " := " + value
                lines.append(declaration)
    lines.append("independent compiler replay: " + payload["replay"]["status"])
    trust = payload["trust"]
    lines.append("transitive trust coverage: " + trust["coverage"])
    if trust["observedAxioms"] is not None:
        lines.append("observed axioms: " + ", ".join(trust["observedAxioms"]))
    diagnostic = payload.get("diagnostic")
    if diagnostic:
        lines.append(diagnostic["code"] + ": " + diagnostic["message"])
    lines.append("capture: " + str(payload["captureId"]))
    lines.append("term: " + payload["termDigest"])
    lines.append("scope: selected source goal; enclosing declaration and prose correspondence remain separate")
    return "\n".join(lines) + "\n"
