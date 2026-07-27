"""Shared source-index exception without codec/model import cycles."""


class SourceIndexError(ValueError):
    """Raised when a sound source index cannot be constructed or decoded."""


__all__ = ["SourceIndexError"]
