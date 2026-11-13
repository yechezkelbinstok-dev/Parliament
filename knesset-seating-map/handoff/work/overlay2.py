import numpy as np, json, cv2
from model2 import *
obs=json.load(open('obs.json')); PH=['U1','U3']
NM=[s[0] for s in SPEC]; v=np.load('fit2_v.npy')
q=dict(zip(NM,v[:len(NM)])); cams={p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
COL={'G':(0,165,255),'L':(255,80,80),'R':(80,80,255),'B':(80,220,80)}
for p,src in [('U1','U1.jpg'),('U3','U3.jpg')]:
    im=cv2.imread(src)
    kind='mon' if p=='U3' else 'np'
    for el,n in COUNTS.items():
        X=np.array([seat_xyz(el,i,q,'np') for i in range(n)])
        uv,zc=project(X,cams[p])
        for i,(u,vv) in enumerate(uv):
            if zc[i]<=0: continue
            cv2.circle(im,(int(u),int(vv)),6,COL[el[0]],2)
        # also monitors for R branches in U3
        if p=='U3' and el[0]=='R':
            Xm=np.array([seat_xyz(el,i,q,'mon') for i in range(n)]); uvm,_=project(Xm,cams[p])
            for (u,vv) in uvm: cv2.drawMarker(im,(int(u),int(vv)),(0,255,255),cv2.MARKER_SQUARE,10,2)
    for o in obs:
        if o['photo']==p: cv2.drawMarker(im,(int(o['u']),int(o['v'])),(0,0,255),cv2.MARKER_TILTED_CROSS,9,1)
    cv2.imwrite(f'ov_{p}.jpg',im)
print('done')
