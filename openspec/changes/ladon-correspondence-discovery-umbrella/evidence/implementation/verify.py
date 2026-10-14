"""Verify recorded identities and bookkeeping, never mathematical correspondence."""
from pathlib import Path
import hashlib
import json
import runpy

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inventory = json.loads((HERE / 'source-inventory.json').read_text())
for row in inventory['records']:
    assert digest(HERE / row['frozenPath']) == row['sha256'], row['frozenPath']

coverage = json.loads((HERE / 'coverage.json').read_text())
for selection in coverage['ranges']:
    assert digest(HERE / selection['source']) == selection['sourceSha256']
    spans = [r for r in coverage['claims'] if r['source'] == selection['source']]
    observed = [n for r in spans for n in range(r['lines'][0], r['lines'][1] + 1)]
    assert observed == list(range(selection['selectedLines'][0], selection['selectedLines'][1] + 1))
assert sum(r['formalSupport'] is not None for r in coverage['claims']) == 2
assert any(r['reviewStatus'] == 'unexamined' for r in coverage['claims'])

for comparison in json.loads((HERE / 'contracts.json').read_text())['comparisons']:
    for key in ('claimSource', 'formalSource'):
        source = comparison[key]
        assert digest(HERE / source['path']) == source['sha256']

allowed = {'propext', 'Classical.choice', 'Quot.sound'}
for name, count in [('controls-01', 10), ('target-01', 3)]:
    run = HERE / 'runs' / name
    record = json.loads((run / 'record.json').read_text())
    assert record['returncode'] == 0 and record['policyAccepted']
    assert len(record['expected']) == count
    assert digest(run / 'stdout.txt') == record['stdoutSha256']
    for subject in record['expected']:
        assert set(record['observedAxioms'][subject]) <= allowed
    sources = list(run.glob('*.lean'))
    assert len(sources) == 1 and digest(sources[0]) == record['sourceSha256']
failed = json.loads((HERE / 'runs/original-goal-01/record.json').read_text())
assert failed['returncode'] != 0 and not failed['policyAccepted']

reference = json.loads((HERE / 'evaluation/reference-labels.json').read_text())
assert len(reference['cases']) == 14
assert sum(r['class'] == 'excerpt' for r in reference['cases']) == 12
assert sum(r['expectedDiscrepancy'] for r in reference['cases'] if r['class'] == 'excerpt') == 6
for row in reference['cases']:
    assert digest(HERE / 'evaluation/cases' / row['case'] / 'INPUT.md') == row['sourceSha256']

evaluation = 'not-run'
if (HERE / 'evaluation/scores.json').exists():
    result = runpy.run_path(str(HERE / 'evaluation/verify_evaluation.py'))['verify']()
    assert result['status'] == 'passed'
    evaluation = '28 first attempts recorded; identity/accounting verified; scores attributed'

print(json.dumps({'status': 'passed', 'scope': 'recorded identity and bookkeeping checks only',
    'frozenSources': len(inventory['records']), 'sourceSpans': len(coverage['claims']),
    'expectedControlAxiomReports': 10, 'expectedTargetAxiomReports': 3,
    'preparedCases': 14, 'detectionEvaluation': evaluation,
    'correspondenceAuthority': 'attributed source reviews, not checked here'}))
