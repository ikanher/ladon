import mpmath as m
m.mp.dps=80
T=100; q=m.mpf('0.0025'); eps=m.mpf(1)
Phi=lambda x: m.erfc(-x/m.sqrt(2))/2

def values(sigma,a,xi):
 mu=1/m.mpf(sigma); a=m.mpf(a); alpha=m.exp(xi)
 pQ=Phi(a)**T; pP=((1-q)*Phi(a)+q*Phi(a-mu))**T
 m2=((1-q)**2*Phi(a)+2*q*(1-q)*Phi(a-mu)+q*q*m.exp(mu*mu)*Phi(a-2*mu))**T
 v=m2-2*alpha*pP+alpha*alpha*pQ
 residual=(m.sqrt(pQ*v)+pP-alpha*pQ)/2
 return max(0,1-pP-alpha*(1-pQ)),1-pP+min(pP,residual)
lower=values('0.268600','3.669486',eps)[0]
forward=values('0.286000','4.020051',eps)[1]
reverse_dual=max(0,1-m.exp(eps)+m.exp(eps)*values('0.286000','3.454911',-eps)[1])
reverse_floor=max(0,1-m.exp(eps)*(1-q)**T)
for n,v in [('lower',lower),('forward',forward),('reverse_dual',reverse_dual),('reverse_floor',reverse_floor),('reverse_best',min(reverse_dual,reverse_floor)),('relative_width_percent',100*(m.mpf('0.286000')-m.mpf('0.268600'))/m.mpf('0.2692892144'))]:print(n, m.nstr(v,60))
print('Diagnostic arithmetic only; no outward rational enclosure or PLD replay.')
