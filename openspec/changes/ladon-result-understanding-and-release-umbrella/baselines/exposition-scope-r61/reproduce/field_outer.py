import json
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon'); state=root/'.codex/state/exposition-scope-r61'
receipt=state/'field-outer-receipt.json'
assert not receipt.exists(), 'Preserve historical attempts.'
budget=json.loads((state/'budget.json').read_text()); prior=budget['chargedUpperBoundSeconds']
result=run_bounded_target_process([str(root/'.venv/bin/python'),str(state/'field.py')],cwd=root,timeout_seconds=budget['budgetSeconds']-prior,max_output_bytes=8388608,max_rss_bytes=34359738368)
receipt.write_text(json.dumps(asdict(result),indent=2)+'\n')
budget=json.loads((state/'budget.json').read_text())
budget['innerCommandSeconds']=budget['chargedUpperBoundSeconds']-prior
budget['chargedUpperBoundSeconds']=prior+result.elapsed_seconds
budget['accounting']='Outer wall time includes fixture input loading, all CLI trials and assertions; inner times are subrecords, not added twice. Prepared fixture construction and required qualification are outside this custom operational budget.'
(state/'budget.json').write_text(json.dumps(budget,indent=2)+'\n')
print(json.dumps({'exitCode':result.returncode,'seconds':result.elapsed_seconds,'peakRssBytes':result.peak_rss_bytes,'output':result.stdout,'stderr':result.stderr[-2500:]}))
raise SystemExit(result.returncode or int(result.timed_out or result.output_limited or result.memory_limited))
