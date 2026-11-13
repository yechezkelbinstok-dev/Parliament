import numpy as np, json, sys, importlib
from scipy.optimize import least_squares
mode=sys.argv[1]   # 'holdout' or 'asym'
M=importlib.import_module('model5' if mode=='asym' else 'model4')
from model4 import project
PH=['U1','U3','A','U2']; SIZE={'U1':(2048,1366),'U3':(2048,1366),'A':(1600,1157),'U2':(2048,1366)}
OBS=json.load(open('obs.json'))+json.load(open('obs_A.json'))+json.load(open('obs_U2.json'))
import model4
NM4=[s[0] for s in model4.SPEC]; vcur=np.load('fit4_v.npy'); q4=dict(zip(NM4,vcur[:len(NM4)])); cams=[vcur[len(NM4)+8*i:len(NM4)+8*i+8] for i in range(4)]
NM=[s[0] for s in M.SPEC]; lo=np.array([s[2] for s in M.SPEC]); hi=np.array([s[3] for s in M.SPEC])
x0=np.array([q4[n] if n in q4 else q4[n[:-1]] for n in NM])
camlo=np.array([-10,-10,-10,-300,-300,-300,150,-0.5]); camhi=-camlo; camhi[6]=8000
L=np.concatenate([lo]+[camlo]*4); Hh=np.concatenate([hi]+[camhi]*4); v0=np.concatenate([x0]+cams)
def unpack(v): return dict(zip(NM,v[:len(NM)])),{p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
def resid(v,obs):
    q,c=unpack(v); out=[]
    for p in PH:
        ob=[o for o in obs if o['photo']==p]
        if not ob: continue
        X=np.array([M.feat(o['el'],o['idx'],q,o['kind']) for o in ob]); uv,zc=project(X,c[p],*SIZE[p])
        d=(uv-np.array([[o['u'],o['v']] for o in ob]))*(2048/SIZE[p][0]); d[zc<=0.3]+=1000; out.append(d.ravel())
    return np.concatenate(out)
def fit(obs,v=v0):
    return least_squares(lambda v:resid(v,obs),v,bounds=(L,Hh),loss='soft_l1',f_scale=5,max_nfev=15000,x_scale='jac').x
def plan(q):
    return {(el,i):M._seg(el,i,q)[0] for el,n in M.COUNTS.items() for i in range(n)}
if mode=='holdout':
    S0=plan(unpack(v0)[0])
    tests={'far table arm + back rows in the 2026 side photo':lambda o:o['photo']=='U3' and o['el'] in ('B1','B2','GL'),
           'all government-table data from the 2025 side photo':lambda o:o['photo']=='U2' and o['el'] in ('GL','GH'),
           'outermost far row L4 in the 2026 side photo':lambda o:o['photo']=='U3' and o['el']=='L4',
           'outermost far row L4 in the 2025 side photo':lambda o:o['photo']=='U2' and o['el']=='L4',
           'x':lambda o:False}
    tests.pop('x')
    _old={'side view of back rows + far table arm (2026 side photo)':lambda o:o['photo']=='U3' and o['el'] in ('B1','B2','GL'),
           'back rows in the 2023 back-corner photo':lambda o:o['photo']=='A' and o['el'][0]=='B',
           'back rows seen from the dais':lambda o:o['photo']=='U1' and o['el'][0]=='B',
           'right-hand rows seen from the dais':lambda o:o['photo']=='U1' and o['el'][0]=='R',
           'far-side rows L2-L4 (2026 side photo)':lambda o:o['photo']=='U3' and o['el'] in ('L2','L3','L4')}
    tests.update({'back rows in the 2023 back-corner photo':_old['back rows in the 2023 back-corner photo'],'back rows seen from the dais':_old['back rows seen from the dais']})
    for name,f in tests.items():
        tr=[o for o in OBS if not f(o)]; te=[o for o in OBS if f(o)]
        v=fit(tr); e=np.linalg.norm(resid(v,te).reshape(-1,2),axis=1)
        S1=plan(unpack(v)[0]); dp=np.array([np.linalg.norm(S1[k]-S0[k]) for k in S0])
        print(f'HOLDOUT [{name}] n={len(te)}: predicted vs actual px median {np.median(e):.1f}, 90% {np.percentile(e,90):.1f} | map moves median {np.median(dp):.2f}, max {np.max(dp):.2f} seat-widths')
else:
    v=fit(OBS); q,_=unpack(v); e=np.linalg.norm(resid(v,OBS).reshape(-1,2),axis=1)
    print('asymmetric fit median px',round(float(np.median(e)),2))
    for k in ['g1','g2']+[f'{a}{k}' for k in range(1,5) for a in ('xV','yV','aF','aK')]:
        a,b=q[k+'L'],q[k+'R']; ang=k[:2] in ('g1','g2','aF','aK')
        f=np.degrees if ang else (lambda x:x)
        print(f'{k:4s} L {f(a):7.2f}  R {f(b):7.2f}  diff {f(a-b):+6.2f}{"°" if ang else " seat-widths"}')
    S0=plan(unpack(v)[0]); 
    # mirror check: distance between each left seat and the mirror image of its right twin
    mm=[]
    for el in ['L1','L2','L3','L4','GL']:
        er='R'+el[1] if el[0]=='L' else 'GR'
        for i in range(M.COUNTS[el]):
            a=S0[(el,i)]; b=S0[(er,i)]; mm.append(np.linalg.norm(a-np.array([-b[0],b[1]])))
    print('left vs mirrored right: median %.2f, max %.2f seat-widths'%(np.median(mm),np.max(mm)))
