from __future__ import annotations

import subprocess
import sys
import time

def test_entrypoint_dispatches_proof_search_without_general_cli(tmp_path) -> None:
    from ladon.entrypoint import main

    assert main(["proof-search", "index", "status", "--repo-root", str(tmp_path)]) == 0


def test_lightweight_proof_search_startup_has_lower_import_overhead() -> None:
    def elapsed(command: list[str]) -> float:
        started = time.perf_counter()
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return time.perf_counter() - started

    executable = sys.executable
    lightweight = min(elapsed([executable, "-c", "from ladon.entrypoint import main"]) for _ in range(3))
    general = min(elapsed([executable, "-c", "import ladon.cli"]) for _ in range(3))
    assert lightweight < general * 0.75
