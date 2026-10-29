import hashlib,json
from pathlib import Path
from ladon.real_prose_native_codec import encode_history,decode_history
from ladon.real_prose_native_payload import recognition_history
f=json.loads(Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json').read_text())
a=json.loads(Path('.codex/state/real-prose-native/live/navier-produced.json').read_text())
nodes=[];seen={}
def intern(value):
 if isinstance(value,dict):
  keys=sorted(value);row=['object',keys,[intern(value[k]) for k in keys]]
 elif isinstance(value,list):row=['array',[intern(x) for x in value]]
 else:row=['scalar',value]
 key=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
 if key not in seen:seen[key]=len(nodes);nodes.append(row)
 return seen[key]
def expand(index):
 row=nodes[index]
 if row[0]=='object':return {k:expand(v) for k,v in zip(row[1],row[2],strict=True)}
 if row[0]=='array':return [expand(v) for v in row[1]]
 return row[1]
raw_pair={'authored':json.loads(json.dumps(a)),'formal':f}
a['check']['result']['artifacts'][-1]['payload']['recognition']=decode_history(a['check']['result']['artifacts'][-1]['payload']['recognition'])
pair={'authored':a,'formal':f}
root=intern(pair)
assert expand(root)==pair
restored=expand(root)
p=restored['authored']['check']['result']['artifacts'][-1]['payload']
p['recognition']=encode_history(p['recognition'])
assert restored==raw_pair
graph={'schema':'probe-json-dag-v1','root':root,'nodes':nodes}
encoded=encode_history(graph)
assert decode_history(encoded)==graph
result={'rawPairBytes':len(json.dumps(raw_pair,separators=(',',':'),ensure_ascii=False).encode()),
 'graphBytes':len(json.dumps(graph,separators=(',',':'),ensure_ascii=False).encode()),
 'encodedGraphBytes':len(json.dumps(encoded,separators=(',',':'),ensure_ascii=False).encode()),'nodes':len(nodes),
 'roundtripExact':True,'productionActivated':False}
Path('.codex/state/real-prose-connection/GRAPH-FEASIBILITY.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
