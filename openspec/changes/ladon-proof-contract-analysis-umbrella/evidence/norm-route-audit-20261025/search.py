import json,subprocess
from pathlib import Path
base=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/norm-route-audit-20261025')
common=['.venv/bin/python','-m','ladon.entrypoint','proof-search','search']
queries=[('inverse-bound','name',['--text','inverse bound','--query-mode','all']),('coefficient-seminorm','name',['--text','coefficient_seminorm_bound','--query-mode','phrase']),('weight-summable','name',['--text','summable weight','--query-mode','all']),('inverse-types','type-text',['--pattern','inverse']),('order-four','type-text',['--pattern','+ 4']),('coeff-seminorm-types','type-text',['--pattern','coeffSeminorm']),('xjet-types','type-text',['--pattern','xJet'])]
commands=[]
for name,kind,extra in queries:
 cmd=common+[kind,'--repo-root','.codex/state/navier-stokes-informed-diagnostic/formalization',*extra,'--scope','namespace','--root','NavierStokes','--limit','30','--freshness','stored','--format','json','--output',str(base/(name+'.json'))]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
 commands.append({'name':name,'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 assert r.returncode==0,(name,r.stderr)
with (base/'SEARCH-COMMANDS.json').open('x') as f:json.dump(commands,f,indent=2);f.write('\n')
print('queries completed:',len(commands))
for name in ['index-build','index-status','inverse-bound','order-four']:
 x=json.loads((base/(name+'.json')).read_text());print(name, list(x))
