from pathlib import Path
from dataclasses import asdict
import json,sys
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/real-native').resolve();out=base/'native-cli';out.mkdir(exist_ok=False)
production=json.loads((base/'qualification-final/canonical-production.json').read_text());artifact=production['artifacts'][-1]
p=out/'contract.json';p.write_text(json.dumps(artifact));rows=[]
for operation in ['validate','inspect','canonicalize']:
 command=[sys.executable,'-m','ladon.entrypoint','proofir',operation,str(p)]
 r=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=30,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (out/(operation+'-command.json')).write_text(json.dumps(asdict(r),indent=2));assert r.returncode==0 and r.succeeded
 result=json.loads(r.stdout)
 if operation=='canonicalize':assert result==artifact
 elif operation=='inspect':assert result['contract']['authority']=='none' and result['contract']['admission']=='recorded-checked'
 else:assert result['status']=='valid'
 rows.append({'operation':operation,'status':'passed','exitCode':r.returncode})
(base/'native-cli-results.json').write_text(json.dumps(rows,indent=2));print('Actual fresh native contract passed public proofir validate/inspect/canonicalize.')
