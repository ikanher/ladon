import importlib.util, sys, itertools, hashlib, json
sys.path.insert(0, '/home/codex/projects/ladon/src')

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
old=load('baseline_lean_toolchain','/home/codex/projects/ladon/openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/source-path-r51/reproduce/baseline-lean_toolchain.py')
new=load('current_lean_toolchain','/home/codex/projects/ladon/src/ladon/lean_toolchain.py')
parts=['','.', '..','src','tests','scripts','docs','a','雪','é','x'*4096,'x'*4097,'name.lean','helper.lean','lakefile.toml','\x00','~','//server','\\server','C:\\root','./','...']
probes=set(parts)
for n in (2,3,4):
 for xs in itertools.product(parts[:10]+parts[12:18], repeat=n):
  probes.add('/'.join(xs))
  if len(probes)>100000: break
for sep in ('//','///','\\'):
 for p in parts: probes.add(sep+p)

def result(fn,x):
 try: return ('ok',fn(x))
 except BaseException as e: return ('err',type(e).__name__,str(e))
count=0
for x in probes:
 a=result(old._validate_source_relative_path,x); b=result(new._validate_source_relative_path,x)
 if a!=b: print('MISMATCH',repr(x),a,b); raise SystemExit(1)
 count+=1
# Validate public filter equivalence on combinations, including failures before classification.
sets=[tuple(x) for x in itertools.product(['.','../bad.txt','notes/../readme.txt','src//A.lean','./src/A.lean','docs/readme.md','src/../x','vendor/nested/lakefile.toml'], repeat=2)]
for xs in sets:
 a=result(old._filter_source_material,xs); b=result(new._filter_source_material,xs)
 if a!=b: print('FILTER MISMATCH',xs,a,b); raise SystemExit(1)
print(json.dumps({'validator_cases':count,'filter_cases':len(sets),'result':'identical'}))
