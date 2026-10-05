import hashlib,json,os,platform,subprocess
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/candidate');wheel=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/dist/ladon-0.2.0-py3-none-any.whl')
def digest(data):return 'sha256:'+hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');return digest(path.read_bytes())
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=candidate).decode().strip()
files=subprocess.check_output(['git','ls-files','-z'],cwd=candidate).decode().split('\0')
manifest={'candidateCommit':commit,'files':{p:digest((candidate/p).read_bytes()) for p in files if p}}
source=save(root/'source-manifest-r46.json',manifest)
producer=digest((candidate/'scripts/run_child_acceptance.py').read_bytes())
leanroot=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin')
tool={'pin':(candidate/'tests/fixtures/lean_integration/lean-toolchain').read_text().strip(),'executables':{name:{'path':str(leanroot/name),'digest':digest((leanroot/name).read_bytes())} for name in ('lean','lake')},'compiledFixture':{'path':str(candidate/'tests/fixtures/lean_integration/.lake/build/lib/lean/LadonFixture.olean'),'digest':digest((candidate/'tests/fixtures/lean_integration/.lake/build/lib/lean/LadonFixture.olean').read_bytes())}}
environment={'schema':'ladon-acceptance-environment-v1','platform':platform.platform(),'hostNetworkNamespace':os.readlink('/proc/self/ns/net'),'networkHarnessParentIdentityEnvironment':'LADON_ACCEPTANCE_HOST_NETWORK_NAMESPACE','networkHarness':['bwrap','--unshare-net','--bind','/','/','--proc','/proc','--dev','/dev'],'posture':'trusted-repository-only','procAvailable':Path('/proc/self/status').is_file(),'pythonOverrides':'PYTHONPATH, PYTHONHOME and PYTEST_ADDOPTS unset','pytestAutoload':'disabled','leanFixture':tool,'runtimes':{r:{'python':str(Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s')/r/'bin/python'),'console':str(Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s')/r/'bin/ladon'),'consoleDigest':digest((Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s')/r/'bin/ladon').read_bytes())} for r in ('py311','py312')}}
envref=save(root/'environment-r46.json',environment)
wdigest=digest(wheel.read_bytes());cobj={'candidateCommit':commit,'sourceTreeIdentity':source,'wheelDigest':wdigest}
identity=digest(json.dumps(cobj,sort_keys=True,separators=(',',':')).encode())
save(root/'candidate-identity-r46.json',cobj)
context={'hostNetworkNamespace':os.readlink('/proc/self/ns/net'),'candidateIdentity':identity,'sourceTreeIdentity':source,'wheelDigest':wdigest,'workingDirectory':str(candidate),'producerIdentity':producer,'environmentRef':envref,'sourceManifestPath':str(root/'source-manifest-r46.json')}
save(root/'context-r46.json',context)
print(json.dumps({'commit':commit,'wheelDigest':wdigest,'sourceTreeIdentity':source,'producerIdentity':producer,'trackedFiles':len(manifest['files'])}))
