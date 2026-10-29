from pathlib import Path
import json,sys
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/real-bound-binding').resolve();m=base/'public-matrix';root=m/'dependent';p=root/'Case.lean';original=p.read_bytes()
out=base/'stale-controls';out.mkdir(exist_ok=False)
def invoke(name,input):
 cmd=[sys.executable,'-m','ladon.entrypoint','investigation','contract','check-bound-prefix',
 '--root',str(root),'--input',str(input),'--proof',str(m/'dependent-positive-proof.json'),'--timeout-seconds','600']
 r=run_bounded_target_process(cmd,cwd=Path.cwd(),timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (out/(name+'.json')).write_text(json.dumps(asdict(r),indent=2))
 result=json.loads(r.stdout);assert r.returncode==2 and result['status']=='invalid',(name,result)
 print(name,result,flush=True)
try:
 p.write_bytes(original+b'\n-- changed source, unchanged declaration names\n')
 invoke('stale-source',m/'dependent-positive-plan.json')
finally:
 p.write_bytes(original)
assert p.read_bytes()==original
invoke('receipt-is-not-plan',m/'dependent-positive-result.json')
