"""Resource, custody and replay boundaries supplement the frozen acceptance set."""

import json
from copy import deepcopy

import pytest
from test_proof_contract_cli import invoke
from test_real_prose_observation_contract import inputs as _inputs_fixture
from test_real_prose_observation_contract import module, observe


@pytest.fixture
def inputs(tmp_path):
    return _inputs_fixture.__wrapped__(tmp_path)


def test_historical_inspection_and_explicit_replay(tmp_path, inputs):
    result = observe(tmp_path, inputs)
    inspection = module().inspect_prose_observation(result)
    assert inspection['sourceFreshness'] == 'not-checked'
    assert inspection['authority'] == 'none' and inspection['freshCheck'] is False
    snapshot = tmp_path / 'saved.json'
    snapshot.write_text(json.dumps(result))
    replay = invoke('replay-prose-bound', '--input', snapshot, '--root', tmp_path,
                    '--timeout-seconds', '60')
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)['status'] == 'observed'


def test_actual_deep_type_stops_bounded_expression_rendering(tmp_path, inputs):
    reading, context = inputs
    reading['formula']['binder']['domain'] = ' → '.join(['Nat'] * 160)
    reading['formula']['body'] = {'tag': 'const', 'name': 'True'}
    result = observe(tmp_path, (reading, context))
    assert result['status'] == 'unavailable'
    assert result['check']['result']['observation']['status'] == 'render-limit'
    assert 'depth' in result['check']['result']['observation']['reason']


@pytest.mark.parametrize('flag,code', [('timed_out', 'timeout'), ('output_limited', 'output-limit')])
def test_outer_resource_stop_does_not_launch_dependents(tmp_path, inputs, monkeypatch, flag, code):
    from ladon.process_supervisor import ProcessResult

    def stopped(*_args, **_kwargs):
        return ProcessResult((), -1, '', '', 0.01, **{flag: True})

    monkeypatch.setattr('ladon.proof_contract_obligation_supervision._run', stopped)
    result = observe(tmp_path, inputs)
    assert result['status'] == 'unavailable'
    assert result['check']['diagnostic']['code'] == code
    assert result['check']['result'] is None


def test_changed_context_during_observation_is_rejected(tmp_path, inputs, monkeypatch):
    import ladon.real_prose_worker as worker
    from ladon.real_prose_inputs import implementation_identity

    def changed(_job, _request, _source, _context, _execution, _result):
        (tmp_path / 'Context.lean').write_text('import Lean\n-- changed during execution\n')

    monkeypatch.setattr(worker, '_observe', changed)
    job = {'version': 1, 'root': str(tmp_path), 'workspace': str(tmp_path),
           'request': {'interpretation': inputs[0], 'context': inputs[1]},
           'deadlineMonotonic': 0, 'implementationDigest': implementation_identity(),
           'maxRssBytes': 12 * 1024**3, 'maxOutputBytes': 8 * 1024**2, 'previous': None}
    with pytest.raises(ValueError, match='changed during'):
        worker._compute(job)


def test_changed_compiled_context_is_rejected(tmp_path, inputs, monkeypatch):
    from ladon.real_prose_inputs import observation_identity

    result = observe(tmp_path, inputs)
    changed = deepcopy(result)
    inventory = changed['check']['result']['compiledInventory']['inventory']
    inventory['modules'][0]['digest'] = 'sha256:' + '0' * 64
    changed['snapshotId'] = observation_identity(changed)
    with pytest.raises(ValueError, match='compiled'):
        module().inspect_prose_observation(changed, tmp_path)


def test_bad_worker_owner_is_rejected_after_rehash(tmp_path, inputs):
    from ladon.real_prose_inputs import observation_identity

    result = observe(tmp_path, inputs)
    worker = result['check']['result']['observation']
    worker['target'] = 'Unrelated.Theorem'
    result['check']['result']['workerJson'] = json.dumps(worker)
    result['snapshotId'] = observation_identity(result)
    with pytest.raises(ValueError, match='identity'):
        module().inspect_prose_observation(result, tmp_path)


@pytest.mark.parametrize('limit', [0, 601, float('nan')])
def test_invalid_deadline_is_rejected_before_execution(tmp_path, inputs, limit):
    with pytest.raises(ValueError):
        module().observe_prose_bound(tmp_path, *inputs, timeout_seconds=limit)


def test_stopped_first_observation_cannot_be_promoted_after_rehash(tmp_path, inputs):
    from ladon.real_prose_inputs import observation_identity

    result = observe(tmp_path, inputs)
    result['check']['result']['processReceipts'][0]['memory_limited'] = True
    result['snapshotId'] = observation_identity(result)
    with pytest.raises(ValueError, match='stopped'):
        module().inspect_prose_observation(result)


def test_configured_cap_is_forwarded_without_automatic_increase(tmp_path, inputs, monkeypatch):
    from ladon.process_supervisor import ProcessResult

    seen = []

    def stopped(_data, bounds, _runner, **_kwargs):
        seen.append(bounds['max_rss_bytes'])
        return ProcessResult((), -1, '', '', 0.01, memory_limited=True, peak_rss_bytes=1)

    monkeypatch.setattr('ladon.proof_contract_obligation_supervision._run', stopped)
    cap = 64 * 1024**2
    result = module().observe_prose_bound(tmp_path, *inputs, max_rss_bytes=cap)
    assert result['status'] == 'unavailable' and seen == [cap]
    assert result['check']['processReceipt']['requestedMaxRssBytes'] == cap


def test_older_semantic_consumer_rejects_prose_observation(tmp_path, inputs):
    from ladon.proof_contracts import validate_contract

    with pytest.raises(ValueError):
        validate_contract(observe(tmp_path, inputs))


@pytest.mark.parametrize('encoded', ['[]', 'null', '"unrelated"'])
def test_nonobject_worker_output_is_rejected_structurally(encoded):
    from ladon.real_prose_expression import parse_worker

    with pytest.raises(TypeError, match='object'):
        parse_worker(encoded)


def test_replay_freshness_and_observation_share_the_supervised_job(tmp_path, inputs, monkeypatch):
    from ladon.process_supervisor import ProcessResult

    original = observe(tmp_path, inputs)
    seen = []

    def stopped(data, bounds, _runner, **_kwargs):
        job = json.loads(data)
        seen.append((job, dict(bounds)))
        return ProcessResult((), -1, '', '', 0.01, timed_out=True)

    monkeypatch.setattr('ladon.proof_contract_obligation_supervision._run', stopped)
    replay = module().replay_prose_observation(original, tmp_path, timeout_seconds=1)
    job, bounds = seen[0]
    assert replay['status'] == 'unavailable' and len(seen) == 1
    assert job['previous'] == original
    assert job['deadlineMonotonic'] == bounds['deadlineMonotonic']
    assert bounds['timeout_seconds'] == 1
