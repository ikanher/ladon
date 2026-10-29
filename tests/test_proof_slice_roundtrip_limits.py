"""Both printers reject oversized closed text before parser/elaborator work."""

from pathlib import Path

import pytest

from ladon._source_goal_helpers import helper_source
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

ROOT = Path(__file__).parent / "fixtures/correspondence_m1"
LEAN = Path(__file__).parents[1] / "src/ladon/lean"


@pytest.mark.parametrize("helper", ["ladon_proof_slice_helper.lean", "ladon_scoped_slice_helper.lean"])
def test_closed_text_limit_precedes_reelaboration(tmp_path, helper):
    prefix = helper_source(LEAN / helper).decode().split('elab "#ladon_proof_slice ', 1)[0]
    source = tmp_path / "Oversized.lean"
    source.write_text(prefix + """
run_meta do
  let name := Name.mkSimple (String.ofList (List.replicate 1048576 'x'))
  let target := mkForall name BinderInfo.default (mkConst ``Nat) (mkConst ``True)
  let proof := mkLambda name BinderInfo.default (mkConst ``Nat) (mkConst ``True.intro)
  let _ ← checkedRoundtrip target proof
""")
    toolchain = pinned_toolchain(ROOT)
    result = run_bounded_target_process(
        [str(toolchain.lean_path), str(source)], cwd=ROOT,
        env=dict(toolchain.environment), timeout_seconds=60,
        max_output_bytes=1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    assert not result.succeeded
    assert "serialized closed expression exceeds 1 MiB" in result.stdout
    assert not result.timed_out and not result.memory_limited and not result.output_limited
