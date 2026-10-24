import hashlib
import json
import shutil
import tarfile
from pathlib import Path

p = Path('openspec/changes/ladon-proof-contract-probes/evidence/FINITE-CALIBRATION-20261018')
p.mkdir(parents=True)
old = json.loads(Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/source-pair-20261018/RUNTIME.json').read_text())
changed = [r['path'] for r in old['files'] if hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() != r['sha256']]
assert changed == ['src/ladon/proof_contract_cli.py'], changed
new = [str(f) for f in Path('src/ladon').glob('*probe_calibration*.py')]
new.append('src/ladon/lean/ladon_probe_separator.lean')
paths = sorted({r['path'] for r in old['files']} | set(new))
assert len(paths) == 505, len(paths)
rows = [{'path': s, 'bytes': Path(s).stat().st_size, 'sha256': hashlib.sha256(Path(s).read_bytes()).hexdigest()} for s in paths]
with (p / 'RUNTIME.json').open('x') as f:
    json.dump({'entries': len(rows), 'scope': 'Prior complete500 runtime plus4 calibration modules and1 Lean asset; only old CLI dispatch changed.', 'files': rows}, f, indent=2)
with tarfile.open(p / 'runtime.tar.gz', 'x:gz') as tf:
    for s in paths:
        tf.add(s, arcname=s, recursive=False)
scratch = Path('.codex/state/proof-contract-analysis/probe-calibration')
for name in ('CONTRACT.txt', 'FEASIBILITY.json', 'FEASIBILITY-START.json', 'compile.json', 'feasibility.py',
             'feasibility.log', 'separator-process.json', 'incomplete-counterexample-process.json',
             'application-process.json', 'run_acceptance.py', 'red-root.log', 'capacity-red.log',
             'HARNESS-INCIDENT.json', 'interrupted-integration-command.json',
             'interrupted-integration-result.json', 'interrupted-integration.log',
             'pre-audit-fix-integration-command.json', 'pre-audit-fix-integration-result.json',
             'pre-audit-fix-integration.log'):
    shutil.copyfile(scratch / name, p / name)
for directory in ('review', 'red', 'green'):
    shutil.copytree(scratch / directory, p / directory, ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile('docs/PROOF_CONTRACTS.md', p / 'PUBLIC-API.md')
print('Frozen505', hashlib.sha256((p / 'RUNTIME.json').read_bytes()).hexdigest(), flush=True)
