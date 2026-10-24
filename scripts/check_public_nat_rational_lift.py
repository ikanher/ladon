"""Qualify the public Nat/rational lift API under one shared 30-minute clock.

Run with PYTHONPATH=src from this checkout; --output must name a new directory.
No downloads, builds, automatic retries, or reference manuscript answers.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import time
from pathlib import Path

import ladon
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

ROOT = Path(__file__).resolve().parents[1]
PRIOR_PATH = ROOT / 'scripts/check_nat_rational_lift_feasibility.py'
SPEC = importlib.util.spec_from_file_location('lift_feasibility', PRIOR_PATH)
prior = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prior)
OVERRIDE = (b'\ninstance (priority := 2000) skewOne : OfNat Rat 1 := '
            b'{ ofNat := Rat.ofInt (Int.negSucc 0) }\n')


def case_passed(expected, result):
    """Separate mathematical rejection from an unavailable observation."""
    status = result.get('status')
    code = (result.get('diagnostic') or {}).get('code')
    if expected == 'proof-rejected':
        return status == 'rejected' and code in {'proof-rejected', 'trust-rejected'}
    if expected == 'trust-rejected':
        return status == 'rejected' and code == expected
    if expected == 'semantic-goal-mismatch':
        return status in {'rejected', 'unsupported'} and code == expected
    if expected in {'lifted-counterexample', 'spurious-countermodel'}:
        return status == expected and _positive(result)
    return status == expected


def _positive(result):
    realized = result['status'] == 'lifted-counterexample'
    evidence = 'realizationEvidence' if realized else 'spuriousnessEvidence'
    other = 'spuriousnessEvidence' if realized else 'realizationEvidence'
    return all((result.get('checkId'), result.get('sourceVerified') is True,
                result.get('sourceFormulaFidelity') == 'unverified',
                result.get('originalClaimRefuted') is False,
                result.get('formalClaimRefuted') is realized,
                result.get(evidence), result.get(other) is None,
                result.get('openObligation') is None))


def _cases():
    cases = prior._cases()
    cases[0] = (*cases[0][:4], 'lifted-counterexample', *cases[0][5:])
    cases[1] = (*cases[1][:4], 'spurious-countermodel', *cases[1][5:])
    cases.append(('overridden-numeral', '1', 'incompatibility', prior.INCOMPATIBILITY,
                  'semantic-goal-mismatch', 'nat-cast-v1', False))
    return cases


def _workspace(output, name):
    workspace = output / (name + '-workspace')
    workspace.mkdir()
    for filename in ('lean-toolchain', 'Fixture.lean'):
        shutil.copyfile(prior.FIXTURE / filename, workspace / filename)
    if name == 'overridden-numeral':
        source = workspace / 'Fixture.lean'
        source.write_bytes(source.read_bytes() + OVERRIDE)
    return workspace


def _run_case(case, output, deadline):
    from ladon.proof_contract_bridge import _resource_stop
    from ladon.proof_contract_lift_check import check_nat_rational_lift

    name, _value, mode, term, expected, _profile, _strict = case
    workspace = _workspace(output, name)
    source = (workspace / 'Fixture.lean').read_bytes()
    plan = prior._request(case, source)
    request = {'repoRoot': str(workspace), 'goal': prior._goal(),
               'witness': plan['witness'], 'interpretation': plan['interpretation'],
               'mode': mode, 'deadlineMonotonic': deadline, 'limits': {}}
    prior._write(output / (name + '-request.json'), request)
    prior._write(output / (name + '-plan.json'), plan)
    if term is not None:
        (output / (name + '-term.lean')).write_text(term)
    started = time.monotonic()
    checked = check_nat_rational_lift(request, plan['planId'], term)
    prior._write(output / (name + '-check.json'), checked)
    unchanged = source == (workspace / 'Fixture.lean').read_bytes()
    row = {'case': name, 'planId': plan['planId'], 'expected': expected,
           'observed': checked['status'], 'diagnostic': checked['diagnostic'],
           'passed': case_passed(expected, checked) and unchanged,
           'sourceUnchanged': unchanged, 'elapsedSeconds': time.monotonic() - started,
           'resourceStop': _resource_stop(checked, {'max_rss_bytes': DEFAULT_MAX_RSS_BYTES})}
    print(json.dumps(row), flush=True)
    return row


def run(output, timeout, external_deadline=None):
    Path(ladon.__file__).resolve().relative_to(ROOT / 'src')
    started = time.monotonic()
    deadline = prior._effective_deadline(started, timeout, external_deadline)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    identity = {'runnerSha256': prior._digest(Path(__file__).read_bytes()),
                'caseProviderSha256': prior._digest(PRIOR_PATH.read_bytes()),
                'fixtureSha256': prior._digest((prior.FIXTURE / 'Fixture.lean').read_bytes())}
    prior._write(output / 'start.json', {'startedMonotonic': started,
        'deadlineMonotonic': deadline, 'timeoutSeconds': timeout,
        'externalDeadline': external_deadline, 'identity': identity})
    rows = []
    for case in _cases():
        if time.monotonic() >= deadline:
            break
        rows.append(_run_case(case, output, deadline))
        if rows[-1]['resourceStop']:
            break
    result = {'schema': 'ladon-public-lift-qualification-v1', 'cases': rows,
              'passed': len(rows) == len(_cases()) and all(row['passed'] for row in rows),
              'elapsedSeconds': time.monotonic() - started, 'identity': identity,
              'scope': 'constructed-source-interpretation-only',
              'sourceFormulaFidelity': 'unverified'}
    prior._write(output / 'RESULT.json', result)
    return 0 if result['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=int, default=1800)
    parser.add_argument('--deadline-monotonic', type=float)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 1800:
        parser.error('timeout must be within the shared 30-minute gate')
    return run(args.output, args.timeout_seconds, args.deadline_monotonic)


if __name__ == '__main__':
    raise SystemExit(main())
