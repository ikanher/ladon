"""Source-run preflight must reject safely before any formal work."""
import importlib
import time


def _request(tmp_path):
    return {'repoRoot': tmp_path, 'outputDir': tmp_path / 'run',
            'analysisArtifact': {}, 'context': {'artifacts': []},
            'sourceBindings': {'parentSnapshot': {}, 'parentReadingId': 'reading:test',
                               'providers': []},
            'deadlineMonotonic': time.monotonic() + 30, 'maxCheckAttempts': 1,
            'limits': {'timeout_seconds': 1, 'max_output_bytes': 8 * 1024**2,
                       'max_rss_bytes': 12 * 1024**3}}


def _rejecting_validation(monkeypatch):
    from ladon import proof_contract_obligation_supervision as supervised

    calls = []

    def reject(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'rejected', 'result': None,
                'diagnostic': {'code': 'native-validation', 'message': 'invalid artifact'}}

    monkeypatch.setattr(supervised, 'run_obligation_validation', reject)
    return calls


def test_paths_reach_native_validation_and_rejection_stays_rejected(tmp_path, monkeypatch):
    calls = _rejecting_validation(monkeypatch)
    module = importlib.import_module('ladon.proof_contract_obligation_checks')
    result = module.check_obligation_sources(_request(tmp_path))
    assert len(calls) == 1
    assert result['status'] == 'rejected'
    assert result['wholeMethodAuthority'] == 'none'
    assert not result['sourceChecks']


def test_existing_empty_run_receives_no_summary_or_other_mutation(tmp_path, monkeypatch):
    calls = _rejecting_validation(monkeypatch)
    module = importlib.import_module('ladon.proof_contract_obligation_checks')
    request = _request(tmp_path)
    output = request['outputDir']
    output.mkdir()
    (output / 'sentinel').write_bytes(b'preserve')
    request['repoRoot'], request['outputDir'] = str(tmp_path), str(output)
    result = module.check_obligation_sources(request)
    assert result['status'] == 'rejected'
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {'sentinel': b'preserve'}
    assert not calls


def test_escaped_json_size_is_bounded_before_validation(tmp_path, monkeypatch):
    calls = _rejecting_validation(monkeypatch)
    module = importlib.import_module('ladon.proof_contract_obligation_checks')
    request = _request(tmp_path)
    request['repoRoot'], request['outputDir'] = str(tmp_path), str(request['outputDir'])
    request['analysisArtifact'] = {'escape': '"' * (5 * 1024**2)}
    result = module.check_obligation_sources(request)
    assert result['status'] == 'rejected'
    assert not calls
    assert not (tmp_path / 'run').exists()


def test_malformed_closed_request_reports_bounded_failure(tmp_path):
    module = importlib.import_module('ladon.proof_contract_obligation_checks')
    request = _request(tmp_path)
    request['unexpected'] = 'secret' * 10000
    result = module.check_obligation_sources(request)
    assert result['status'] == 'rejected'
    assert result.get('diagnostic')
    assert len(str(result)) < 10000
    assert not (tmp_path / 'run').exists()
