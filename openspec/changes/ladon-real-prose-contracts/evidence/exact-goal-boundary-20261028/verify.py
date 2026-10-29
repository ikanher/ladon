import hashlib
import json
import sqlite3
from pathlib import Path

base = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

roots = [('legacyRuntime', Path('.'), Path('.codex/state/real-prose-native/AUDIT-REVISION-FINAL.json')),
         ('primary', Path('.codex/state/navier-stokes-informed-diagnostic'),
          Path('.codex/state/navier-stokes-informed-diagnostic/SOURCE-MANIFEST.json'))]
for name in ['navier-source-pair-20261027', 'coordinate-norm-bridge-20261027']:
    root = Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence') / name
    roots.append((name, root, root/'ARTIFACTS.json'))
for name in ['proposition-feasibility-20261027', 'prose-observation-production-20261027',
             'prose-shape-v2-20261027', 'authored-real-native-20261027',
             'exact-connection-feasibility-20261027']:
    root = Path('openspec/changes/ladon-real-prose-contracts/evidence') / name
    roots.append((name, root, root/'ARTIFACTS.json'))
verified = {}
for key, root, manifest in roots:
    values = json.loads(manifest.read_text())
    assert all((root/name).is_file() and digest(root/name) == expected for name, expected in values.items()), key
    verified[key] = {'unchanged': True, 'files': len(values)}
old = Path('openspec/changes/ladon-real-prose-contracts/evidence/exact-connection-feasibility-20261027')
assert (base.parent/'real-prose-connection/Context-before-canonical.lean').read_bytes() == (old/'Context-before-canonical.lean').read_bytes()
helper = Path('src/ladon/lean/LadonProseExactGoal.lean')
result = json.loads((base/'INFORMED-RESULT.json').read_text())
process = json.loads((base/'INFORMED-PROCESS.json').read_text())
completion = json.loads((base/'INFORMED-COMPLETION.json').read_text())
capture = json.loads((base/'INFORMED-CAPTURE.json').read_text())['capture']
assert result['helperDigest'] == digest(helper) == digest(base/'informed-project/LadonProseExactGoal.lean')
assert capture['source']['digest'] == 'sha256:'+digest(base/'informed-project/ExactCase.lean')
assert completion['status'] == 'completed' and completion['replay']['status'] == 'accepted'
assert completion['trust']['accepted'] is True and completion['trust']['coverage'] == 'complete'
assert not set(completion['trust']['observedAxioms']) - {'Classical.choice','Quot.sound','propext'}
assert process['returncode'] == 0 and not any(process[k] for k in ['timed_out','output_limited','memory_limited'])
assert process['elapsed_seconds'] <= 600 and process['peak_rss_bytes'] <= 12*1024**3
assert len(process['stdout'].encode())+len(process['stderr'].encode()) <= 8*1024**2
assert '32 passed' in (base/'FINAL-CANONICAL-TESTS.txt').read_text()
assert '35 passed' in (base/'COMPATIBILITY.txt').read_text()
paths = list(Path('tests').glob('test_real_prose_exact_goal*.py'))
with sqlite3.connect('file:.codex/state/ultra-proof-contract.sqlite3?mode=ro',uri=True) as db:
    for path in paths:
        row = db.execute('SELECT sha256 FROM frozen_tests WHERE path=?',(str(path.resolve()),)).fetchone()
        assert row and row[0] == digest(path), str(path)
    revisions = db.execute('SELECT count(*) FROM frozen_test_revisions WHERE path=?',
        (str(Path('tests/test_real_prose_exact_goal.py').resolve()),)).fetchone()[0]
    assert revisions >= 1
assert Path('tests/test_real_prose_exact_goal.py').read_bytes() == (base/'quality-proposal/proposed.py').read_bytes()
verified['newHelper'] = {'path': str(helper), 'sha256': digest(helper)}
verified['frozenCurrentTests'] = {str(path): digest(path) for path in paths}
verified['approvedFrozenRefactorRevisionRetained'] = True
verified['componentTests'] = 32
verified['compatibilityTests'] = 35
verified['informedBoundary'] = {'status': result['status'], 'seconds': process['elapsed_seconds'],
    'peakRssBytes': process['peak_rss_bytes'], 'freshFormalAdmission': False, 'nativeConnection': False}
verified['oldProseCurrentnessRequiresReplay'] = True
verified['legacyAdmissionPredicatesUnchanged'] = True
verified['task22Complete'] = False
verified['committed'] = False
verified['pushed'] = False
(base/'VERIFICATION.json').write_text(json.dumps(verified,indent=2)+'\n')
print({'protectedInputs':verified['primary']['files'],'legacyRuntimeUnchanged':verified['legacyRuntime']['files'],
       'sealedPacketsUnchanged':len(roots)-2,'frozenTestsVerified':len(paths),
       'passedChecks':67,'informedBoundary':'kernel-replayed','nativeConnection':False})
