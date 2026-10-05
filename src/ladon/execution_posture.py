"""Shared target-execution policy for the trusted-repository Lean profile."""

from __future__ import annotations

ISOLATION_UNAVAILABLE = "target-isolation-unavailable"


class TargetIsolationUnavailable(ValueError):
    """The requested target-initializer isolation cannot be provided."""


def target_execution_posture(*, require_isolation: bool = False) -> dict[str, object]:
    """Report configured policy without probing or executing a target."""

    if not isinstance(require_isolation, bool):
        raise TypeError("require_isolation must be a boolean")
    return {
        "targetExecution": "not-run",
        "targetTrustRequirement": "trusted-repository-only",
        "initializerIsolation": "absent",
        "isolationRequired": require_isolation,
        "policySatisfied": not require_isolation,
        "diagnosticCode": ISOLATION_UNAVAILABLE if require_isolation else None,
        "network": "not-assessed",
        "environment": "sanitized-by-worker",
    }


def require_target_execution_policy(*, require_isolation: bool = False) -> None:
    """Reject required isolation before any executable preflight or target load."""

    posture = target_execution_posture(require_isolation=require_isolation)
    if not posture["policySatisfied"]:
        raise TargetIsolationUnavailable(
            "Target initializer isolation is required but unavailable in the "
            "trusted-repository Lean profile."
        )
