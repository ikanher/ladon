"""Repeated installed requests with per-run preservation and clean-build parity."""
import hashlib
import json
import os
import sqlite3
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent / 'installed-measurements'
OUT.mkdir(exist_ok=True)
CLI = ROOT / 'temp/index-history-installed/3.11/bin/ladon'
ENV = dict(os.environ)
ENV.pop('PYTHONPATH', None)
ENV.pop('PYTHONHOME', None)
FIELDS = 'name candidate_name name_casefold name_segments namespace kind module package path line column_number start_offset end_offset block_sha256 type_text type_text_bytes type_text_truncated type_status authority privacy locality structure_name doc_text rendered_type conclusion_text fingerprint head arity is_proposition semantic_status helper_identity lean_identity'.split()
PROJECTIONS = [('modules', 'name path package generated source_sha256 source_bytes line_count evidence_status'.split()), ('declarations', FIELDS), ('module_imports', 'source target line column_number authority'.split())]


def records(path):
    with sqlite3.connect(path) as conn:
        names = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        return {name: sorted(conn.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall(), key=repr) for (name,) in names}


def command(project, label, args):
    argv = [str(CLI), *args, '--repo-root', '.', '--format', 'json']
    result = subprocess.run(['/usr/bin/time', '-v', '-o', str(OUT / (label + '.time')), *argv], cwd=project, env=ENV, capture_output=True, text=True)
    (OUT / (label + '.stdout')).write_text(result.stdout)
    (OUT / (label + '.stderr')).write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout), argv


def compare(active, clean):
    with sqlite3.connect(active) as left, sqlite3.connect(clean) as right:
        counts = {}
        for table, fields in PROJECTIONS:
            query = 'SELECT ' + ','.join('"' + field + '"' for field in fields) + ' FROM ' + table
            a, b = sorted(left.execute(query).fetchall(), key=repr), sorted(right.execute(query).fetchall(), key=repr)
            assert a == b, table
            counts[table] = len(a)
        return counts


samples = []
for kind in ('fixture', 'adam'):
    project = ROOT / 'temp/index-history-field' / kind
    source = project / ('CapsuleFixture.lean' if kind == 'fixture' else 'Mf/Optimization/FiniteMemoryAdam/CumulativePairing.lean')
    index = project / '.ladon/index/proof-search.sqlite'
    for iteration in range(1, 4):
        label = f'{kind}-{iteration}'
        before = records(index)
        history = index.with_name(index.name + '.history')
        old_hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in history.glob('*.sqlite')}
        source.write_text(source.read_text() + f'\n-- final installed measurement {label}\n')
        stopped = threading.Event()
        observed = [0, 0]
        def sampler():
            while not stopped.is_set():
                size = 0
                for p in index.parent.rglob('*'):
                    if p.name.endswith(('.tmp', '-journal', '-wal', '-shm')):
                        try: size += p.lstat().st_size
                        except FileNotFoundError: pass
                observed[0] = max(observed[0], size)
                observed[1] += 1
                stopped.wait(0.001)
        thread = threading.Thread(target=sampler)
        thread.start()
        try:
            payload, argv = command(project, label, ['proof-search', 'index', 'update'])
        finally:
            stopped.set()
            thread.join()
        for path, digest in old_hashes.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        for snapshot in payload['preservedSnapshots']:
            assert records(history / snapshot['path']) == before
        clean = project / f'.ladon/index/measurement-clean-{iteration}.sqlite'
        command(project, label + '-clean', ['proof-search', 'index', 'build', '--index', str(clean)])
        parity = compare(index, clean)
        samples.append({'input': kind, 'iteration': iteration, 'cwd': str(project), 'command': argv,
                        'outputSha256': hashlib.sha256((OUT / (label + '.stdout')).read_bytes()).hexdigest(),
                        'activeBytes': index.stat().st_size, 'historyBytes': payload['historyBytes'],
                        'temporaryDatabaseBytes': payload['temporaryDatabaseBytes'],
                        'sampledTemporaryAndSidecarPeakBytes': observed[0], 'diskSamples': observed[1],
                        'extractedModules': payload.get('extractedModules'), 'reusedModules': payload.get('reusedModules'),
                        'preservedSnapshotCount': len(payload['preservedSnapshots']),
                        'preservedAllRows': True, 'existingArchivesUnchanged': True, 'cleanLexicalParity': parity,
                        'resourceFile': label + '.time'})
(OUT / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
print('All six installed measurements preserve evidence and match clean lexical builds.')
