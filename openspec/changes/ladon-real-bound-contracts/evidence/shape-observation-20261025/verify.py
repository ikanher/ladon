import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

primary_root = ROOT / '.codex/state/navier-stokes-informed-diagnostic'
primary = json.loads((primary_root / 'SOURCE-MANIFEST.json').read_text())
assert all(digest(primary_root / name) == expected for name, expected in primary.items())
history = {}
base = ROOT / 'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence'
for name in ['jet-contract-frontier-20261025', 'norm-route-audit-20261025']:
    directory = base / name
    files = json.loads((directory/'ARTIFACTS.json').read_text())
    assert all(digest(directory / p) == expected for p, expected in files.items())
    history[name] = len(files)
baseline = json.loads((ROOT/'.codex/state/real-bound-contracts/baseline.json').read_text())
old_unchanged = {p:digest(ROOT/p)==value for p,value in baseline['files'].items()}
assert all(old_unchanged.values())
board = json.loads((ROOT/'.codex/state/real-bound-contracts/frozen-tests-verification.json').read_text())
changed = [r['path'] for r in board['frozenTests'] if r.get('matches') is False]
assert changed == [str(ROOT/'tests/test_rational_lean_encoder_v2.py')]
new_frozen = [r for r in board['frozenTests'] if 'test_real_bound' in r['path']
              or '/fixtures/real_bound_observation/' in r['path']]
assert len(new_frozen) == 5 and all(r['matches'] for r in new_frozen)
source_paths = ['src/ladon/real_bound_shape.py','src/ladon/_real_bound_terms.py',
                'src/ladon/real_bound_observation.py','src/ladon/proof_contract_cli.py',
                'tests/test_real_bound_shape.py','tests/test_real_bound_shape_origins.py',
                'tests/test_real_bound_observation.py','tests/fixtures/real_bound_observation/NamedBound.lean',
                'tests/fixtures/real_bound_observation/lean-toolchain']
result = {'primaryFilesUnchanged':len(primary), 'priorArtifactsUnchanged':history,
          'historicalRuntimeUnchanged':old_unchanged, 'newFrozenFilesMatch':len(new_frozen),
          'preexistingBoardMismatches':changed,
          'runtimeAndTestIdentities':{p:digest(ROOT/p) for p in source_paths}}
(OUT/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(primary),'primary files,',sum(history.values()),'prior artifacts and historical contract runtime; new frozen files match.')
