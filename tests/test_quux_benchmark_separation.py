from __future__ import annotations

import json
from pathlib import Path

from ladon.benchmark_contract import OPTIONAL_LIVE_NAMES

ROOT = Path(__file__).parents[1]


def test_benchmark_contract_cannot_enable_quux() -> None:
    assert "quux" not in OPTIONAL_LIVE_NAMES
    schema = json.loads(
        (ROOT / "src/ladon/schemas/ladon-benchmark-manifest-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert "quux" not in json.dumps(schema).casefold()
    fixture = json.loads(
        (ROOT / "tests/fixtures/benchmark_harness/manifest-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert "quux" not in json.dumps(fixture).casefold()
