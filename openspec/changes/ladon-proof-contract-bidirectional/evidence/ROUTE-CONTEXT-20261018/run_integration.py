import json,os,subprocess,time
from pathlib import Path
p=Path('openspec/changes/ladon-proof-contract-bidirectional/evidence/ROUTE-CONTEXT-20261018')
assert json.loads((p/'source-verification.json').read_text())['status']=='PASS'
old=json.loads((p.parent/'CONTEXT-OBLIGATIONS-20261018/integration-command.json').read_text())
files=[v for v in old['commandVector'] if v.startswith('tests/')]+[str(f) for f in sorted(Path('tests').glob('test_proof_contract_route_context_*.py'))]
assert len(files)==len(set(files))
command=['.venv/bin/python','-m','pytest','-q',*files,'--junitxml='+str(p/'integration.xml')]
with (p/'integration-command.json').open('x') as f:json.dump({'environment':{'PYTHONPATH':'src:tests'},'commandVector':command,'testOwnerFiles':len(files),'selection':'All prior964 tests across150owners plus all new route-context testfiles; no exclusions.'},f,indent=2)
started=time.monotonic()
with (p/'integration.log').open('x') as log:r=subprocess.run(command,env={**os.environ,'PYTHONPATH':'src:tests'},stdout=log,stderr=subprocess.STDOUT,check=False)
with (p/'integration-status.json').open('x') as f:json.dump({'exitCode':r.returncode,'elapsedSeconds':time.monotonic()-started},f)
print(r.returncode,time.monotonic()-started);raise SystemExit(r.returncode)
