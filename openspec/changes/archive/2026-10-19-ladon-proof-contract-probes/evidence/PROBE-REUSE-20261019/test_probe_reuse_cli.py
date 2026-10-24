"""The ordinary check-probe CLI accepts a prior result for exact reuse."""
import json

from test_proof_contract_application_probe_boundaries import request

from ladon.proof_contract_cli import contract_main


def test_check_probe_loads_prior_result_and_passes_it_as_cache(tmp_path, monkeypatch, capsys):
    import ladon.proof_contract_probes as probes

    current = request()
    inputs = tmp_path / 'request.json'
    terms = tmp_path / 'terms.json'
    prior = tmp_path / 'prior-result.json'
    inputs.write_text(json.dumps(current))
    terms.write_text('{}')
    cache = {'schema': 'ladon-application-probe-cache-v1',
             'planId': 'sha256:' + 'a' * 64, 'goals': []}
    prior.write_text(json.dumps({'schema': 'ladon-application-probe-v1', 'cache': cache}))
    observed = {}

    def check(request_value, plan_id, terms_value, *, cached_result=None):
        observed.update(request=request_value, plan_id=plan_id, terms=terms_value,
                        cached_result=cached_result)
        return {'schema': 'ladon-application-probe-v1', 'status': 'unresolved',
                'planId': plan_id, 'goals': [], 'residuals': [], 'diagnostic': None,
                'checkerAuthority': 'none', 'wholeMethodAuthority': 'none',
                'mathematicalFalsity': 'not-established', 'memoryReportBackRequired': False}

    monkeypatch.setattr(probes, 'check_application_probe', check)
    status = contract_main(['check-probe', '--input', str(inputs), '--plan-id', cache['planId'],
        '--terms', str(terms), '--reuse-result', str(prior)])
    assert status == 2
    assert observed == {'request': current, 'plan_id': cache['planId'], 'terms': {},
                        'cached_result': cache}
    assert json.loads(capsys.readouterr().out)['checkerAuthority'] == 'none'
