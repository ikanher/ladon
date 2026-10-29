import json
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process

base = Path(__file__).resolve().parent
mode = sys.argv[1]
receipt_path = base/(mode+'-PROCESS.json')
assert not receipt_path.exists()
with tempfile.TemporaryDirectory(prefix='matrix-scratch-',dir=base) as scratch:
    result = run_bounded_target_process([sys.executable,str(base/'matrix.py'),mode],cwd=Path.cwd(),
        env={**os.environ,'PYTHONPATH':str(Path('src').resolve()),'LADON_MATRIX_SCRATCH':scratch},
        timeout_seconds=600,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
receipt_path.write_text(json.dumps(asdict(result),indent=2)+'\n')
print({'mode':mode,'returncode':result.returncode,'seconds':result.elapsed_seconds,
       'peakRssGiB':result.peak_rss_bytes/1024**3,'timeout':result.timed_out,
       'memoryLimit':result.memory_limited,'outputLimit':result.output_limited})
print(result.stdout);print(result.stderr)
raise SystemExit(0 if result.succeeded else 1)
