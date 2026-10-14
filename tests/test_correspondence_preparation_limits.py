"""Actual preparation interruption preserves an explicit unattempted frontier."""
import json

from test_correspondence_prepared_context import _case

from ladon import correspondence_preparation as preparation
from ladon.correspondence_check import prepare_correspondence
from ladon.entrypoint import main


def test_public_actual_compile_timeout_withholds_acceptance_and_names_frontier(tmp_path, monkeypatch, capsys):
    repo, source, compiled, fresh, _, _, _ = _case(tmp_path)
    record = json.loads((repo / 'positive.json').read_bytes())
    plan = prepare_correspondence(record, fresh, {'n': 'n'})
    plan_path, terms, output = [tmp_path / name for name in ('plan.json', 'terms.json', 'checked.json')]
    plan_path.write_text(json.dumps(plan))
    terms.write_text('[]')
    original = preparation.run_bounded_target_process
    def limited(*args, **kwargs):
        kwargs['timeout_seconds'] = .03
        return original(*args, **kwargs)
    monkeypatch.setattr(preparation, 'run_bounded_target_process', limited)
    code = main(['investigation', 'check', '--plan', str(plan_path), '--terms', str(terms),
                 '--repo', str(repo), '--root', str(repo), '--preparation', 'request',
                 '--output', str(output)])
    result = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code == 2 and result['status'] == 'invalid'
    assert not output.exists()
    assert result['planId'] == plan['planId']
    assert result['unattemptedObligations'] == [r['id'] for r in plan['obligations']]
    assert result['process']['timed_out'] is True
    assert result['process']['returncode'] != 0
    assert not list(compiled.glob('LadonPrepared*'))
    assert source.read_bytes().startswith(b'import Lean')
