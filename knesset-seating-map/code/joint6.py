import numpy as np, json, sys
from scipy.optimize import least_squares
from model4 import *
from cam2 import project2, center2
import cam2
SIZE={'U1':(2048,1366),'U3':(2048,1366),'A':(1600,1157),'U2':(2048,1366),'P1':(2048,1365)}
NM=[s[0] for s in SPEC]; LOq=np.array([s[2] for s in SPEC]); HIq=np.array([s[3] for s in SPEC])
def load_obs():
    o=json.load(open('obs.json'))+json.load(open('obs_A.json'))+json.load(open('obs_U2.json'))+json.load(open('obs_extraB.json'))+json.load(open('obs_P1.json'))
    return o
def init():
    v5=np.load('fit5_v.npy'); q0=v5[:len(NM)]
    cams={p:v5[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(['U1','U3','A','U2'])}
    cams['P1']=np.array(json.load(open('cam_P1b.json')))
    return q0,cams
class Joint:
    def __init__(s,PH,cams):
        s.PH=PH; s.sz=[len(cams[p]) for p in PH]
        s.lo=np.concatenate([LOq]+[cam2.LO[:n] for n in s.sz]); s.hi=np.concatenate([HIq]+[cam2.HI[:n] for n in s.sz])
        s.hi[len(NM):][[i for i in range(sum(s.sz))]]=s.hi[len(NM):]
    def pack(s,q0,cams): return np.concatenate([q0]+[cams[p] for p in s.PH])
    def unpack(s,v):
        q=dict(zip(NM,v[:len(NM)])); c={}; o=len(NM)
        for p,n in zip(s.PH,s.sz): c[p]=v[o:o+n]; o+=n
        return q,c
    def resid(s,v,obs):
        q,c=s.unpack(v); out=[]
        for p in s.PH:
            ob=[x for x in obs if x['photo']==p]
            if not ob: continue
            X=np.array([feat(x['el'],x['idx'],q,x['kind']) for x in ob]); uv,zc=project2(X,c[p],*SIZE[p])
            d=(uv-np.array([[x['u'],x['v']] for x in ob]))*(2048/SIZE[p][0]); d[zc<=0.3]+=1000; out.append(d.ravel())
        return np.concatenate(out)
    def fit(s,v0,obs,nfev=20000):
        return least_squares(lambda v:s.resid(v,obs),np.clip(v0,s.lo,s.hi),bounds=(s.lo,s.hi),loss='soft_l1',f_scale=5,max_nfev=nfev,x_scale='jac').x
if __name__=='__main__':
    PH=['U1','U3','A','U2','P1']; q0,cams=init(); J=Joint(PH,cams); obs=load_obs()
    v=J.fit(J.pack(q0,cams),obs)
    e=np.linalg.norm(J.resid(v,obs).reshape(-1,2),axis=1)
    print('n',len(e),'median px',round(float(np.median(e)),2),'rms',round(float(np.sqrt(np.mean(e**2))),2))
    i=0; from collections import defaultdict; agg=defaultdict(list)
    for p in PH:
        for x in [x for x in obs if x['photo']==p]: agg[p].append(e[i]); i+=1
    print({p:round(float(np.median(vv)),2) for p,vv in agg.items()})
    np.save('fit6_v.npy',v); json.dump({'PH':PH,'sz':J.sz},open('fit6_meta.json','w'))
    q,c=J.unpack(v)
    for p in PH: print(p,'centre',np.round(center2(c[p]),2))
