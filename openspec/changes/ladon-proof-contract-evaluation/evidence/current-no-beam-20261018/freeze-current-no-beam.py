import datetime
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

root = Path.cwd()
out = root / 'openspec/changes/ladon-proof-contract-evaluation/evidence/current-no-beam-20261018'
out.mkdir(exist_ok=True)
snapshot = root / '.codex/state/proof-contract-analysis/current-no-beam-20261018'
snapshot.mkdir(exist_ok=True)
files = sorted(p for p in (root / 'src').rglob('*') if p.is_file()
               and '__pycache__' not in p.parts and p.suffix != '.pyc')
files.extend(root / p for p in ['pyproject.toml', 'uv.lock'])
rows = []
for path in files:
    relative = path.relative_to(root)
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    rows.append({'path': str(relative), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'bytes': path.stat().st_size})
launcher = snapshot / 'run-ladon'
launcher.write_text('#!/bin/sh\nTASK_BASELINE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexport PYTHONPATH="$TASK_BASELINE/src"\nexec /home/codex/projects/ladon/.venv/bin/python -m ladon.entrypoint "$@"\n')
launcher.chmod(0o755)
rows.append({'path': 'run-ladon', 'sha256': hashlib.sha256(launcher.read_bytes()).hexdigest(),
             'bytes': launcher.stat().st_size})
manifest = {'schema': 'ladon-contract-no-beam-runtime-v1',
 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'snapshotRoot': str(snapshot), 'baseCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
 'gitStatus': subprocess.check_output(['git', 'status', '--short'], text=True),
 'python': subprocess.check_output([str(root / '.venv/bin/python'), '--version'], text=True).strip(),
 'packages': sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions()),
 'freezePreparation': 'Initial metadata capture failed because this uv venv has no pip; retried using importlib.metadata before any measurement or manifest publication.',
 'files': rows, 'beamEnabled': False,
 'qualification': {'contractNativeContextTests': {'passed': 615, 'seconds': 77.86},
                   'discoveryEvaluationContextTests': {'passed': 61, 'seconds': 15.17},
                   'ruff': 'pass src/tests/scripts', 'strictQualityIssues': 0,
                   'independentNativeRecheck': 226},
 'limitations': ['Partial umbrella implementation: domain, producers and propagation only.',
                 'Whole-paper fault detection and full repository readiness unestablished.',
                 'Same legacy search policy; contract analysis is not exercised by discovery benchmarks.']}
(out / 'RUNTIME.json').write_text(json.dumps(manifest, indent=2) + '\n')
(snapshot / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(out / 'runtime.tar.gz', 'w:gz') as archive:
    for row in rows:
        archive.add(snapshot / row['path'], arcname=row['path'])
print(json.dumps({'snapshot': str(snapshot), 'files': len(rows), 'manifestSha256': hashlib.sha256((out / 'RUNTIME.json').read_bytes()).hexdigest(),
                  'archiveSha256': hashlib.sha256((out / 'runtime.tar.gz').read_bytes()).hexdigest()}))
