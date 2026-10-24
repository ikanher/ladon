"""Actual checked transport preserves the predicate that erased carriers lose."""

from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES


def test_checked_subtype_transport_and_membership_erasure_counterexample():
    root = Path(__file__).parent / "fixtures/proof_contract_production"
    toolchain = pinned_toolchain(root)
    checked = run_bounded_target_process(
        [str(toolchain.lean_path), "RestrictedTransport.lean"], cwd=root,
        env=dict(toolchain.environment), timeout_seconds=60,
        max_output_bytes=1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    assert checked.succeeded, checked.stdout + checked.stderr
    assert "sorryAx" not in checked.stdout
    for theorem in ("subtype_to_guarded", "alpha_renamed_presentation",
                    "membership_erasure_is_not_equivalent"):
        assert f"'{theorem}' does not depend on any axioms" in checked.stdout
