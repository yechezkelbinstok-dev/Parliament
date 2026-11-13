import cv2, numpy as np, json, sys
src,out,ymin=sys.argv[1],sys.argv[2],int(sys.argv[3])
im=cv2.imread(src); H,W=im.shape[:2]; s=W/2048
I=im.astype(int); B,G,R=I[...,0],I[...,1],I[...,2]
m=(((B>150)&(B-R>35))|((B>200)&(G>200)&(R>190))).astype(np.uint8)*255; m[:ymin]=0
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
n,l,st,ce=cv2.connectedComponentsWithStats(m)
res=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if a<60*s*s or w<10*s or h<7*s or w>110*s or h>80*s: continue
    if a/(w*h)<0.45: continue
    res.append(dict(id=len(res),x=float(ce[i][0]),y=float(ce[i][1]),w=int(w),h=int(h)))
json.dump(res,open(out+'.json','w'))
vis=im.copy()
for r in res:
    cv2.rectangle(vis,(int(r['x']-r['w']/2),int(r['y']-r['h']/2)),(int(r['x']+r['w']/2),int(r['y']+r['h']/2)),(0,0,255),1)
    cv2.putText(vis,str(r['id']),(int(r['x']-r['w']/2),int(r['y']-r['h']/2)-2),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1,cv2.LINE_AA)
cv2.imwrite(out+'.png',vis); print(len(res))
