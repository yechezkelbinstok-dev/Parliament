import numpy as np, json
from scipy.optimize import least_squares
from model3 import *
OBS=json.load(open('obs.json')); PH=['U1','U3']
NM=[s[0] for s in SPEC]; lo=np.array([s[2] for s in SPEC]); hi=np.array([s[3] for s in SPEC])
camlo=np.array([-10,-10,-10,-200,-200,-200,500,-0.5]); camhi=-camlo; camhi[6]=6000
L=np.concatenate([lo]+[camlo]*2); Hh=np.concatenate([hi]+[camhi]*2)
vfull=np.load('fit3_v.npy')
def unpack(v): return dict(zip(NM,v[:len(NM)])),{p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
def resid(v,obs):
    q,c=unpack(v); out=[]
    for p in PH:
        ob=[o for o in obs if o['photo']==p]
        if not ob: continue
        X=np.array([seat_xyz(o['el'],o['idx'],q,o['kind']) for o in ob]); uv,zc=project(X,c[p])
        d=uv-np.array([[o['u'],o['v']] for o in ob]); d[zc<=0.5]+=500; out.append(d.ravel())
    return np.concatenate(out)
def allseats(q):
    return {(el,i):seat_xyz(el,i,q)[:2] for el,n in COUNTS.items() for i in range(n)}
q0,_=unpack(vfull)
# (b) hold-out tests
S0=allseats(q0)
tests={'side view of back rows + far table arm':lambda o:o['photo']=='U3' and o['el'] in ('B1','B2','GL'),
       'front view of right-hand rows':lambda o:o['photo']=='U1' and o['el'][0]=='R',
       'front view of back rows':lambda o:o['photo']=='U1' and o['el'][0]=='B',
       'side view of far-side rows L2-L4':lambda o:o['photo']=='U3' and o['el'] in ('L2','L3','L4')}
for name,f in tests.items():
    tr=[o for o in OBS if not f(o)]; te=[o for o in OBS if f(o)]
    s=least_squares(lambda v:resid(v,tr),vfull,bounds=(L,Hh),loss='soft_l1',f_scale=5,max_nfev=6000,x_scale='jac')
    e=np.linalg.norm(resid(s.x,te).reshape(-1,2),axis=1)
    q1,_=unpack(s.x); S1=allseats(q1)
    dplan=np.array([np.linalg.norm(S1[k]-S0[k]) for k in S0])
    print(f'HOLDOUT [{name}] n={len(te)}: predicted-vs-actual px median {np.median(e):.1f} max {np.max(e):.1f} | whole-plan shift median {np.median(dplan):.3f} max {np.max(dplan):.3f} pitch')
