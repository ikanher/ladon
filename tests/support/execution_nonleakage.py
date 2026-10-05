"""Scan execution evidence for synthetic discarded caller environment inputs."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

SYNTHETIC_ENVIRONMENT = {
    'LADON_TEST_PRIVATE_NAME': 'synthetic-private-ladon-637101',
    'API_TOKEN': 'synthetic-private-token-637102',
    'LEAN_PATH': 'synthetic-caller-library-637103',
    'ELAN_TOOLCHAIN': 'synthetic-caller-toolchain-637104',
    'BASH_ENV': 'synthetic-caller-shell-637105',
    'GIT_CONFIG_COUNT': 'synthetic-caller-git-637106',
    'LANGUAGE': 'synthetic-caller-language-637107',
}
# LEAN_PATH is intentionally recorded when Ladon derives it from compiled roots.
FORBIDDEN_MARKERS = tuple(SYNTHETIC_ENVIRONMENT.values()) + tuple(
    key for key in SYNTHETIC_ENVIRONMENT if key != 'LEAN_PATH'
)


def poison_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Inject safe synthetic values into this test's caller environment."""
    for key, value in SYNTHETIC_ENVIRONMENT.items():
        monkeypatch.setenv(key, value)
    return dict(os.environ)


def assert_no_discarded_input(value: object) -> None:
    """Check keys and values in raw output or a complete JSON-like evidence object."""
    if isinstance(value, bytes):
        data = value
    elif isinstance(value, str):
        data = value.encode()
    else:
        data = json.dumps(value, sort_keys=True, default=str).encode()
    for marker in FORBIDDEN_MARKERS:
        assert marker.encode() not in data, 'discarded caller environment input leaked'


def assert_clean_files(directory: Path) -> None:
    """Scan generated output and SQLite sidecars while retaining live WAL files."""
    for path in directory.rglob('*'):
        if path.is_file():
            assert_no_discarded_input(path.read_bytes())
