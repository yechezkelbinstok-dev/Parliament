# asymmetric variant of model4: left and right sides get their own parameters
import numpy as np
from model3 import SPEC as SPEC3, COUNTS, NF, SIDES
from model4 import project, cam_center
SIDE_KEYS=['g1','g2']+[f'{a}{k}' for k in range(1,5) for a in ('xV','yV','aF','aK','z')]
SPEC=[]
for n,v,lo,hi in SPEC3:
    if n in SIDE_KEYS: SPEC+= [(n+'L',v,lo,hi),(n+'R',v,lo,hi)]
    else: SPEC.append((n,v,lo,hi))
def _seg(el, idx, q):
    if el=='GH': return np.array([(idx-2)*q['pGH'],0.0]), np.array([0.0,1.0]), 0.0
    if el in ('GL','GR'):
        sd=el[1]; s=SIDES[sd]; g1=q['g1'+sd]; g2=q['g2'+sd]
        VH=np.array([s*2.5*q['pGH'],0.0]); e2=np.array([s*np.sin(g2),-np.cos(g2)]); e1=np.array([s*np.sin(g1),-np.cos(g1)])
        V1=VH+5*q['pG2']*e2
        if idx>=6: p=VH+((10-idx)+0.5)*q['pG2']*e2; d=e2
        else: p=V1+((5-idx)+0.5)*q['pG1']*e1; d=e1
        n=np.array([d[1],-d[0]]); n=n if s*n[0]>0 else -n; return p,n,0.0
    if el[0] in 'LR':
        sd=el[0]; s=SIDES[sd]; k=int(el[1]); nF=NF[k]
        V=np.array([s*q[f'xV{k}{sd}'],q[f'yV{k}{sd}']]); aF=q[f'aF{k}{sd}']; aK=q[f'aK{k}{sd}']
        eF=np.array([s*np.sin(aF),-np.cos(aF)]); eK=np.array([-s*np.sin(aK),np.cos(aK)])
        if idx<nF: p=V+((nF-1-idx)+0.5)*eF; d=eF
        else: p=V+((idx-nF)+0.5)*eK; d=eK
        n=np.array([d[1],-d[0]]); n=n if s*n[0]>0 else -n; return p,n,q[f'z{k}{sd}']
    if el[0]=='B':
        j=int(el[1]); m=COUNTS[el]; c=(m-1)/2; t=(idx-c)*q['pB']; ps=q[f'ps{j}']
        p=np.array([t*np.cos(ps), q[f'yB{j}']-abs(t)*np.sin(ps)]); sg=1.0 if t>=0 else -1.0
        n=np.array([sg*np.sin(ps),np.cos(ps)]); return p,n/np.linalg.norm(n),q[f'zB{j}']
def feat(el, idx, q, kind='np'):
    p,n,z=_seg(el,idx,q)
    if kind=='mon': p=p+q['dm']*n; z=z+q['hm']
    return np.array([p[0],p[1],z])
