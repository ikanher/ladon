"""Public generic live matrix; every connection repeats actual fresh checks."""
import copy
import json
import os
import tempfile
import sys
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0,str(Path('tests').resolve()))
from real_prose_connection_live_helpers import interpretation
from ladon.proof_contract_cli import contract_main
from ladon.proof_slice import pinned_toolchain
from ladon.real_prose_native_production import produce_real_prose_bound

if os.environ.get('LADON_MATRIX_SCRATCH'):
    tempfile.tempdir = os.environ['LADON_MATRIX_SCRATCH']

base = Path(__file__).resolve().parent
q = base/'qualified-set'
root = Path((q/'ROOT.txt').read_text().strip())
out = base/'public-matrix'
out.mkdir(exist_ok=True)
context = {'schema':'ladon-prose-bound-context-v1','file':'Context.lean','module':'Context','scope':'file-end'}


def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,ensure_ascii=False)


def reading(label,source_root,*,global_scope=False,change=None):
    value = interpretation(source_root,global_scope=global_scope)
    value['id'] = 'generic:'+label
    if change is not None:change(value)
    authored = produce_real_prose_bound(source_root,value,context,
        alternative_id='generic:'+label,author='public-acceptance',timeout_seconds=120)
    path = out/(label+'-authored.json')
    save(path,authored)
    assert authored['status'] == 'authored',{'label':label,'status':authored['status']}
    return path


def cli(label,args,expected):
    output = out/(label+'-connection.json')
    started = time.monotonic()
    buffer = StringIO()
    with redirect_stdout(buffer):
        code = contract_main([*args,'--output',str(output)])
    result = json.loads(output.read_text() if output.exists() else buffer.getvalue())
    row = {'case':label,'exitCode':code,'status':result.get('status'),'seconds':time.monotonic()-started}
    check = result.get('check') or {}
    receipt = check.get('processReceipt') or {}
    row.update({'peakRssBytes':receipt.get('peak_rss_bytes'),'diagnostic':check.get('diagnostic')})
    with (out/'RESULTS.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
    assert result['status'] == expected,row
    assert code == (0 if expected == 'connected' else 2),row
    assert result['admission'] == 'unresolved' and result['sourceTheoremProof'] == 'not-checked'
    return result


def connect(label,authored,source_root,term,expected,premises=None):
    path = out/(label+'-request.json')
    save(path,{'schema':'ladon-real-prose-connection-request-v1','term':term,'premises':premises or []})
    return cli(label,['connect-real-prose-bound','--formal',str(q/'FORMAL.json'),
        '--authored',str(authored),'--formal-root',str(root),'--prose-root',str(source_root),
        '--request',str(path),'--timeout-seconds','300'],expected)


def clone(extra):
    target = out/('extended-prose-'+mode)
    target.mkdir()
    (target/'lean-toolchain').write_bytes((root/'lean-toolchain').read_bytes())
    (target/'.lake/build/lib/lean').mkdir(parents=True)
    for i,library in enumerate(pinned_toolchain(root).library_roots):
        destination = target/f'.lake/packages/import{i}/.lake/build/lib/lean'
        destination.parent.mkdir(parents=True)
        destination.symlink_to(library,target_is_directory=True)
    (target/'Context.lean').write_text((root/'Context.lean').read_text()+extra)
    (target/'claim.txt').write_bytes((root/'claim.txt').read_bytes())
    return target


def change_carrier(value):
    value['symbols']['J'] = {'leanName':'ConnectionIntBound','leanType':'Int → Set Nat → Nat → Real → Prop'}
    value['symbols']['A'] = {'leanName':'ConnectionIntScale','leanType':'Int → Int'}
    value['formula']['body']['body']['items'][1]['binder']['domain'] = 'Int'


def change_set(value):
    value['symbols']['J'] = {'leanName':'ConnectionBoolBound','leanType':'Real → Set Bool → Nat → Real → Prop'}
    value['formula']['body']['body']['items'][1]['body']['binder']['domain'] = 'Set Bool'


def uniform_constant(value):
    original = value['formula']
    k = original['body']
    guard,body = k['body']['items']
    k['body']['items'] = [guard,{**original,'body':body}]
    value['formula'] = k


mode = sys.argv[1]
if mode == 'global-replay':
    authored = reading('global',root,global_scope=True)
    term = '''by
  intro original n
  obtain ⟨K,hK,h⟩ := original n
  refine ⟨K,hK,?_⟩
  intro f C hC hb
  exact h f Set.univ C hC hb'''
    connect('global',authored,root,term,'connected')
    cli('set-replay',['replay-real-prose-connection','--input',str(q/'CONNECTION.json'),
        '--formal',str(q/'FORMAL.json'),'--authored',str(q/'AUTHORED.json'),
        '--formal-root',str(root),'--prose-root',str(root),'--timeout-seconds','300'],'connected')
elif mode in {'typed-negative','conditional-constant'}:
    target = clone('''\ndef ConnectionIntBound (f : Int) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, (f : Real) ≤ C
 def ConnectionIntScale (f : Int) := 2*f
 def ConnectionBoolBound (f : Real) (S : Set Bool) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, f ≤ C
 def ConnectionAssumption : Prop := True
def ConnectionBadOperator (f : Real) := f+1
theorem ConnectionReverseWitness :
    (∀ n : Nat, ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
      TransferExamples.bound f S (ConnectionShift n) C →
      TransferExamples.bound (ConnectionBadOperator f) S n (ConnectionProduct K C)) →
    (∀ n : Nat, ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
      TransferExamples.bound f S (n+4) C →
      TransferExamples.bound (TransferExamples.twice f) S n (K*C)) := by
  intro _
  exact TransferExamples.first
''')
    for label,change in ([('wrong-carrier',change_carrier),('wrong-set',change_set)] if mode == 'typed-negative' else []):
        authored = reading(label,target,change=change)
        connect(label,authored,target,'by intro original; exact original','unresolved')
    if mode == 'conditional-constant':
        authored = reading('conditional',target)
        connect('conditional',authored,target,'by intro original assumption; exact original','connected',
                premises=['ConnectionAssumption'])
        authored = reading('uniform-constant',root,change=uniform_constant)
        connect('uniform-constant',authored,root,'by intro original; exact original','unresolved')
        def reverse_operator(value):
            value['symbols']['A'] = {'leanName':'ConnectionBadOperator','leanType':'Real → Real'}
        authored = reading('reverse-direction',target,change=reverse_operator)
        connect('reverse-direction',authored,target,'ConnectionReverseWitness','unresolved')
else:
    raise ValueError('unknown matrix mode')
