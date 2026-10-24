import hashlib, json, tarfile
from pathlib import Path
R=Path('openspec/changes/ladon-proof-contract-evaluation/evidence')
def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check_manifest(root, manifest):
    m=load(manifest); bad=[]
    for rel,digest in m.items():
        p=Path(root)/rel
        if not p.is_file() or sha(p)!=digest: bad.append(rel)
    return len(m),bad
# Original baseline: all retained first artifacts remain byte-identical.
legacy_n,legacy_bad=check_manifest(R/'search-baseline-20261018',R/'search-baseline-20261018/RESULT-MANIFEST.json')
# Original baseline runtime: every preserved 422-file hash must still match its immutable tree.
legacy_runtime=load(R/'BASELINE.json'); legacy_runtime_bad=[row['path'] for row in legacy_runtime['files'] if not (Path('.codex/state/proof-contract-analysis/baseline')/row['path']).is_file() or sha(Path('.codex/state/proof-contract-analysis/baseline')/row['path'])!=row['sha256']]
# Runtime payload: exact 447-entry runtime manifest must match both extracted snapshot and archive.
runtime=load(R/'current-no-beam-20261018/RUNTIME.json'); snap=Path(runtime['snapshotRoot'])
with tarfile.open(R/'current-no-beam-20261018/runtime.tar.gz','r:gz') as tf:
    tar={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
snapshot_bad=[]; tar_bad=[]; current_bad=[]
for row in runtime['files']:
    rel=row['path']; expected=row['sha256']; p=snap/rel
    if not p.is_file() or sha(p)!=expected: snapshot_bad.append(rel)
    b=tar.get(rel)
    if b is None or hashlib.sha256(b).hexdigest()!=expected: tar_bad.append(rel)
    if rel!='run-ladon' and (not Path(rel).is_file() or sha(rel)!=expected): current_bad.append(rel)
# Baseline and current portable freeze identities/harnesses/input bytes.
oldp=R/'search-baseline-20261018'; newp=R/'portable-no-beam-20261018'
of,nf=load(oldp/'FREEZE.json'),load(newp/'FREEZE.json')
portable_inputs_equal=of['inputs']==nf['inputs']
portable_input_hashes=[]
for rel,digest in nf['inputs'].items():
    p=newp/rel
    portable_input_hashes.append((rel,p.is_file() and sha(p)==digest))
portable_harness_equal=sha(oldp/'measure.py')==sha(newp/'measure.py')
portable_cases_equal=(oldp/'CASES.json').read_bytes()==(newp/'CASES.json').read_bytes()
portable_routes_equal=(oldp/'ROUTES.json').read_bytes()==(newp/'ROUTES.json').read_bytes()
# Matrix task, source, object, toolchain and manifest must match both frozen arms and live bytes.
oldm=load(R/'matrix-baseline-20261018/FREEZE.json'); newm=load(R/'matrix-no-beam-20261018/FREEZE.json')
oldmi=oldm['inputs']; newmi=newm['inputs']; matrix_common={k:(oldmi[k],newmi[k]) for k in oldmi if k in newmi}
# The only expected matrix input change is the pointer/hash to the selected runtime manifest.
old_without_runtime={k:v for k,v in oldmi.items() if not k.endswith('/BASELINE.json')}
new_without_runtime={k:v for k,v in newmi.items() if not k.endswith('/RUNTIME.json')}
matrix_nonruntime_same=sorted(old_without_runtime.values())==sorted(new_without_runtime.values())
matrix_live={p:sha(p)==digest for p,digest in newmi.items()}
targets=load(R/'matrix-baseline-20261018/TARGETS.json')
target_current={x['source']:sha(x['source'])==x['currentSha256'].removeprefix('sha256:') for x in targets['targets']}
# Every captured raw process artifact is integrity-bound by its measurement record.
def artifact_checks(value, rows=None):
    rows=[] if rows is None else rows
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("digest"), str):
            path=Path(value["path"]); expected=value["digest"].removeprefix("sha256:")
            rows.append((str(path),path.is_file() and sha(path)==expected))
        for v in value.values(): artifact_checks(v,rows)
    elif isinstance(value,list):
        for v in value: artifact_checks(v,rows)
    return rows
