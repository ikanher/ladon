from pathlib import Path
import importlib.util
import json
import sys
root=Path('/home/codex/projects/ladon')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module
old=load('supplemental_old',root/'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/source-path-r51/reproduce/baseline-lean_toolchain.py')
new=load('supplemental_new',root/'src/ladon/lean_toolchain.py')
def result(fn,value):
    try: return ('accepted',fn(value))
    except Exception as error: return ('rejected',type(error).__name__,str(error))
paths=['src/'+chr(0)+'.lean',chr(0),'//src/A.lean','///src/A.lean','/'.join(['x']*64),'./'+'/'.join(['x']*65)]
for path in paths:
    assert result(old._validate_source_relative_path,path)==result(new._validate_source_relative_path,path)
    assert result(old._filter_source_material,(path,))==result(new._filter_source_material,(path,))
print(json.dumps({'pathCases':len(paths),'comparisons':len(paths)*2,'status':'identical','scope':'actual NUL, POSIX leading slashes and depth limits; preserves legacy behavior'}))
