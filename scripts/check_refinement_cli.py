"""Run the constructed refinement example through this checkout's public CLI.

Use PYTHONPATH=src. The output directory must be new. All subprocesses share
one deadline; a failed or resource-limited step stops the example without retry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from check_nat_rational_lift_feasibility import INCOMPATIBILITY, _goal

import ladon

ROOT = Path(__file__).resolve().parents[1]
TEXT = "Let n be a natural number. If n < 2, then n = 0.\n"


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def command(output, name, arguments, deadline, expected=0):
    argv = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', *map(str, arguments)]
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src')}
    start = time.monotonic()
    run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True,
                         timeout=max(0.001, deadline - start), check=False)
    (output / (name + '.stdout')).write_text(run.stdout)
    (output / (name + '.stderr')).write_text(run.stderr)
    receipt = {'argv': argv, 'exitCode': run.returncode, 'expectedExitCode': expected,
               'elapsedSeconds': time.monotonic() - start}
    write(output / (name + '.command.json'), receipt)
    if run.returncode != expected:
        raise ValueError(f'{name}: exit {run.returncode}, expected {expected}; stop progress')


def workspace(output):
    root = output / 'workspace'
    root.mkdir()
    fixture = ROOT / 'tests/fixtures/proof_contract_lifting'
    for name in ('Fixture.lean', 'lean-toolchain'):
        shutil.copyfile(fixture / name, root / name)
    (root / 'source.txt').write_text(TEXT)
    return root


def observation(plan):
    return {'schema': 'ladon-investigation-observation-v1', 'id': 'constructed-example',
            'source': {**plan['scope'], 'quote': TEXT.strip()}, 'author': 'constructed-example',
            'assertion': TEXT.strip(),
            'comparison': 'The rational abstraction admits a negative input.',
            'evidence': 'The rational input -1 satisfies x < 2 and falsifies x = 0.',
            'formalSources': [], 'dependencies': 'Selected natural-number interpretation.'}


def request(root, finding_id):
    source = {'path': 'source.txt', 'sha256': hashlib.sha256(TEXT.encode()).hexdigest(),
              'startLine': 1, 'endLine': 1, 'quote': TEXT.strip()}
    witness = {'id': 'negative-one', 'status': 'abstract-countermodel', 'assignment': {'x': '-1'}}
    interpretation = {'profile': 'nat-cast-v1', 'formalClaim': 'LiftFixture.Claim',
                      'formalPredicate': 'LiftFixture.Predicate',
                      'source': {'path': 'Fixture.lean', 'sha256': hashlib.sha256(
                          (root / 'Fixture.lean').read_bytes()).hexdigest()}}
    return {'schema': 'ladon-proof-contract-refinement-request-v1',
            'originalFinding': {'id': finding_id, 'status': 'abstract-countermodel',
                                'discrepancy': {'kind': 'encoded-rational-counterexample'},
                                'witness': witness},
            'baseGoal': _goal(), 'lift': {'interpretation': interpretation,
                                        'mode': 'incompatibility', 'term': INCOMPATIBILITY},
            'refinementConstraints': [{'id': 'nonnegative', 'expression': {
                'op': 'ge', 'left': {'var': 'x'}, 'right': {'rat': 0}},
                'justification': {'kind': 'source-cited-refinement', 'source': source,
                                  'nonclaim': 'Span validation does not certify formula fidelity.'}}],
            'repairConstraints': [{'id': 'assume-zero', 'expression': {
                'op': 'eq', 'left': {'var': 'x'}, 'right': {'rat': 0}},
                'justification': {'kind': 'proposed-repair',
                                  'rationale': 'Additional assumption proposed for comparison.'}}]}


def prepare(output, root, deadline):
    command(output, 'init', ['init', '--text', root / 'source.txt', '--root', root,
                            '--correspondence', '--output', output / 'plan.json'], deadline)
    plan = json.loads((output / 'plan.json').read_text())
    write(output / 'observation.json', observation(plan))
    command(output, 'observe', ['observe', '--plan', output / 'plan.json', '--root', root,
                               '--record', output / 'observation.json',
                               '--output', output / 'observed.json'], deadline)
    observed = json.loads((output / 'observed.json').read_text())
    write(output / 'request.json', request(root, observed['observations'][0]['observationId']))


def check_outputs(output):
    artifact = json.loads((output / 'refinement.json').read_text())
    inspection = json.loads((output / 'inspection.json').read_text())
    report = json.loads((output / 'report.json').read_text())
    assert artifact['status'] == 'completed'
    assert artifact['liftResult']['status'] == 'spurious-countermodel'
    assert artifact['liftResult']['spuriousnessEvidence']
    assert artifact['originalCheck']['status'] == 'counterexample'
    assert {row['kind'] for row in artifact['branches']} == {
        'source-cited-refinement', 'proposed-repair'}
    assert all(row['check']['witnessCheck']['status'] == 'outside-assumptions'
               for row in artifact['branches'])
    check_report(artifact, inspection, report)


def check_report(artifact, inspection, report):
    assert inspection['artifact'] == artifact and inspection['leanReplayed'] is False
    assert inspection['liftAuthority'] == 'unverified-saved-result'
    assert report['refinementEvidence'][0]['artifact'] == artifact
    finding = next(row for row in report['findings']
                   if row['findingId'] == artifact['request']['originalFinding']['id'])
    assert finding['refinementIds'] == [artifact['artifactId']]
    assert finding['mathematicalFalsity'] == 'not-established'
    assert finding['branchFindings'] and report['wholePaperCertified'] is False


def run(output, deadline):
    root = workspace(output)
    prepare(output, root, deadline)
    command(output, 'refine', ['contract', 'refine', '--input', output / 'request.json',
                             '--root', root, '--deadline-monotonic', deadline,
                             '--output', output / 'refinement.json'], deadline)
    command(output, 'inspect', ['contract', 'inspect', '--input', output / 'refinement.json',
                              '--root', root, '--output', output / 'inspection.json'], deadline)
    command(output, 'report', ['report', '--plan', output / 'observed.json', '--root', root,
                             '--refinement', output / 'refinement.json',
                             '--output', output / 'report.json'], deadline)
    check_outputs(output)
    original = (root / 'source.txt').read_bytes()
    try:
        (root / 'source.txt').write_text('Changed source.\n')
        command(output, 'stale-inspect', ['contract', 'inspect', '--input',
                output / 'refinement.json', '--root', root], deadline, expected=2)
    finally:
        (root / 'source.txt').write_bytes(original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=int, default=1800)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 1800:
        parser.error('qualification timeout must be 1..1800 seconds')
    output = args.output.resolve()
    output.mkdir()
    started = time.monotonic()
    write(output / 'start.json', {'ladonModule': ladon.__file__, 'startedMonotonic': started,
                                'deadlineMonotonic': started + args.timeout_seconds})
    try:
        run(output, started + args.timeout_seconds)
    except (ValueError, AssertionError, subprocess.TimeoutExpired) as error:
        write(output / 'RESULT.json', {'passed': False, 'error': str(error),
                                     'elapsedSeconds': time.monotonic() - started})
        return 1
    write(output / 'RESULT.json', {'passed': True, 'elapsedSeconds': time.monotonic() - started,
                                 'scope': 'constructed-example-only'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
