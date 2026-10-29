import json,sys
from pathlib import Path
from ladon.correspondence_check import _check_goal
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission_worker import _accepted
b=Path('.codex/state/real-prose-connection').resolve();root=b/'probe-project'
case=sys.argv[1];p=json.loads((b/('probe-'+case+'.json')).read_text())
result=_check_goal(p['goal'],p['term'],root,(root/'Context.lean').read_bytes(),{},pinned_toolchain(root))
out=b/('probe-'+case+'-'+sys.argv[2]+'-result.json');assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n')
print({'case':case,'accepted':_accepted(result),'status':result.get('status'),'diagnostic':result.get('diagnostic')})
