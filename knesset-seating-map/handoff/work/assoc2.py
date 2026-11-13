import numpy as np, json, cv2, sys
from model4 import *
from addphoto import fit_cam
from anchorfit import load_q, overlay
def run(photo,img,camf,screens,texts,anchors,radii=(30,20,12,8),use={'mon':'RB','np':'LG'},extra_fixed=()):
    q=load_q(); im=cv2.imread(img); H,W=im.shape[:2]; s=W/2048
    cam=np.array(json.load(open(camf)))
    S=np.array([[d['x'],d['y']] for d in screens]) if screens else np.zeros((0,2))
    T=np.array([[d['x'],d['y']] for d in texts]) if texts else np.zeros((0,2))
    anch=json.load(open(anchors)) if anchors else []
    for r in radii:
        C=cam_center(cam); items=[]
        for el,n in COUNTS.items():
            for i in range(n):
                k=visible_kind(el,i,q,C)
                if el[0] not in use.get(k,''): continue
                items.append((el,i,k))
        out=[]
        for kind,D in (('mon',S),('np',T)):
            its=[it for it in items if it[2]==kind]
            if not its or len(D)==0: continue
            X=np.array([feat(el,i,q,k) for el,i,k in its]); uv,zc=project(X,cam,W,H)
            dist=np.linalg.norm(uv[:,None,:]-D[None,:,:],axis=2); dist[zc<=0]=1e9
            a=np.argmin(dist,1); b=np.argmin(dist,0)
            for ii,j in enumerate(a):
                if dist[ii,j]<r*s and b[j]==ii:
                    el,i,k=its[ii]; out.append(dict(photo=photo,el=el,idx=i,kind=k,u=float(D[j,0]),v=float(D[j,1])))
        cam,e=fit_cam(q,out,cam,W,H)
        from collections import Counter
        print(photo,'radius',r,'matches',len(out),'median px',round(float(np.median(e)),2),'p90',round(float(np.percentile(e,90)),2),dict(sorted(Counter(o['el'] for o in out).items())))
    json.dump(out,open(f'obs_{photo}.json','w')); json.dump(list(map(float,cam)),open(f'cam_{photo}.json','w'))
    return q,cam,out
if __name__=='__main__':
    photo=sys.argv[1]
    q,cam,out=run(photo,f'{photo}.jpg',f'cam_{photo}.json',json.load(open(f'{photo}M.json')),json.load(open(f'{photo}W.json')) if len(sys.argv)<3 else [],None)
    overlay(photo,f'{photo}.jpg',cam,q,f'ov2{photo}',{'far':(700,560,2048,900,1.0),'nearR':(0,740,1050,1365,0.9),'nearB':(1000,740,2048,1365,0.9)},out)
