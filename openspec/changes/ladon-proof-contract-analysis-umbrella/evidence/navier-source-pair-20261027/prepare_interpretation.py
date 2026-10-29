import hashlib,json
from pathlib import Path
from ladon.correspondence_interpretation import lower_formula
from ladon.proof_slice import pinned_toolchain
b=Path('.codex/state/navier-pair-integration').resolve();root=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
project=b/'project';project.mkdir(exist_ok=False);(project/'lean-toolchain').write_bytes((root/'lean-toolchain').read_bytes())
(project/'.lake/build/lib/lean').mkdir(parents=True)
for i,lib in enumerate(pinned_toolchain(root).library_roots):
 target=project/f'.lake/packages/import{i}/.lake/build/lib/lean';target.parent.mkdir(parents=True);target.symlink_to(lib,target_is_directory=True)
bridge=(b/'ParameterFreeBridge.lean').read_text().replace('import NavierStokes.SmoothFamilyTorusInverse\n','')
prefix=(root/'NavierStokes/SmoothFamilyTorusInverse.lean').read_text()+'\n'+bridge
vocab='''
namespace LadonSourcePair
abbrev PlaneFunction := NavierStokes.TorusInverse.Plane → ℂ
def Smooth (F : PlaneFunction) : Prop := ContDiff ℝ ∞ F
def IsPeriodic (F : PlaneFunction) : Prop := NavierStokes.SmoothFourierData.UnitPeriodic F
def MeanZero (F : PlaneFunction) : Prop := NavierStokes.SmoothFourierData.coefficient F 0 = 0
noncomputable def TemporalInverse (F : PlaneFunction) : PlaneFunction := planeInverse .temporal F
def shiftFour (n : Nat) : Nat := n + 4
def shiftFive (n : Nat) : Nat := n + 5
def realProduct (a b : Real) : Real := a * b
end LadonSourcePair
'''
prefix+=vocab
source=b/'prose-input/pages-95-96.txt';lines=source.read_text().splitlines();start=next(i for i,t in enumerate(lines,1) if t.startswith('Lemma 8.6.'));end=next(i for i,t in enumerate(lines[start:],start+1) if t.startswith('For a pair'))-1
span={'path':str(source.relative_to(Path.cwd())),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'startLine':start,'endLine':end,'quote':'\n'.join(lines[start-1:end])}
def var(n):return {'tag':'var','id':n}
def const(n):return {'tag':'const','name':n}
def app(n,*args):return {'tag':'app','symbol':n,'args':list(args)}
def q(tag,n,domain,body):return {'tag':tag,'binder':{'id':n,'name':n,'domain':domain},'body':body}
def imp(p,c):return {'tag':'implies','premise':p,'conclusion':c}
def nonneg(n):return {'tag':'le','left':const('0'),'right':var(n)}
symbols={n:{'leanName':'LadonSourcePair.'+name,'leanType':typ} for n,name,typ in [('bound','TorusJetBound','LadonSourcePair.PlaneFunction → Nat → Real → Prop'),('inverse','TemporalInverse','LadonSourcePair.PlaneFunction → LadonSourcePair.PlaneFunction'),('shift','shiftFour','Nat → Nat'),('multiply','realProduct','Real → Real → Real'),('smooth','Smooth','LadonSourcePair.PlaneFunction → Prop'),('periodic','IsPeriodic','LadonSourcePair.PlaneFunction → Prop'),('meanZero','MeanZero','LadonSourcePair.PlaneFunction → Prop')]}
conclusion=app('bound',app('inverse',var('F')),var('n'),app('multiply',var('K'),var('C')))
for premise in reversed([app('smooth',var('F')),app('periodic',var('F')),app('meanZero',var('F')),nonneg('C'),app('bound',var('F'),app('shift',var('n')),var('C'))]):conclusion=imp(premise,conclusion)
formula=q('forall','n','Nat',q('exists','K','Real',{'tag':'and','items':[nonneg('K'),q('forall','F','LadonSourcePair.PlaneFunction',q('forall','C','Real',conclusion))]}))
record={'id':'reading:navier-8.19-full-frechet-convention','source':span,'formula':formula,'symbols':symbols}
(b/'interpretation-record.json').write_text(json.dumps(record,indent=2)+'\n')
lowered=lower_formula(formula,symbols);(b/'interpretation-lowered.txt').write_text(lowered+'\n')
# Source-bound type definition, no axiom or proof of four-order claim.
(project/'PaperVocabulary.lean').write_text(prefix+'\nnamespace LadonSourcePair\ndef FourOrderReading : Prop := '+lowered+'\nend LadonSourcePair\n')
# Same scoped reading with only the derivative shift changed for the faithful control.
five=lowered.replace('LadonSourcePair.shiftFour','LadonSourcePair.shiftFive')
term='''by
  intro n
  obtain ⟨K, hK, h⟩ := LadonSourcePair.plane_inverse_five .temporal n
  refine ⟨K, hK, ?_⟩
  intro F C hf hp _hmean hC hb
  exact h F C hf hp hC hb'''
(b/'five-term.txt').write_text(term+'\n')
for name,prop in [('FiveOrderControl',five),('FourOrderProbe',lowered)]:
 text=prefix+'\nexample : '+prop+' := by\n  skip\n';(project/(name+'.lean')).write_text(text)
(b/'goal-positions.json').write_text(json.dumps({name:len((project/(name+'.lean')).read_text().splitlines()) for name in ['FiveOrderControl','FourOrderProbe']},indent=2)+'\n')
(b/'PROSE-FREEZE.json').write_text(json.dumps({'sourceOnlyReports':{str(p.relative_to(b)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [b/'navier_prose_46/source-reading.md',b/'navier_prose_47/source-audit.md']},'phase':'source readings frozen before new formal mapping; root already answer-informed','convention':'full real Frechet derivative prefix on universal cover; coordinate norm equivalence not Lean checked','selectedComponent':'estimate only; original solvability assertions retained separately','interpretationSha256':hashlib.sha256((b/'interpretation-record.json').read_bytes()).hexdigest()},indent=2)+'\n')
print('Created original-source-copy project and four-order typed reading; no claim proof added.')