# Hash and semantic checks on raw measurement sets.
base_meas=load(oldp/'results/MEASUREMENTS.json'); current_meas=load(newp/'results/MEASUREMENTS.json')
base_mat=load(R/'matrix-baseline-20261018/MEASUREMENTS.json'); current_mat=load(R/'matrix-no-beam-20261018/MEASUREMENTS.json')
scores=load(R/'current-no-beam-20261018/SCORES.json')
full_graph_equal=[(r['case'],r['expansionBudget'],r['result']) for r in base_meas['graphs']]==[(r['case'],r['expansionBudget'],r['result']) for r in current_meas['graphs']]
status=lambda m:[(r['case'],[(a['candidate'],a['status']) for a in r.get('result',{}).get('assessments',[])]) for r in m['cases']]
candidate_status_equal=status(base_meas)==status(current_meas)
portable_limits_equal=of['bounds']==nf['bounds']
matrix_limits_equal=oldm['bounds']==newm['bounds']
limits={}
for arm,m in [('legacy',base_meas),('current',current_meas)]:
    records=[r['result']['generation'] for r in m['cases'] if 'result' in r]
    records += [a['measurement'] for r in m['cases'] for a in r.get('result',{}).get('assessments',[]) if a.get('measurement')]
    records += [r for group in m['preparation'].values() for r in group]
    limits[arm]={'n':len(records),'timeouts':sum(bool(x.get('timedOut')) for x in records),'outputStops':sum(bool(x.get('outputLimited')) for x in records),'memoryStops':sum(bool(x.get('memoryLimited')) for x in records),'maxRss':max(x.get('peakRssSampledBytes',0) for x in records),'maxOutput':max(x.get('outputBytes',0) for x in records)}
# Matrix score recomputation; preserve both cases in denominator.
mat_rows={}
for arm,m in [('legacy',base_mat),('current',current_mat)]:
    rows=[]
    for row in m['rows']:
        check=row['payload']['candidates'][0]['check']; met=row['measurement']
        rows.append((row['case'],met['status'],check['status'],check['residualPremises'],met['timedOut'],met['memoryLimited'],met['outputLimited'],met['peakRssSampledBytes']))
    mat_rows[arm]=rows
results={
 'legacyResultManifest':{'entries':legacy_n,'bad':legacy_bad},
 'legacyRuntime':{'manifestEntries':len(legacy_runtime['files']),'hashMismatches':legacy_runtime_bad},
 'runtime':{'manifestEntries':len(runtime['files']),'bytes':sum(x['bytes'] for x in runtime['files']),'snapshotBad':snapshot_bad,'archiveEntries':len(tar),'archiveBad':tar_bad,'snapshotVsCurrentBadExceptLauncher':current_bad,'runLadonShaMatches':sha(snap/'run-ladon')==next(x['sha256'] for x in runtime['files'] if x['path']=='run-ladon')},
 'portable':{'inputsMapsEqual':portable_inputs_equal,'allCurrentInputsMatch':all(ok for _,ok in portable_input_hashes),'badInputs':[p for p,ok in portable_input_hashes if not ok],'harnessEqual':portable_harness_equal,'casesEqual':portable_cases_equal,'routesEqual':portable_routes_equal,'boundsEqual':portable_limits_equal,'graphCount':[len(base_meas['graphs']),len(current_meas['graphs'])],'fullGraphOutputsEqual':full_graph_equal,'candidateStatusesEqual':candidate_status_equal,'limits':limits},
 'matrix':{'allFrozenInputIdentitiesSameExceptRuntimeManifest':matrix_nonruntime_same,'liveInputsMatch':matrix_live,'targetCount':targets['targetCount'],'uniqueOwners':targets['uniqueSourceOwners'],'targetsCurrentHashesMatch':target_current,'measurementsDenominators':[base_mat['denominator'],current_mat['denominator']],'semanticRows':mat_rows,'boundsEqual':matrix_limits_equal},
 'capturedArtifactDigests':{'portable':artifact_checks(base_meas)+artifact_checks(current_meas),'matrix':artifact_checks(base_mat)+artifact_checks(current_mat)},
 'scoreHashes':{'legacyPortable':sha(oldp/'results/MEASUREMENTS.json')==scores['portable']['legacy']['measurementSha256'],'currentPortable':sha(newp/'results/MEASUREMENTS.json')==scores['portable']['currentNoBeam']['measurementSha256'],'legacyMatrix':sha(R/'matrix-baseline-20261018/MEASUREMENTS.json')==scores['matrix']['legacy']['measurementSha256'],'currentMatrix':sha(R/'matrix-no-beam-20261018/MEASUREMENTS.json')==scores['matrix']['currentNoBeam']['measurementSha256']},
 'nonclaims':scores['nonclaims']}
print(json.dumps(results,indent=2))
