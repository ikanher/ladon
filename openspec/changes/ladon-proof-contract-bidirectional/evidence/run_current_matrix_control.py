"""Recheck the existing two-context matrix control with the current checkout."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import ladon
from ladon.evaluation_process import captured_text, measure_command

ROOT = Path(__file__).resolve().parents[4]
EVALUATION = ROOT / 'openspec/changes/ladon-proof-contract-evaluation/evidence'
BOUNDS = {'timeoutSeconds': 60, 'maxRssBytes': 12 * 1024**3, 'maxOutputBytes': 8 * 1024**2}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def verify_runtime(manifest):
    assert Path(ladon.__file__).resolve().is_relative_to(ROOT / 'src')
    for row in manifest['files']:
        assert digest(ROOT / row['path']) == row['sha256'], row['path']


def run(output, runtime_path):
    output.mkdir(parents=True, exist_ok=False)
    prior = json.loads((EVALUATION / 'matrix-no-beam-20261018/FREEZE.json').read_text())
    runtime = json.loads(runtime_path.read_text())
    verify_runtime(runtime)
    task_path = Path(prior['sourceTask'])
    task = json.loads(task_path.read_text())
    repo = Path(task['leanRepository'])
    source_inputs = {name: sha for name, sha in prior['inputs'].items()
                     if name.startswith(str(repo)) or name == str(task_path)}
    assert all(digest(Path(name)) == sha for name, sha in source_inputs.items())
    frozen = {'schema': 'ladon-current-matrix-control-v1', 'bounds': BOUNDS,
        'inputs': source_inputs, 'runtimeManifest': str(runtime_path),
        'runtimeManifestSha256': digest(runtime_path), 'harnessSha256': digest(Path(__file__)),
        'candidate': prior['candidate'], 'caseOrder': prior['caseOrder'],
        'scope': 'known-development-compatibility-control', 'beamEnabled': False,
        'newContractWorkflowExercised': False}
    save(output / 'FREEZE.json', frozen)
    rows = []
    for case in task['contexts']:
        target = output / case['id']
        argv = [sys.executable, '-m', 'ladon.entrypoint', 'proof-search', 'discover',
            '--repo-root', str(repo), '--module', task['module'], '--goal', task['goal'],
            '--candidate', prior['candidate'], '--format', 'json', '--projection', 'review',
            '--max-candidates', '1', '--batch-size', '1', '--timeout-seconds', '60',
            '--max-output-mib', '8', '--max-rss-mib', '12288', '--toolchain-mode', 'explicit',
            '--lean-path', task['leanPath'], '--lake-path', task['lakePath'],
            '--scratch-mode', 'advisory', '--evidence-store', str(target / 'evidence.sqlite')]
        for local in case['locals']:
            argv.extend(['--local', local])
        record = measure_command(argv, cwd=ROOT, environment=os.environ, bounds=BOUNDS,
                                 output=target, stem='first')
        payload = json.loads(captured_text(record)) if record['status'] == 'passed' else None
        row = {'case': case['id'], 'measurement': record, 'payload': payload}
        save(target / 'FIRST.json', row)
        rows.append(row)
        print(case['id'], record['status'], record['runtimeSeconds'], flush=True)
        if record['memoryLimited']:
            print('Stop progress and report back to user: the 12 GiB memory limit was not enough.', flush=True)
            break
    verify_runtime(runtime)
    assert all(digest(Path(name)) == sha for name, sha in source_inputs.items())
    save(output / 'MEASUREMENTS.json', {'schema': 'ladon-current-matrix-control-v1',
        'denominator': 2, 'notRunCases': 2 - len(rows), 'rows': rows})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve(), args.runtime.resolve())
