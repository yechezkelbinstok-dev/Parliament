import numpy as np, cv2
from model3 import SPEC, COUNTS, NF, SIDES
def _seg(el, idx, q):
    """returns (point2d, outward_normal2d, z)"""
    if el=='GH':
        return np.array([(idx-2)*q['pGH'],0.0]), np.array([0.0,1.0]), 0.0
    if el in ('GL','GR'):
        s=SIDES[el[1]]; g1=q['g1']; g2=q['g2']
        VH=np.array([s*2.5*q['pGH'],0.0]); e2=np.array([s*np.sin(g2),-np.cos(g2)]); e1=np.array([s*np.sin(g1),-np.cos(g1)])
        V1=VH+5*q['pG2']*e2
        if idx>=6: p=VH+((10-idx)+0.5)*q['pG2']*e2; d=e2
        else: p=V1+((5-idx)+0.5)*q['pG1']*e1; d=e1
        n=np.array([d[1],-d[0]]); n=n if s*n[0]>0 else -n
        return p, n, 0.0
    if el[0] in 'LR':
        s=SIDES[el[0]]; k=int(el[1]); nF=NF[k]
        V=np.array([s*q[f'xV{k}'],q[f'yV{k}']]); aF=q[f'aF{k}']; aK=q[f'aK{k}']
        eF=np.array([s*np.sin(aF),-np.cos(aF)]); eK=np.array([-s*np.sin(aK),np.cos(aK)])
        if idx<nF: p=V+((nF-1-idx)+0.5)*eF; d=eF
        else: p=V+((idx-nF)+0.5)*eK; d=eK
        n=np.array([d[1],-d[0]]); n=n if s*n[0]>0 else -n
        return p, n, q[f'z{k}']
    if el[0]=='B':
        j=int(el[1]); m=COUNTS[el]; c=(m-1)/2; t=(idx-c)*q['pB']; ps=q[f'ps{j}']
        p=np.array([t*np.cos(ps), q[f'yB{j}']-abs(t)*np.sin(ps)])
        sg=1.0 if t>=0 else -1.0
        n=np.array([sg*np.sin(ps),np.cos(ps)]); n/=np.linalg.norm(n)
        return p, n, q[f'zB{j}']
def feat(el, idx, q, kind='np'):
    p,n,z=_seg(el,idx,q)
    if kind=='mon': p=p+q['dm']*n; z=z+q['hm']
    return np.array([p[0],p[1],z])
def visible_kind(el, idx, q, C):
    p,n,z=_seg(el,idx,q)
    return 'mon' if np.dot(C[:2]-p,n)>0 else 'np'
def project(X,cam,W,H):
    R,_=cv2.Rodrigues(cam[0:3]); Xc=(R@X.T).T+cam[3:6]
    x=Xc[:,0]/Xc[:,2]; y=Xc[:,1]/Xc[:,2]; d=1+cam[7]*(x*x+y*y)
    return np.stack([cam[6]*x*d+W/2,cam[6]*y*d+H/2],1),Xc[:,2]
def cam_center(cam):
    R,_=cv2.Rodrigues(cam[0:3]); return -R.T@cam[3:6]
