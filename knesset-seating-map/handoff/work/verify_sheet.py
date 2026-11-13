import numpy as np, json, cv2
from model4 import *
NM=[s[0] for s in SPEC]; v=np.load('cur_v.npy'); q=dict(zip(NM,v[:len(NM)]))
PH=[('U1','U1.jpg'),('U3','U3.jpg'),('A','A.jpg')]
COL={'G':(0,140,255),'L':(255,90,60),'R':(60,60,255),'B':(40,200,40)}
panels=[]
for i,(p,img) in enumerate(PH):
    cam=v[len(NM)+8*i:len(NM)+8*i+8]; im=cv2.imread(img); H,W=im.shape[:2]; C=cam_center(cam); s=W/2048
    for el,n in COUNTS.items():
        for k in range(n):
            kind=visible_kind(el,k,q,C); uv,zc=project(feat(el,k,q,kind)[None],cam,W,H)
            if zc[0]>0: cv2.circle(im,(int(uv[0,0]),int(uv[0,1])),max(4,int(9*s)),COL[el[0]],max(2,int(3*s)))
    h=520; im=cv2.resize(im,(int(W*h/H),h)); panels.append(im)
Wt=max(p.shape[1] for p in panels)
sheet=np.full((sum(p.shape[0] for p in panels)+20*len(panels),Wt,3),255,np.uint8); y=0
for p in panels: sheet[y:y+p.shape[0],:p.shape[1]]=p; y+=p.shape[0]+20
cv2.imwrite('verification.jpg',sheet,[cv2.IMWRITE_JPEG_QUALITY,88]); print(sheet.shape)
