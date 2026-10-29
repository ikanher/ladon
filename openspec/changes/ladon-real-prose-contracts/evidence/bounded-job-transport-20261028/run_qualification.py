import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process

base = Path(__file__).resolve().parent
assert not (base/'QUALIFICATION-PROCESS.json').exists()
result = run_bounded_target_process([sys.executable, str(base/'qualify.py')], cwd=Path.cwd(),
    env={**os.environ,'PYTHONPATH':str(Path('src').resolve())},timeout_seconds=600,
    max_output_bytes=8*1024**2,max_rss_bytes=12*1024**3)
(base/'QUALIFICATION-PROCESS.json').write_text(json.dumps(asdict(result),indent=2)+'\n')
print({'returncode':result.returncode,'seconds':result.elapsed_seconds,
       'peakRssMiB':result.peak_rss_bytes/1024**2,'timedOut':result.timed_out,
       'memoryLimited':result.memory_limited,'outputLimited':result.output_limited})
print(result.stdout);print(result.stderr)
raise SystemExit(0 if result.succeeded else 1)
