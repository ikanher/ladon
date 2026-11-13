from pathlib import Path
import json,hashlib,shutil,datetime,sys,subprocess
repo=Path('/home/codex/projects/ladon');b=repo/'openspec/changes/ladon-semantic-pitfalls-umbrella/evidence';e=b/'synthetic-launch-r01';r=Path('/home/codex/projects/ladon-evaluations/synthetic-r01')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert (e/'WORKSPACE-COPY.json').exists()
prepared=json.loads((r/'PREPARED-FILES.json').read_text())['files']
case=json.loads((b/'synthetic-evaluation-r01/CASESET-FREEZE.json').read_text())
runtime=json.loads((e/'RUNTIME.json').read_text())
for p,h in runtime['sourceHashes'].items():assert sha(repo/p)==h
for tool,h in runtime['toolHashes'].items():assert sha(Path(runtime['toolchainRoot'])/'bin'/tool)==h
registration=b/'synthetic-comparison-r01'
for line in (registration/'SHA256SUMS').read_text().splitlines():
 h,p=line.split('  ',1);assert sha(registration/p)==h
results=[];order=[]
for index,u in enumerate(case['units'],1):
 for arm in (['control','assisted'] if index%2 else ['assisted','control']):
  w=r/u['id']/arm;assert (w/'project').is_dir();assert not list((w/'outputs').iterdir())
  assert set(str(p.relative_to(w/'project')) for p in (w/'project').rglob('*') if p.is_file() or p.is_symlink())==set(prepared)
  for name,data in prepared.items():
   p=w/'project'/name
   if 'symlink' in data:assert p.is_symlink() and str(p.readlink())==data['symlink']
   else:
    assert p.is_file() and sha(p)==data['sha256'],str(p)
    assert p.stat().st_ino!=(r/'prepared'/name).stat().st_ino,str(p)
  for name,h in u['allowlistedFiles'].items():assert sha(w/name)==h
  assert sha(w/'RECIPE.md')==sha(b/'synthetic-workflow-r01/RECIPE.md')
  shutil.copyfile(e/'CHECK.py',w/'CHECK.py')
  manifest={'schema':'ladon-synthetic-unit-launch-v2','status':'ready-unactivated','arm':arm,'workspace':str(w),'model':'gpt-6-luna','reasoningEffort':'medium','context':'fresh; no inheritance; no prior case work','pythonExecutable':runtime['pythonExecutable'],'pythonInvocation':str(repo/'.venv/bin/python'),'ladonSourceRoot':str(repo/'src'),'toolchainBin':str(Path(runtime['toolchainRoot'])/'bin'),'allowedReadRoots':[str(w),str(repo/'src/ladon'),str(repo/'.venv'),runtime['pythonExecutable'],runtime['toolchainRoot'],'system Python standard library and system shared libraries required by registered executables'],'isolation':'procedural path/communication restrictions; no OS access-control claim','checkingRunner':'CHECK.py','clockActivation':'CHECK.py --activate before reading context.md or project mathematical sources; SESSION.json records actual start and deadline','wallSeconds':1200,'commandTimeoutSeconds':600,'maxRssBytes':12*1024**3,'maxOutputBytes':16*1024**2,'topLevelCheckingCommands':20,'underlyingLeanStarts':'descriptive; null if unavailable; sampled observations labeled sampled','registrationSha256':sha(registration/'SHA256SUMS'),'runtimeSnapshotSha256':sha(e/'RUNTIME.json'),'commonSetupReceiptSha256':sha(e/'SETUP.json'),'projectInventorySha256':sha(r/'PREPARED-FILES.json'),'inputFiles':{name:sha(w/name) for name in ['context.md','manifest.json','RECIPE.md','PROMPT.md','CHECK.py']},'outputDirectory':str(w/'outputs'),'controlSharedSupervisorOnly':arm=='control','noNetwork':True}
  (w/'LAUNCH.json').write_text(json.dumps(manifest,indent=2)+'\n')
  (w/'PROMPT.md').write_text((registration/'ARM-PROMPT.md').read_text().replace('WORKSPACE',str(w)).replace('ARM (control or assisted)',arm))
  with (w/'PROMPT.md').open('a') as f:
   f.write('\nBefore reading mathematical source, run the registered Python with CHECK.py --activate. Use CHECK.py -- COMMAND for each checking command. LAUNCH.json specifies the exact Python/source paths. The shared runner imports only the common process supervisor; control must not use Ladon native interfaces. FIRST-INTERPRETATIONS.md, FINDINGS.md and COSTS.json belong in outputs/.\n')
  # Bind the final delivered prompt after adding the common operational instructions.
  manifest['inputFiles']['PROMPT.md']=sha(w/'PROMPT.md');(w/'LAUNCH.json').write_text(json.dumps(manifest,indent=2)+'\n')
  results.append({'workspace':str(w),'manifestSha256':sha(w/'LAUNCH.json'),'verifiedProjectFiles':len(prepared),'outputsEmpty':True,'activated':False});order.append(str(w))
  print(u['id'],arm,'full byte verification passed',flush=True)
record={'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ready-to-launch','auditContextsStarted':0,'workspaces':results,'launchOrder':order,'registrationPolicyVersion':2,'runtimeSourcesAndToolchainMatch':True,'allProjectFilesByteVerified':True,'independentProjectInodes':True,'instruction':'Launch each listed workspace in its own fresh Luna-medium context. Supply PROMPT.md, not this inventory or evaluation records. Activation must precede source inspection. No mathematical workers were launched during preparation.'}
(e/'READINESS.json').write_text(json.dumps(record,indent=2)+'\n');(e/'CURRENT.json').write_text(json.dumps({'recordedAtUtc':record['recordedAtUtc'],'status':'ready-to-launch','auditContextsStarted':0,'readiness':'READINESS.json','remainingGates':[],'activation':'Pending until actual audit launch; each SESSION.json will bind start and deadline.'},indent=2)+'\n')
