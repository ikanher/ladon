"""Deterministic 57.65/90 public continuation consumes work without clock reset."""

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path


def test_public_driver_performs_real_next_action_at_57_65_minutes(tmp_path, monkeypatch):
    import ladon.investigation_cli as cli
    import ladon.investigation_finalization as finalization

    real_initialize = cli.initialize
    now = datetime.now(UTC)
    started = now - timedelta(minutes=57, seconds=39)

    def initialize(*args, **kwargs):
        return real_initialize(*args, **kwargs, now=started)

    real_receipt = finalization.progress_receipt

    def receipt(*args, **kwargs):
        return real_receipt(*args, **kwargs, now=now)

    monkeypatch.setattr(cli, 'initialize', initialize)
    monkeypatch.setattr(finalization, 'progress_receipt', receipt)
    # Initialization's source validator uses its real clock; the simulated
    # start is historical, and every terminal decision uses the fixed clock.
    path = Path(__file__).parents[1] / 'scripts/demo_investigation_finalization.py'
    spec = importlib.util.spec_from_file_location('continuation_demo', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / 'continued'
    result = module.run(output)
    original = json.loads((output / 'plan.json').read_text())
    later = json.loads((output / 'continued.json').read_text())
    checkpoint = json.loads((output / 'checkpoint.json').read_text())
    assert result['status'] == 'continue'
    assert original['startedAt'] == later['startedAt'] == started.isoformat()
    assert checkpoint['remainingSeconds'] == 1941
    assert original['budgetSeconds'] == later['budgetSeconds'] == 5400
    assert not original['correspondenceBundles'] and len(later['correspondenceBundles']) == 1
    assert not (output / 'terminal.json').exists()
