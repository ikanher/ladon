"""Replay feedback owners through installed CLIs in a disposable lexical project."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
FIELD = ROOT / 'temp/let-signature-field'
OLD = ROOT / 'temp/index-history-installed/3.11/bin/ladon'
NEW = ROOT / 'temp/let-signature-installed/3.11/bin/ladon'
OWNERS = ('Mf/Optimization/FiniteMemoryAdam/InitializedMaskCarriedMemory.lean',
          'Mf/Optimization/FiniteMemoryAdam/InitializedGaussianCarriedMemory.lean')


def main():
    FIELD.mkdir(parents=True, exist_ok=True)
    repo = FIELD / 'repo'
    source_hashes = {}
    for relative in OWNERS:
        source = ROOT.parent / 'lean/matrix-factorization' / relative
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        source_hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    events = []

    def call(label, cli, *arguments):
        timing = FIELD / (label + '.time')
        command = [str(cli), *arguments]
        result = subprocess.run(['/usr/bin/time', '-v', '-o', str(timing), *command],
                                cwd=ROOT, text=True, capture_output=True, check=False)
        (FIELD / (label + '.stdout')).write_text(result.stdout)
        (FIELD / (label + '.stderr')).write_text(result.stderr)
        events.append({'label': label, 'command': command, 'exitCode': result.returncode,
                       'outputSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                       'timeReport': timing.read_text()})
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    assert call('old-version', OLD, 'version', '--json')['package']['version'] == '0.2.2'
    assert call('new-version', NEW, 'version', '--json')['package']['version'] == '0.2.3'
    common = ['--repo-root', str(repo), '--format', 'json']
    call('old-build', OLD, 'proof-search', 'index', 'build', *common)
    before = call('old-query', OLD, 'proof-search', 'search', 'type-text', *common,
                  '--pattern', 'defaultCarriedMemoryCoefficient', '--limit', '100')
    status = call('new-status', NEW, 'proof-search', 'index', 'status', *common)
    assert status['freshness'] == 'stale-configuration'
    update = call('new-update', NEW, 'proof-search', 'index', 'update', *common)
    assert update['sourceChanges'] == {'added': 0, 'changed': 0, 'removed': 0}
    assert update['extractedModules'] == update['lexicalRecoveryModules'] == 2
    after = call('new-query', NEW, 'proof-search', 'search', 'type-text', *common,
                 '--pattern', 'defaultCarriedMemoryCoefficient', '--limit', '100')
    names = [row['candidateName'] for row in after['results']]
    assert any(name.endswith('.streamRun_joint_centered_carried_remainder') for name in names)
    assert len(after['results']) > len(before['results'])
    for row in after['results']:
        assert ':= by' not in row['typeText']
    database = repo / '.ladon/index/proof-search.sqlite'
    digest = hashlib.sha256(database.read_bytes()).hexdigest()
    assert call('new-noop', NEW, 'proof-search', 'index', 'update', *common)['status'] == 'unchanged'
    assert hashlib.sha256(database.read_bytes()).hexdigest() == digest
    assert call('final-status', NEW, 'proof-search', 'index', 'status', *common)['freshness'] == 'fresh'
    (OUT / 'field-replay.json').write_text(json.dumps({
        'sourceHashes': source_hashes, 'events': events,
        'beforeCandidates': [row['candidateName'] for row in before['results']],
        'afterCandidates': names, 'scope': 'two copied source owners; lexical only, no Lean execution',
    }, indent=2) + '\n')
    print('Installed old-to-new recovery:', len(before['results']), '->', len(names), 'matches')


if __name__ == '__main__':
    main()
