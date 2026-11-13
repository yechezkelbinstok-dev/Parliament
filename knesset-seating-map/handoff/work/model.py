import numpy as np, json, cv2
from scipy.optimize import least_squares
COUNTS={'L1':7,'L2':9,'L3':11,'L4':13,'R1':7,'R2':9,'R3':11,'R4':13,'B1':6,'B2':8,'B3':10,'B4':16,'GL':11,'GR':11,'GH':5}
NF={1:4,2:5,3:6,4:7}
SIDES={'L':-1,'R':1}
IMG={'U1':(2048,1366),'U3':(2048,1366)}
class P:
    """parameter vector with named slots"""
    def __init__(s): s.names=[]; s.init=[]
    def add(s,n,v): s.names.append(n); s.init.append(float(v))
    def idx(s): return {n:i for i,n in enumerate(s.names)}
def build_params(sym=False):
    P_=P()
    P_.add('pG',0.85)
    for sd in ('L','R'):
        P_.add(f'g1{sd}',0.0); P_.add(f'g2{sd}',np.radians(20))
    for sd in ('L','R'):
        for k in range(1,5):
            P_.add(f'xV{sd}{k}',5.0+2.0*k); P_.add(f'yV{sd}{k}',-4.0+0.8*k)
            P_.add(f'aF{sd}{k}',0.0); P_.add(f'aK{sd}{k}',np.radians(25)); P_.add(f'z{sd}{k}',0.3*k)
    for j in range(1,5):
        P_.add(f'yB{j}',1.4*j); P_.add(f'xc{j}',0.0); P_.add(f'th{j}',0.0); P_.add(f'zB{j}',0.3*j)
    P_.add('pB',1.0)
    P_.add('dm',0.45); P_.add('hm',0.25)
    return P_
def seat_xyz(el, idx, q, kind='np'):
    """world position of seat idx of element el"""
    if el=='GH':
        return np.array([(idx-2)*q['pG'],0.0,0.0])
    if el in ('GL','GR'):
        s=SIDES[el[1]]; pG=q['pG']; g1=q['g1'+el[1]]; g2=q['g2'+el[1]]
        VH=np.array([s*2.5*pG,0.0])
        e2=np.array([s*np.sin(g2),-np.cos(g2)]); e1=np.array([s*np.sin(g1),-np.cos(g1)])
        V1=VH+5*pG*e2
        if idx>=6: p2=VH+((10-idx)+0.5)*pG*e2
        else: p2=V1+((5-idx)+0.5)*pG*e1
        return np.array([p2[0],p2[1],0.0])
    if el[0] in 'LR':
        sd=el[0]; s=SIDES[sd]; k=int(el[1]); nF=NF[k]
        V=np.array([q[f'xV{sd}{k}'],q[f'yV{sd}{k}']]); aF=q[f'aF{sd}{k}']; aK=q[f'aK{sd}{k}']
        eF=np.array([s*np.sin(aF),-np.cos(aF)]); eK=np.array([-s*np.sin(aK),np.cos(aK)])
        if idx<nF: p2=V+((nF-1-idx)+0.5)*eF; d=eF
        else: p2=V+((idx-nF)+0.5)*eK; d=eK
        z=q[f'z{sd}{k}']
        if kind=='mon':
            n=np.array([d[1],-d[0]])
            if s*n[0]<0: n=-n
            p2=p2+q['dm']*n; z=z+q['hm']
        return np.array([p2[0],p2[1],z])
    if el[0]=='B':
        j=int(el[1]); n=COUNTS[el]; th=q[f'th{j}']
        p2=np.array([q[f'xc{j}'],q[f'yB{j}']])+(idx-(n-1)/2)*q['pB']*np.array([np.cos(th),np.sin(th)])
        return np.array([p2[0],p2[1],q[f'zB{j}']])
    raise ValueError(el)
def project(X, cam, photo):
    rv=cam[0:3]; tv=cam[3:6]; f=cam[6]; k1=cam[7]
    R,_=cv2.Rodrigues(rv)
    Xc=(R@X.T).T+tv
    x=Xc[:,0]/Xc[:,2]; y=Xc[:,1]/Xc[:,2]
    r2=x*x+y*y; d=1+k1*r2
    W,H=IMG[photo]
    return np.stack([f*x*d+W/2, f*y*d+H/2],1), Xc[:,2]
