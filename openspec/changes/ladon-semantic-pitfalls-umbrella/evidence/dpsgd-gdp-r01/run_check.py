"""Bounded audit check using this checkout's existing process supervisor."""
import dataclasses
import datetime
import json
import sys
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process

out = Path(__file__).resolve().parent
inputs = json.loads((out / 'INPUTS.json').read_text())
remaining = (datetime.datetime.fromisoformat(inputs['deadlineUTC']) - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if remaining <= 0:
    raise SystemExit('Frozen audit deadline reached; preserve unresolved work.')
label, *command = sys.argv[1:]
if not command or '/' in label:
    raise SystemExit('Expected a simple result label and a command.')
record = out / (label + '.json')
if record.exists():
    raise SystemExit('Result already exists; use a new attempt label.')
result = run_bounded_target_process(command, cwd=Path(inputs['repository']),
    timeout_seconds=min(600, remaining), max_output_bytes=8 * 1024**2,
    max_rss_bytes=12288 * 1024**2, observe_resources=True)
record.write_text(json.dumps(dataclasses.asdict(result), indent=2) + '\n')
print(json.dumps({k: v for k, v in dataclasses.asdict(result).items() if k not in ('stdout', 'stderr', 'resource_observations')}))
if result.memory_limited:
    print('Stop progress and report back to user: the 12 GiB process-tree memory limit was not enough.')
raise SystemExit(0 if result.succeeded else 1)
