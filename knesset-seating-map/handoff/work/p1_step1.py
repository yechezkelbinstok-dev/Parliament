from anchorfit import *
q=load_q()
spec=[('P1M.json','R4',[(0,28),(1,43),(2,48),(3,56),(4,65),(5,78),(6,83),(8,99),(9,104),(10,107),(11,111),(12,113)]),
      ('P1M.json','R3',[(0,22),(1,29),(2,36),(3,49),(5,64),(6,74),(7,81),(8,86),(9,92),(10,98)]),
      ('P1M.json','R2',[(5,54),(6,61),(7,67),(8,76)]),
      ('P1M.json','R1',[(5,37),(6,45)])]
obs=build('P1','P1.jpg',spec,q,'mon')
best=solve('P1','P1.jpg',obs,q)
med,cam,e=best
print('median px',round(med,2),'max',round(float(e.max()),1),'f/W',round(float(cam[6]/2048),2),'centre',np.round(cam_center(cam),2))
for o,ee in zip(obs,e):
    if ee>5: print('  large',o['el'],o['idx'],o['kind'],round(float(ee),1))
json.dump(list(map(float,cam)),open('cam_P1.json','w')); json.dump(obs,open('anch_P1.json','w'))
overlay('P1','P1.jpg',cam,q,'ovP1',{'far':(700,560,2048,900,1.0),'nearR':(0,740,1050,1365,0.9),'nearB':(1000,740,2048,1365,0.9)},obs)
