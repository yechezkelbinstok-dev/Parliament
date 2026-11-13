import numpy as np, json, cv2, sys
from scipy.optimize import least_squares
from model4 import *
NM=[s[0] for s in SPEC]
def load_q(path='fit3_v.npy'):
    v=np.load(path); return dict(zip(NM,v[:len(NM)]))
def fit_cam(q, obs, cam0, W, H, fix_k1=False):
    X=np.array([feat(o['el'],o['idx'],q,o['kind']) for o in obs]); U=np.array([[o['u'],o['v']] for o in obs])
    def r(c):
        cc=c.copy()
        if fix_k1: cc[7]=0
        uv,zc=project(X,cc,W,H); d=uv-U; d[zc<=0.3]+=1000; return d.ravel()
    lo=[-10,-10,-10,-300,-300,-300,150,-0.5]; hi=[10,10,10,300,300,300,8000,0.5]
    s=least_squares(r,np.clip(cam0,lo,hi),bounds=(lo,hi),loss='soft_l1',f_scale=3*W/2048,max_nfev=5000)
    e=np.linalg.norm(r(s.x).reshape(-1,2),axis=1); return s.x, e
def pnp_init(q, anchors, W, H, f):
    X=np.array([feat(a['el'],a['idx'],q,a['kind']) for a in anchors],float); U=np.array([[a['u'],a['v']] for a in anchors],float)
    K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1]],float)
    ok,rv,tv=cv2.solvePnP(X,U,K,None,flags=cv2.SOLVEPNP_SQPNP)
    return np.concatenate([rv.ravel(),tv.ravel(),[f,0.0]])
def associate(q, cam, dets, W, H, radius):
    C=cam_center(cam); items=[]
    for el,n in COUNTS.items():
        for i in range(n):
            k=visible_kind(el,i,q,C); items.append((el,i,k,feat(el,i,q,k)))
    X=np.array([it[3] for it in items]); uv,zc=project(X,cam,W,H)
    D=np.array([[d[0],d[1]] for d in dets])
    ok=(zc>0.3)&(uv[:,0]>-5)&(uv[:,0]<W+5)&(uv[:,1]>-5)&(uv[:,1]<H+5)
    dist=np.linalg.norm(uv[:,None,:]-D[None,:,:],axis=2); dist[~ok]=1e9
    a=np.argmin(dist,1); b=np.argmin(dist,0); out=[]
    for i,j in enumerate(a):
        if dist[i,j]<radius and b[j]==i:
            el,idx,k,_=items[i]; out.append(dict(el=el,idx=idx,kind=k,u=D[j][0],v=D[j][1]))
    return out, uv, items, ok
def run(photo, img, anchors, f0, radii=(40,25,15,10), fix_k1=False, qpath='fit3_v.npy'):
    q=load_q(qpath); im=cv2.imread(img); H,W=im.shape[:2]; s=W/2048
    dets=json.load(open(f'det_{photo}.json'))
    # snap anchors to detections when close
    D=np.array([[d[0],d[1]] for d in dets])
    for a in anchors:
        dd=np.linalg.norm(D-[a['u'],a['v']],axis=1); j=np.argmin(dd)
        if dd[j]<6*s: a['u'],a['v']=float(D[j,0]),float(D[j,1])
    cam=pnp_init(q,anchors,W,H,f0)
    cam,e=fit_cam(q,anchors,cam,W,H,fix_k1)
    print(photo,'anchor fit: median px',round(float(np.median(e)),2),'max',round(float(np.max(e)),2),'f',round(float(cam[6])))
    for r in radii:
        m,uv,items,ok=associate(q,cam,dets,W,H,r*s)
        cam,e=fit_cam(q,m,cam,W,H,fix_k1)
        print(' radius',r,'matches',len(m),'median px',round(float(np.median(e)),2),'p90',round(float(np.percentile(e,90)),2))
    m,uv,items,ok=associate(q,cam,dets,W,H,radii[-1]*s)
    for o in m: o['photo']=photo
    json.dump(m,open(f'obs_{photo}.json','w')); json.dump(list(map(float,cam)),open(f'cam_{photo}.json','w'))
    vis=im.copy(); Ms={(o['el'],o['idx']) for o in m}
    for (el,i,k,_),p,o in zip(items,uv,ok):
        if not o: continue
        col=(0,255,0) if (el,i) in Ms else (0,0,255)
        cv2.circle(vis,(int(p[0]),int(p[1])),max(2,int(6*s)),col,max(1,int(2*s)))
    cv2.imwrite(f'add_{photo}.jpg',vis)
    return m,cam
if __name__=='__main__':
    pass
