"""Shared constants and errors for the semantic evidence registry."""

from __future__ import annotations

import sqlite3

REGISTRY_SCHEMA = "ladon-semantic-evidence-registry-v1"
REGISTRY_SCHEMA_VERSION = 1
REGISTRY_APPLICATION_ID = 0x4C53454D  # ASCII "LSEM".
DEFAULT_MAX_DATABASE_BYTES = 512 * 1024 * 1024
DEFAULT_BUSY_TIMEOUT_MS = 5_000
MIN_DATABASE_BYTES = 64 * 1024
SEMANTIC_EVIDENCE_CACHE_VERSION = "semantic-evidence-v1"


class SemanticEvidenceRegistryError(RuntimeError):
    """Base class for persistent semantic-evidence failures."""


class SemanticEvidenceRegistrySchemaError(SemanticEvidenceRegistryError):
    """The selected path is not this registry's exact schema generation."""


class SemanticEvidenceRegistryConflict(SemanticEvidenceRegistryError):
    """Stored content conflicts with an immutable content identity."""


class SemanticEvidenceRegistryNotFound(SemanticEvidenceRegistryError):
    """A requested artifact, environment, or typed reference is absent."""


class SemanticEvidenceRegistryBusy(SemanticEvidenceRegistryError):
    """Another writer retained SQLite ownership beyond the finite timeout."""


class SemanticEvidenceRegistryCapacity(SemanticEvidenceRegistryError):
    """The configured complete-database byte ceiling prevented an append."""


def raise_registry_operational_error(error: BaseException) -> None:
    """Translate stable SQLite ownership and capacity failures."""

    if not isinstance(error, sqlite3.OperationalError):
        return
    message = str(error).lower()
    if "locked" in message or "busy" in message:
        raise SemanticEvidenceRegistryBusy(
            "semantic evidence registry remained busy beyond its timeout"
        ) from error
    if "full" in message or "max_page_count" in message:
        raise SemanticEvidenceRegistryCapacity(
            "semantic evidence registry reached its configured byte limit"
        ) from error
