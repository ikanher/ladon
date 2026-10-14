"""Immutable termination receipts preserve unfinished work and the original clock."""
import json
from datetime import UTC, datetime, timedelta


def test_public_checkpoint_then_premature_finalize_continues_with_original_clock(tmp_path, capsys):
    """Checkpoint is immutable; ordinary unfinished finalization exits 2 and saves no terminal receipt."""
    from ladon.entrypoint import main
    from ladon.investigation_correspondence import initialize_v3

    text = tmp_path / 'source.txt'
    text.write_text('First source assertion.\nSecond source assertion.\n', encoding='utf-8')
    started = datetime.now(UTC) - timedelta(minutes=57, seconds=39)
    plan_value = initialize_v3(text, tmp_path, minutes=90, unit_lines=1, now=started)
    plan = tmp_path / 'plan.json'
    original = json.dumps(plan_value, sort_keys=True).encode()
    plan.write_bytes(original)
    checkpoint = tmp_path / 'checkpoint.json'
    terminal = tmp_path / 'terminal.json'

    assert main(['investigation', 'checkpoint', '--plan', str(plan), '--root', str(tmp_path),
                 '--output', str(checkpoint)]) == 0
    checkpoint_value = json.loads(checkpoint.read_text(encoding='utf-8'))
    _assert_checkpoint_clock(checkpoint_value, plan_value, plan, original)

    code = main(['investigation', 'finalize', '--plan', str(plan), '--root', str(tmp_path),
                 '--output', str(terminal)])
    assert code == 2
    outcome = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert outcome['status'] == 'continue'
    assert outcome['next']
    assert not terminal.exists()
    assert plan.read_bytes() == original


def _assert_checkpoint_clock(checkpoint_value, plan_value, plan, original):
    assert checkpoint_value['startedAt'] == plan_value['startedAt']
    assert checkpoint_value['budgetSeconds'] == plan_value['budgetSeconds']
    assert checkpoint_value['next']
    assert plan.read_bytes() == original

