"""Actual finite counterexamples prevent converse and necessity claims."""

import shutil
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES


def test_backward_sufficiency_does_not_imply_converse_or_necessity():
    fixture = Path(__file__).parent / 'fixtures/proof_contract_obligations'
    source = fixture / 'BackwardMath.lean'
    assert source.is_file()
    lean = shutil.which('lean')
    assert lean is not None
    checked = run_bounded_target_process(
        [lean, str(source.resolve())], cwd=fixture, timeout_seconds=60,
        max_output_bytes=1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert not any((checked.timed_out, checked.memory_limited, checked.output_limited))
    assert 'sorryAx' not in checked.stdout
    assert "'BackwardMath.no_converse' does not depend on any axioms" in checked.stdout
    assert "'BackwardMath.sufficient_not_necessary' does not depend on any axioms" in checked.stdout
