"""Use-site typing must govern numeral-only application semantics."""
import hashlib
import json
from pathlib import Path

from ladon.entrypoint import main
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution

FIXTURE = Path(__file__).parent / 'fixtures/correspondence_m1'


def test_public_rat_division_and_wrong_but_provable_control(tmp_path):
    source = tmp_path / 'claim.txt'
    source.write_text('Forty-one twentieths is strictly greater than two.\n')
    fraction = {'tag': 'app', 'symbol': 'divide', 'args': [
        {'tag': 'const', 'name': '41'}, {'tag': 'const', 'name': '20'}]}
    execution = prepare_direct_lean_execution(FIXTURE, None, pinned_toolchain(FIXTURE),
                                              require_compiled_module=False)
    for index, (domain, relation, expected) in enumerate([
        ('Rat', 'lt', 'true'), ('Rat', 'eq', 'false'), ('Nat', 'eq', 'true'),
    ]):
        record = {'id': f'numeral-{index}', 'source': {'path': source.name,
                  'startLine': 1, 'endLine': 1, 'quote': source.read_text().strip(),
                  'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
                  'formula': {'tag': relation, 'left': {'tag': 'const', 'name': '2'},
                              'right': fraction},
                  'symbols': {'divide': {'leanName': 'HDiv.hDiv',
                                        'leanType': f'{domain} → {domain} → {domain}'}}}
        authored, output = tmp_path / f'record-{index}.json', tmp_path / f'output-{index}.json'
        authored.write_text(json.dumps(record))
        assert main(['investigation', 'interpret', '--record', str(authored), '--root',
                     str(tmp_path), '--output', str(output)]) == 0
        formula = json.loads(output.read_text())['loweredFormula']
        check = tmp_path / 'Check.lean'
        check.write_text('import Lean\nimport Init.Data.Rat\n#eval decide (' + formula + ')\n')
        result = run_bounded_target_process([*execution.command, str(check)], cwd=FIXTURE,
                 env=execution.environment, timeout_seconds=60, max_output_bytes=1024**2,
                 max_rss_bytes=32*1024**3)
        assert result.succeeded, result.stderr + result.stdout
        # Interpreter output is a semantic regression control, not a proof receipt.
        assert result.stdout.strip() == expected
