from pathlib import Path
import tempfile,shutil,json,subprocess,os,time,hashlib
out=Path('/home/codex/projects/ladon/openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/synthetic-launch-r01');script=out/'CHECK.py';env=dict(os.environ,PYTHONPATH='/home/codex/projects/ladon/src');python='/home/codex/projects/ladon/.venv/bin/python';checks={}
with tempfile.TemporaryDirectory(prefix='ladon-launch-probe-') as tmp:
 p=Path(tmp);shutil.copyfile(script,p/'CHECK.py');(p/'project').mkdir();(p/'outputs').mkdir();(p/'LAUNCH.json').write_text(json.dumps({'ladonSourceRoot':'/home/codex/projects/ladon/src','toolchainBin':'/usr/bin','pythonExecutable':str(Path(python).resolve())}))
 def run(*args):return subprocess.run([python,str(p/'CHECK.py'),*args],env=env,capture_output=True,text=True)
 checks['unactivatedRefused']=run('--','/bin/true').returncode!=0
 checks['activationAccepted']=run('--activate').returncode==0
 checks['reactivationRefused']=run('--activate').returncode!=0
 (p/'outputs/ACTIVE').touch();checks['parallelRefused']=run('--','/bin/true').returncode!=0;(p/'outputs/ACTIVE').unlink()
 checks['failedCommandRecorded']=run('--','/bin/false').returncode==1 and (p/'outputs/command-01.result.json').exists()
 for _ in range(19):assert run('--','/bin/true').returncode==0
 checks['command21Refused']=run('--','/bin/true').returncode!=0 and len(list((p/'outputs').glob('command-*.request.json')))==20
 s=p/'outputs/SESSION.json';d=json.loads(s.read_text());d['deadlineUnix']=time.time()-1;s.write_text(json.dumps(d));checks['expiredRefused']=run('--','/bin/true').returncode!=0
 shutil.rmtree(p/'outputs');(p/'outputs').mkdir();assert run('--activate').returncode==0
 d=json.loads(s.read_text());d['deadlineUnix']=time.time()+0.4;s.write_text(json.dumps(d));r=run('--','/bin/sleep','3');rec=json.loads((p/'outputs/command-01.result.json').read_text());checks['remainingDeadlineTerminatesChild']=r.returncode==1 and rec['timed_out']
 (p/'outputs/command-02.request.json').write_text('{}');checks['incompleteReceiptRefused']=run('--','/bin/true').returncode!=0
 # New activation for the incomplete-receipt check, since expired-session refusal is distinct.
 d['deadlineUnix']=time.time()+30;s.write_text(json.dumps(d));checks['incompleteReceiptRefused']=run('--','/bin/true').returncode!=0 and not (p/'outputs/command-03.request.json').exists()
assert all(checks.values()),checks
(out/'RUNNER-PROBES.json').write_text(json.dumps({'checks':checks,'runnerSha256':hashlib.sha256(script.read_bytes()).hexdigest(),'scope':'Synthetic /bin commands only; no case prose, Lean attempts or auditors','enforcement':'Procedural top-level command budget; existing supervisor enforces process resource caps.'},indent=2)+'\n');print(checks)
