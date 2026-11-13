import numpy as np, json, cv2
from model4 import *
from anchorfit import load_q, overlay
from cam2 import *
q=load_q(); W,H=2048,1365
cam=np.array(json.load(open('cam_P1.json'))); anch=json.load(open('anch_P1.json'))
S=json.load(open('P1M.json')); T=json.load(open('P1W.json'))
def assoc(cam,kinds,els,D,r,shift=(0,0),excl=()):
    C=center2(cam); its=[(el,i,visible_kind(el,i,q,C)) for el in els for i in range(COUNTS[el])]
    its=[it for it in its if it[2] in kinds and (it[0],it[1]) not in excl]
    if not its: return []
    X=np.array([feat(*it[:2],q,it[2]) for it in its]); uv,zc=project2(X,cam,W,H); uv=uv+np.array(shift)
    P=np.array([[d['x'],d['y']] for d in D]); dist=np.linalg.norm(uv[:,None]-P[None],axis=2); dist[zc<=0]=1e9
    a=np.argmin(dist,1); b=np.argmin(dist,0); out=[]
    for ii,j in enumerate(a):
        if dist[ii,j]<r and b[j]==ii: out.append(dict(photo='P1',el=its[ii][0],idx=its[ii][1],kind=its[ii][2],u=float(P[j,0]),v=float(P[j,1])))
    return out
# 1) back rows: predictions are offset by about (+27,-5) px from the R-row-only camera
B=assoc(cam,('mon',),['B1','B2','B3','B4'],S,16,shift=(27,-5))
print('B matched with offset:',sorted((o['el'],o['idx']) for o in B))
obs=anch+B
cam,e=fit_cam2(q,obs,cam,W,H)
print('R+B fit (11-param camera): median',round(float(np.median(e)),2),'p90',round(float(np.percentile(e,90)),2),'max',round(float(e.max()),1))
# 2) iterate: add everything visible, tightening the radius
fixed={(o['el'],o['idx']) for o in obs}
for r in (14,10,7):
    extra=assoc(cam,('mon',),['R1','R2','R3','R4','B1','B2','B3','B4'],S,r,excl=fixed)+assoc(cam,('np',),['GL','L1','L2','L3','L4'],T,r)
    cur=obs+extra
    cam,e=fit_cam2(q,cur,cam,W,H)
    from collections import Counter
    print('radius',r,'n',len(cur),'median',round(float(np.median(e)),2),'p90',round(float(np.percentile(e,90)),2),dict(sorted(Counter(o['el'] for o in cur).items())))
json.dump(cur,open('obs_P1.json','w')); json.dump(list(map(float,cam)),open('cam_P1b.json','w'))
print('camera centre',np.round(center2(cam),2),'f/W',round(float(cam[6]/W),3),'k1 k2',round(float(cam[7]),3),round(float(cam[8]),3),'pp offset',round(float(cam[9]),1),round(float(cam[10]),1))
bad=[(o['el'],o['idx'],round(float(x),1)) for o,x in zip(cur,e) if x>6]
print('residual > 6 px:',bad)
