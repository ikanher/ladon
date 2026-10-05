"""Closed versioned application observations shared by live and stored owners."""
from __future__ import annotations

from collections.abc import Mapping

from ladon.semantic_candidate_protocol import validate_v4_context_populations

APPLICATION_OBSERVATION_FIELDS = (
    "applicationObservationVersion", "semanticProtocol", "residualContexts", "selectedDeclaration",
)
V4_PROTOCOLS = frozenset({
    "ladon-lean-semantic-v4/check-candidate", "ladon-lean-semantic-v4/check-candidates",
})


def validate_application_observation(shape: Mapping) -> None:
    """Do not fill missing observations or treat a marker as proof of execution."""
    if not all(field in shape for field in APPLICATION_OBSERVATION_FIELDS):
        raise ValueError("v4 application observation is incomplete")
    version = shape["applicationObservationVersion"]
    if type(version) is not int or version != 4 or shape["semanticProtocol"] not in V4_PROTOCOLS:
        raise ValueError("application observation has an unsupported version or protocol")
    selected = shape["selectedDeclaration"]
    _validate_selected_declaration(selected)
    residual_count = _residual_count(shape)
    validate_v4_context_populations(
        shape["residualContexts"], selected["binders"], residual_count=residual_count,
    )


def _validate_selected_declaration(selected) -> None:
    if not isinstance(selected, Mapping) or set(selected) != {"name", "typeDisplay", "typeStructural", "binders"}:
        raise ValueError("v4 selected declaration observation is invalid")
    if not all(isinstance(selected[k], str) and selected[k] for k in ("name", "typeDisplay", "typeStructural")):
        raise ValueError("v4 selected declaration identity is invalid")


def _residual_count(shape):
    if "residualPremises" not in shape:
        # A raw stored-field read cannot assert full application completeness.
        # Full receipt validation independently requires the expression population.
        return None
    expressions = shape["residualPremises"]
    if not isinstance(expressions, list):
        raise TypeError("v4 residual expression observation is invalid")
    for expression in expressions:
        if not isinstance(expression, Mapping) or set(expression) != {"typeDisplay", "typeStructural"}:
            raise ValueError("v4 residual expression observation is invalid")
        if not all(isinstance(v, str) and v for v in expression.values()):
            raise ValueError("v4 residual expression observation is invalid")
    return len(expressions)
