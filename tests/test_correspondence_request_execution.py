"""Public checking retains all fresh evidence in an immutable prepared request."""
import hashlib

from test_correspondence_prepared_context import _case

from ladon.correspondence_check import check_correspondence, prepare_correspondence


def test_request_route_checks_every_link_and_reports_all_actual_processes(tmp_path):
    repo, source, _, fresh, _, _, _ = _case(tmp_path)
    prose = repo / 'preparation.txt'
    prose.write_text('Every natural number equals itself.\n')
    var = {'tag': 'var', 'id': 'n'}
    record = {'id': 'request-control', 'source': {'path': prose.name, 'startLine': 1,
              'endLine': 1, 'quote': prose.read_text().strip(),
              'sha256': hashlib.sha256(prose.read_bytes()).hexdigest()},
              'formula': {'tag': 'forall', 'binder': {'id': 'n', 'name': 'n', 'domain': 'Nat'},
                          'body': {'tag': 'eq', 'left': var, 'right': var}}, 'symbols': {}}
    plan = prepare_correspondence(record, fresh, {'n': 'n'})
    terms = [{'obligation': identity, 'mode': 'prove', 'term': term} for identity, term in [
        ('interpretation', 'by intro h; exact h'), ('object-map', 'by intro n; trivial'),
        ('conclusion', 'by intro n; dsimp; intro _ _; rfl')]]
    original = source.read_bytes()
    result = check_correspondence(plan, terms, repo, preparation='request')
    _assert_result_binding(result, source, original, plan)
    for row in result['checks']:
        _assert_proof_row(row)
    _assert_metrics(result, repo)


def _assert_result_binding(result, source, original, plan):
    assert result['parentSupport'] == 'supported-for-attributed-interpretation', [(r['obligation'], r['status'], r.get('completion', {})) for r in result['checks']]
    assert result['preparationMode'] == 'request'
    assert result['compiledImportIdentityReuses'] > 0
    assert source.read_bytes() == original
    assert {row['obligation'] for row in result['checks']} == {r['id'] for r in plan['obligations']}


def _assert_proof_row(row):
    assert row['capture']['status'] == 'captured'
    assert row['completion']['replay']['status'] == 'accepted'
    assert row['completion']['trust']['accepted']
    assert row['completion']['trust']['coverage'] == 'complete'
    assert 'sorryAx' not in row['completion']['trust']['observedAxioms']


def _assert_metrics(result, repo):
    metrics = result['executionAccounting']
    assert metrics['checkCount'] == len(result['checks'])
    assert metrics['distinctProseSubjects'] == metrics['typingProbeCount'] == 1
    assert metrics['processCount'] == len(metrics['processes'])
    assert metrics['processCount'] > len(result['checks']) * 7
    assert metrics['stages']['source-preparation']['processCount'] >= 1
    _assert_preparation_count(metrics, repo)


def _assert_preparation_count(metrics, repo):
    compiler_calls = [r for r in metrics['processes']
                      if r['stage'] == 'source-preparation' and '-o' in r['command']]
    assert len(compiler_calls) == 1
    assert not list((repo / '.lake/build/lib/lean').glob('LadonPrepared*'))
