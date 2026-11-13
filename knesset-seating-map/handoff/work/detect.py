import cv2, numpy as np, json, sys
src, out, ymin, ymax = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
im = cv2.imread(src); H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
V = hsv[...,2].astype(int); S = hsv[...,1].astype(int); B = lab[...,2].astype(int)  # b*: <128 bluish
mask = ((V > 175) & (S < 80) & (B < 134)).astype(np.uint8)*255
mask[:ymin] = 0; mask[ymax:] = 0
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2,2),np.uint8))
n, lbl, stats, cents = cv2.connectedComponentsWithStats(mask)
cands = []
for i in range(1, n):
    x,y,w,h,a = stats[i]
    if a < 25 or a > 2500: continue
    if w > 70 or h > 70: continue
    fill = a/(w*h)
    if fill < 0.45: continue
    cands.append(dict(id=len(cands), x=float(cents[i][0]), y=float(cents[i][1]), w=int(w), h=int(h), a=int(a)))
json.dump(cands, open(out+'.json','w'))
vis = im.copy()
for c in cands:
    cv2.circle(vis, (int(c['x']),int(c['y'])), 3, (0,0,255), -1)
    cv2.putText(vis, str(c['id']), (int(c['x'])+4,int(c['y'])-3), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0,255,255), 1, cv2.LINE_AA)
cv2.imwrite(out+'.png', vis)
print(len(cands), 'candidates')
