"""Final installed CLI, ordinary project cwd, exact preservation and offline replay."""
import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent / 'installed-workflow'
OUT.mkdir(exist_ok=True)
CLI = ROOT / 'temp/index-history-installed/3.11/bin/ladon'
ENV = dict(os.environ)
ENV.pop('PYTHONPATH', None)
ENV.pop('PYTHONHOME', None)
records = []


def run(project, label, arguments, *, expected=0, console=CLI):
    command = [str(console), *arguments, '--repo-root', '.', '--format', 'json']
    completed = subprocess.run(['/usr/bin/time', '-v', '-o', str(OUT / (label + '.time')), *command],
                               cwd=project, env=ENV, text=True, capture_output=True, check=False)
    (OUT / (label + '.stdout')).write_text(completed.stdout)
    (OUT / (label + '.stderr')).write_text(completed.stderr)
    records.append({'label': label, 'cwd': str(project), 'command': command,
                    'exit': completed.returncode,
                    'stdoutSha256': hashlib.sha256(completed.stdout.encode()).hexdigest()})
    assert completed.returncode == expected, (label, completed.stderr)
    return json.loads(completed.stdout) if expected == 0 else None


def rows(connection):
    tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return {name: sorted(connection.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall(), key=repr)
            for (name,) in tables}


for kind, theorem, source in [
    ('fixture', 'CapsuleFixture.chosen', 'CapsuleFixture.lean'),
    ('adam', 'Mf.Optimization.FiniteMemoryAdam.Cumulative.pairing_lower',
     'Mf/Optimization/FiniteMemoryAdam/CumulativePairing.lean'),
]:
    project = ROOT / 'temp/index-history-field' / kind
    index = project / '.ladon/index/proof-search.sqlite'
    fresh = run(project, kind + '-acquire-before', ['theorem', 'lineage', theorem, '--refresh', 'always', '--max-rss-mib', '32768'])
    with sqlite3.connect(index) as connection:
        original = rows(connection)
    path = project / source
    path.write_text(path.read_text() + '\n-- installed v0.2.2 preservation smoke\n')
    update = run(project, kind + '-update', ['proof-search', 'index', 'update'])
    selected = update['preservedSnapshots'][0]['snapshotId']
    archive = index.with_name(index.name + '.history') / (selected + '.sqlite')
    with sqlite3.connect(archive) as connection:
        assert rows(connection) == original
    (OUT / (kind + '-row-parity.json')).write_text(json.dumps({
        'allTablesEqual': True, 'tables': len(original), 'snapshotId': selected,
        'counts': {name: len(value) for name, value in original.items()},
        'originalRowDigests': {name: hashlib.sha256(repr(value).encode()).hexdigest() for name, value in original.items()},
    }, indent=2) + '\n')
    run(project, kind + '-search', ['proof-search', 'search', 'name', '--text', theorem])
    run(project, kind + '-history', ['proof-search', 'index', 'history', '--limit', '1'])
    historical = run(project, kind + '-historical', ['theorem', 'lineage', theorem, '--history', selected, '--refresh', 'never'])
    assert historical['schema'] == 'ladon-theorem-lineage-history-result-v1'
    assert historical['currentAssociation'] == 'not-established'
    assert historical['closureId'] == fresh['closureId']
    current = run(project, kind + '-acquire-after', ['theorem', 'lineage', theorem, '--refresh', 'always', '--max-rss-mib', '32768'])
    assert current['closureId'] != historical['closureId']
    if kind == 'fixture':
        old = ROOT / 'temp/field-reliability-installed-field/venv/bin/ladon'
        run(project, 'older-reader-rejection', ['proof-search', 'search', 'name', '--text', theorem], expected=2, console=old)
(OUT / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
print('Installed ordinary workflows passed:', len(records), 'commands')
