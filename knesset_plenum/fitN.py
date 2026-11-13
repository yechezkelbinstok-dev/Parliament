import numpy as np, json, sys
from scipy.optimize import least_squares
from model4 import *
PH=sys.argv[1].split(','); out=sys.argv[2]
obs=json.load(open('obs.json'))
for p in PH:
    if p not in ('U1','U3'): obs+=json.load(open(f'obs_{p}.json'))
obs+=json.load(open('obs_extraB.json'))
obs=[o for o in obs if o['photo'] in PH]
SIZE={'U1':(2048,1366),'U3':(2048,1366),'A':(1600,1157),'C':(1650,700),'N1':(550,375),'N2':(739,415),'U2':(2048,1366)}
NM=[s[0] for s in SPEC]; lo=np.array([s[2] for s in SPEC]); hi=np.array([s[3] for s in SPEC])
camlo=np.array([-10,-10,-10,-300,-300,-300,150,-0.5]); camhi=-camlo; camhi[6]=8000
v3=np.load('fit4_v.npy'); q3=v3[:len(NM)]
cam0={p:v3[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(['U1','U3','A','U2'])}
for p in PH:
    if p not in cam0: cam0[p]=np.array(json.load(open(f'cam_{p}.json')))
def unpack(v): return dict(zip(NM,v[:len(NM)])),{p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
W8={p:2048.0/SIZE[p][0] for p in PH}   # weight residuals to a common 2048-px scale
def resid(v,obs=obs):
    q,c=unpack(v); out=[]
    for p in PH:
        ob=[o for o in obs if o['photo']==p]
        if not ob: continue
        X=np.array([feat(o['el'],o['idx'],q,o['kind']) for o in ob]); uv,zc=project(X,c[p],*SIZE[p])
        d=(uv-np.array([[o['u'],o['v']] for o in ob]))*W8[p]; d[zc<=0.3]+=1000; out.append(d.ravel())
    return np.concatenate(out)
v0=np.concatenate([q3]+[cam0[p] for p in PH]); L=np.concatenate([lo]+[camlo]*len(PH)); Hh=np.concatenate([hi]+[camhi]*len(PH))
s=least_squares(resid,np.clip(v0,L,Hh),bounds=(L,Hh),loss='soft_l1',f_scale=5,max_nfev=20000,x_scale='jac')
np.save(out,s.x)
r=resid(s.x).reshape(-1,2); e=np.linalg.norm(r,axis=1)
print('photos',PH,'n',len(e),'median px(2048-scale)',round(float(np.median(e)),2),'rms',round(float(np.sqrt(np.mean(e**2))),2))
from collections import defaultdict
agg=defaultdict(list); i=0
for p in PH:
    for o in [o for o in obs if o['photo']==p]: agg[(p,o['el'])].append(e[i]); i+=1
print(' '.join(f"{k[0]}:{k[1]}={np.mean(vv):.1f}" for k,vv in sorted(agg.items())))
q,c=unpack(s.x)
for n in NM: print(f'{n:5s} {np.degrees(q[n]) if n[:2] in ("g1","g2","aF","aK","ps") else q[n]:8.3f}', end=' |')
print()
