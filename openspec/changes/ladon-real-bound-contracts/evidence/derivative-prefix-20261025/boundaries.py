"""Public source freshness, schema separation and historical-receipt controls."""
import hashlib,json,sys
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/derivative-prefix').resolve();out=base/'boundaries';out.mkdir(exist_ok=False)
root=base/'generic-first/project';plan=base/'generic-first/plan.json';proof=base/'generic-first/proof.json'
def run(name,operation,input,selected=root):
 r=run_bounded_target_process([sys.executable,'-m','ladon.entrypoint','investigation','contract',operation,
 '--root',str(selected),'--input',str(input),'--proof',str(proof),'--timeout-seconds','600'],
 cwd=Path.cwd(),timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (out/(name+'.json')).write_text(json.dumps(asdict(r),indent=2))
 assert r.returncode==2 and json.loads(r.stdout)['status']=='invalid',(name,r.stdout,r.stderr)
 print(name,'invalid',flush=True)
source=root/'JointFamilies.lean';original=source.read_bytes()
try:
 source.write_bytes(original+b'\n-- unchanged names, changed bytes\n')
 run('stale-source','check-derivative-prefix',plan)
finally:source.write_bytes(original)
assert source.read_bytes()==original
run('receipt-is-not-plan','check-derivative-prefix',base/'generic-first/result.json')
run('derivative-plan-on-v1-command','check-bound-prefix',plan)
legacy=base/'v1-replay/dependent-positive-plan.json'
assert legacy.exists()
run('v1-plan-on-derivative-command','check-derivative-prefix',legacy,base/'v1-replay/dependent')
changed=json.loads(plan.read_text());changed['measure']={'declaration':'Other.measure','arguments':[]}
(out/'injected-measure.json').write_text(json.dumps(changed))
run('injected-measure','check-derivative-prefix',out/'injected-measure.json')
(out/'RESULTS.json').write_text(json.dumps({'invalidInputs':5,'sourceRestored':True,
 'sourceDigest':hashlib.sha256(original).hexdigest()},indent=2))
