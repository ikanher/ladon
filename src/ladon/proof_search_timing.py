"""Request-local exclusive work timings for index operations."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import monotonic

_ACTIVE = ContextVar('ladon_index_timing', default=None)


@contextmanager
def update_timing():
    totals = dict.fromkeys(('enumeration', 'hashing', 'extraction', 'database'), 0.0)
    token = _ACTIVE.set((totals, []))
    try:
        yield totals
    finally:
        _ACTIVE.reset(token)


@contextmanager
def phase(name):
    active = _ACTIVE.get()
    if active is None:
        yield
        return
    totals, stack = active
    started = monotonic()
    frame = [0.0]
    stack.append(frame)
    try:
        yield
    finally:
        elapsed = monotonic() - started
        stack.pop()
        totals[name] += max(0.0, elapsed - frame[0])
        if stack:
            stack[-1][0] += elapsed


def timed_phase(name):
    def decorate(function):
        @wraps(function)
        def timed(*args, **kwargs):
            with phase(name):
                return function(*args, **kwargs)
        return timed
    return decorate
