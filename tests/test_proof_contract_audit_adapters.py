"""Exercise existing operation semantics through the public bounded audit API."""
import json

from support.proofir_v3_native import ENVIRONMENT
from test_proof_contract_audit_boundaries import _run, _version_only_runner
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_obligation_bundles import _request
from test_proof_contract_source import prose_inputs
from test_proof_contract_worker_scratch import _repo

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_obligation_artifacts import request_payload


def test_obligations_then_native_inspection_keep_conditional_authority(tmp_path):
    _, request = _request()
    context = {'artifacts': [request.derivation_artifact, *request.contract_artifacts]}
    plan = _fixture_plan(stages=[
        {'id': 'demands', 'operation': 'obligations', 'request': {
            'graph': request.derivation_artifact, 'contracts': request.contract_artifacts,
            'request': request_payload(request), 'analysisId': 'analysis:audit-demands'}},
        {'id': 'inspect', 'operation': 'inspect', 'request': {
            'artifact': {'auditStage': 'demands', 'pointer': ''}, 'context': context}},
    ])
    report = _run(_write_plan(tmp_path / 'plan.json', plan), tmp_path / 'run')
    assert report['status'] == 'completed', report
    artifact = json.loads((tmp_path / 'run/stages/inspect.json').read_text())['result']
    assert artifact['payload']['stage'] == 'obligations'
    assert artifact['payload']['result']['checkerAuthority'] == 'none'
    assert artifact['payload']['result']['mathematicalFalsity'] == 'not-established'


def test_prose_snapshot_and_inspection_preserve_pre_match_attribution(tmp_path):
    root, _source, _other, _concurrent, lake, lean, _hash, _context = _repo(tmp_path / 'repo')
    interpretation, contract, origins = prose_inputs(root)
    plan = _fixture_plan(stages=[
        {'id': 'reading', 'operation': 'produce-prose', 'request': {
            'interpretation': interpretation, 'contract': contract, 'featureOrigins': origins,
            'alternativeId': 'reading:audit', 'environmentRef': ENVIRONMENT, 'author': 'fixture'}},
        {'id': 'inspect', 'operation': 'inspect', 'request': {
            'snapshot': {'auditStage': 'reading', 'pointer': ''}}},
    ])
    plan.update(repoRoot=str(root), sourceFiles=['claim.txt'])
    report = _run(_write_plan(tmp_path / 'plan.json', plan), tmp_path / 'run',
                  runner=_version_only_runner(lake, lean))
    assert report['status'] == 'completed', report
    snapshot = json.loads((tmp_path / 'run/stages/reading.json').read_text())['result']
    checked = json.loads((tmp_path / 'run/stages/inspect.json').read_text())['result']
    assert checked == snapshot
    assert snapshot['phase'] == 'pre-match'
    assert snapshot['fidelity'] == 'attributed-unreviewed'
    assert snapshot['contract']['features']['regularity']['state'] == 'unknown'


def test_stricter_child_deadline_is_retained_and_partial_work_is_not_promoted(tmp_path):
    plan = _fixture_plan()
    plan['stages'][0]['request']['request']['bounds']['deadlineUtc'] = '2000-01-01T00:00:00Z'
    path = _write_plan(tmp_path / 'plan.json', plan)
    original = path.read_bytes()
    calls = []

    def tracked(command, **kwargs):
        calls.append(command)
        return run_bounded_target_process(command, **kwargs)

    result = _run(path, tmp_path / 'run', runner=tracked)
    assert result['status'] == 'partial', result
    assert len(calls) == 1
    assert path.read_bytes() == original
    artifact = json.loads((tmp_path / 'run/stages/propagate.json').read_text())['result']
    assert artifact['payload']['result']['complete'] is False
    assert not (tmp_path / 'run/stages/inspect.json').exists()
