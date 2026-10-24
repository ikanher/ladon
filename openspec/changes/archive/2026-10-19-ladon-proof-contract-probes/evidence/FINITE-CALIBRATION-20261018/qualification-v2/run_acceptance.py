"""Serial public-CLI source controls; one 240-second clock, memory stop last."""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_probe_calibration import probe_calibration_profile

p = Path(sys.argv[1]).resolve()
origin = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else None
started = origin['startedMonotonic'] if origin else time.monotonic()
deadline = origin['deadlineMonotonic'] if origin else started + 240
root = p / 'probe-repo'
root.mkdir()
shutil.copyfile('tests/fixtures/proof_contract_planned_source/lean-toolchain', root / 'lean-toolchain')
profile = probe_calibration_profile()
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}
manifest = json.loads((p / 'RUNTIME.json').read_text())


def verify_runtime():
    for row in manifest['files']:
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']


def request():
    return {'repoRoot': str(root), 'left': [False, True, False, True, False],
            'right': [False, True, False, True, False], 'family': list(range(5)),
            'certificateRef': profile, 'deadlineMonotonic': deadline, 'limits': dict(limits)}


results = []


def run(name, req, expected_status):
    verify_runtime()
    assert time.monotonic() < deadline, 'Original clock expired; no further control attempted'
    (p / (name + '-request.json')).write_text(json.dumps(req, ensure_ascii=False, indent=2))
    output = p / (name + '-result.json')
    command = [str(Path('.venv/bin/python').absolute()), '-m', 'ladon.entrypoint',
               'investigation', 'contract', 'probe-calibration', '--input',
               str(p / (name + '-request.json')), '--output', str(output)]
    process = run_bounded_target_process(command, cwd=Path.cwd(),
        env={**os.environ, 'PYTHONPATH': 'src:tests'}, timeout_seconds=deadline-time.monotonic(),
        max_rss_bytes=limits['max_rss_bytes'], max_output_bytes=limits['max_output_bytes'])
    receipt = {'command': command, 'returnCode': process.returncode,
               'elapsedSeconds': process.elapsed_seconds, 'peakRssBytes': process.peak_rss_bytes,
               'timedOut': process.timed_out, 'memoryLimited': process.memory_limited,
               'outputLimited': process.output_limited, 'stdout': process.stdout, 'stderr': process.stderr}
    (p / (name + '-process.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    assert not (process.timed_out or process.memory_limited or process.output_limited), receipt
    result = json.loads(output.read_text())
    assert result['status'] == expected_status, (name, result)
    assert process.returncode == (2 if expected_status in ('rejected', 'incomplete') else 0)
    assert result['wholeMethodAuthority'] == 'none' and result['mathematicalFalsity'] == 'not-established'
    assert result['sourceFidelity'] == 'not-assessed'
    for goal in result['goals']:
        if 'result' in goal:
            raw = load_goal_evidence(root, goal['result'])
            if goal['status'] == 'checked-support':
                assert _accepted_check(raw)
    verify_runtime()
    results.append({'name': name, 'status': result['status'], 'goals': len(result['goals']),
                    'equivalence': result['objectEquivalence'], 'distinction': result['objectDistinction']})
    print(name, expected_status, round(time.monotonic()-started, 3), flush=True)
    return result


(p / 'SOURCE-START.json').write_text(json.dumps({'startedMonotonic': started,
    'deadlineMonotonic': deadline, 'budgetSeconds': 240, 'runtimeEntries': manifest['entries']}, indent=2))
verify_runtime()
equal = run('full-equal', request(), 'checked-object-equivalence')
assert equal['objectEquivalence'] and equal['certificateVerified'] and len(equal['goals']) == 3
unequal_request = request()
unequal_request['right'][4] = True
unequal = run('full-unequal', unequal_request, 'checked-object-distinction')
assert unequal['objectDistinction'] and not unequal['objectEquivalence'] and len(unequal['goals']) == 3
partial = request()
partial.update(family=[0, 1, 2, 3], certificateRef=None)
partial['right'][4] = True
incomplete = run('incomplete-uncertified', partial, 'scoped-agreement')
assert not incomplete['objectEquivalence'] and not incomplete['goals']
uncertified = request()
uncertified['certificateRef'] = None
assert not run('full-uncertified', uncertified, 'scoped-agreement')['objectEquivalence']
subset = request()
subset['family'] = [0, 1, 2, 3]
assert not run('incomplete-certificate', subset, 'rejected')['goals']
for field in ['objectClassId', 'sourceDigest', 'templateVersion']:
    wrong = request()
    wrong['certificateRef'] = {**profile, field: 'changed'}
    assert not run('wrong-' + field, wrong, 'rejected')['goals']
expired = request()
expired['deadlineMonotonic'] = started - 1
assert not run('expired', expired, 'incomplete')['goals']
# Deliberately last: do not retry or raise the memory cap after this stop.
memory_request = request()
memory_request['limits']['max_rss_bytes'] = 1024**2
memory = run('memory-last', memory_request, 'incomplete')
assert memory['memoryReportBackRequired'] is True and memory['diagnostic']['code'] == 'memory-limit'
assert len(memory['goals']) == 1 and 'Stop progress' in memory['diagnostic']['message']
verify_runtime()
(p / 'SOURCE-VERIFICATION.json').write_text(json.dumps({'status': 'PASS',
    'budgetSeconds': 240, 'elapsedSeconds': time.monotonic()-started,
    'runtimeEntries': manifest['entries'], 'runtimeUnchanged': True,
    'controls': results, 'actualAcceptedGoals': 6, 'memoryLastWithoutRetry': True}, indent=2))
print('SOURCE PASS', time.monotonic()-started, flush=True)
