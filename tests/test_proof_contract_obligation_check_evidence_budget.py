"""Oversized final metadata must retain an explicit incomplete bounded receipt."""
import importlib
import json
import time


def test_summary_budget_stop_preserves_counts_and_a_bounded_saved_report(tmp_path):
    module = importlib.import_module('ladon.proof_contract_obligation_checks')
    ceiling = 8 * 1024**2
    before = ceiling - 16 * 1024
    (tmp_path / 'existing-evidence.bin').write_bytes(b'x' * before)
    checks = [{'providerDeclaration': 'p' * 512, 'status': 'unresolved', 'routes': []}
              for _ in range(128)]
    state = {'sourceChecks': checks, 'providerSliceRequests': [], 'routeCoverage': [],
             'files': ['existing-evidence.bin'], 'bytes': before, 'outputOwned': True,
             'attempts': 0}
    report = module._finish(tmp_path, {}, state, time.monotonic())
    assert report['status'] == 'incomplete'
    assert report['omittedCoverage']['sourceChecks'] == 128
    assert report['wholeMethodAuthority'] == 'none'
    assert report['mathematicalFalsity'] == 'not-established'
    _assert_saved_summary_and_budget(tmp_path, report, ceiling)


def _assert_saved_summary_and_budget(tmp_path, report, ceiling):
    assert json.loads((tmp_path / 'summary.json').read_text()) == report
    total = sum(p.stat().st_size for p in tmp_path.iterdir() if p.is_file())
    assert total == report['resourceAccounting']['evidenceBytes']
    assert total <= ceiling
