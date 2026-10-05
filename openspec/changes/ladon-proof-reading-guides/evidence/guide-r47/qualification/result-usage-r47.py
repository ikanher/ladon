import hashlib,json,os,runpy,subprocess,sys
from pathlib import Path
base=Path('/home/codex/.cache/ladon-qualification-r47/ladon-guides-r47b-9nrffih0/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r47/ladon-guides-r47b-9nrffih0/candidate');out=base/'result-usage-r47';out.mkdir(exist_ok=False)
sys.path.insert(0,str(candidate/'tests'))
helper=runpy.run_path(str(candidate/'tests/test_result_resolution.py'))
manifest,artifacts=helper['inputs']()
manifest_path=out/'synthetic-manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
artifact_paths=[]
for index,a in enumerate(artifacts):
 p=out/f'artifact-{index}.json';p.write_text(json.dumps(a,indent=2)+'\n');artifact_paths.append(p)
environment={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'}}
rows=[]
for runtime in ('py311','py312'):
 console=Path('/home/codex/.cache/ladon-qualification-r47/ladon-guides-r47b-9nrffih0')/runtime/'bin/ladon'
 for scenario,path,files in [('exact-synthetic-stored-target',manifest_path,artifact_paths),('frozen-exposition-no-canonical-inputs',candidate/'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/fixed-epoch-v1/manifest.json',[])]:
  argv=[str(console),'result','resolve',str(path)]
  for file in files:argv+=['--artifact',str(file)]
  proc=subprocess.run(argv,cwd=out,env=environment,capture_output=True,timeout=15)
  stem=out/f'{scenario}-{runtime}';stdout=stem.with_suffix('.stdout');stderr=stem.with_suffix('.stderr');stdout.write_bytes(proc.stdout);stderr.write_bytes(proc.stderr)
  assert proc.returncode==0,proc.stderr
  result=json.loads(proc.stdout)
  expected={'resolved':1} if scenario.startswith('exact-') else {'unresolved':20}
  assert result['canonicalResolution']['statuses']==expected
  rows.append({'scenario':scenario,'runtime':runtime,'argv':argv,'workingDirectory':str(out),'exitCode':proc.returncode,'statuses':expected,'stdoutPath':str(stdout),'stdoutDigest':'sha256:'+hashlib.sha256(proc.stdout).hexdigest(),'stderrPath':str(stderr),'stdoutBytes':len(proc.stdout),'nonclaim':'Synthetic source-map example is producer-supplied metadata, not a live Lean or informal-correspondence check.'})
(out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
