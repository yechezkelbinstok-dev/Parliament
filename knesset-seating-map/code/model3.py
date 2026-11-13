import numpy as np, cv2
from model2 import COUNTS, NF, SIDES, project, lookat
D=np.radians
SPEC=[('pG1',0.65,0.4,1.6),('pG2',0.6,0.4,1.6),('pGH',0.62,0.4,1.6),('g1',D(2),D(-15),D(15)),('g2',D(11),D(0),D(70))]
for k in range(1,5):
    SPEC+=[(f'xV{k}',2.5+1.9*k,2,30),(f'yV{k}',-2.6+0.64*k,-20,12),(f'aF{k}',0.0,D(-25),D(25)),(f'aK{k}',D(15),D(0),D(85)),(f'z{k}',0.1*k,-1.5,4)]
for j in range(1,5):
    SPEC+=[(f'yB{j}',0.2+1.85*j,0.2,15),(f'zB{j}',0.1*j,-1.5,4),(f'ps{j}',D(3),D(-25),D(25))]
SPEC+=[('pB',0.97,0.7,1.6),('dm',-0.2,-1.0,1.2),('hm',-0.15,-1.0,1.2)]
def seat_xyz(el, idx, q, kind='np'):
    if el=='GH': return np.array([(idx-2)*q['pGH'],0.0,0.0])
    if el in ('GL','GR'):
        s=SIDES[el[1]]; g1=q['g1']; g2=q['g2']
        VH=np.array([s*2.5*q['pGH'],0.0]); e2=np.array([s*np.sin(g2),-np.cos(g2)]); e1=np.array([s*np.sin(g1),-np.cos(g1)])
        V1=VH+5*q['pG2']*e2
        p2=VH+((10-idx)+0.5)*q['pG2']*e2 if idx>=6 else V1+((5-idx)+0.5)*q['pG1']*e1
        return np.array([p2[0],p2[1],0.0])
    if el[0] in 'LR':
        s=SIDES[el[0]]; k=int(el[1]); nF=NF[k]
        V=np.array([s*q[f'xV{k}'],q[f'yV{k}']]); aF=q[f'aF{k}']; aK=q[f'aK{k}']
        eF=np.array([s*np.sin(aF),-np.cos(aF)]); eK=np.array([-s*np.sin(aK),np.cos(aK)])
        if idx<nF: p2=V+((nF-1-idx)+0.5)*eF; d=eF
        else: p2=V+((idx-nF)+0.5)*eK; d=eK
        z=q[f'z{k}']
        if kind=='mon':
            n=np.array([d[1],-d[0]]); n=n if s*n[0]>0 else -n
            p2=p2+q['dm']*n; z=z+q['hm']
        return np.array([p2[0],p2[1],z])
    if el[0]=='B':
        j=int(el[1]); n=COUNTS[el]; c=(n-1)/2; t=(idx-c)*q['pB']; ps=q[f'ps{j}']
        # chevron: halves tilted by ps, centre (apex) furthest back when ps>0
        return np.array([t*np.cos(ps), q[f'yB{j}']-abs(t)*np.sin(ps), q[f'zB{j}']])
