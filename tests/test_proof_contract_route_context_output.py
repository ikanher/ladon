"""Evidence capacity must stop before retaining an oversized goal result."""
from ladon.proof_contract_route_context import _admit_check, _base


def test_large_evidence_is_not_attached_or_promoted():
    result = _base()
    result['binding'] = {'limits': {'max_rss_bytes': 12 * 1024**3}}
    result['goals'] = [{'id': 'source-reading', 'status': 'unresolved'}]
    checked = {'result': {'untrustedEvidence': 'x' * (8 * 1024**2)}}
    assert _admit_check(result, checked, 'by trivial') is False
    assert result['diagnostic']['code'] == 'output-limit'
    assert 'result' not in result['goals'][0]
    assert result['demandDischarged'] is False


def test_memory_guidance_survives_oversized_evidence():
    result = _base()
    result['binding'] = {'limits': {'max_rss_bytes': 1024**2}}
    checked = {'memoryLimited': True, 'result': {'evidence': 'x' * (8 * 1024**2)}}
    assert _admit_check(result, checked, 'by trivial') is False
    assert result['memoryReportBackRequired'] is True
    assert 'Stop progress and report back to user' in result['diagnostic']['message']
