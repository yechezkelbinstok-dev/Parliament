import numpy as np, json, cv2, sys
from model4 import *
from addphoto import pnp_init, fit_cam
NM=[s[0] for s in SPEC]
def load_q(path='fit5_v.npy'):
    v=np.load(path); return dict(zip(NM,v[:len(NM)]))
def build(photo, img, spec, q, kinddefault=None):
    """spec: list of (detfile, el, [(idx, detid), ...]) or (None, el, [(idx,(u,v)),...])"""
    obs=[]
    for detf,el,pairs in spec:
        D={r['id']:(r['x'],r['y']) for r in json.load(open(detf))} if detf else {}
        for idx,did in pairs:
            u,v=(D[did] if detf else did)
            obs.append(dict(photo=photo,el=el,idx=idx,kind=kinddefault,u=float(u),v=float(v)))
    return obs
def solve(photo,img,obs,q,fs=(0.45,0.6,0.8,1.0,1.3)):
    im=cv2.imread(img); H,W=im.shape[:2]; best=None
    for f in fs:
        try:
            cam=pnp_init(q,obs,W,H,f*W)
            # pick visible kind from the camera side, then refit
            for it in range(3):
                C=cam_center(cam)
                for o in obs:
                    if o.get('fixkind') is None: o['kind']=visible_kind(o['el'],o['idx'],q,C)
                cam,e=fit_cam(q,obs,cam,W,H)
            if best is None or np.median(e)<best[0]: best=(float(np.median(e)),cam,e)
        except Exception as ex: pass
    return best
def overlay(photo,img,cam,q,out,crops,obs=()):
    im=cv2.imread(img); H,W=im.shape[:2]; C=cam_center(cam); s=W/2048
    COL={'G':(0,140,255),'L':(255,90,60),'R':(60,60,255),'B':(40,220,40)}
    for el,n in COUNTS.items():
        for i in range(n):
            k=visible_kind(el,i,q,C); uv,zc=project(feat(el,i,q,k)[None],cam,W,H); u,v=uv[0]
            if zc[0]<=0 or not(-20<u<W+20 and -20<v<H+20): continue
            cv2.drawMarker(im,(int(u),int(v)),COL[el[0]],cv2.MARKER_CROSS,int(12*s),max(1,int(2*s)))
            cv2.putText(im,f'{el}.{i}',(int(u)+4,int(v)-4),cv2.FONT_HERSHEY_SIMPLEX,0.36*s+0.05,(255,255,255),1,cv2.LINE_AA)
    for o in obs: cv2.circle(im,(int(o['u']),int(o['v'])),int(5*s),(0,255,255),1)
    for name,(x0,y0,x1,y1,sc) in crops.items():
        cv2.imwrite(f'{out}_{name}.png',cv2.resize(im[y0:y1,x0:x1],None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA if sc<1 else cv2.INTER_CUBIC))
