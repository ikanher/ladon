"""One-off external-tool qualification; not a Ladon runtime or CLI module."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

import psutil

out = Path(__file__).resolve().parent
mode = sys.argv[1]
repo = Path('/home/codex/projects/lean/matrix-factorization')
case = out / mode
case.mkdir()
args = [
    'theorem', 'lineage',
    'Mf.DP.pSamplingOperator_ofDPEventBound_le_classicalSubsamplingEventBoundWitness',
    '--repo-root', str(repo), '--refresh', 'never', '--view', 'summary',
    '--format', 'json', '--output', '-',
]
command = [sys.executable]
if mode == 'memray':
    command += ['-m', 'memray', 'run', '--quiet', '--aggregate', '--native',
                '-o', str(case / 'allocations.bin')]
command += ['-m', 'ladon.entrypoint', *args]
if mode == 'child-control':
    child_code = 'import time; data=bytearray(64*1024**2); time.sleep(0.8)'
    parent_code = (
        'import subprocess,sys; data=bytearray(16*1024**2); '
        f'child=subprocess.Popen([sys.executable, "-c", {child_code!r}]); child.wait()'
    )
    command = [sys.executable, '-c', parent_code]
started = time.monotonic()
peaks = {'root': {}, 'descendants': {}, 'tree': {}}
count = 0
errors = {}
sampling_seconds = 0
max_descendants = 0
with (case / 'stdout.json').open('w') as stdout, (case / 'stderr.txt').open('w') as stderr:
    process = subprocess.Popen(command, cwd=repo, stdout=stdout, stderr=stderr,
                               start_new_session=True)
    parent = psutil.Process(process.pid)
    try:
        with (case / 'samples.jsonl').open('w') as samples:
            while process.poll() is None:
                if time.monotonic() - started > 120:
                    raise TimeoutError('120-second exercise deadline')
                sample_start = time.monotonic()
                rows = []
                try:
                    processes = [parent, *parent.children(recursive=True)]
                except psutil.Error as error:
                    processes = [parent]
                    errors[type(error).__name__] = errors.get(type(error).__name__, 0) + 1
                for observed in processes:
                    try:
                        mem = observed.memory_full_info()
                        rows.append({'pid': observed.pid, 'name': observed.name(),
                                     'role': 'root' if observed.pid == process.pid else 'descendant',
                                     'rss': mem.rss, 'pss': mem.pss, 'uss': mem.uss})
                    except psutil.Error as error:
                        errors[type(error).__name__] = errors.get(type(error).__name__, 0) + 1
                for role in peaks:
                    selected = [row for row in rows if role == 'tree' or row['role'] == role.rstrip('s')]
                    for metric in ('rss', 'pss', 'uss'):
                        value = sum(row[metric] for row in selected)
                        peaks[role][metric] = max(peaks[role].get(metric, 0), value)
                max_descendants = max(max_descendants, len([r for r in rows if r['role'] != 'root']))
                duration = time.monotonic() - sample_start
                sampling_seconds += duration
                samples.write(json.dumps({'elapsedSeconds': time.monotonic() - started,
                                          'samplingSeconds': duration, 'processes': rows}) + '\n')
                count += 1
                try:
                    process.wait(timeout=max(0.001, 0.1 - duration))
                except subprocess.TimeoutExpired:
                    pass
    finally:
        if process.poll() is None:
            descendants = parent.children(recursive=True)
            parent.terminate()
            for child in descendants:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs([parent, *descendants], timeout=2)
            for child in alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            process.wait()
report = {
    'command': command, 'cwd': str(repo), 'mode': mode, 'targetReturncode': process.returncode,
    'elapsedSeconds': time.monotonic() - started, 'sampleCount': count,
    'samplingSeconds': sampling_seconds, 'requestedIntervalSeconds': 0.1,
    'peakSampledBytes': peaks, 'maximumObservedDescendants': max_descendants,
    'unavailableReadings': errors,
    'versions': {name: importlib.metadata.version(name) for name in ('ladon','psutil','memray')},
    'limitations': [
        'One local run; no cold/warm classification or benchmark inference.',
        'Sequential sampled readings can miss peaks, transient or reparented children.',
        'RSS sums may double-count shared pages; PSS includes only observed processes.',
        'Profiler and sampling overhead is included; sampler itself is outside measured tree.',
        'Memray covers its Python interpreter and native extensions, not Lean executables.',
        'Sampled zero descendants does not establish that no child ever ran.',
    ],
}
(case / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(process.returncode)
