"""Reproduce offline inspection of the immutable r44 field evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

base = Path(sys.argv[3]).resolve()
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
manifest_path = base / 'assembled/note.canonical.result.json'
manifest = json.loads(manifest_path.read_text())
original = base / 'assembled/component-assessments.json'
assessment = json.loads(original.read_text())
targets = {t['id']: t for t in manifest['targets']}
kinds = {'conventional-proof-no-formal-mapping-claimed': 'conventional-only',
         'source-correspondence': 'source-correspondence',
         'implication-without-checked-adapter': 'reported-implication-without-checked-adapter'}
rows = []
for i, row in enumerate(assessment['components']):
    rows.append({'id': f'component-assessment-{i}', 'claimId': row['claim_id'],
                 'componentId': row['id'], 'claimRevision': row['claim_revision'],
                 'targetRevisions': [{'targetId': t, 'revision': targets[t]['revision']} for t in row['target_ids']],
                 'kind': kinds[row['assessment']], 'author': {'id': row['author'], 'kind': 'model'},
                 'basis': row['basis'], 'scope': row['scope'],
                 'differences': [row['differences']] if row['differences'] else [],
                 'evidenceRefs': ['sha256:' + hashlib.sha256(original.read_bytes()).hexdigest() + f'#/components/{i}']})
companion = {'schema': 'ladon-result-assessments-v1', 'resultId': manifest['resultId'],
             'manifestRevision': manifest['revision'], 'assessments': rows}
companion_path = out / 'assessments.json'
companion_path.write_text(json.dumps(companion, ensure_ascii=False, indent=2) + '\n')
artifacts = sorted((base / 'assembled/artifacts').glob('*.json'))
argv = [sys.argv[1], 'result', 'inspect', str(manifest_path), '--assessments', str(companion_path)]
for path in artifacts:
    argv += ['--artifact', str(path)]
records = []
for section in ['components', 'checking', 'targets', 'assessments', 'claims', 'reviews', 'assumptions', 'lineage']:
    cursor = None
    seen = []
    number = 0
    while True:
        args = argv + ['--section', section]
        if cursor:
            args += ['--cursor', cursor]
        prefix = out / f'{section}-{number:02}'
        prefix.with_suffix('.command.json').write_text(json.dumps(args) + '\n')
        start = time.monotonic()
        measured_args = ['/usr/bin/time', '-f', '{\"peakRssKiB\":%M}', '-o', str(prefix.with_suffix('.resources.json')), *args]
        process = subprocess.run(measured_args, cwd='/tmp', capture_output=True, timeout=60)
        elapsed = time.monotonic() - start
        prefix.with_suffix('.stdout.json').write_bytes(process.stdout)
        prefix.with_suffix('.stderr.txt').write_bytes(process.stderr)
        assert process.returncode == 0, process.stderr.decode()
        page = json.loads(process.stdout)
        assert len(process.stdout) <= 32768
        seen.extend(page['rows'])
        records.append({'section': section, 'page': number, 'elapsedSeconds': elapsed,
                        'stdoutBytes': len(process.stdout), 'rows': len(page['rows']), 'exitCode': process.returncode,
                        **json.loads(prefix.with_suffix('.resources.json').read_text())})
        cursor = page['pagination']['nextCursor']
        number += 1
        if not cursor:
            assert len(seen) == page['pagination']['total']
            break
    (out / f'{section}-rows.json').write_text(json.dumps(seen, ensure_ascii=False, indent=2) + '\n')
(out / 'measurements.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps({'pages': len(records), 'sections': 8, 'rows': sum(r['rows'] for r in records),
                  'maxOutputBytes': max(r['stdoutBytes'] for r in records)}))
