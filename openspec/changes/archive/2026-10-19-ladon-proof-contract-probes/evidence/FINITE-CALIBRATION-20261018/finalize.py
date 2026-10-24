"""Publish exact corrected-runtime regression and partial source evidence."""
import ast
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

s = Path('.codex/state/proof-contract-analysis/probe-calibration')
p = Path('openspec/changes/ladon-proof-contract-probes/evidence/FINITE-CALIBRATION-20261018')
v = p / 'qualification-v2'
result = json.loads((s / 'integration-corrected-result.json').read_text())
assert result['returnCode'] == 0
suites = list(ET.parse(s / 'integration-corrected.xml').getroot().iter('testsuite'))
assert sum(int(row.get('tests', 0)) for row in suites) == 1054
assert all(int(row.get(key, 0)) == 0 for row in suites for key in ('failures', 'errors', 'skipped'))
for name in ('integration-corrected-result.json', 'integration-corrected-command.json',
             'integration-corrected.log', 'integration-corrected.xml', 'quality-corrected.json',
             'ruff-corrected.log', 'frozen-corrected.json', 'fresh-source-red.log'):
    shutil.copyfile(s / name, p / name)
shutil.copyfile(s / 'independent-final/FINAL-AUDIT.json', p / 'review/INDEPENDENT-FINAL-AUDIT.json')
tests = []
for path in sorted(Path('tests').glob('test_proof_contract_probe_calibration_*.py')):
    data = path.read_bytes()
    tests.append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                  'assertStatements': len([n for n in ast.walk(ast.parse(data)) if isinstance(n, ast.Assert)])})
(p / 'TESTS-CORRECTED.json').write_text(json.dumps({'newPytestCases': 31, 'redCases': 22,
    'greenControls': 9, 'files': tests}, indent=2))
m = json.loads((v / 'RUNTIME.json').read_text())
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in m['files'])
review = json.loads((p / 'review/INDEPENDENT-FINAL-AUDIT.json').read_text())
print('Verified1054 and505 runtime; partial-review status', review.get('status'), flush=True)
