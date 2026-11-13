import cv2, sys
src,out,x0,y0,x1,y1,sc=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7]),float(sys.argv[7])
step=int(sys.argv[8]) if len(sys.argv)>8 else 50
im=cv2.imread(src)[y0:y1,x0:x1]
im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
H,W=im.shape[:2]
for gx in range((x0//step+1)*step, x1, step):
    X=int((gx-x0)*sc); cv2.line(im,(X,0),(X,H),(0,255,255) if gx%(step*2)==0 else (0,180,255),1)
    cv2.putText(im,str(gx),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1,cv2.LINE_AA)
for gy in range((y0//step+1)*step, y1, step):
    Y=int((gy-y0)*sc); cv2.line(im,(0,Y),(W,Y),(0,255,255) if gy%(step*2)==0 else (0,180,255),1)
    cv2.putText(im,str(gy),(2,Y-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1,cv2.LINE_AA)
cv2.imwrite(out,im)
