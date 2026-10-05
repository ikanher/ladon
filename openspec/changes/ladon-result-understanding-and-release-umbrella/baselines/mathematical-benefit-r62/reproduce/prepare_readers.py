from pathlib import Path
import json,shutil,hashlib,time
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path((state/'run-path').read_text().strip());matrix=(root/'../lean/matrix-factorization').resolve();shared=run/'shared';shared.mkdir();start=time.monotonic()
source=shared/'source';source.mkdir();rows=[]
for p in sorted((matrix/'Mf/DP').rglob('*.lean')):
 rel=p.relative_to(matrix);raw=p.read_bytes();dest=source/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append({'path':str(rel),'bytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()})
(source/'lean-toolchain').write_bytes((matrix/'lean-toolchain').read_bytes())
(source/'lakefile.toml').write_text('name = "readerSourcePopulation"\n[[lean_lib]]\nname = "Mf"\n')
original=Path('/home/codex/.cache/ladon-reader-loop-r49/shared/evidence');evidence=shared/'evidence';shutil.copytree(original,evidence)
# Unchanged genuine guide/assessment references remain background available to both arms.
for name,originalname in [('manifest.json','manifest.json'),('guide.json','assets/00092.json'),('assessments.json','assets/00089.json'),('exposition.tex','assets/00091.bin')]:shutil.copy2(original/originalname,shared/name)
(r62guide:=Path('/home/codex/.cache/ladon-qualification-r61/ladon-exposition-scope-r61-z3sf9fbx/field-fixture/correct-guide.json'))
condition=json.loads(r62guide.read_text())['steps'][0]['explanation']
paragraphs=[{'id':'passage-17','claim':'cor:fixed-epoch-all-horizon','component':'average','paragraph':'The supplied uniform transcript targets formally establish both transcript and average-only optimality under the sufficient condition.'}, {'id':'passage-42','claim':'lem:binomial-propagation','component':'propagation','paragraph':condition}, {'id':'passage-68','claim':'lem:binomial-propagation','component':'propagation','paragraph':condition.replace('If fixedEpochCenterGap point h boundary ≥ 0, ', '')}]
(shared/'passages.json').write_text(json.dumps({'scope':'Neutral unreviewed evaluation passages; assess each on its merits. No case-specific reviews or proposed repairs supplied.','passages':paragraphs},ensure_ascii=False,indent=2)+'\n')
# No answer-labelled guide or r61 synthetic review/receipt inputs enter shared materials.
for arm in ['application-ordinary','application-augmented','exposition-ordinary','exposition-augmented']:
 cwd=run/arm;cwd.mkdir();(cwd/'lean-toolchain').write_bytes((matrix/'lean-toolchain').read_bytes());(cwd/'.lake/build/lib').mkdir(parents=True);(cwd/'.lake/build/lib/lean').symlink_to(matrix/'.lake/build/lib/lean',target_is_directory=True);(cwd/'.lake/packages').symlink_to(matrix/'.lake/packages',target_is_directory=True)
 for name,new in [('ContextA','TaskOne'),('ContextB','TaskTwo')]:
  raw=Path('/home/codex/.cache/ladon-handoff-r60-i80pkq23/fixture',name+'.lean').read_text();(cwd/(new+'.lean')).write_text(raw)
 (cwd/'mathematics').symlink_to(shared,target_is_directory=True)
(state/'prepared-identity.json').write_text(json.dumps({'sourcePopulation':'entire declared Mf/DP source subtree at preparation time, not selected expected owner','sourceFiles':len(rows),'sourceBytes':sum(x['bytes'] for x in rows),'sourceInventoryDigest':'sha256:'+hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'sourceCopySeconds':time.monotonic()-start,'knownImportScaffold':'Both task goal files preserve the original import of CenterGapPropagation; this is disclosed task scaffolding, not unassisted blind discovery. The search population itself is unfiltered.','caseSpecificAuthoredReviewsSupplied':False,'genuineGuideAndAssessmentSupplied':True,'proseControls':'Correct/altered case labels and expectation key are evaluator-only; passage IDs are neutral. Missing-premise insertion narrows original claim.','neighborSourceOrBuildWrites':False},indent=2)+'\n')
(shared/'source-inventory.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'run':str(run),'sourceFiles':len(rows),'sourceBytes':sum(x['bytes'] for x in rows),'preparationSeconds':time.monotonic()-start}))
