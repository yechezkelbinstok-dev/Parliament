import numpy as np, json, sys
from scipy.optimize import least_squares
from model2 import *
obs=json.load(open('obs.json')); PH=['U1','U3']
NM=[s[0] for s in SPEC]; x0=np.array([s[1] for s in SPEC]); lo=np.array([s[2] for s in SPEC]); hi=np.array([s[3] for s in SPEC])
camlo=np.array([-10,-10,-10,-200,-200,-200,500,-0.5]); camhi=-camlo; camhi[6]=6000
def unpack(v):
    q=dict(zip(NM,v[:len(NM)])); return q,{p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
def resid(v):
    q,c=unpack(v); out=[]
    for p in PH:
        ob=[o for o in obs if o['photo']==p]
        X=np.array([seat_xyz(o['el'],o['idx'],q,o['kind']) for o in ob])
        uv,zc=project(X,c[p]); d=uv-np.array([[o['u'],o['v']] for o in ob]); d[zc<=0.5]+=500
        out.append(d.ravel())
    return np.concatenate(out)
best=None
starts=[((0,-17,3.5),(18,-3,9)),((0,-14,4.5),(16,-1,8)),((0,-20,3),(20,-4,10)),((0,-16,5),(15,-2,11))]
for C1,C3 in starts:
    cams=[lookat(C1,(0,-2,0)),lookat(C3,(0,-2,0))]
    v0=np.concatenate([x0]+cams); L=np.concatenate([lo]+[camlo]*2); Hh=np.concatenate([hi]+[camhi]*2)
    m=np.zeros(len(v0),bool); m[len(NM):]=True
    def rc(vc):
        v=v0.copy(); v[m]=vc; return resid(v)
    s1=least_squares(rc,v0[m],bounds=(L[m],Hh[m]),loss='soft_l1',f_scale=30,max_nfev=3000)
    v1=v0.copy(); v1[m]=s1.x
    s2=least_squares(resid,v1,bounds=(L,Hh),loss='soft_l1',f_scale=5,max_nfev=8000,x_scale='jac')
    r=resid(s2.x).reshape(-1,2); e=np.linalg.norm(r,axis=1)
    print('start',C1,C3,'rms',round(float(np.sqrt(np.mean(e**2))),2),'median',round(float(np.median(e)),2))
    if best is None or np.median(e)<best[0]: best=(np.median(e),s2.x)
np.save('fit2_v.npy',best[1])
q,c=unpack(best[1])
for n in NM: print(f'{n:5s}', round(float(np.degrees(q[n]) if n[:2] in ('g1','g2','aF','aK') else q[n]),3))
for p in PH: print(p,'f',round(float(c[p][6]),1),'k1',round(float(c[p][7]),4))
r=resid(best[1]).reshape(-1,2); e=np.linalg.norm(r,axis=1)
from collections import defaultdict
agg=defaultdict(list); i=0
for p in PH:
    for o in [o for o in obs if o['photo']==p]: agg[(p,o['el'])].append(e[i]); i+=1
for k,vv in sorted(agg.items()): print(k,'n',len(vv),'mean',round(float(np.mean(vv)),1),'max',round(float(np.max(vv)),1))
