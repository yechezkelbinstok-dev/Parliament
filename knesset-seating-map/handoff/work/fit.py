import numpy as np, json, cv2, sys
from scipy.optimize import least_squares
from model import *
obs=json.load(open('obs.json'))
P_=build_params(); NM=P_.names; IX=P_.idx(); x0=np.array(P_.init)
PH=['U1','U3']
def lookat(C,T,f=1400.0):
    C=np.array(C,float); fw=np.array(T,float)-C; fw/=np.linalg.norm(fw)
    up=np.array([0,0,1.0]); rt=np.cross(fw,up); rt/=np.linalg.norm(rt); dn=np.cross(fw,rt)
    R=np.stack([rt,dn,fw]); rv,_=cv2.Rodrigues(R); t=-R@C
    return np.concatenate([rv.ravel(),t,[f,0.0]])
cams={'U1':lookat((0,-17,3.5),(0,0,0)),'U3':lookat((18,-3,9),(0,-2,0))}
def unpack(v):
    q={n:v[i] for i,n in enumerate(NM)}
    c={}; o=len(NM)
    for p in PH: c[p]=v[o:o+8]; o+=8
    return q,c
def resid(v,weights=None):
    q,c=unpack(v); r=[]
    for p in PH:
        ob=[o for o in obs if o['photo']==p]
        X=np.array([seat_xyz(o['el'],o['idx'],q,o['kind']) for o in ob])
        uv,zc=project(X,c[p],p)
        tgt=np.array([[o['u'],o['v']] for o in ob])
        d=uv-tgt
        d[zc<=0]*=10
        r.append(d.ravel())
    return np.concatenate(r)
v0=np.concatenate([x0]+[cams[p] for p in PH])
# stage 1: cameras only
mask=np.zeros(len(v0),bool); mask[len(NM):]=True
def r_cam(vc):
    v=v0.copy(); v[mask]=vc; return resid(v)
s1=least_squares(r_cam,v0[mask],loss='soft_l1',f_scale=20,max_nfev=4000)
v1=v0.copy(); v1[mask]=s1.x
print('stage1 rms',np.sqrt(np.mean(r_cam(s1.x)**2)))
# stage 2: everything (pitch of MK desks fixed = 1 by construction)
s2=least_squares(resid,v1,loss='soft_l1',f_scale=4,max_nfev=20000,x_scale='jac')
r=resid(s2.x).reshape(-1,2)
print('stage2 rms px',np.sqrt(np.mean(np.sum(r**2,1))), 'median',np.median(np.linalg.norm(r,axis=1)))
np.save('fit_v.npy',s2.x)
q,c=unpack(s2.x)
for n in NM:
    val=q[n]
    print(f'{n:6s} {np.degrees(val) if n[:2] in ("g1","g2","aF","aK","th") else val:9.3f}')
for p in PH: print(p,'f',round(c[p][6],1),'k1',round(c[p][7],4))
# per-element residuals
i=0
from collections import defaultdict
agg=defaultdict(list)
for p in PH:
    for o in [o for o in obs if o['photo']==p]:
        agg[(p,o['el'])].append(np.linalg.norm(r[i])); i+=1
for k,vv in sorted(agg.items()): print(k, 'n',len(vv),'mean px',round(np.mean(vv),1),'max',round(np.max(vv),1))
