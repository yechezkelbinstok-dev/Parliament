import numpy as np, json
from model2 import *
obs=json.load(open('obs.json')); PH=['U1','U3']
NM=[s[0] for s in SPEC]; v=np.load('fit2_v.npy')
q=dict(zip(NM,v[:len(NM)])); cams={p:v[len(NM)+8*i:len(NM)+8*i+8] for i,p in enumerate(PH)}
for p in PH:
    for el in ['GH','GL','GR','B1','B2','B3','B4']:
        ob=[o for o in obs if o['photo']==p and o['el']==el]
        if not ob: continue
        X=np.array([seat_xyz(o['el'],o['idx'],q,o['kind']) for o in ob]); uv,_=project(X,cams[p])
        print(p,el,' '.join(f"{o['idx']}:({uv[i,0]-o['u']:+.0f},{uv[i,1]-o['v']:+.0f})" for i,o in enumerate(ob)))
