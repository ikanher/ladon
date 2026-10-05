"""Record ordinary installed CLI controls outside the checkout; never run Lean."""
import json
import os
from dataclasses import asdict
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process

root = Path('/home/codex/projects/ladon')
state = root / '.codex/state/exposition-scope-r61'
run = Path((state / 'run-path').read_text().strip())
fixture = run / 'field-fixture'
field = run / 'field'
field.mkdir(exist_ok=True)
original = Path('/home/codex/.cache/ladon-reader-loop-r49/shared/evidence')
bundle = original.parent / 'result.zip'
index = json.loads((original / 'bundle.json').read_text())
artifact_options = [value for row in index['inventory'] if row['role'] == 'artifact'
                    for value in ('--artifact', str(original / row['path']))]
env = dict(os.environ)
for name in ('PYTHONPATH', 'PYTHONHOME', 'PYTEST_ADDOPTS'):
    env.pop(name, None)


def command(runtime, name, arguments, expected=0):
    receipt_path = field / (name + '.command.json')
    if receipt_path.exists():
        raise SystemExit('Preserve historical trial; select a new label, never overwrite.')
    budget = json.loads((state / 'budget.json').read_text())
    remaining = budget['budgetSeconds'] - budget['chargedUpperBoundSeconds']
    if remaining < 1:
        raise SystemExit('Cumulative r61 offline field budget exhausted.')
    argv = [str(run / runtime / 'bin/ladon'), 'result', *arguments]
    result = run_bounded_target_process(argv, cwd=Path('/tmp'), env=env,
                                        timeout_seconds=min(60, remaining),
                                        max_output_bytes=8388608, max_rss_bytes=34359738368)
    (field / (name + '.stdout')).write_text(result.stdout)
    (field / (name + '.stderr')).write_text(result.stderr)
    receipt = asdict(result)
    receipt['stdout'] = {'path': name + '.stdout', 'bytes': len(result.stdout.encode())}
    receipt['stderr'] = {'path': name + '.stderr', 'bytes': len(result.stderr.encode())}
    receipt.update(cwd='/tmp', expectedExitCode=expected, runtime=runtime)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    budget['chargedUpperBoundSeconds'] += result.elapsed_seconds
    budget['trials'].append({'path': str(receipt_path), 'chargedSeconds': result.elapsed_seconds})
    (state / 'budget.json').write_text(json.dumps(budget, indent=2) + '\n')
    print(json.dumps({'name': name, 'exitCode': result.returncode, 'seconds': result.elapsed_seconds,
                      'peakRssBytes': result.peak_rss_bytes}), flush=True)
    assert result.returncode == expected and not (result.timed_out or result.memory_limited or result.output_limited)
    if expected:
        assert not result.stdout
        return json.loads(result.stderr)
    assert not result.stderr and len(result.stdout.encode()) <= 32768
    if '--format' in arguments and arguments[arguments.index('--format') + 1] == 'text':
        return {key: json.loads(value) for key, value in (line.split(': ', 1) for line in result.stdout.splitlines())}
    return json.loads(result.stdout)


def exposition(runtime, name, control, claim, component, fmt='json', changed=False):
    manifest = fixture / ('changed-manifest.json' if changed else 'manifest.json')
    args = ['guide', str(manifest), '--guide-inputs', str(fixture / (control + '-guide.json')),
            '--assessments', str(fixture / 'assessments.json'), *artifact_options,
            '--section', 'exposition', '--claim', claim, '--component', component, '--format', fmt]
    return command(runtime, name, args)


def run_controls():
    claim = 'cor:fixed-epoch-all-horizon'
    transcript = command('py311', 'bundle-transcript', ['inspect', str(bundle), '--claim', claim, '--component', 'transcript'])
    card = transcript['rows'][0]
    assert card['statementScope'] == 'whole-claim-context'
    assert card['claimComponentCoverage']['mapped'] == 1 and card['claimComponentCoverage']['unmapped'] == 1
    assert all(row['statementAuthority'] == 'stored-canonical-type-text' for row in card['formalStatements'])
    average = command('py311', 'bundle-average', ['inspect', str(bundle), '--claim', claim, '--component', 'average'])
    assert average['rows'][0]['mapping']['status'] == 'unmapped'
    assert average['rows'][0]['formalStatements'] == []
    assert any(row['kind'] == 'conventional-only' for row in average['rows'][0]['assessments'])
    original_guide = command('py311', 'bundle-propagation', ['guide', str(bundle), '--section', 'exposition',
        '--claim', 'lem:binomial-propagation', '--component', 'propagation'])
    assert original_guide['rows'][0]['selectedComponent']['componentScope']['status'] == 'reported'
    a = exposition('py311', 'correct-json', 'correct', 'lem:binomial-propagation', 'propagation')
    b = exposition('py311', 'correct-text', 'correct', 'lem:binomial-propagation', 'propagation', 'text')
    assert a == b
    row = a['rows'][0]
    assert row['reviewStatus'] == 'current-attributed-reviews' and row['reviews'][0]['status'] == 'approved'
    assert '0 ≤ Mf.DP.fixedEpochCenterGap point h boundary' in row['supportingStatements'][0]['typeText']
    omitted = exposition('py311', 'omitted-boundary', 'omitted-boundary', 'lem:binomial-propagation', 'propagation')
    assert omitted['rows'][0]['reviews'][0]['status'] == 'disputed'
    assert 'unresolved' in omitted['rows'][0]['reviews'][0]['rationale']
    broad = exposition('py311', 'broadened-average', 'broadened-average', claim, 'average')
    assert broad['rows'][0]['selectedComponent']['formalStatements'] == []
    assert broad['rows'][0]['selectedComponent']['mapping']['status'] == 'unmapped'
    historical = exposition('py311', 'historical', 'correct', 'lem:binomial-propagation', 'propagation', changed=True)
    assert historical['rows'][0]['paragraph']['currency'] == 'historical'
    assert historical['rows'][0]['supportingStatements'] == []
    assert historical['rows'][0]['selectedComponent']['formalStatements'] == []
    assert historical['rows'][0]['recheckNotices']
    for value in (a, omitted, broad, historical):
        assert value['rows'][0]['mathematicalVerdict'] == 'not-inferred'
        assert value['rows'][0]['reuseApplicability'] == 'not-checked'
    other = exposition('py312', 'py312-correct', 'correct', 'lem:binomial-propagation', 'propagation')
    assert other == a
    error = command('py312', 'py312-invalid-component', ['guide', str(bundle), '--section', 'exposition',
        '--claim', 'lem:binomial-propagation', '--component', 'missing'], expected=2)
    assert error['exitClass'] == 'invocation'
    (field / 'assertions.json').write_text(json.dumps({'status': 'passed', 'recordedCommands': 10,
        'scope': 'root-authored deterministic controls on ordinary installed CLI; no fresh readers or Lean checks'}, indent=2) + '\n')


run_controls()
