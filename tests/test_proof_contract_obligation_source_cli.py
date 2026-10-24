"""The public workflow checks every retained source demand and saves complete inputs."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from support.proof_contract_planned_source import build_plan_request
from test_proof_contract_cli import invoke
from test_proof_contract_planned_source import FIXTURE

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_obligation_artifacts import obligations_artifact


@pytest.fixture(scope='module')
def inputs(tmp_path_factory):
    base = tmp_path_factory.mktemp('whole-source-cli')
    root = base / 'repo'
    root.mkdir()
    for name in ('ThreeSteps.lean', 'lean-toolchain'):
        shutil.copyfile(FIXTURE / name, root / name)
    snapshots = {}
    for name in ('firstBound', 'secondBound', 'thirdBound', 'alternateBound', 'endpoint'):
        snapshot = produce_formal_snapshot(root, 'ThreeSteps.lean', 'ThreeSteps',
                                          'ThreeSteps.' + name, timeout_seconds=30)
        assert snapshot['status'] == 'extracted', snapshot
        snapshots[name] = snapshot
    plan = build_plan_request(snapshots)
    native = obligations_artifact(plan, analysis_id='analysis:whole-source')
    context = {a['artifactId']: a for snap in snapshots.values() for a in snap['artifacts']}
    context[plan.derivation_artifact['artifactId']] = plan.derivation_artifact
    providers = []
    for name in ('firstBound', 'secondBound', 'thirdBound', 'alternateBound'):
        snap = snapshots[name]
        contract = next(a for a in snap['artifacts'] if a['artifactKind'] == 'proofir.contract')
        providers.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                                          'localId': contract['payload']['contractId']},
                          'providerSnapshot': snap, 'providerReadingId': 'reading:' + name,
                          'terms': ['by exact ThreeSteps.' + name]})
    values = {'analysis': native, 'context': {'artifacts': list(context.values())},
              'sources': {'parentSnapshot': snapshots['endpoint'],
                          'parentReadingId': plan.desired_reading_identity['readingId'],
                          'providers': providers}}
    paths = {}
    for key, value in values.items():
        path = base / (key + '.json')
        path.write_text(json.dumps(value))
        paths[key] = path
    return base, root, paths


def _invoke(inputs, output, *, sources=None):
    _, root, paths = inputs
    return invoke('check-obligations', '--input', paths['analysis'], '--context', paths['context'],
                  '--sources', paths['sources'] if sources is None else sources,
                  '--root', root, '--output-dir', output, '--timeout-seconds', '180')


@pytest.fixture(scope='module')
def checked(inputs):
    base, root, _ = inputs
    before = hashlib.sha256((root / 'ThreeSteps.lean').read_bytes()).hexdigest()
    output = base / 'checked'
    process = _invoke(inputs, output)
    assert process.returncode == 0, process.stdout + process.stderr
    report = json.loads(process.stdout)
    return output, report, before


def test_public_source_run_checks_all_four_demands_without_promoting_method(checked, inputs):
    _, report, before = checked
    checks = report['sourceChecks']
    assert len(checks) == 4
    statuses = {r['providerDeclaration']: r['status'] for r in checks}
    assert statuses == {'ThreeSteps.firstBound': 'checked-support',
                        'ThreeSteps.secondBound': 'unresolved',
                        'ThreeSteps.thirdBound': 'checked-support',
                        'ThreeSteps.alternateBound': 'checked-support'}
    assert report['wholeMethodAuthority'] == 'none'
    assert report['mathematicalFalsity'] == 'not-established'
    assert len(report['routes']) == 2
    assert any(r['describedRoute'] and r['sourceCheckStatus'] == 'unresolved' for r in report['routes'])
    assert any(not r['describedRoute'] and r['sourceCheckStatus'] == 'checked' for r in report['routes'])
    assert hashlib.sha256((inputs[1] / 'ThreeSteps.lean').read_bytes()).hexdigest() == before


def test_saved_source_requests_reconstruct_exact_construction_digests(checked):
    from ladon._proof_contract_source_obligations_formula import _formula_symbols
    from ladon._proof_contract_source_obligations_staging import _request_digest, _source_prefix

    output, report, _ = checked
    for check in report['sourceChecks']:
        request = json.loads((output / check['sourceRequest']).read_text())
        result = json.loads((output / check['construction']).read_text())
        assert 'deadlineMonotonic' in request and 'planRequest' in request
        assert request['planResult']['schema'] == 'ladon-contract-obligation-planner-v2'
        parent, provider = request['parentSnapshot'], request['providerSnapshot']
        expected = {'kind': 'forallNat2', **_formula_symbols(provider['observation']['normalizedTypeExpr'])}
        expected['offset'] = result['selectedRequirement']['contractRecord']['features']['regularity']['offset']
        _, prefix = _source_prefix(Path(request['repoRoot']), parent, provider)
        assert _request_digest(request, parent, provider, expected, prefix) == result['requestDigest']


def test_existing_run_directory_is_preserved_without_another_check(checked, inputs):
    output, _, _ = checked
    before = {str(p.relative_to(output)): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    process = _invoke(inputs, output)
    assert process.returncode == 2
    assert {str(p.relative_to(output)): p.read_bytes() for p in output.rglob('*') if p.is_file()} == before


def test_missing_providers_emit_requests_without_claiming_discharge(inputs):
    base, _, paths = inputs
    sources = json.loads(paths['sources'].read_text())
    sources['providers'] = []
    path = base / 'missing-sources.json'
    path.write_text(json.dumps(sources))
    process = _invoke(inputs, base / 'missing', sources=path)
    assert process.returncode == 0, process.stdout + process.stderr
    report = json.loads(process.stdout)
    assert len(report['providerSliceRequests']) == 4
    assert all(row['status'] == 'not-dispatched' for row in report['providerSliceRequests'])
    assert all(row['status'] == 'unavailable-provider' for row in report['sourceChecks'])
    assert report['mathematicalFalsity'] == 'not-established'
