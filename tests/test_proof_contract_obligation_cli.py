"""Public obligations planning and inspection retain immutable inputs and results."""
import json
from dataclasses import replace

from test_proof_contract_cli import invoke
from test_proof_contract_obligation_bundles import _request

ALIASES = {'goal_ref': 'goalRef', 'rule_bindings': 'ruleBindings',
           'endpoint_interfaces': 'endpointInterfaces', 'scope_bindings': 'scopeBindings',
           'desired_contract': 'desiredContract', 'desired_reading_identity': 'desiredReadingIdentity',
           'described_route_step_refs': 'describedRouteStepRefs',
           'per_application_backward_choices': 'perApplicationBackwardChoices',
           'route_priorities': 'routePriorities', 'bounds': 'bounds'}


def _files(tmp_path, *, expired=False):
    _, request = _request()
    if expired:
        request = replace(request, bounds={'deadlineUtc': '2000-01-01T00:00:00Z'})
    data = {'graph': request.derivation_artifact,
            'request': {v: getattr(request, k) for k, v in ALIASES.items()},
            'context': {'artifacts': [request.derivation_artifact, *request.contract_artifacts]}}
    data.update({f'contract-{i}': c for i, c in enumerate(request.contract_artifacts)})
    files = {}
    for name, value in data.items():
        path = tmp_path / (name + '.json')
        path.write_text(json.dumps(value))
        files[name] = path
    return files


def _invoke(files, output):
    args = ['obligations', '--derivation', files['graph'], '--request', files['request'],
            '--analysis-id', 'analysis:cli-bundle', '--output', output]
    for name, path in files.items():
        if name.startswith('contract-'):
            args += ['--contract', path]
    return invoke(*args)


def test_cli_plan_and_inspect_preserve_full_bundle_and_collisions(tmp_path):
    files = _files(tmp_path)
    output = tmp_path / 'obligations.json'
    process = _invoke(files, output)
    assert process.returncode == 0, process.stdout + process.stderr
    before = output.read_bytes()
    checked = invoke('inspect', '--input', output, '--context', files['context'])
    assert checked.returncode == 0, checked.stdout + checked.stderr
    result = json.loads(checked.stdout)
    assert result['payload']['stage'] == 'obligations'
    assert any('obligationBundle' in r for r in result['payload']['result']['routeComparisons'])
    assert _invoke(files, output).returncode == 2
    assert output.read_bytes() == before


def test_cli_expired_partial_plan_remains_historically_inspectable(tmp_path):
    files = _files(tmp_path, expired=True)
    output = tmp_path / 'partial.json'
    process = _invoke(files, output)
    assert process.returncode == 0, process.stdout + process.stderr
    checked = invoke('inspect', '--input', output, '--context', files['context'])
    assert checked.returncode == 0, checked.stdout + checked.stderr
    result = json.loads(checked.stdout)['payload']['result']
    assert result['status'] == 'partial'
    assert result['coverage']['pendingBranches']
    assert result['mathematicalFalsity'] == 'not-established'


def test_cli_drift_invalidates_old_bundle_without_overwrite(tmp_path):
    files = _files(tmp_path)
    output = tmp_path / 'obligations.json'
    assert _invoke(files, output).returncode == 0
    before = output.read_bytes()
    files['context'].write_text(json.dumps({'artifacts': []}))
    checked = invoke('inspect', '--input', output, '--context', files['context'])
    assert checked.returncode == 2
    assert output.read_bytes() == before


def test_cli_rejects_extra_request_authority_without_output(tmp_path):
    files = _files(tmp_path)
    request = json.loads(files['request'].read_text())
    request['proofAccepted'] = True
    files['request'].write_text(json.dumps(request))
    output = tmp_path / 'invalid.json'
    assert _invoke(files, output).returncode == 2
    assert not output.exists()
