"""Supervise required candidate gates separately from the frozen offline budget."""
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process

root = Path('/home/codex/projects/ladon')
state = root / '.codex/state/benefit-readers-r62'
mode = sys.argv[1]
path = state / (mode + '-final-outer-receipt.json')
assert not path.exists(), 'Preserve previous required-gate attempts.'
result = run_bounded_target_process(
    [str(root / '.venv/bin/python'), str(state / 'qualify.py'), mode],
    cwd=root, timeout_seconds=600, max_output_bytes=8388608, max_rss_bytes=34359738368)
path.write_text(json.dumps(asdict(result), indent=2) + '\n')
print(json.dumps({'mode': mode, 'exitCode': result.returncode, 'seconds': result.elapsed_seconds,
                  'peakRssBytes': result.peak_rss_bytes, 'output': result.stdout[-3000:], 'stderr': result.stderr[-1500:]}))
raise SystemExit(result.returncode or int(result.timed_out or result.output_limited or result.memory_limited))
