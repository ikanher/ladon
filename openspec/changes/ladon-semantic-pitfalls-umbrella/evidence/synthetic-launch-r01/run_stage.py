"""Bounded experiment command runner; produces receipts, not proof authority."""
import dataclasses
import json
import os
import sys
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process

name, cwd, *command = sys.argv[1:]
output = Path(__file__).resolve().parent
environment = dict(os.environ)
for key in list(environment):
    if key.startswith(("LEAN_PATH", "LEAN_SRC_PATH", "LAKE_PACKAGES_DIR")):
        environment.pop(key)
result = run_bounded_target_process(
    command, cwd=Path(cwd).resolve(), timeout_seconds=3600,
    max_output_bytes=16 * 1024 * 1024, max_rss_bytes=12 * 1024**3,
    env=environment, observe_resources=True,
)
record = dataclasses.asdict(result)
(output / f"{name}.stdout").write_text(record.pop("stdout"))
(output / f"{name}.stderr").write_text(record.pop("stderr"))
(output / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n")
raise SystemExit(0 if result.succeeded else 1)
