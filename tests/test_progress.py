from __future__ import annotations

import io
import json
import threading
from unittest.mock import patch

import pytest

from ladon.progress import (
    ProgressEvent,
    ProgressReporter,
    ResourceLimitExceeded,
    RunBudget,
    RunLimits,
    descendant_pids,
    process_tree_rss_bytes,
)


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_auto_progress_is_silent_when_stderr_is_redirected() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(mode="auto", run_id="run", stream=stream)
    phase = reporter.phase("discover")

    phase.start()
    phase.finish(status="complete", completed=2, total=2)

    assert reporter.mode == "off"
    assert stream.getvalue() == ""


def test_json_progress_is_one_schema_versioned_document_per_line() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(mode="json", run_id="run-1", stream=stream)

    reporter.emit(
        ProgressEvent(
            run_id="run-1",
            phase="discover",
            kind="update",
            status="running",
            elapsed_seconds=1.25,
            completed=100,
            total=2600,
            cache={"hits": 7},
        )
    )

    payload = json.loads(stream.getvalue())
    assert payload == {
        "cache": {"hits": 7},
        "completed": 100,
        "elapsedSeconds": 1.25,
        "event": "update",
        "phase": "discover",
        "runId": "run-1",
        "schemaVersion": 1,
        "status": "running",
        "total": 2600,
    }


def test_auto_progress_uses_plain_events_for_a_tty() -> None:
    stream = TtyBuffer()
    reporter = ProgressReporter(mode="auto", run_id="run", stream=stream)
    phase = reporter.phase("indexing")

    phase.start()
    phase.finish(status="complete", completed=3)

    assert reporter.mode == "plain"
    assert "ladon: progress indexing start running" in stream.getvalue()
    assert "finish complete 3" in stream.getvalue()


def test_count_progress_emits_at_bounded_hundred_unit_intervals() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(mode="json", run_id="run", stream=stream)
    phase = reporter.phase("discover")

    phase.start()
    for completed in range(1, 251):
        phase.update(completed=completed, total=2600)
    phase.finish(status="complete", completed=250, total=2600)

    events = [json.loads(line) for line in stream.getvalue().splitlines()]
    updates = [event for event in events if event["event"] == "update"]
    assert [event["completed"] for event in updates] == [100, 200]
    assert events[-1]["completed"] == 250
    assert events[-1]["total"] == 2600


def test_run_budget_reports_wall_and_report_byte_crossings() -> None:
    budget = RunBudget(RunLimits(wall_seconds=1.0, report_bytes=10))
    with patch("ladon.progress.monotonic", return_value=budget.started_at + 2.0), pytest.raises(
        ResourceLimitExceeded
    ) as wall:
            budget.check("module_dag")
    assert wall.value.kind == "overall_wall_time"
    assert budget.crossed and budget.crossed["phase"] == "module_dag"

    byte_budget = RunBudget(RunLimits(report_bytes=10))
    with pytest.raises(ResourceLimitExceeded) as report:
        byte_budget.check_report_bytes("serialization", 11)
    assert report.value.kind == "report_bytes"


def test_descendant_selection_and_linux_rss_probe_are_bounded() -> None:
    rows = {
        10: (1, 100),
        11: (10, 200),
        12: (11, 300),
        20: (1, 400),
    }

    assert descendant_pids(10, rows) == {10, 11, 12}
    assert process_tree_rss_bytes(10) is None or process_tree_rss_bytes(10) >= 0


def test_active_wall_watchdog_sets_cancellation_and_preserves_crossing() -> None:
    cancel = threading.Event()
    budget = RunBudget(
        RunLimits(wall_seconds=0.02),
        sample_interval_seconds=0.005,
    )

    with pytest.raises(ResourceLimitExceeded) as crossing, budget.watch(
        "lean_extraction", cancel
    ):
            assert cancel.wait(timeout=1)

    assert crossing.value.kind == "overall_wall_time"
    assert crossing.value.phase == "lean_extraction"
    assert budget.crossed is not None
    assert budget.crossed["phase"] == "lean_extraction"


def test_watchdog_without_runtime_limits_is_a_single_noop_context() -> None:
    entered: list[str] = []

    with RunBudget(RunLimits()).watch("discover", threading.Event()):
        entered.append("discover")

    assert entered == ["discover"]


def test_active_rss_watchdog_records_observation_and_cancels() -> None:
    cancel = threading.Event()
    budget = RunBudget(
        RunLimits(rss_bytes=100),
        sample_interval_seconds=0.005,
    )
    observations = iter((50, 150))

    def observed_rss(_pid: int) -> int:
        return next(observations, 150)

    with patch("ladon.progress.process_tree_rss_bytes", side_effect=observed_rss), pytest.raises(
        ResourceLimitExceeded
    ) as crossing, budget.watch("module_dag", cancel):
                assert cancel.wait(timeout=1)

    assert crossing.value.kind == "process_tree_rss"
    assert crossing.value.observed == 150
    assert budget.metadata()["observed"]["peakRssBytes"] == 150
