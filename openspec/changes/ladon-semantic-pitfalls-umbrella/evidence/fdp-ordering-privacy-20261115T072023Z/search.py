from itertools import product
from fractions import Fraction
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linprog
N=4
pairs=list(product(range(N), repeat=2)); index={v:i for i,v in enumerate(pairs)}
A=[]; b=[]
for x in pairs:
 for y in pairs:
  if sum(a!=bb for a,bb in zip(x,y))!=1:continue
  row=np.zeros(N*N);row[index[x]]=1;row[index[y]]=-2
  A.append(row);b.append(0)
  A.append(-row);b.append(1)
c=np.zeros(N*N)
for x in [(0,1),(0,2),(1,2)]:c[index[x]]+=1/3
for x in [(3,1),(3,2),(1,2)]:c[index[x]]-=5/9
r=linprog(-c,A_ub=A,b_ub=b,bounds=(0,1),method='highs')
record=dict(success=bool(r.success),message=r.message)
if r.success:
 vals=[Fraction(float(x)).limit_denominator(1000000) for x in r.x]
 def q(v):return vals[index[v]]
 violations=[]
 for x in pairs:
  for y in pairs:
   if sum(a!=bb for a,bb in zip(x,y))==1:
    if q(x)>2*q(y) or 1-q(x)>2*(1-q(y)):violations.append([x,y])
 P=sum(map(q,[(0,1),(0,2),(1,2)]))/3
 Q=sum(map(q,[(3,1),(3,2),(1,2)]))/3
 record.update(values=[[str(q((a,bb))) for bb in range(N)] for a in range(N)],exactPrivacyViolations=violations,normalized=all(0<=v<=1 for v in vals),P=str(P),Q=str(Q),gap=str(P-Fraction(5,3)*Q),floatingObjective=float(-r.fun))
Path(__file__).with_name('search-result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
