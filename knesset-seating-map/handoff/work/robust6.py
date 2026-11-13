import numpy as np, json, sys
from scipy.optimize import least_squares
from model4 import *
from model4 import _seg
from joint6 import Joint, init, load_obs, NM
PH=['U1','U3','A','U2','P1']; q0,cams=init(); obs=load_obs()
v6=np.load('fit6_v.npy'); J=Joint(PH,cams); q6,c6=J.unpack(v6); cams6={p:c6[p] for p in PH}
def plan(q): return {(el,i):_seg(el,i,q)[0] for el,n in COUNTS.items() for i in range(n)}
P6=plan(q6)
def moved(q):
    P=plan(q); d=np.array([np.linalg.norm(P[k]-P6[k]) for k in P6]); return np.median(d),np.max(d)
v5=np.load('fit5_v.npy'); q5=dict(zip(NM,v5[:len(NM)]))
print('map change from adding photo 1 (vs 4-photo map): median %.3f, max %.3f seat widths'%moved(q5))
tests={
 'drop photo 1 entirely':(lambda o:o['photo']=='P1', ['U1','U3','A','U2']),
 'drop the 2023 back-corner photo entirely':(lambda o:o['photo']=='A', ['U1','U3','U2','P1']),
 'drop the 2026 side photo entirely':(lambda o:o['photo']=='U3', ['U1','A','U2','P1']),
 'drop the dais photo entirely':(lambda o:o['photo']=='U1', ['U3','A','U2','P1']),
 'drop the 2025 side photo entirely':(lambda o:o['photo']=='U2', ['U1','U3','A','P1']),
 'hide back rows in both back-corner photos':(lambda o:o['photo'] in ('A','P1') and o['el'][0]=='B', PH),
 'hide government table everywhere except the dais photo':(lambda o:o['el'][0]=='G' and o['photo']!='U1', PH),
}
for name,(f,ph) in tests.items():
    tr=[o for o in obs if not f(o)]; te=[o for o in obs if f(o)]
    Jt=Joint(ph,cams6); vt=Jt.fit(Jt.pack(np.array([q6[n] for n in NM]),cams6),tr,nfev=12000)
    qt,_=Jt.unpack(vt); md,mx=moved(qt)
    msg=f'{name:58s} map moves median {md:.3f}, max {mx:.3f} seat widths'
    if set(o['photo'] for o in te)<=set(ph):
        e=np.linalg.norm(Jt.resid(vt,te).reshape(-1,2),axis=1); msg+=f' | hidden seats predicted to {np.median(e):.1f} px (median)'
    print(msg,flush=True)
