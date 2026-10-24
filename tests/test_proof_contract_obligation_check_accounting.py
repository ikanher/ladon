"""Evidence accounting and early worker failures retain complete stop reports."""
import json

from test_proof_contract_obligation_check_boundaries import _request

from ladon.proof_contract_obligation_checks import check_obligation_sources
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def test_validation_memory_stop_is_reported_without_source_work(tmp_path, monkeypatch):
    from ladon import proof_contract_obligation_supervision as supervision

    message = memory_limit_message(DEFAULT_MAX_RSS_BYTES, DEFAULT_MAX_RSS_BYTES + 1)
    monkeypatch.setattr(supervision, 'run_obligation_validation', lambda *args, **kwargs: {
        'status': 'incomplete', 'result': None,
        'diagnostic': {'code': 'memory-limit', 'message': message}})
    report = check_obligation_sources(_request(tmp_path))
    assert report['status'] == 'incomplete'
    assert report['memoryReportBackRequired'] is True
    assert report['stopReason'] == message
    assert report['sourceChecks'] == []


def test_aggregate_evidence_count_includes_identical_saved_summary(tmp_path, monkeypatch):
    from ladon import proof_contract_obligation_supervision as supervision

    monkeypatch.setattr(supervision, 'run_obligation_validation', lambda *args, **kwargs: {
        'status': 'rejected', 'result': None,
        'diagnostic': {'code': 'native-validation', 'message': 'rejected'}})
    report = check_obligation_sources(_request(tmp_path))
    output = tmp_path / 'run'
    total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    assert report['resourceAccounting']['evidenceBytes'] == total
    assert total <= 8 * 1024**2
    assert json.loads((output / report['summaryPath']).read_text()) == report
