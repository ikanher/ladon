"""Prepare labelled paragraph controls from immutable r49/r60 materials."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

from ladon.result_guide_inputs import validate_result_guide
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import content_revision

state = Path('/home/codex/projects/ladon/.codex/state/exposition-scope-r61')
run = Path((state / 'run-path').read_text().strip())
fixture = run / 'field-fixture'
fixture.mkdir()
original = Path('/home/codex/.cache/ladon-reader-loop-r49/shared/evidence')
manifest = json.loads((original / 'manifest.json').read_text())
guide = json.loads((original / 'assets/00092.json').read_text())
assessment = original / 'assets/00089.json'
shutil.copy2(original / 'manifest.json', fixture / 'manifest.json')
shutil.copy2(assessment, fixture / 'assessments.json')
shutil.copy2(original / 'assets/00092.json', fixture / 'original-guide.json')


def write(name, value):
    (fixture / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def step_revision(step):
    value = {key: value for key, value in step.items() if key != 'revision'}
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return 'sha256:' + hashlib.sha256(b'ladon-result-guide-v1/step\0' + encoded).hexdigest()


def control(name, step_id, text, status, rationale, receipts):
    step = copy.deepcopy(next(row for row in guide['steps'] if row['id'] == step_id))
    step.update(explanation=text, prerequisites=[], author={'identity': 'root-labelled-synthetic-control', 'kind': 'model'})
    for receipt in receipts:
        source = Path('/home/codex/.cache/ladon-handoff-r60-i80pkq23') / receipt
        shutil.copy2(source, fixture / receipt) if not (fixture / receipt).exists() else None
        step['sources'].append({'locator': receipt, 'digest': 'sha256:' + hashlib.sha256(source.read_bytes()).hexdigest()})
    step['revision'] = step_revision(step)
    value = {'schema': guide['schema'], 'resultId': guide['resultId'], 'manifestRevision': manifest['revision'],
             'steps': [step], 'citations': [], 'reviews': [{
                 'id': 'synthetic-' + name, 'scope': 'explanation', 'stepId': step['id'],
                 'stepRevision': step['revision'], 'targetRevisions': step['targetRevisions'],
                 'reviewer': {'identity': 'root-labelled-control-not-independent-review', 'kind': 'model'},
                 'status': status, 'rationale': rationale, 'timestamp': '2026-10-05T00:00:00Z'}]}
    validate_result_guide(value, manifest)
    write(name + '-guide.json', value)
    return value


correct = ('Let point be a fixed-epoch point with point.epoch < point.horizon, h > 0, '
           'boundary ≥ 0 and query > boundary. If fixedEpochCenterGap point h boundary ≥ 0, '
           'the propagation lemma gives fixedEpochCenterGap point h query > 0.')
good = control('correct', 'center-propagation', correct, 'approved',
              'Synthetic scope control: the passage retains every displayed prerequisite. The r60 A '
              'receipt records an independently replayed application, not a review of proof strategy.',
              ['completion-a.stdout'])
control('omitted-boundary', 'center-propagation', correct.replace(
    'If fixedEpochCenterGap point h boundary ≥ 0, ', ''), 'disputed',
    'Synthetic altered control: the cited application lacks the boundary-gap premise; r60 B leaves '
    '0 ≤ Mf.DP.fixedEpochCenterGap point h boundary unresolved. Revise by adding that premise. '
    'This does not establish that the conclusion is false or the premise is necessary for every proof.',
    ['completion-b-json.stdout'])
control('broadened-average', 'conditional-all-horizons',
        'The supplied uniform transcript targets formally establish both transcript and average-only '
        'optimality under the sufficient condition.', 'with-differences',
        'Synthetic altered control: the average component has no formal mapping. Keep the transcript '
        'conclusion scoped to its bindings and describe the average-only strengthening as conventional '
        'exposition according to the supplied assessment; unformalized does not mean false.', [])
changed = copy.deepcopy(manifest)
claim = next(row for row in changed['claims'] if row['id'] == 'lem:binomial-propagation')
claim['statement'] += ' [Synthetic revision-change control; no live source was edited.]'
claim['revision'] = content_revision('claim', claim)
changed['revision'] = content_revision('manifest', changed)
validate_result_manifest(changed)
write('changed-manifest.json', changed)
write('controls.json', {'classification': 'root-authored synthetic engineering controls, not reader sessions or independent reviews',
                        'realManifestRevision': manifest['revision'], 'changedManifestRevision': changed['revision'],
                        'scope': 'offline projections; cited r60 receipts are historical explicit operations, never imported as fresh checks',
                        'cases': ['correct', 'omitted-boundary', 'broadened-average', 'changed-manifest']})
print(json.dumps({'fixture': str(fixture), 'manifestRevision': manifest['revision']}))
