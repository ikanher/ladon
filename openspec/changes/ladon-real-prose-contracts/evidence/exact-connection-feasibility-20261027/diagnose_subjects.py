"""Offline diagnostic only: no acceptance predicate or production activation."""
import hashlib,json
from pathlib import Path
b=Path('.codex/state/real-prose-connection')
def fingerprint(encoded):
 prefix='ladon-expr-dag-v1:'
 assert encoded.startswith(prefix)
 graph=json.loads(encoded[len(prefix):]);hashes=[]
 changed=0
 for index,row in enumerate(graph['nodes']):
  tag=row[0]
  if tag in {'forallE','lam'}:
   assert len(row)==5
   refs=row[3:];assert all(type(r) is int and 0<=r<index for r in refs)
   value=[tag,'<binder-name>',row[2],*[hashes[r] for r in refs]];changed+=1
  elif tag=='app':
   refs=row[1:];assert len(refs)==2 and all(type(r) is int and 0<=r<index for r in refs)
   value=[tag,*[hashes[r] for r in refs]]
  elif tag=='letE':
   assert len(row)==6
   refs=row[2:5];assert all(type(r) is int and 0<=r<index for r in refs)
   value=[tag,'<binder-name>',*[hashes[r] for r in refs],row[5]];changed+=1
  elif tag=='proj':
   assert len(row)==4 and type(row[3]) is int and 0<=row[3]<index
   value=[tag,row[1],row[2],hashes[row[3]]]
  else:
   assert tag in {'const','sort','bvar','lit'},tag
   value=row
  hashes.append(hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest())
 return hashes[graph['root']],changed
cases=[]
for n in [1,2,3]:
 j=json.loads((b/f'probe-five-{n}-result.json').read_text())
 capture=j.get('capture',{}).get('capture',{}).get('goal',{}).get('typeStructural')
 typed=j.get('typedSubject',{}).get('subject',{}).get('structural')
 c=j.get('completion',{})
 cases.append({'attempt':n,'outerStatus':j.get('status'),'completionStatus':c.get('status'),
  'completionDiagnostic':c.get('diagnostic'),'kernelReplay':c.get('replay',{}).get('status'),
  'completeTrust':c.get('trust',{}).get('accepted'),'rawSubjectsEqual':capture==typed,
  'diagnosticOnlyAlphaFingerprintsEqual':fingerprint(capture)[0]==fingerprint(typed)[0] if capture and typed else None})
(b/'SUBJECT-DIAGNOSTIC.json').write_text(json.dumps({'productionAcceptanceUnchanged':True,'cases':cases},indent=2)+'\n')
print(cases)
