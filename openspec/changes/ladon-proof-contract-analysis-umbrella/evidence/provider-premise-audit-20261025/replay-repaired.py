import hashlib
import json
import sys
from pathlib import Path
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal
from ladon.proof_slice import pinned_toolchain

repo = Path('/home/codex/projects/ladon')
evidence = repo / 'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/provider-premise-audit-20261025'
evidence = evidence / 'repaired'
evidence.mkdir(exist_ok=True)
root = repo / '.codex/state/navier-stokes-informed-diagnostic/formalization'
slice_path = repo / 'openspec/changes/ladon-scoped-slice-traversal/evidence/completion-roundtrip/actual-slice.json'
node = json.loads(slice_path.read_text())['nodes'][0]
original = root / 'NavierStokes/SmoothFamilyTorusInverse.lean'
key = sys.argv[1]
observation = node if key == 'application' else next(p['providerObservation'] for p in node['premises'] if str(p['occurrence']) == key)
destination = evidence / ('replay-' + key)
destination.mkdir()
source = original.read_text() + '\nexample : ' + observation['closedType'] + ' := by\n  skip\n'
path = root / '.ladon/provider-premise-audit' / ('ReplayRepaired' + key.title() + '.lean')
path.parent.mkdir(parents=True, exist_ok=True)
with path.open('x') as stream:
    stream.write(source)
(destination / 'source.lean').write_text(source)
(destination / 'term.lean.txt').write_text(observation['closedProof'])
(destination / 'input.json').write_text(json.dumps({'sliceSha256': hashlib.sha256(slice_path.read_bytes()).hexdigest(), 'sourceSha256': hashlib.sha256(original.read_bytes()).hexdigest(), 'sourcePath': str(path.relative_to(root)), 'case': key, 'maxRssBytes':12*1024**3, 'timeoutSecondsPerProcess':60}, indent=2)+'\n')
toolchain = pinned_toolchain(root)
capture = capture_source_goal(SourceGoalCaptureRequest(root, str(path.relative_to(root)), 'ReplayRepaired' + key.title(), len(source.splitlines()), 4, toolchain))
(destination / 'capture.json').write_text(json.dumps(capture, indent=2)+'\n')
print(json.dumps({'case':key, 'phase':'capture', 'status':capture['status'], 'diagnostic':capture.get('diagnostic')}), flush=True)
if capture['status'] != 'captured':
    sys.exit(2)
completion = complete_source_goal(SourceGoalCompletionRequest(root, capture['capture'], observation['closedProof'], toolchain))
(destination / 'completion.json').write_text(json.dumps(completion, indent=2)+'\n')
print(json.dumps({'case':key, 'phase':'completion', 'status':completion['status'], 'diagnostic':completion.get('diagnostic'), 'trust':completion.get('trust'), 'resources':completion.get('resourceAccounting')}), flush=True)
sys.exit(0 if completion['status'] == 'completed' else 3)
