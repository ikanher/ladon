import hashlib
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from ladon._bounded_json_graph import canonical
from ladon.bounded_json_transport import TransportLimits, unpack_json

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
             'exact-connection-feasibility-20261027', 'exact-goal-boundary-20261028']:
    root = Path('openspec/changes/ladon-real-prose-contracts/evidence') / name
    roots.append((name, root, root/'ARTIFACTS.json'))
verified = {}
for key, root, manifest in roots:
    values = json.loads(manifest.read_text())
    assert all((root/name).is_file() and digest(root/name) == expected for name, expected in values.items()), key
    verified[key] = {'unchanged':True, 'files':len(values)}
old_helper = Path('openspec/changes/ladon-real-prose-contracts/evidence/exact-goal-boundary-20261028/LadonProseExactGoal.lean')
assert digest(Path('src/ladon/lean/LadonProseExactGoal.lean')) == digest(old_helper)
original_authored = Path('openspec/changes/ladon-real-prose-contracts/evidence/authored-real-native-20261027/live/navier-produced.json')
assert digest(original_authored) == digest(Path('.codex/state/real-prose-native/live/navier-produced.json'))
wire = (base/'PAIR-WIRE.json').read_bytes()
value = unpack_json(wire)
formal_path = Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json')
original = {'formal':json.loads(formal_path.read_text()), 'authored':json.loads(original_authored.read_text())}
assert canonical(value) == canonical(original)
worker = json.loads((base/'WORKER-PROCESS.json').read_text())
outer = json.loads((base/'QUALIFICATION-PROCESS.json').read_text())
qualification = json.loads((base/'QUALIFICATION.json').read_text())
assert worker['stdoutDigest'] == 'sha256:'+digest(base/'PAIR-WIRE.json')
assert worker['stdoutBytes'] == len(wire) == qualification['wireBytes']
assert qualification['expandedBytes'] == len(canonical(value))
assert 8*1024**2 < qualification['expandedBytes'] <= 32*1024**2
for receipt in [worker, outer]:
    assert receipt['returncode'] == 0
    assert not any(receipt[key] for key in ['timed_out','memory_limited','output_limited'])
    assert receipt['elapsed_seconds'] <= 600 and receipt['peak_rss_bytes'] <= 12*1024**3
assert '61 passed' in (base/'FINAL-TESTS.txt').read_text()
assert '33 passed' in (base/'COMPATIBILITY.txt').read_text()
tests = list(Path('tests').glob('test_bounded_json_transport*.py'))
with sqlite3.connect('file:.codex/state/ultra-proof-contract.sqlite3?mode=ro',uri=True) as db:
    for path in tests:
        row = db.execute('SELECT sha256 FROM frozen_tests WHERE path=?',(str(path.resolve()),)).fetchone()
        assert row and row[0] == digest(path)
paths = [Path('src/ladon/bounded_json_transport.py'), Path('src/ladon/_bounded_json_graph.py'), *tests]
verified.update({'currentComponentRevision':{str(path):digest(path) for path in paths},
                 'componentTests':61, 'compatibilityTests':33, 'seededCasesWithinOneTest':500,
                 'fullPairRoundtripExact':True, 'frozenTestsUnchanged':True,
                 'profileLimits':asdict(TransportLimits()), 'informedQualification':qualification,
                 'exactGoalHelperUnchanged':True, 'nativeConnection':False, 'freshFormalAdmission':False,
                 'oldProseCurrentnessRequiresReplay':True,'childProgress':'4/6','parentProgress':'8/12',
                 'committed':False,'pushed':False})
(base/'VERIFICATION.json').write_text(json.dumps(verified,indent=2)+'\n')
print({'protectedInputsUnchanged':verified['primary']['files'], 'sealedPacketsUnchanged':len(roots)-2,
       'frozenTestsUnchanged':len(tests),'passedScopedChecks':94,'fullPairRoundtripExact':True,
       'nativeConnection':False})
