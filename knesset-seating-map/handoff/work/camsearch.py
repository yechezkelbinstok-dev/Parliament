import numpy as np, json, cv2, sys, time
from scipy.spatial import cKDTree
from model4 import *
from model4 import _seg
from addphoto import fit_cam, associate
NM=[s[0] for s in SPEC]
def all_feats(q):
    els=[]; P={}
    for el,n in COUNTS.items():
        for i in range(n):
            p,nrm,z=_seg(el,i,q); els.append((el,i)); P[(el,i)]=(p,nrm,z)
    return els,P
def search(photo, img, qpath, n=120000, seed=0, sigma=6.0):
    v=np.load(qpath); q=dict(zip(NM,v[:len(NM)]))
    im=cv2.imread(img); H,W=im.shape[:2]; s=W/2048
    D=np.array([[d[0],d[1]] for d in json.load(open(f'det_{photo}.json'))]); tree=cKDTree(D)
    els,P=all_feats(q)
    pts=np.array([P[e][0] for e in els]); nrm=np.array([P[e][1] for e in els]); zz=np.array([P[e][2] for e in els])
    mon=np.c_[pts+q['dm']*nrm, zz+q['hm']]; npl=np.c_[pts, zz]
    rng=np.random.default_rng(seed); best=[]
    t0=time.time()
    B=4000
    for b in range(n//B):
        C=np.c_[rng.uniform(-24,24,B),rng.uniform(-24,18,B),rng.uniform(1.5,15,B)]
        T=np.c_[rng.uniform(-8,8,B),rng.uniform(-10,8,B),np.zeros(B)]
        f=rng.uniform(0.45,1.7,B)*W; roll=rng.normal(0,0.04,B)
        fw=T-C; fw/=np.linalg.norm(fw,axis=1,keepdims=True)
        rt=np.cross(fw,[0,0,1.0]); rt/=np.linalg.norm(rt,axis=1,keepdims=True); dn=np.cross(fw,rt)
        # roll
        cr,sr=np.cos(roll)[:,None],np.sin(roll)[:,None]; rt2=cr*rt+sr*dn; dn2=-sr*rt+cr*dn
        R=np.stack([rt2,dn2,fw],1)                                   # B x 3 x 3
        # visible feature per camera: monitor if camera on outward side
        side=np.einsum('bk,nk->bn',C[:,:2],nrm)-np.sum(pts*nrm,1)[None,:]   # B x N
        X=np.where(side[...,None]>0, mon[None], npl[None])          # B x N x 3
        Xc=np.einsum('bij,bnj->bni',R,X-C[:,None,:])
        zc=Xc[...,2]; u=f[:,None]*Xc[...,0]/zc+W/2; vv=f[:,None]*Xc[...,1]/zc+H/2
        ok=(zc>0.5)&(u>0)&(u<W)&(vv>0)&(vv<H)
        UV=np.stack([u,vv],-1)
        d,_=tree.query(UV.reshape(-1,2)); d=d.reshape(B,-1)
        sc=np.where(ok,np.exp(-(d/(sigma*s))**2/2),0).sum(1)
        for k in np.argsort(-sc)[:5]:
            best.append((sc[k],C[k],T[k],f[k],roll[k]))
    best.sort(key=lambda t:-t[0]); best=best[:25]
    print(photo,'search',round(time.time()-t0,1),'s; top scores',[round(float(b[0]),1) for b in best[:6]])
    # refine top candidates with association + camera fit
    dets=json.load(open(f'det_{photo}.json')); res=[]
    for sc,C,T,f,roll in best:
        fw=T-C; fw/=np.linalg.norm(fw); rt=np.cross(fw,[0,0,1.0]); rt/=np.linalg.norm(rt); dn=np.cross(fw,rt)
        R=np.stack([rt,dn,fw]); rv,_=cv2.Rodrigues(R); cam=np.concatenate([rv.ravel(),-R@C,[f,0.0]])
        try:
            for r in (30,20,12,8):
                m,_,_,_=associate(q,cam,dets,W,H,r*s)
                if len(m)<8: break
                cam,e=fit_cam(q,m,cam,W,H)
            m,_,_,_=associate(q,cam,dets,W,H,8*s)
            if len(m)>=8:
                _,e=fit_cam(q,m,cam,W,H); res.append((len(m),float(np.median(e)),cam,m))
        except Exception as ex: pass
    res.sort(key=lambda t:(-t[0],t[1]))
    for t in res[:5]: print('  refined: matches',t[0],'median px',round(t[1],2),'cam centre',np.round(cam_center(t[2]),2),'f',round(float(t[2][6])))
    return res
if __name__=='__main__':
    photo,img,qpath=sys.argv[1],sys.argv[2],sys.argv[3]
    res=search(photo,img,qpath,n=int(sys.argv[4]) if len(sys.argv)>4 else 120000)
    if res:
        n,med,cam,m=res[0]
        json.dump(list(map(float,cam)),open(f'cam_{photo}.json','w'))
        for o in m: o['photo']=photo
        json.dump(m,open(f'auto_{photo}.json','w'))
