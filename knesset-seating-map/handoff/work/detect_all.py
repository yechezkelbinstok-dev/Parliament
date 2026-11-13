import cv2, numpy as np, json, sys
def detect(src, ymin=0, ymax=None):
    im=cv2.imread(src); H,W=im.shape[:2]; s=W/2048.0
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); I=im.astype(int); B,G,R=I[...,0],I[...,1],I[...,2]
    out=[]
    # screens: bright, bluish or neutral-white
    m1=(((hsv[...,2]>165)&(hsv[...,1]<95))|((B>150)&(B-R>35))).astype(np.uint8)*255
    # LED name text: saturated blue/cyan on dark, merged horizontally
    m2=((B>140)&(B-R>60)&(G>80)).astype(np.uint8)*255
    m2=cv2.dilate(m2,cv2.getStructuringElement(cv2.MORPH_RECT,(max(3,int(9*s)),max(1,int(3*s)))))
    for m in (m1,m2):
        if ymax is None: ymax=H
        m[:ymin]=0; m[ymax:]=0
        n,l,st,ce=cv2.connectedComponentsWithStats(m)
        for i in range(1,n):
            x,y,w,h,a=st[i]
            if a<max(6,int(20*s*s)) or w>140*s or h>90*s: continue
            out.append([float(ce[i][0]),float(ce[i][1]),int(w),int(h)])
    # merge near-duplicates
    pts=[]
    for p in sorted(out,key=lambda p:-p[2]*p[3]):
        if all((p[0]-q[0])**2+(p[1]-q[1])**2>(4*s)**2 for q in pts): pts.append(p)
    return pts
if __name__=='__main__':
    src,out=sys.argv[1],sys.argv[2]; ymin=int(sys.argv[3]) if len(sys.argv)>3 else 0
    pts=detect(src,ymin); json.dump(pts,open(out,'w')); print(len(pts))
