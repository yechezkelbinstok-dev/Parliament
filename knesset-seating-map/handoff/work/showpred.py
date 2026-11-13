import numpy as np, json, cv2, sys
from model4 import *
from addphoto import load_q
photo,img=sys.argv[1],sys.argv[2]; x0,y0,x1,y1=map(int,sys.argv[3:7]); sc=float(sys.argv[7]); els=sys.argv[8].split(',')
q=load_q(sys.argv[9] if len(sys.argv)>9 else 'fit3_v.npy'); cam=np.array(json.load(open(f'cam_{photo}.json')))
im=cv2.imread(img); H,W=im.shape[:2]; C=cam_center(cam)
dets=json.load(open(f'det_{photo}.json'))
crop=cv2.resize(im[y0:y1,x0:x1],None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
for d in dets:
    if x0<=d[0]<x1 and y0<=d[1]<y1: cv2.circle(crop,(int((d[0]-x0)*sc),int((d[1]-y0)*sc)),3,(255,255,0),-1)
for el,n in COUNTS.items():
    if el not in els and els!=['all']: continue
    for i in range(n):
        k=visible_kind(el,i,q,C); uv,zc=project(feat(el,i,q,k)[None],cam,W,H)
        u,v=uv[0]
        if zc[0]<=0 or not (x0<=u<x1 and y0<=v<y1): continue
        P=(int((u-x0)*sc),int((v-y0)*sc))
        cv2.drawMarker(crop,P,(0,0,255) if k=='np' else (0,200,0),cv2.MARKER_CROSS,14,2)
        cv2.putText(crop,f'{el}.{i}',(P[0]+4,P[1]-4),cv2.FONT_HERSHEY_SIMPLEX,0.38,(0,255,255),1,cv2.LINE_AA)
cv2.imwrite(sys.argv[10] if len(sys.argv)>10 else f'pred_{photo}.png',crop)
