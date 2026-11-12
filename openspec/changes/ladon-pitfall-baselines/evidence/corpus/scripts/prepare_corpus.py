"""Compile this development corpus and retain exact commands and preparation evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    output=ROOT/'reviews/r3-preparation.json'
    report={'schema':'ladon-corpus-preparation-v1','commands':[],'inputs':{},'artifacts':[],'status':'running'}
    def run(args,cwd):
        r=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=600)
        report['commands'].append({'args':[str(a) for a in args],'cwd':str(cwd),'exitStatus':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode or 'sorryAx' in r.stdout+r.stderr:
            raise RuntimeError(f'preparation failed: {args}')
    paths=[ROOT/'cases.json',ROOT/'INPUTS.md']
    for folder in ['lean','mathlib']:
        project=ROOT/folder
        paths += [p for p in project.rglob('*.lean') if '.lake' not in p.parts]
        paths += [project/n for n in ['lean-toolchain','lakefile.toml','lake-manifest.json']]
    paths+=list((ROOT/'scripts').glob('*.py'))
    report['inputs']={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(paths))}
    try:
        for folder,subdir in [('lean','CoreCases'),('mathlib','ExistenceCases')]:
            project=ROOT/folder
            run(['lake','build'],project)
            run(['lake','env','lean','--version'],project)
            for case in sorted((project/subdir).glob('*.lean')):
                rel=case.relative_to(project); dest=Path('.lake/build/lib/lean')/rel.with_suffix('.olean')
                (project/dest).parent.mkdir(parents=True,exist_ok=True)
                run(['lake','env','lean','-o',str(dest),str(rel)],project)
            run(['lake','env','lean','Validation.lean'],project)
            for case in [project/('Pitfalls.lean' if folder=='lean' else 'LeastElement.lean'),*sorted((project/subdir).glob('*.lean'))]:
                compiled=project/'.lake/build/lib/lean'/case.relative_to(project).with_suffix('.olean')
                report['artifacts'].append({'source':str(case.relative_to(ROOT)),'sourceSha256':digest(case),'artifact':str(compiled.relative_to(ROOT)),'artifactSha256':digest(compiled)})
        run([sys.executable,str(ROOT/'scripts/check_corpus.py')],ROOT)
        run([sys.executable,str(ROOT/'scripts/check_isolation.py')],ROOT)
        assert all(digest(ROOT/p)==h for p,h in report['inputs'].items()),'inputs drifted during preparation'
        report['status']='passed'
    except Exception as exc:
        report['status']='failed'; report['error']=str(exc)
        raise
    finally:
        output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"PASS: {len(report['inputs'])} input hashes, {len(report['artifacts'])} compiled artifacts, {len(report['commands'])} commands; {output}")

if __name__=='__main__': main()
