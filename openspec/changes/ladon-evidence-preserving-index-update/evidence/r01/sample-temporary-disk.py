"""Observe private SQLite publication files while running ordinary CLI updates."""
import json
import os
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
CLI = Path(os.environ.get('LADON_CONSOLE', ROOT / '.venv/bin/ladon'))
records = []
for kind in ('fixture', 'adam'):
    project = ROOT / 'temp/index-history-field' / kind
    source = project / ('CapsuleFixture.lean' if kind == 'fixture' else 'Mf/Optimization/FiniteMemoryAdam/CumulativePairing.lean')
    index = project / '.ladon/index/proof-search.sqlite'
    source.write_text(source.read_text() + '\n-- root ordinary storage observation\n')
    stop = threading.Event()
    peak = [0]
    samples = [0]
    def sample():
        while not stop.is_set():
            observed = 0
            for item in index.parent.rglob('*'):
                if item.name.endswith(('.tmp', '-journal', '-wal', '-shm')):
                    try:
                        observed += item.lstat().st_size
                    except FileNotFoundError:
                        pass
            peak[0] = max(peak[0], observed)
            samples[0] += 1
            stop.wait(0.001)
    thread = threading.Thread(target=sample)
    thread.start()
    try:
        result = subprocess.run(['/usr/bin/time', '-v', '-o', str(OUT / f'{kind}-disk.time'),
                                 str(CLI), 'proof-search', 'index', 'update', '--repo-root', '.', '--format', 'json'],
                                cwd=project, capture_output=True, text=True, check=False)
    finally:
        stop.set()
        thread.join()
    (OUT / f'{kind}-disk.stdout').write_text(result.stdout)
    (OUT / f'{kind}-disk.stderr').write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    records.append({'input': kind, 'peakObservedTemporaryAndSidecarBytes': peak[0],
                    'samples': samples[0], 'sampleIntervalSeconds': 0.001,
                    'activeBytes': index.stat().st_size, 'registeredHistoryBytes': payload['historyBytes'],
                    'temporaryDatabaseBytes': payload['temporaryDatabaseBytes'],
                    'limitation': 'Sampled peak is a lower bound; sub-millisecond allocation can be missed. Includes index-local temporary and journal/WAL files, excludes source copies and lock files.'})
(OUT / 'temporary-disk-samples.json').write_text(json.dumps(records, indent=2) + '\n')
