#!/usr/bin/env python3
"""Run a frozen discovery study explicitly; external unavailability never gates CI."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import ladon
from ladon.acceptance_network import observe_network_isolation
from ladon.evaluation_baselines import run_baseline
from ladon.evaluation_corpus import (
    digest_bytes,
    validate_evaluation_plan,
    verify_repository_snapshot,
)
from ladon.evaluation_ladon import run_ladon
from ladon.evaluation_metrics import summarize_method
from ladon.evaluation_process import measure_command
from ladon.lean_toolchain import resolve_toolchain_context


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'output', 'ladon', 'toolchain-root', 'candidate-context', 'wheel'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--prepare-portable', action='store_true')
    return parser.parse_args()


def installed_scope(args, root):
    require_installed_python(root, args.ladon)
    path = root / 'scripts/run_child_acceptance.py'
    spec = importlib.util.spec_from_file_location('evaluation_acceptance_owner', path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    context, _ = owner._read_object(args.candidate_context)
    if Path(context['workingDirectory']).resolve() != root or owner._file_digest(args.wheel) != context['wheelDigest']:
        raise ValueError('study candidate or wheel differs from selected context')
    owner._validate_manifest(context, Path(__file__))
    owner._package_members(args.wheel, ladon.__file__)
    return owner, context


def require_installed_python(root, console):
    origin = Path(ladon.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    if not sys.flags.isolated or origin.is_relative_to(root) or not origin.is_relative_to(prefix):
        raise ValueError('study requires isolated imports from the selected installed environment')
    if console.resolve() != (Path(sys.executable).parent / 'ladon').resolve():
        raise ValueError('study console must belong to the selected installed interpreter')


def selected_tools(repository, args):
    pin = repository['toolchain']
    directory = args.toolchain_root / pin.replace('/', '--').replace(':', '---') / 'bin'
    lean, lake = directory / 'lean', directory / 'lake'
    if not lean.is_file() or not lake.is_file():
        raise FileNotFoundError('registered toolchain is not locally installed: ' + pin)
    return lean, lake


def prepare_repository(repository, cases, plan, args, root):
    repo = verify_repository_snapshot(repository, root)
    lean, lake = selected_tools(repository, args)
    output = args.output / repository['id']
    output.mkdir()
    preparation = []
    for case in cases:
        compiled = repo / '.lake/build/lib/lean' / (case['module'].replace('.', '/') + '.olean')
        if not compiled.is_file() and not repository['optional'] and args.prepare_portable:
            compiled.parent.mkdir(parents=True, exist_ok=True)
            argv = [str(lean), '-o', str(compiled), case['sourceFile']]
            record = measure_command(argv, cwd=repo, environment={'PATH': str(lean.parent), 'LANG': 'C.UTF-8'},
                                     bounds=plan['policy']['bounds'], output=output,
                                     stem='compile-' + case['id'])
            preparation.append(record)
            if record['status'] != 'passed':
                raise ValueError('explicit portable preparation failed')
        if not compiled.is_file():
            raise FileNotFoundError('registered compiled module is unavailable: ' + case['module'])
    context = resolve_toolchain_context(repo, lean_path=lean, lake_path=lake)
    index = output / 'index.sqlite'
    bounds = {**plan['policy']['bounds'], 'timeoutSeconds': plan['policy']['bounds']['indexPreparationTimeoutSeconds']}
    record = measure_command([str(args.ladon), 'proof-search', 'index', 'build', '--repo-root', str(repo),
                              '--index', str(index), '--format', 'json'], cwd=output,
                             environment=context.environment, bounds=bounds, output=output, stem='index')
    preparation.append(record)
    return context, index if record['status'] == 'passed' else None, preparation


def unavailable_repository(repository, cases, methods, reason):
    return {'repository': repository['id'], 'split': repository['split'], 'status': 'unavailable',
            'reason': reason, 'cases': [{'case': case['id'], 'methods': {
                method: {'status': 'unavailable', 'reason': reason,
                         'metrics': summarize_method({'status': 'unavailable', 'reason': reason}, case['expectedAcceptableCandidates'])}
                for method in methods}} for case in cases]}


def measure_case(case, context, index, plan, args, directory):
    output = directory / case['id']
    output.mkdir()
    rows = {}
    for method in plan['methods']:
        if method == 'ladon' and index is None:
            rows[method] = {'method': method, 'status': 'failed',
                            'reason': 'bounded Ladon index preparation failed',
                            'metrics': {'status': 'preparation-failed', 'verifiedCandidateRecall': 0.0,
                                        'incorrectSuggestionRate': None,
                                        'timeToFirstAcceptedCandidateSeconds': None}}
            continue
        target = output / method.replace('?', '-search').replace('#', 'hash-')
        target.mkdir()
        try:
            result = run_ladon(case, context, plan['policy']['bounds'], target,
                               console=args.ladon, index=index) if method == 'ladon' else run_baseline(
                                   method, case, context, plan['policy']['bounds'], target)
            rows[method] = {**result, 'metrics': summarize_method(result, case['expectedAcceptableCandidates'])}
        except (ValueError, KeyError, TypeError, OSError) as error:
            rows[method] = {'status': 'failed', 'reason': str(error), 'metrics': None,
                            'evidenceDirectory': str(target), 'nonclaims': ['Adapter failure cannot supply a success or baseline win.']}
    return {'case': case['id'], 'split': case['split'], 'methods': rows}


def measure_repository(repository, plan, args, root):
    cases = [case for case in plan['cases'] if case['repository'] == repository['id']]
    try:
        context, index, preparation = prepare_repository(repository, cases, plan, args, root)
    except (OSError, ValueError, RuntimeError) as error:
        return unavailable_repository(repository, cases, plan['methods'], str(error))
    rows = [measure_case(case, context, index, plan, args, args.output / repository['id']) for case in cases]
    verify_repository_snapshot(repository, root)
    return {'repository': repository['id'], 'split': repository['split'], 'status': 'measured',
            'context': context.to_dict(), 'preparation': preparation, 'cases': rows,
            'nonclaims': ['Selected compiled library roots do not prove correspondence with every source revision.']}


def main():
    args = arguments()
    root = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_text())
    owner, context = installed_scope(args, root)
    validate_evaluation_plan(plan, root)
    network = observe_network_isolation(context['hostNetworkNamespace'])
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for repository in plan['repositories']:
        rows.append(measure_repository(repository, plan, args, root))
        (args.output / 'progress.json').write_text(json.dumps(rows, indent=2) + '\n')
    owner._validate_manifest(context, Path(__file__))
    owner._package_members(args.wheel, ladon.__file__)
    validate_evaluation_plan(plan, root)
    report = {'schema': 'ladon-discovery-evaluation-study-v1', 'schemaVersion': 1,
              'preregistrationIdentity': plan['preregistrationIdentity'],
              'planDigest': digest_bytes(args.plan.read_bytes()), 'candidateScope': context,
              'studyProducerIdentity': digest_bytes(Path(__file__).read_bytes()),
              'commandVector': [sys.executable, '-I', __file__, *sys.argv[1:]],
              'networkIsolation': network, 'repositories': rows,
              'nonclaims': ['Measured outcomes do not themselves promote readiness.',
                            'No unavailable method/repository supplies a baseline win.',
                            'Source-derived goal labels cannot supply independent maintainer labels.']}
    (args.output / 'study.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'recorded', 'output': str(args.output),
                      'repositoriesMeasured': sum(row['status'] == 'measured' for row in rows)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
