import numpy as np, cv2
COUNTS={'L1':7,'L2':9,'L3':11,'L4':13,'R1':7,'R2':9,'R3':11,'R4':13,'B1':6,'B2':8,'B3':10,'B4':16,'GL':11,'GR':11,'GH':5}
NF={1:4,2:5,3:6,4:7}
SIDES={'L':-1,'R':1}
D=np.radians
# symmetric parameter set: name, init, lo, hi
SPEC=[('pG',0.85,0.5,1.6),('g1',0.0,D(-15),D(15)),('g2',D(20),D(0),D(70))]
for k in range(1,5):
    SPEC+=[(f'xV{k}',5.0+2.0*k,2,30),(f'yV{k}',-4.0+0.8*k,-20,12),(f'aF{k}',0.0,D(-25),D(25)),(f'aK{k}',D(30),D(0),D(85)),(f'z{k}',0.25*k,-1.5,4)]
for j in range(1,5):
    SPEC+=[(f'yB{j}',1.3*j,0.2,15),(f'zB{j}',0.25*j,-1.5,4)]
SPEC+=[('pB',1.0,0.7,1.6),('dm',0.4,-0.2,1.2),('hm',0.25,-0.6,1.2)]
def seat_xyz(el, idx, q, kind='np'):
    if el=='GH': return np.array([(idx-2)*q['pG'],0.0,0.0])
    if el in ('GL','GR'):
        s=SIDES[el[1]]; pG=q['pG']; g1=q['g1']; g2=q['g2']
        VH=np.array([s*2.5*pG,0.0]); e2=np.array([s*np.sin(g2),-np.cos(g2)]); e1=np.array([s*np.sin(g1),-np.cos(g1)])
        V1=VH+5*pG*e2
        p2=VH+((10-idx)+0.5)*pG*e2 if idx>=6 else V1+((5-idx)+0.5)*pG*e1
        return np.array([p2[0],p2[1],0.0])
    if el[0] in 'LR':
        s=SIDES[el[0]]; k=int(el[1]); nF=NF[k]
        V=np.array([s*q[f'xV{k}'],q[f'yV{k}']]); aF=q[f'aF{k}']; aK=q[f'aK{k}']
        eF=np.array([s*np.sin(aF),-np.cos(aF)]); eK=np.array([-s*np.sin(aK),np.cos(aK)])
        if idx<nF: p2=V+((nF-1-idx)+0.5)*eF; d=eF
        else: p2=V+((idx-nF)+0.5)*eK; d=eK
        z=q[f'z{k}']
        if kind=='mon':
            n=np.array([d[1],-d[0]]);  n=n if s*n[0]>0 else -n
            p2=p2+q['dm']*n; z=z+q['hm']
        return np.array([p2[0],p2[1],z])
    if el[0]=='B':
        j=int(el[1]); n=COUNTS[el]
        return np.array([(idx-(n-1)/2)*q['pB'],q[f'yB{j}'],q[f'zB{j}']])
def project(X,cam,W=2048,H=1366):
    R,_=cv2.Rodrigues(cam[0:3]); Xc=(R@X.T).T+cam[3:6]
    x=Xc[:,0]/Xc[:,2]; y=Xc[:,1]/Xc[:,2]; d=1+cam[7]*(x*x+y*y)
    return np.stack([cam[6]*x*d+W/2,cam[6]*y*d+H/2],1),Xc[:,2]
def lookat(C,T,f=1400.0):
    C=np.array(C,float); fw=np.array(T,float)-C; fw/=np.linalg.norm(fw)
    rt=np.cross(fw,[0,0,1.0]); rt/=np.linalg.norm(rt); dn=np.cross(fw,rt)
    R=np.stack([rt,dn,fw]); rv,_=cv2.Rodrigues(R); return np.concatenate([rv.ravel(),-R@C,[f,0.0]])
