"""Deadline traces replay historical decisions without claiming clock authenticity."""

from datetime import UTC, datetime

import pytest


def test_deadline_exhaustion_latches_if_wall_clock_moves_back(monkeypatch):
    from ladon import _contract_propagation_deadline as clocks

    deadline = datetime(2026, 1, 2, tzinfo=UTC)
    now = iter([datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 3, tzinfo=UTC)])
    monkeypatch.setattr(clocks, "_utc_now", lambda: next(now))
    budget = clocks.DeadlineObservation(deadline)
    assert budget.expired() is False
    assert budget.expired() is True
    assert budget.expired() is True
    assert budget.finish() == {"checks": 3, "firstExceededCheck": 2}


def test_historical_deadline_replay_does_not_read_current_time(monkeypatch):
    from ladon import _contract_propagation_deadline as clocks

    def forbidden():
        raise AssertionError("historical replay read the current clock")

    monkeypatch.setattr(clocks, "_utc_now", forbidden)
    budget = clocks.DeadlineObservation(datetime(2000, 1, 1, tzinfo=UTC),
                                       replay={"checks": 3, "firstExceededCheck": 2})
    assert [budget.expired() for _ in range(3)] == [False, True, True]
    assert budget.finish() == {"checks": 3, "firstExceededCheck": 2}


@pytest.mark.parametrize("trace", [
    {"checks": True, "firstExceededCheck": None},
    {"checks": 2, "firstExceededCheck": 3},
    {"checks": 1, "firstExceededCheck": 0},
    {"checks": 2, "firstExceededCheck": None, "trusted": True},
])
def test_invalid_deadline_trace_cannot_be_replayed(trace):
    from ladon._contract_propagation_deadline import DeadlineObservation

    with pytest.raises((TypeError, ValueError)):
        DeadlineObservation(datetime(2000, 1, 1, tzinfo=UTC), replay=trace)


def test_short_and_unconsumed_replay_traces_are_rejected():
    from ladon._contract_propagation_deadline import DeadlineObservation

    budget = DeadlineObservation(None, replay={"checks": 1, "firstExceededCheck": None})
    with pytest.raises(ValueError):
        budget.finish()
    assert budget.expired() is False
    with pytest.raises(ValueError):
        budget.expired()
