import hashlib,json
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/candidate');bundle=root/'integration-bundle-r46';bundle.mkdir(exist_ok=False);(bundle/'objects').mkdir()
def digest(data):return 'sha256:'+hashlib.sha256(data).hexdigest()
def jbytes(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
context=json.loads((root/'context-r46.json').read_text());context.pop('sourceManifestPath');context.pop('hostNetworkNamespace');commit=json.loads((root/'candidate-r46.json').read_text())['commit'];report={};receipts={}
for family in ('correctness','authority','integration','discovery'):
 rows={}
 def put(data):
  ref=digest(data);relative='objects/'+ref[7:];p=bundle/relative
  if p.exists():assert p.read_bytes()==data
  else:p.write_bytes(data)
  rows[ref]={'digest':ref,'path':relative};return ref
 def file(path):return put(Path(path).read_bytes())
 def obj(value):return put(jbytes(value))
 invpath=candidate/f'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/{family}-acceptance-inventory.json';inv=json.loads(invpath.read_text());resultrefs=[];logrefs=[];commands=[];nodes={}
 for runtime in ('py311','py312'):
  result=json.loads((root/f'{family}-r46-{runtime}.json').read_text());assert result['exitCode']==0 and not result.get('qualificationError'),result
  assert result['initialCollection']==result['collected'] and sorted(result['passed'])==sorted(result['collected']);assert not any(result[key] for key in ('failed','skipped','collectionErrors'))
  result['logArtifactRef']=file(root/f'{family}-r46-{runtime}.log');ref=obj(result);resultrefs.append(ref);logrefs.append(result['logArtifactRef']);commands.append({'command':result['command'],'status':'passed','evidenceDigest':ref});nodes[runtime]=len(result['collected'])
 for field,path in {'wheelDigest':candidate.parent/'dist/ladon-0.2.0-py3-none-any.whl','producerIdentity':candidate/'scripts/run_child_acceptance.py','environmentRef':root/'environment-r46.json','sourceTreeIdentity':root/'source-manifest-r46.json'}.items():assert file(path)==context[field]
 checks={'requirements':inv['requiredSourceChecks'],'status':'passed','sourceFileRefs':{path:file(candidate/path) for req in inv['requiredSourceChecks'] for path in req['files']}}
 if family=='authority':
  quality=json.loads((root/'source-quality-r46.json').read_text())
  for row in quality:row['logArtifactRef']=file(row.pop('logPath'))
  checks['qualityCommands']=quality
 receipt={'schema':'ladon-child-exit-receipt-v1','status':'passed','exitClass':inv['exitClass'],**context,'analysisCompleteness':'complete','omissions':[],
 'inventoryArtifactRef':file(invpath),'candidateArtifactRef':file(root/'candidate-identity-r46.json'),'sourceChecksArtifactRef':obj(checks),
 'resultArtifactRefs':resultrefs,'logArtifactRefs':logrefs,'commands':commands,'commandVector':json.loads((root/f'{family}-r46-py311.json').read_text())['commandVector'],
 'limitations':['Local integrity and recorded coverage do not authenticate producers or establish OS isolation, arbitrary target-code secrecy, held-out mathematical benefit or public distribution authority.','Historical evidence and failed qualification attempts keep their original identities. New qualification cannot retroactively supply pre-edit TDD chronology.']}
 if family=='integration':
  prereq=json.loads((root/'prerequisites-r46/commands.json').read_text());assert len(prereq)==len(inv['integrationPrerequisites']) and all(r['exitCode']==0 for r in prereq);refs=[]
  for row in prereq:row['logArtifactRef']=file(row.pop('logPath'));refs.append(obj(row))
  receipt.update(candidateCommit=commit,outputDirectory=str(root/'prerequisites-r46'),integrationPrerequisiteArtifactRefs=refs,childReceiptArtifactRefs={k:obj(r) for k,r in receipts.items()},additionalEvidenceArtifactRefs=[file(root/'baseline-comparison-r46.json'),file(root/'result-installed-r46-py311.log'),file(root/'result-installed-r46-py312.log'),file(candidate.parent/'dist/ladon-0.2.0.tar.gz')])
 receipt['evidenceFiles']=list(rows.values());receipt['receiptIdentity']=digest(jbytes(receipt));receipts[family]=receipt;(bundle/f'{family}-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');report[family]={'receiptIdentity':receipt['receiptIdentity'],'evidenceFileCount':len(rows),'nodes':nodes}
(root/'integration-bundle-r46-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
