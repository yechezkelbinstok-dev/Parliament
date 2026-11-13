import numpy as np, json
from scipy.optimize import least_squares
import model5 as M
from cam2 import project2
import cam2
from joint6 import init, load_obs, SIZE, NM as NM4
PH=['U1','U3','A','U2','P1']; obs=load_obs()
v6=np.load('fit6_v.npy'); q6=dict(zip(NM4,v6[:len(NM4)]))
o=len(NM4); cams={}
for p in PH:
    n=11 if p=='P1' else 8; cams[p]=v6[o:o+n]; o+=n
NM=[s[0] for s in M.SPEC]; lo=np.array([s[2] for s in M.SPEC]); hi=np.array([s[3] for s in M.SPEC])
x0=np.array([q6[n] if n in q6 else q6[n[:-1]] for n in NM])
sz=[len(cams[p]) for p in PH]
L=np.concatenate([lo]+[cam2.LO[:n] for n in sz]); Hh=np.concatenate([hi]+[cam2.HI[:n] for n in sz])
def unpack(v):
    q=dict(zip(NM,v[:len(NM)])); c={}; k=len(NM)
    for p,n in zip(PH,sz): c[p]=v[k:k+n]; k+=n
    return q,c
def resid(v):
    q,c=unpack(v); out=[]
    for p in PH:
        ob=[x for x in obs if x['photo']==p]
        X=np.array([M.feat(x['el'],x['idx'],q,x['kind']) for x in ob]); uv,zc=project2(X,c[p],*SIZE[p])
        d=(uv-np.array([[x['u'],x['v']] for x in ob]))*(2048/SIZE[p][0]); d[zc<=0.3]+=1000; out.append(d.ravel())
    return np.concatenate(out)
v0=np.concatenate([x0]+[cams[p] for p in PH])
s=least_squares(resid,np.clip(v0,L,Hh),bounds=(L,Hh),loss='soft_l1',f_scale=5,max_nfev=20000,x_scale='jac')
q,_=unpack(s.x); e=np.linalg.norm(resid(s.x).reshape(-1,2),axis=1)
print('asymmetric fit median px',round(float(np.median(e)),2))
for k in ['g2']+[f'aK{k}' for k in range(1,5)]+[f'xV{k}' for k in range(1,5)]+[f'yV{k}' for k in range(1,5)]:
    a,b=q[k+'L'],q[k+'R']; ang=k[:2] in ('g2','aK')
    f=np.degrees if ang else (lambda x:x)
    print(f'{k:4s} left {f(a):7.2f}  right {f(b):7.2f}  diff {f(a-b):+6.2f}{" deg" if ang else " seat widths"}')
S=lambda el,i: M._seg(el,i,q)[0]
mm=[np.linalg.norm(S(el,i)-np.array([-S(er,i)[0],S(er,i)[1]])) for el,er in [('L1','R1'),('L2','R2'),('L3','R3'),('L4','R4'),('GL','GR')] for i in range(M.COUNTS[el])]
print('left vs mirrored right, all side-row and table seats: median %.3f, 90%% %.3f, max %.3f seat widths'%(np.median(mm),np.percentile(mm,90),np.max(mm)))
