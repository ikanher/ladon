"""Observed fvar identity survives Unicode presentation without source rewriting."""
import hashlib
import shutil
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice


def test_actual_subscript_context_generates_and_replays_every_link(tmp_path):
    fixture = Path(__file__).parent / 'fixtures/correspondence_m1'
    root = tmp_path / 'repo'
    shutil.copytree(fixture, root, ignore=shutil.ignore_patterns('.ladon', '*.olean'))
    source = root / 'Identity.lean'
    source.write_text('''import Lean
namespace Identity
 theorem bridge (x : Nat) (h : x < 8) : x < 9 := Nat.lt.step h
 theorem selected (x₀ : Nat) (h₀ : x₀ < 8) : x₀ < 9 := bridge x₀ h₀
end Identity
''')
    original = source.read_bytes()
    prose = root / 'identity.txt'
    prose.write_text('Every natural less than eight is less than nine.\n')
    variable = {'tag': 'var', 'id': 'n'}
    def relation(bound):
        return {'tag': 'lt', 'left': variable, 'right': {'tag': 'const', 'name': str(bound)}}
    record = {'id': 'unicode', 'source': {'path': prose.name, 'startLine': 1,
              'endLine': 1, 'quote': prose.read_text().strip(),
              'sha256': hashlib.sha256(prose.read_bytes()).hexdigest()},
              'formula': {'tag': 'forall', 'binder': {'id': 'n', 'name': 'number', 'domain': 'Nat'},
                          'body': {'tag': 'implies', 'premise': relation(8), 'conclusion': relation(9)}},
              'symbols': {}}
    actual = extract_proof_slice(root, 'Identity.lean', 'Identity', 'Identity.selected',
                                'Identity.bridge', scoped=True)
    assert actual['complete'], actual
    identity = next(r['localId'] for r in actual['localContext'] if r['name'] == 'x₀')
    plan = prepare_correspondence(record, actual,
                                  {'profile': 'local-identity-v1', 'entries': {identity: 'n'}})
    assert not plan['residuals']
    assert {o['id'] for o in plan['obligations']} == {
        'interpretation', 'conditional', 'object-map', 'premise-1', 'conclusion', 'provider-1'}
    terms = [{'obligation': name, 'mode': 'prove', 'term': term} for name, term in [
        ('interpretation', 'by intro h; exact h'),
        ('object-map', 'by intro n; trivial'),
        ('premise-1', 'by intro n x h; exact h'),
        ('conclusion', 'by intro n x h formal; exact formal')]]
    result = check_correspondence(plan, terms, root)
    assert result['parentSupport'] == 'supported-for-attributed-interpretation', result
    assert all(c['status'] == 'supported' for c in result['checks'])
    assert source.read_bytes() == original
