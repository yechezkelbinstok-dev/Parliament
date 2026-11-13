import cv2, numpy as np, json, sys
src,out=sys.argv[1],sys.argv[2]
ymin=int(sys.argv[3]) if len(sys.argv)>3 else 0
im=cv2.imread(src).astype(int); Bc,Gc,Rc=im[...,0],im[...,1],im[...,2]
m=((Bc>140)&(Bc-Rc>60)&(Gc>80)&(Bc>=Gc)).astype(np.uint8)*255
m[:ymin]=0
k=cv2.getStructuringElement(cv2.MORPH_RECT,(9,3))
m2=cv2.dilate(m,k)
n,l,st,ce=cv2.connectedComponentsWithStats(m2)
res=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if a<15 or w<6: continue
    if h>40 or w>200: continue
    sub=m[y:y+h,x:x+w]; ys,xs=np.nonzero(sub)
    if len(xs)<8: continue
    res.append(dict(id=len(res),x=float(xs.mean()+x),y=float(ys.mean()+y),w=int(w),h=int(h),x0=int(x),x1=int(x+w)))
json.dump(res,open(out+'.json','w'))
vis=cv2.imread(src)
for r in res:
    cv2.rectangle(vis,(r['x0'],int(r['y'])-r['h']//2-1),(r['x1'],int(r['y'])+r['h']//2+1),(0,0,255),1)
    cv2.putText(vis,str(r['id']),(r['x0'],int(r['y'])-r['h']//2-3),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1,cv2.LINE_AA)
cv2.imwrite(out+'.png',vis); print(len(res))
