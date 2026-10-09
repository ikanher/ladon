"""Compact discovery summaries expose limits and unresolved applications."""
from test_semantic_result_projection import _discovery_payload

from ladon.semantic_result_projection import project_semantic_result


def test_compact_discovery_exposes_limit_and_closed_residual_counts():
    payload, registry = _discovery_payload()
    result = project_semantic_result(payload, projection='llm', registered_artifacts=registry)
    assert result['request']['maxCandidates'] == payload['request']['maxCandidates']
    counts = result['coverage']['candidatePopulation']
    assert counts['closedAccepted'] == 1
    assert counts['applicableWithResiduals'] == 0
    assert result['coverage']['canonical']['accepted'] == 1
