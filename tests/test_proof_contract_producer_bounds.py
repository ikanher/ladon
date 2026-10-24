"""Public statement observation preserves caller supervision and output limits."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from ladon import proof_contract_production as production
from ladon.process_supervisor import ProcessResult


@pytest.fixture
def inputs(monkeypatch, tmp_path):
    captured = {
        "root": tmp_path, "sourceBytes": b"import Std\n", "sourceHash": "a" * 64,
        "helperBytes": b"helper", "helperHash": "b" * 64,
        "toolchain": SimpleNamespace(context_identity="context:test"),
        "execution": SimpleNamespace(command=["lean"], environment={}),
    }
    monkeypatch.setattr(production, "_capture_inputs", lambda *args: captured)
    monkeypatch.setattr(production, "_verify_inputs", lambda *args: None)
    return captured


def failed(command, **kwargs):
    return ProcessResult(tuple(command), 1, "", "controlled runner failure", 0.0)


def test_custom_supervisor_receives_exact_bounds(inputs):
    calls = []

    def run(command, **kwargs):
        calls.append(kwargs)
        return failed(command, **kwargs)

    result = production.produce_formal_contract(
        inputs["root"], "Test.lean", "Test", "Test.bound", runner=run,
        timeout_seconds=7, max_output_bytes=4096, max_rss_bytes=123456,
    )
    assert result["status"] == "unavailable"
    assert len(calls) == 1
    assert calls[0]["timeout_seconds"] == 7
    assert calls[0]["max_output_bytes"] == 4096
    assert calls[0]["max_rss_bytes"] == 123456
    assert result["processReceipts"][0]["requestedMaxOutputBytes"] == 4096


@pytest.mark.parametrize("cap", [0, -1, True, 64 * 1024**2 + 1])
def test_bad_output_cap_stops_before_input_capture(monkeypatch, tmp_path, cap):
    def unexpected(*args):
        pytest.fail("invalid bounds reached target input capture")

    monkeypatch.setattr(production, "_capture_inputs", unexpected)
    with pytest.raises((ValueError, TypeError)):
        production.produce_formal_contract(
            tmp_path, "Test.lean", "Test", "Test.bound", max_output_bytes=cap,
        )


def test_helper_result_file_uses_same_output_cap(inputs):
    def oversized(command, **kwargs):
        Path(command[-1]).write_bytes(b"x" * 4097)
        return ProcessResult(tuple(command), 0, "", "", 0.0)

    with pytest.raises(ValueError, match="(limit|bound|large|size)"):
        production.produce_formal_contract(
            inputs["root"], "Test.lean", "Test", "Test.bound", runner=oversized,
            max_output_bytes=4096,
        )


def test_default_supervisor_lookup_remains_patchable(monkeypatch, inputs):
    calls = []

    def patched(command, **kwargs):
        calls.append(kwargs)
        return failed(command, **kwargs)

    monkeypatch.setattr(production, "run_bounded_target_process", patched)
    result = production.produce_formal_contract(
        inputs["root"], "Test.lean", "Test", "Test.bound",
    )
    assert result["status"] == "unavailable"
    assert calls[0]["max_output_bytes"] == 8 * 1024**2


def test_snapshot_api_forwards_bounds_and_supervisor(monkeypatch, tmp_path):
    from ladon import proof_contract_formal as formal

    calls = []

    def observe(*args, **kwargs):
        calls.append(kwargs)
        return {"status": "unavailable", "contract": None}

    monkeypatch.setattr(formal, "_observe", observe)
    monkeypatch.setattr(formal, "_artifacts", lambda *args: [])
    formal.produce_formal_snapshot(
        tmp_path, "Test.lean", "Test", "Test.bound", runner=failed,
        max_output_bytes=4096,
    )
    assert calls[0]["runner"] is failed
    assert calls[0]["max_output_bytes"] == 4096
