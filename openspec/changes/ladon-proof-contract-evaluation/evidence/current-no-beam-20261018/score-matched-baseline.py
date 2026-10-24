import collections
import hashlib
import json
import statistics
from pathlib import Path

root=Path.cwd()
b=root/'openspec/changes/ladon-proof-contract-evaluation/evidence'
out=b/'current-no-beam-20261018'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')

def portable_score(folder):
 m=load(folder/'results/MEASUREMENTS.json');cases=m['cases']
 positives=[c for c in cases if c['role']=='positive'];controls=[c for c in cases if c['role']!='positive']
 assessments=[a for c in cases for a in c.get('result',{}).get('assessments',[])]
 records=[c['result']['generation'] for c in cases if 'result' in c]
 records += [a['measurement'] for a in assessments if a.get('measurement')]
 prep=[r for rows in m['preparation'].values() for r in rows]
 graph=[]
 for budget in [8,32,128]:
  rows=[r for r in m['graphs'] if r['expansionBudget']==budget]
  graph.append({'expansionBudget':budget,'denominator':len(rows),
    'supportedCasesFound':sum(r['result']['status']=='complete' for r in rows),
    'supportedDenominator':sum(r['expectedSupported'] for r in rows),
    'unsupportedDenominator':sum(not r['expectedSupported'] for r in rows),
    'expandedStates':sum(r['result']['expandedStates'] for r in rows)})
 return {'measurementSha256':sha(folder/'results/MEASUREMENTS.json'),
   'denominator':len(cases),'positiveDenominator':len(positives),'controlDenominator':len(controls),
   'positivesClosed':sum(bool(c.get('metrics',{}).get('closedCandidates')) for c in positives),
   'controlsFalselyClosed':sum(bool(c.get('metrics',{}).get('closedCandidates')) for c in controls),
   'unresolvedCases':sum(c.get('metrics',{}).get('status')!='measured' for c in cases),
   'terminalAssessments':dict(collections.Counter(a['status'] for a in assessments)),
   'independentReplays':sum(a.get('measurement') is not None for a in assessments),
   'independentReplaysPassed':sum(a.get('measurement',{}).get('status')=='passed' for a in assessments if a.get('measurement')),
   'advisoryScratchCompiled':sum(a.get('scratch',{}).get('status')=='compiled' for a in assessments if a.get('scratch')),
   'summedCaseProcessSeconds':sum(r['runtimeSeconds'] for r in records),
   'summedPreparationProcessSeconds':sum(r['runtimeSeconds'] for r in prep),
   'medianPositiveFirstAcceptedSeconds':statistics.median(c['metrics']['timeToFirstAcceptedCandidateSeconds'] for c in positives),
   'peakRssSampledBytes':max(r['peakRssSampledBytes'] for r in records+prep),
   'resourceStops':{k:sum(bool(r.get(k)) for r in records+prep) for k in ['timedOut','memoryLimited','outputLimited']},
   'graphs':graph}

def matrix_score(folder):
 m=load(folder/'MEASUREMENTS.json'); rows=[]
 for r in m['rows']:
  check=r['payload']['candidates'][0]['check']; process=r['measurement']
  rows.append({'case':r['case'],'processStatus':process['status'],
    'status':check['status'], 'residuals':check['residualPremises'],
    'runtimeSeconds':process['runtimeSeconds'],'peakRssSampledBytes':process['peakRssSampledBytes'],
    'resourceStops':{k:process[k] for k in ['timedOut','memoryLimited','outputLimited']}})
 return {'measurementSha256':sha(folder/'MEASUREMENTS.json'),'denominator':m['denominator'],'cases':rows}

oldp=b/'search-baseline-20261018'; newp=b/'portable-no-beam-20261018'
oldm=b/'matrix-baseline-20261018';newm=b/'matrix-no-beam-20261018'
for folder,manifest in [(oldp,b/'BASELINE.json'),(newp,out/'RUNTIME.json')]:
 f=load(folder/'FREEZE.json');assert sha(manifest)==f['baselineManifestSha256']
 for path,digest in f['inputs'].items():assert sha(folder/path)==digest,(folder,path)
 runtime=Path(f['runtime'])
 for row in load(manifest)['files']:assert sha(runtime/row['path'])==row['sha256'],row['path']
for folder in [oldm,newm]:
 f=load(folder/'FREEZE.json')
 for path,digest in f['inputs'].items():assert sha(Path(path))==digest,path
assert load(oldp/'CASES.json')==load(newp/'CASES.json')
assert (oldp/'ROUTES.json').read_bytes()==(newp/'ROUTES.json').read_bytes()
for key in load(oldp/'FREEZE.json')['inputs']:
 assert sha(oldp/key)==sha(newp/key),key
old=load(oldp/'results/MEASUREMENTS.json');new=load(newp/'results/MEASUREMENTS.json')
assert [(r['case'],r['expansionBudget'],r['result']) for r in old['graphs']]==[(r['case'],r['expansionBudget'],r['result']) for r in new['graphs']]
assert [(r['case'],[(a['candidate'],a['status']) for a in r['result']['assessments']]) for r in old['cases']]==[(r['case'],[(a['candidate'],a['status']) for a in r['result']['assessments']]) for r in new['cases']]
comparison={'schema':'ladon-no-beam-matched-engineering-comparison-v1',
 'portable':{'legacy':portable_score(oldp),'currentNoBeam':portable_score(newp)},
 'matrix':{'legacy':matrix_score(oldm),'currentNoBeam':matrix_score(newm)},
 'comparability':{'portableInputBytesIdentical':True,'portableHarnessBytesIdentical':True,
   'graphInputsAndCompleteOutputsIdentical':True,'portableCandidateStatusesIdentical':True,
   'boundsIdentical':load(oldp/'FREEZE.json')['bounds']==load(newp/'FREEZE.json')['bounds'],
   'matrixHarnessBytesIdentical':sha(oldm/'measure.py')==sha(newm/'measure.py'),
   'matrixBoundsIdentical':load(oldm/'FREEZE.json')['bounds']==load(newm/'FREEZE.json')['bounds'],
   'beamEnabled':False,'executionOrder':'Legacy earlier, current later; one observation per case, unrandomized.',
   'pathDifference':'Each arm has a separate same-depth working directory and immutable runtime snapshot.'},
 'nonclaims':['No beam policy exercised.','No causal speedup estimate from one unrandomized run.',
              'Existing discovery path does not invoke new contract analysis.',
              'Known development cases, no unfamiliar-source fault detection estimate.',
              'Original A/B/C promotion protocol unchanged and incomplete; C has zero admitted cases.']}
write(out/'SCORES.json',comparison)
write(out/'RUNNER.json',{'script':str(root/'.codex/state/proof-contract-analysis/run-matched-baseline.py'),
 'sha256':sha(root/'.codex/state/proof-contract-analysis/run-matched-baseline.py'),
 'behavior':'Unchanged legacy harness bytes; explicit runtime and manifest module globals replaced before freeze/measure. Portable inputs copied excluding generated .lake caches. Both arms refuse existing output.',
 'snapshotSourceMatchesCurrent':all(sha(root/r['path'])==r['sha256'] for r in load(out/'RUNTIME.json')['files'] if r['path']!='run-ladon')})
print(json.dumps(comparison,indent=2))
