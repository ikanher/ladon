"""Shared supervision preserves the reason and user instruction on a stop."""

import importlib
from time import monotonic

import pytest

from ladon import process_supervisor
from ladon.process_supervisor import ProcessResult
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def test_memory_stop_preserves_cap_peak_and_report_back_instruction(monkeypatch):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    peak = DEFAULT_MAX_RSS_BYTES + 1024
    monkeypatch.setattr(process_supervisor, "run_bounded_target_process", lambda *_a, **_kw:
                        ProcessResult(("lean",), -9, "", "", 0, memory_limited=True,
                                      peak_rss_bytes=peak))
    with pytest.raises(api.SourceResourceLimit) as caught:
        api._runner(monotonic() + 5)(
            ["lean"], timeout_seconds=30, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
        )
    assert str(caught.value) == memory_limit_message(DEFAULT_MAX_RSS_BYTES, peak)


@pytest.mark.parametrize("flag,reason", [("timed_out", "timeout"),
                                         ("output_limited", "output")])
def test_other_resource_stops_retain_the_actual_reason(monkeypatch, flag, reason):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    stopped = ProcessResult(("lean",), -9, "", "", 0, **{flag: True})
    monkeypatch.setattr(process_supervisor, "run_bounded_target_process", lambda *_a, **_kw: stopped)
    with pytest.raises(api.SourceResourceLimit, match=reason):
        api._runner(monotonic() + 5)(["lean"], timeout_seconds=30)


def test_each_subprocess_gets_remaining_deadline_without_changing_other_bounds(monkeypatch):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    calls = []

    def supervised(command, **kwargs):
        calls.append(kwargs)
        return ProcessResult(tuple(command), 0, "", "", 0)

    monkeypatch.setattr(process_supervisor, "run_bounded_target_process", supervised)
    api._runner(monotonic() + 5)(
        ["lean"], timeout_seconds=30, max_output_bytes=4096,
        max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    assert len(calls) == 1
    assert 0 < calls[0]["timeout_seconds"] <= 5
    assert calls[0]["max_output_bytes"] == 4096
    assert calls[0]["max_rss_bytes"] == DEFAULT_MAX_RSS_BYTES


def test_expired_runner_starts_no_subprocess(monkeypatch):
    api = importlib.import_module("ladon.proof_contract_source_obligations")

    def forbidden(*_args, **_kwargs):
        pytest.fail("expired deadline launched a subprocess")

    monkeypatch.setattr(process_supervisor, "run_bounded_target_process", forbidden)
    with pytest.raises(api.SourceResourceLimit):
        api._runner(monotonic() - 1)(["lean"], timeout_seconds=30)
