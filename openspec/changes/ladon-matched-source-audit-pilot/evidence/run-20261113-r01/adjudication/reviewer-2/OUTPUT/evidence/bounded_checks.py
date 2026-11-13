import hashlib, json, math, re
from pathlib import Path
root = Path(__file__).resolve().parents[2]
inputs = root / 'INPUT'
lean = inputs / 'capsule/lean'
source = inputs / 'capsule/sources/latex/natural-language'
files = sorted(lean.rglob('*.lean'))
texts = {p.relative_to(lean).as_posix():p.read_text() for p in files}
print('Method: bounded static source inspection and diagnostic double-precision arithmetic; no Lean execution, network, outside-source inspection, or theorem falsity inference.')
print('Lean source count:', len(files))
for name in ['deterministic_koutoft_training_accountant_proof.tex','poisson_fixed_participation_finite_bracket_proof.tex']:
    data=(source/name).read_bytes()
    print('Source:', name, 'sha256:', hashlib.sha256(data).hexdigest())
claims=json.loads((inputs/'SCORE-POPULATION.json').read_text())['selected_claims']
for i,c in enumerate(claims,1):
    short=c['declaration'].split('.')[-1]
    lines=texts[c['lean_path']].splitlines()
    hits=[j for j,line in enumerate(lines,1) if re.match(r'(?:def|abbrev|theorem)\s+'+re.escape(short)+r'\b',line)]
    print('Selected declaration',i,c['declaration'],c['lean_path'],hits)
training=(source/'deterministic_koutoft_training_accountant_proof.tex').read_text()
paths=sorted(set(re.findall(r'\\decl\{([^{}]+\.lean)\}',training)))
print('Training note distinct cited Lean paths:',len(paths))
print('Present cited paths:',[p for p in paths if p in texts])
print('Missing cited paths:',[p for p in paths if p not in texts])
missing=['checkKOutOfTCandidate_sound','kOutOfTTrainingTranscript_approxDP_of_formal','formalApproxDP_of_saturatingTrainingApproxDP','signedHiddenGaussianStopLossDomination','kOutOfTTrainingTranscript_replaceOne_approxDP_of_directFormal','sampledGaussian_calibration_interval_of_finiteBracket_replayCertificate']
for symbol in missing:
    hits=[]
    for path,txt in texts.items():
        for i,line in enumerate(txt.splitlines(),1):
            if re.match(r'(?:def|abbrev|theorem|lemma)\s+'+re.escape(symbol)+r'\b',line):
                hits.append([path,i])
    print('Local declaration inventory:',symbol,hits)
T,q,eps=100,0.0025,1.0
cdf=lambda x: 0.5*math.erfc(-x/math.sqrt(2))
def masses(sigma,a):
    mu=1/sigma
    p=((1-q)*cdf(a)+q*cdf(a-mu))**T
    r=cdf(a)**T
    m=((1-q)**2*cdf(a)+2*q*(1-q)*cdf(a-mu)+q*q*math.exp(mu*mu)*cdf(a-2*mu))**T
    return p,r,m
def forward(sigma,a,xi):
    p,r,m=masses(sigma,a)
    v=m-2*math.exp(xi)*p+math.exp(2*xi)*r
    residual=(math.sqrt(max(0,r*v))+p-math.exp(xi)*r)/2
    return 1-p+min(p,residual)
p,r,_=masses(0.268600,3.669486)
print('Diagnostic lower:',max(0,1-p-math.exp(eps)*(1-r)))
print('Diagnostic forward upper:',forward(0.286000,4.020051,eps))
print('Diagnostic reverse dual:',max(0,1-math.exp(eps)+math.exp(eps)*forward(0.286000,3.454911,-eps)))
print('Diagnostic reverse floor:',max(0,1-math.exp(eps)*(1-q)**T))
print('Diagnostic relative width percent:',100*(0.286000-0.268600)/0.2692892144)
print('Numeric check is approximate only; no PLD validation or rational enclosure certification.')
