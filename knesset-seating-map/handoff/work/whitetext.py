import cv2, numpy as np, json, sys
src,out,y0,y1=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
im=cv2.imread(src); H,W=im.shape[:2]; s=W/2048
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); V=hsv[...,2].astype(int); S=hsv[...,1].astype(int)
bg=cv2.blur(V.astype(np.float32),(25,9))
m=((V>135)&(S<90)&(V-bg>45)).astype(np.uint8)*255; m[:y0]=0; m[y1:]=0
m2=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_RECT,(max(3,int(7*s)),1)))
n,l,st,ce=cv2.connectedComponentsWithStats(m2); res=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if w<8*s or w>70*s or h<2 or h>12*s or w<2.2*h: continue
    sub=m[y:y+h,x:x+w]; ys,xs=np.nonzero(sub)
    if len(xs)<6: continue
    res.append(dict(id=len(res),x=float(xs.mean()+x),y=float(ys.mean()+y),w=int(w),h=int(h)))
json.dump(res,open(out+'.json','w')); print(len(res))
