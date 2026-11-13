import numpy as np, json, cv2, sys
from model4 import *
NM=[s[0] for s in SPEC]; v=np.load('fit4_v.npy'); q=dict(zip(NM,v[:len(NM)]))
PH=['U1','U3','A','U2']; cams={p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
photo,img,x0,y0,x1,y1,sc,detf=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7]),float(sys.argv[7]),sys.argv[8]
cam=cams[photo]; im=cv2.imread(img); H,W=im.shape[:2]; C=cam_center(cam)
crop=cv2.resize(im[y0:y1,x0:x1],None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
dets=json.load(open(detf)); dets=[(d['x'],d['y']) if isinstance(d,dict) else (d[0],d[1]) for d in dets]
for (u,vv) in dets:
    if x0<=u<x1 and y0<=vv<y1: cv2.circle(crop,(int((u-x0)*sc),int((vv-y0)*sc)),3,(255,255,0),-1)
for el in ['B3','B4']:
    for i in range(COUNTS[el]):
        k=visible_kind(el,i,q,C); uv,zc=project(feat(el,i,q,k)[None],cam,W,H); u,vv=uv[0]
        if not (x0<=u<x1 and y0<=vv<y1): continue
        P=(int((u-x0)*sc),int((vv-y0)*sc))
        cv2.drawMarker(crop,P,(0,0,255) if el=='B4' else (0,200,0),cv2.MARKER_CROSS,16,2)
        cv2.putText(crop,f'{el}.{i}{k[0]}',(P[0]+5,P[1]-5),cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,255,255),1,cv2.LINE_AA)
cv2.imwrite(f'predB_{photo}.png',crop)
