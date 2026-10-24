"""A killed audit stage must preserve and detach the goal lease it delegated."""
import json
import os
import signal
import sys
from pathlib import Path

from test_proof_contract_application_probe_contract import TEMPLATE, fixture
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_worker_scratch import _repo, _shim

from ladon.lean_toolchain import verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process


def test_outer_stage_timeout_recovers_a_delegated_goal_without_deleting_its_bytes(tmp_path):
    from ladon.proof_contract_audit import run_contract_audit

    root, _source, _other, _concurrent, lake, lean, _hash, _context = _repo(tmp_path / 'repo')
    data = fixture()
    for artifact in data['context']['artifacts']:
        if artifact['artifactKind'] == 'proofir.interpretation':
            source = artifact['payload']['record']['source']
            (root / source['path']).write_text(source['quote'])
    shim = tmp_path / 'shim'
    _shim(shim)
    script = shim / 'route_worker_bootstrap.py'
    text = script.read_text().replace('def _block_at_capture(request):',
        'def _block_at_capture(request):\n    import signal\n    signal.signal(signal.SIGTERM, signal.SIG_IGN)')
    text = text.replace('"captureReached": True,', '"captureReached": True, "pid": os.getpid(),')
    text = text.replace('concurrent.write_text("-- changed by concurrent source job\\n")',
                        'concurrent.write_text("-- preexisting concurrent job source\\n")')
    text = text.replace('ladon.proof_contract_route_context_worker',
                        'ladon.proof_contract_probe_worker')
    text = text.replace('route_worker._verify_route_inputs', 'route_worker._verify_pair')
    script.write_text(text)
    marker = tmp_path / 'marker.json'
    bootstrap = '''import hashlib,os,sys,time
from pathlib import Path
from ladon.lean_toolchain import resolve_toolchain_context
import ladon.proof_slice as slices
slices.pinned_toolchain=lambda root: resolve_toolchain_context(Path(root),
    lake_path=Path(os.environ['LADON_TEST_LAKE']),
    lean_path=Path(os.environ['LADON_TEST_LEAN']),environment=os.environ)
import ladon.proof_contract_probes as probes
def fake_check(request, plan_id, terms, **kwargs):
    from ladon.proof_contract_obligation_supervision import _execute_job
    from ladon.process_supervisor import run_bounded_target_process
    root=Path(request['repoRoot'])
    owned={'repoRoot':str(root),'sourcePath':'Source.lean',
        'sourceDigest':'sha256:'+hashlib.sha256((root/'Source.lean').read_bytes()).hexdigest(),
        'goal':'True','term':'True.intro','symbols':{},'binding':{}}
    job={'version':1,'operation':'check-probe-goal','request':owned}
    state={'receipt':None,'inputDigest':None,'bounds':None}
    bounds={**request['limits'],'timeout_seconds':min(2,request['limits']['timeout_seconds']),
        'deadlineMonotonic':request['deadlineMonotonic']}
    def run_goal(command,**options):
        env={**options['env'],'PYTHONPATH':os.environ['LADON_TEST_SHIM']+os.pathsep+options['env']['PYTHONPATH'],
            'LADON_FAKE_LAKE':os.environ['LADON_TEST_LAKE'],
            'LADON_FAKE_LEAN':os.environ['LADON_TEST_LEAN'],
            'LADON_MARKER':os.environ['LADON_TEST_MARKER']}
        return run_bounded_target_process([sys.executable,'-m','route_worker_bootstrap'],
            **{**options,'env':env})
    return _execute_job(job,bounds,state,run_goal,worker_module='ladon.proof_contract_probe_worker')
probes.check_application_probe=fake_check
from ladon.proof_contract_audit_worker import main
raise SystemExit(main())
'''

    def runner(command, **kwargs):
        assert command[-1] == 'ladon.proof_contract_audit_worker'
        environment = {**kwargs['env'], 'LADON_TEST_LAKE': str(lake),
            'LADON_TEST_LEAN': str(lean), 'LADON_TEST_SHIM': str(shim),
            'LADON_TEST_MARKER': str(marker),
            'PYTHONPATH': os.pathsep.join([str(Path('tests').resolve()),
                                         kwargs['env']['PYTHONPATH']])}
        return run_bounded_target_process([sys.executable, '-c', bootstrap],
            **{**kwargs, 'env': environment, 'terminate_grace_seconds': .1})

    plan = _fixture_plan(stages=[{'id': 'check', 'operation': 'check-probe', 'request': {
        'request': {'context': data['context'], 'left': data['sides'][0],
                    'right': data['sides'][1], 'template': TEMPLATE},
        'planId': 'sha256:' + '0' * 64, 'terms': {}}}])
    plan.update(repoRoot=str(root), sourceFiles=['reading-0.txt', 'reading-1.txt'],
                limits={'timeout_seconds': 3, 'max_rss_bytes': 12 * 1024**3,
                        'max_output_bytes': 8 * 1024**2})
    # This source context intentionally includes every Lean file in the Git tree.
    from ladon.lean_toolchain import resolve_toolchain_context
    context = resolve_toolchain_context(root, lake_path=lake, lean_path=lean, environment=os.environ)
    try:
        report = run_contract_audit(_write_plan(tmp_path / 'plan.json', plan),
                                    tmp_path / 'run', runner=runner)
        assert marker.is_file(), report
        reached = json.loads(marker.read_text())
        assert report['code'] == 'timeout', report
        assert not (root / reached['generatedPath']).exists()
        quarantined = list(tmp_path.glob('.ladon-goal-quarantine-*/*/LadonCorrespondence.lean'))
        assert len(quarantined) == 1
        assert b'live tamper control' in quarantined[0].read_bytes()
        verify_toolchain_identities(context)
    finally:
        _kill_recorded_child(marker)


def _kill_recorded_child(marker):
    if not marker.is_file():
        return
    pid = json.loads(marker.read_text()).get('pid')
    if pid:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
