import json, numpy as np
dets=json.load(open('det_A.json')); D=np.array([[d[0],d[1]] for d in dets])
def snap(u,v,r=6):
    dd=np.linalg.norm(D-[u,v],axis=1); j=int(np.argmin(dd))
    return (float(D[j,0]),float(D[j,1])) if dd[j]<r else (float(u),float(v))
R1=[(395,556),(425,568),(457,576),(495,590),(537,601),(600,610),(670,623)]
R2=[(251,574),(276,587),(306,599),(336,613),(372,629),(414,643),(478,657),(551,674),(632,693)]
R3=[(88,581),(108,593),(126,607),(147,623),(173,640),(203,664),(243,683),(311,703),(387,724),(476,748),(576,777)]
B1=[(1118,552),(1085,567),(1047,578),(1007,588),(937,608),(880,625)]            # idx0 (far, chart-left) -> idx5 (near)
B2=[(1277,562),(1252,573),(1225,590),(1193,607),(1153,625),(1098,638),(1035,662),(962,685)]
B3=[(1452,553),(1435,568),(1417,587),(1397,605),(1373,623),(1340,645),(1290,663),(1233,688),(1167,720),(1087,748)]
obs=[]
for el,L in (('R1',R1),('R2',R2),('R3',R3),('B1',B1),('B2',B2),('B3',B3)):
    for i,(u,v) in enumerate(L):
        if el=='R2' and i==6: uu,vv=(u,v)   # dark (switched-off) screen: keep hand position
        else: uu,vv=snap(u,v)
        obs.append(dict(photo='A',el=el,idx=i,kind='mon',u=uu,v=vv))
json.dump(obs,open('obs_A.json','w')); print(len(obs))
