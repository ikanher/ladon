"""Public CLI exposure and expired-clock resource behavior without Lean."""
import json
import time
from pathlib import Path

from ladon.proof_contract_cli import _parser, contract_main

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_route_context'


def test_both_route_context_commands_are_public():
    parser = _parser()
    planned = parser.parse_args(['route-context-obligations', '--input', 'request.json'])
    checked = parser.parse_args(['check-route-context-bridge', '--input', 'request.json',
                                 '--plan-id', 'sha256:' + '1' * 64, '--terms', 'terms.json'])
    assert planned.operation == 'route-context-obligations'
    assert checked.operation == 'check-route-context-bridge'


def test_expired_request_does_not_start_preparation(tmp_path, capsys):
    request = json.loads((FIXTURE / 'observed-request.json').read_text())
    request['deadlineMonotonic'] = time.monotonic() - 1
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(request))
    assert contract_main(['route-context-obligations', '--input', str(path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == 'timeout'
    assert 'preparation' not in result
    assert result['demandDischarged'] is False
