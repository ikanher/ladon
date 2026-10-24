"""Measure a known real-source application pair with the frozen local runtime."""
import hashlib
import json
import os
from pathlib import Path

import ladon
from ladon.evaluation_process import captured_text, measure_command

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
REPO = ROOT.parent / 'lean/matrix-factorization'
BASE = ROOT / '.codex/state/proof-contract-analysis/baseline'
PRIOR = ROOT / 'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines'
TASK = PRIOR / 'read-find-check-r49/reader-task.json'
MANIFEST = ROOT / 'openspec/changes/ladon-proof-contract-evaluation/evidence/BASELINE.json'
BOUNDS = {'timeoutSeconds': 60, 'maxRssBytes': 12 * 1024**3, 'maxOutputBytes': 8 * 1024**2}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def verify(frozen):
    assert Path(ladon.__file__).resolve().is_relative_to(BASE)
    for name, digest in frozen['inputs'].items():
        assert sha(Path(name)) == digest, name
    for row in json.loads(MANIFEST.read_text())['files']:
        assert sha(BASE / row['path']) == row['sha256'], row['path']


def main():
    task = json.loads(TASK.read_text())
    selected = [TASK, MANIFEST, Path(__file__), REPO / 'lean-toolchain', REPO / 'lake-manifest.json',
                REPO / 'Mf/DP/PoissonFixedEpochCenterGapPropagation.lean',
                REPO / '.lake/build/lib/lean/Mf/DP/PoissonFixedEpochCenterGapPropagation.olean']
    frozen = {'schema': 'ladon-matrix-application-baseline-freeze-v1', 'runtime': str(BASE),
              'inputs': {str(path): sha(path) for path in selected}, 'bounds': BOUNDS,
              'sourceTask': str(TASK), 'caseOrder': ['context-A', 'context-B'],
              'candidate': 'Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg',
              'expectations': {'context-A': 'accepted with no residual premise',
                               'context-B': 'unresolved boundary-gap premise; no closed support'},
              'nonclaims': ['Known development fixture; no independent discovery measurement.',
                            'One supplied candidate; no retrieval or beam comparison.',
                            'Missing support from this lemma does not refute the goal.',
                            'Selected source/object hashes do not certify the full import closure.']}
    write(HERE / 'FREEZE.json', frozen)
    verify(frozen)
    rows = []
    for case in task['contexts']:
        output = HERE / 'results' / case['id']
        output.mkdir(parents=True)
        argv = [str(BASE / 'run-ladon'), 'proof-search', 'discover', '--repo-root', str(REPO),
                '--module', task['module'], '--goal', task['goal'], '--candidate', frozen['candidate'],
                '--format', 'json', '--projection', 'review', '--max-candidates', '1', '--batch-size', '1',
                '--timeout-seconds', '60', '--max-output-mib', '8', '--max-rss-mib', '12288',
                '--toolchain-mode', 'explicit', '--lean-path', task['leanPath'], '--lake-path', task['lakePath'],
                '--scratch-mode', 'advisory', '--evidence-store', str(output / 'evidence.sqlite')]
        for local in case['locals']:
            argv.extend(['--local', local])
        record = measure_command(argv, cwd=ROOT, environment=os.environ, bounds=BOUNDS,
                                 output=output, stem='first')
        payload = None
        try:
            payload = json.loads(captured_text(record))
        except json.JSONDecodeError:
            pass
        row = {'case': case['id'], 'measurement': record, 'payload': payload}
        rows.append(row)
        write(output / 'FIRST.json', row)
        print(case['id'], record['status'], record['runtimeSeconds'], flush=True)
        if record.get('memoryLimited'):
            print('Stop progress and report back to user: the 12 GiB memory limit was not enough.', flush=True)
            break
    verify(frozen)
    write(HERE / 'MEASUREMENTS.json', {'schema': 'ladon-matrix-application-baseline-v1',
                                      'runtimeImport': ladon.__file__, 'freezeSha256': sha(HERE / 'FREEZE.json'),
                                      'denominator': 2, 'rows': rows, 'notRunCases': 2 - len(rows)})


if __name__ == '__main__':
    main()
