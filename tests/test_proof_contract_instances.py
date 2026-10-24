from pathlib import Path
from types import SimpleNamespace

import pytest

from ladon.proof_contract_production import (
    DEFAULT_MAX_RSS_BYTES,
    _parse_worker,
    _process_failure_message,
    produce_formal_contract,
)

ROOT = Path(__file__).resolve().parent / "fixtures/proof_contract_production"
SOURCE = "ProducerAdversarial.lean"


def test_local_nat_arithmetic_and_order_instances_are_not_assumed_builtin():
    for declaration in ("custom_mul", "custom_add", "custom_le", "custom_offset"):
        observed = produce_formal_contract(
            ROOT,
            SOURCE,
            "ProducerAdversarial",
            f"ProducerAdversarial.{declaration}",
            timeout_seconds=60,
            max_rss_bytes=12 * 1024**3,
        )
        assert observed["status"] == "unsupported"
        assert observed["contract"] is None
        assert any(
            residual["code"] == "unsupported-carrier-or-instance"
            for residual in observed["residuals"]
        )


def test_module_identity_and_declaration_source_ownership_are_distinct():
    module_decl = produce_formal_contract(
        ROOT,
        SOURCE,
        "ProducerAdversarial",
        "Different.qualified_name_need_not_match_module",
    )
    assert module_decl["status"] == "extracted"
    source_range = module_decl["observation"]["declarationRange"]
    assert source_range["startLine"] <= source_range["endLine"]

    imported_decl = produce_formal_contract(
        ROOT,
        SOURCE,
        "ProducerAdversarial",
        "Nat.zero_le",
    )
    assert imported_decl["status"] == "unavailable"
    assert imported_decl["contract"] is None


def test_worker_json_depth_is_bounded_before_recursive_decode():
    nested = "{" * 257 + "0" + "}" * 257
    with pytest.raises(ValueError, match="nesting bound"):
        _parse_worker('{"version"' + ":" + nested + "}")


def test_memory_failure_uses_shared_cap_and_peak_diagnostic():
    process = SimpleNamespace(
        timed_out=False,
        memory_limited=True,
        output_limited=False,
        peak_rss_bytes=2 * 1024**3,
    )
    message = _process_failure_message(process, DEFAULT_MAX_RSS_BYTES)
    assert "12 GiB" in message
    assert "2 GiB" in message


@pytest.mark.parametrize("timeout,rss", [
    (float("nan"), 12 * 1024**3), (float("inf"), 12 * 1024**3),
    (True, 12 * 1024**3), (60, True), (60, 12.5),
])
def test_formal_process_bounds_reject_nonfinite_or_boolean_values(timeout, rss):
    from ladon.proof_contract_production import _validate_request

    with pytest.raises((TypeError, ValueError)):
        _validate_request(ROOT, "ProducerCases", "ProducerCases.supported_base", timeout, rss)
