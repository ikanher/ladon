"""Composition contracts across the seven public receipt projection boundaries."""

from __future__ import annotations

import copy
from itertools import product

import pytest

from ladon.evidence_receipt import build_evidence_receipt, project_evidence_receipt
from ladon.evidence_receipt_readers import stored_query_receipt

BOUNDARIES = (
    'live-result', 'canonical-artifact', 'sqlite-row', 'dossier',
    'aggregate', 'json-renderer', 'text-renderer',
)


def source_receipt(profile):
    if profile in {'query', 'missing-query'}:
        return stored_query_receipt('theorem-evidence', 'Main.test',
                                    observed=profile == 'query', source_freshness='stale')
    binding, state, outcome, authority, completeness, freshness, environment = {
        'accepted': ('explicit-pinned', 'live', 'accepted', 'elaborator-check', 'complete', 'fresh', 'exact'),
        'residual': ('ambient-observed', 'live', 'accepted', 'elaborator-check', 'partial', 'stale', 'mismatched'),
        'rejected': ('ambient-observed', 'live', 'rejected', 'elaborator-check', 'complete', 'unknown', 'unknown'),
        'partial-process': ('ambient-observed', 'live', 'accepted', 'process-observation', 'partial', 'unknown', 'unknown'),
        'failed-process': ('ambient-observed', 'failed', 'failed', 'process-observation', 'partial', 'stale', 'mismatched'),
        'invalid': ('none', 'failed', 'failed', 'not-assessed', 'invalid', 'not-assessed', 'not-assessed'),
        'absent': ('none', 'absent', 'not-run', 'not-assessed', 'not-assessed', 'not-assessed', 'not-assessed'),
    }[profile]
    return build_evidence_receipt(
        subject={'module': 'Main', 'candidate': 'Main.test', 'goal': 'True', 'localContext': []},
        execution_binding=binding, observation_state=state, operation_outcome=outcome,
        authority_basis=authority, analysis_completeness=completeness,
        source_freshness=freshness, environment_match=environment,
        environment_ref='sha256:' + 'a' * 64, check_run_ref='check:' + 'b' * 64,
        limitations=['Original scope limitation.'],
    )


def expected_observation(source_state, path):
    if source_state in {'failed', 'absent'}:
        return source_state
    if 'aggregate' in path:
        return 'derived'
    if source_state == 'stored' or {'sqlite-row', 'dossier'}.intersection(path):
        return 'stored'
    return source_state


@pytest.mark.parametrize('profile', [
    'accepted', 'residual', 'rejected', 'partial-process', 'failed-process',
    'invalid', 'absent', 'query', 'missing-query',
])
def test_all_three_boundary_paths_preserve_scope_and_exact_receipt_identity(profile):
    source = source_receipt(profile)
    before = copy.deepcopy(source)
    identities = {}
    for path in product(BOUNDARIES, repeat=3):
        result = source
        for boundary in path:
            result = project_evidence_receipt(result, projection_kind=boundary)
        state = expected_observation(source['observationState'], path)
        assert result == {**source, 'observationState': state,
                          'receiptIdentity': result['receiptIdentity']}, path
        # Different transport routes to the same observation carry one identity.
        assert result['receiptIdentity'] == identities.setdefault(state, result['receiptIdentity'])
    assert source == before
    assert len(list(product(BOUNDARIES, repeat=3))) == 343


@pytest.mark.parametrize('profile', ['accepted', 'residual', 'rejected', 'partial-process'])
def test_lost_execution_binding_cannot_be_recovered_by_any_later_boundary(profile):
    source = source_receipt(profile)
    stored = project_evidence_receipt(source, projection_kind='sqlite-row', execution_binding='none',
                                      limitations=['Historical execution unavailable.'])
    for boundary in BOUNDARIES:
        result = project_evidence_receipt(stored, projection_kind=boundary)
        assert result['executionBinding'] == 'none'
        assert set(source['limitations']) < set(result['limitations'])
        for stronger in ['ambient-observed', 'explicit-pinned']:
            with pytest.raises(ValueError, match='executionBinding'):
                project_evidence_receipt(result, projection_kind=boundary, execution_binding=stronger)
