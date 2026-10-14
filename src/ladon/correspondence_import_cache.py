"""Request-scoped reuse of freshly hashed immutable compiled import identities."""
from contextlib import contextmanager
from contextvars import ContextVar

_OWNER = ContextVar('ladon_verified_compiled_imports', default=None)


def cached_import_identity(path):
    owner = _OWNER.get()
    if owner is None or path not in owner.imports:
        return None
    return owner.verify_cached_import(path)


@contextmanager
def verified_import_cache(owner):
    if _OWNER.get() is not None:
        raise ValueError('nested compiled import cache request')
    token = _OWNER.set(owner)
    try:
        yield
    finally:
        _OWNER.reset(token)
