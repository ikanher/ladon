from pathlib import Path
import re, json
import mpmath as m
b=Path('/home/codex/projects/ladon/openspec/changes/ladon-matched-source-audit-pilot/evidence/run-20261113-r01/adjudication/reviewer-1/INPUT/capsule')
k=(b/'sources/latex/natural-language/deterministic_koutoft_training_accountant_proof.tex').read_text()
paths=sorted(set(re.findall(r'\\decl\{(Mf/[^}]+\.lean)\}',k)))
files=list((b/'lean/Mf').rglob('*.lean'))
text='\n'.join(f.read_text() for f in files)
names=['checkKOutOfTCandidate_sound','RequestOnlyUpperCalibration.trainingAccountant_sound','kOutOfTTrainingTranscript_approxDP_of_formal','formalApproxDP_of_saturatingTrainingApproxDP','signedHiddenGaussianStopLossDomination','kOutOfTTrainingTranscript_replaceOne_approxDP_of_directFormal','sampledGaussian_calibration_interval_of_finiteBracket_replayCertificate']
print(json.dumps({'local_lean_source_count':len(files),'K_cited_lean_path_count':len(paths),'K_cited_present':[p for p in paths if (b/'lean'/p).exists()],'K_cited_missing':[p for p in paths if not (b/'lean'/p).exists()],'local_source_substring_matches':{n:[str(f.relative_to(b/'lean')) for f in files if n in f.read_text()] for n in names}},indent=2))
m.mp.dps=60
q=m.mpf('0.0025'); T=100; e=m.mpf(1)
Phi=lambda x:(1+m.erf(x/m.sqrt(2)))/2
pos=lambda x:max(x,m.mpf(0))
def values(s,a,xi):
 u=1/m.mpf(s); a=m.mpf(a)
 p=((1-q)*Phi(a)+q*Phi(a-u))**T; r=Phi(a)**T
 z=((1-q)**2*Phi(a)+2*q*(1-q)*Phi(a-u)+q*q*m.exp(u*u)*Phi(a-2*u))**T
 v=z-2*m.exp(xi)*p+m.exp(2*xi)*r
 residual=(m.sqrt(r*v)+p-m.exp(xi)*r)/2
 return pos(1-p-m.exp(xi)*(1-r)),1-p+min(p,residual)
L,_=values('0.268600','3.669486',e)
_,UF=values('0.286000','4.020051',e)
_,UFminus=values('0.286000','3.454911',-e)
print('L =',m.nstr(L,55)); print('UF =',m.nstr(UF,55))
print('reverse dual =',m.nstr(pos(1-m.exp(e)+m.exp(e)*UFminus),55))
print('reverse floor =',m.nstr(pos(1-m.exp(e)*(1-q)**T),55))
print('relative width percent =',m.nstr(100*(m.mpf('0.286000')-m.mpf('0.268600'))/m.mpf('0.2692892144'),55))
