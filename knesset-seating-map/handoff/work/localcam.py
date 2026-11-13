import numpy as np, json, cv2, sys, itertools
from model4 import *
from addphoto import fit_cam, associate
NM=[s[0] for s in SPEC]
photo,img=sys.argv[1],sys.argv[2]; prior=json.loads(sys.argv[3])   # {"C":[x,y,z],"T":[x,y,z],"dC":d,"f":[..]}
v=np.load('cur_v.npy'); q=dict(zip(NM,v[:len(NM)]))
im=cv2.imread(img); H,W=im.shape[:2]; s=W/2048; dets=json.load(open(f'det_{photo}.json'))
def lookat(C,T,f):
    C=np.array(C,float); fw=np.array(T,float)-C; fw/=np.linalg.norm(fw)
    rt=np.cross(fw,[0,0,1.0]); rt/=np.linalg.norm(rt); dn=np.cross(fw,rt); R=np.stack([rt,dn,fw]); rv,_=cv2.Rodrigues(R)
    return np.concatenate([rv.ravel(),-R@C,[f,0.0]])
res=[]
C0=np.array(prior['C']); T0=np.array(prior['T']); d=prior['dC']
for dx,dy,dz in itertools.product([-d,0,d],[-d,0,d],[-d/2,0,d/2]):
    for tx,ty in itertools.product([-3,0,3],[-3,0,3]):
        for f in prior['f']:
            cam=lookat(C0+[dx,dy,dz],T0+[tx,ty,0],f*W)
            try:
                for r in (45,30,18,10):
                    m,_,_,_=associate(q,cam,dets,W,H,r*s)
                    if len(m)<10: raise Exception
                    cam,e=fit_cam(q,m,cam,W,H)
                m,_,_,_=associate(q,cam,dets,W,H,8*s); _,e=fit_cam(q,m,cam,W,H)
                res.append((len(m),float(np.median(e)),cam))
            except Exception: pass
res.sort(key=lambda t:(-t[0],t[1]))
for n,med,cam in res[:6]: print(photo,'matches',n,'median px',round(med,2),'centre',np.round(cam_center(cam),2),'f/W',round(float(cam[6]/W),2))
json.dump(list(map(float,res[0][2])),open(f'cam_{photo}.json','w'))
