"""Latched deadline decisions and bounded historical replay, without authentication."""

from datetime import UTC, datetime

MAX_DEADLINE_CHECKS = 1_000_000


def _utc_now():
    return datetime.now(UTC)


def validate_deadline_trace(trace):
    if not isinstance(trace, dict) or set(trace) != {"checks", "firstExceededCheck"}:
        raise ValueError("deadline observation must contain checks and firstExceededCheck")
    count, first = trace["checks"], trace["firstExceededCheck"]
    if type(count) is not int or not 0 <= count <= MAX_DEADLINE_CHECKS:
        raise ValueError("deadline observation check count is outside supported bounds")
    if first is not None and (type(first) is not int or not 1 <= first <= count):
        raise ValueError("deadline observation first exceeded check is invalid")
    return {"checks": count, "firstExceededCheck": first}


class DeadlineObservation:
    """One invocation's decisions; replay establishes consistency, not elapsed time."""

    def __init__(self, deadline, *, replay=None):
        if deadline is not None and (not isinstance(deadline, datetime) or deadline.tzinfo is None):
            raise ValueError("deadline must be a timezone-aware datetime or absent")
        self.deadline = deadline
        self._replay = None if replay is None else validate_deadline_trace(replay)
        if deadline is None and self._replay and self._replay["firstExceededCheck"] is not None:
            raise ValueError("an absent deadline cannot have exceeded")
        self._checks = 0
        self._first = None

    def expired(self):
        self._checks += 1
        if self._checks > MAX_DEADLINE_CHECKS:
            raise ValueError("deadline observation check-count resource bound exhausted")
        if self._replay is not None:
            return self._historical_expired()
        if self._first is None and self.deadline is not None and _utc_now() >= self.deadline:
            self._first = self._checks
        return self._first is not None

    def _historical_expired(self):
        if self._checks > self._replay["checks"]:
            raise ValueError("deadline replay consumed more checks than recorded")
        if self._checks == self._replay["firstExceededCheck"]:
            self._first = self._checks
        return self._first is not None

    def finish(self):
        if self._replay is not None and self._checks != self._replay["checks"]:
            raise ValueError("deadline replay left unconsumed recorded checks")
        return {"checks": self._checks, "firstExceededCheck": self._first}
