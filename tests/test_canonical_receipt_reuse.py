"""Private reuse retains each recorded receipt's semantic decision."""
import copy

import pytest
from support.semantic_evidence import semantic_evidence
from support.semantic_execution import with_execution_context
from test_stored_receipt_ownership import rebind_receipt

from ladon._canonical_population import _CanonicalPopulation
from ladon.evidence_receipt_readers import _stored_check_receipt_owned, stored_check_receipt
from ladon.proofir_v3 import detached_content_id


def compare(values):
    owner = _CanonicalPopulation(values)
    check = owner.artifacts[-1]
    environments = list(owner.artifacts[:-1])
    try:
        raw = stored_check_receipt(values[-1], environment_artifacts=values[:-1],
                                   projection_kind='dossier')
    except ValueError as error:
        with pytest.raises(type(error)) as reused:
            _stored_check_receipt_owned(owner, check, environments, projection_kind='dossier')
        assert str(reused.value) == str(error)
    else:
        assert _stored_check_receipt_owned(owner, check, environments,
                                          projection_kind='dossier') == raw


@pytest.mark.parametrize('case', ['accepted', 'applicable-with-residuals', 'rejected', 'compiled', 'timeout'])
@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
def test_complete_partial_rejected_and_process_receipts_match_raw(case, mode):
    values, _, _ = semantic_evidence('reused-receipt', status=case,
                                    scratch=case in {'compiled', 'timeout'})
    values, _ = with_execution_context(values, mode)
    compare(values)
    rebind_receipt(values, execution_binding='ambient-observed' if mode == 'explicit' else 'explicit-pinned')
    compare(values)


@pytest.mark.parametrize('metadata', [None, 'ambient-unbound', 'invalid', '{}', 'null',
                                    '{"selectionMode":"explicit","selectionMode":"ambient"}'])
def test_missing_and_malformed_context_keep_distinct_meanings(metadata):
    values, _, _ = semantic_evidence('reused-context')
    if metadata is not None:
        values, _ = with_execution_context(values, encoded_context=metadata)
    compare(values)
    # Changing the checker identity must retain the raw owner's decision,
    # including contradiction detection where a worker identity is recorded.
    check = values[1]
    check['payload']['checker']['executableDigest'] = 'sha256:' + 'f' * 64
    check['artifactId'] = detached_content_id(check)
    compare(values)


def test_absent_receipt_does_not_validate_unused_execution_metadata():
    values, _, _ = semantic_evidence('reused-absent')
    values, _ = with_execution_context(values, encoded_context='invalid')
    values[1]['extensions']['ladon.process-observation/v1'].pop('evidenceReceipt')
    values[1]['artifactId'] = detached_content_id(values[1])
    before = copy.deepcopy(values)
    compare(values)
    assert values == before
