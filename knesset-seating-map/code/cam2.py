# camera with extra distortion and principal-point offset: [rv(3), t(3), f, k1, k2, cx, cy]
import numpy as np, cv2
from scipy.optimize import least_squares
from model4 import feat, visible_kind, COUNTS
def project2(X,cam,W,H):
    R,_=cv2.Rodrigues(np.asarray(cam[0:3],float)); Xc=(R@X.T).T+cam[3:6]
    x=Xc[:,0]/Xc[:,2]; y=Xc[:,1]/Xc[:,2]; r2=x*x+y*y
    k2=cam[8] if len(cam)>8 else 0.0; cx=cam[9] if len(cam)>9 else 0.0; cy=cam[10] if len(cam)>10 else 0.0
    d=1+cam[7]*r2+k2*r2*r2
    return np.stack([cam[6]*x*d+W/2+cx,cam[6]*y*d+H/2+cy],1),Xc[:,2]
def center2(cam):
    R,_=cv2.Rodrigues(np.asarray(cam[0:3],float)); return -R.T@np.asarray(cam[3:6],float)
LO=np.array([-10,-10,-10,-300,-300,-300,150,-0.6,-0.6,-200,-200]); HI=-LO.copy(); HI[6]=8000
def fit_cam2(q,obs,cam0,W,H,f_scale=3.0):
    cam0=np.concatenate([cam0,np.zeros(11-len(cam0))]) if len(cam0)<11 else np.asarray(cam0,float)
    X=np.array([feat(o['el'],o['idx'],q,o['kind']) for o in obs]); U=np.array([[o['u'],o['v']] for o in obs])
    def r(c):
        uv,zc=project2(X,c,W,H); d=uv-U; d[zc<=0.3]+=1000; return d.ravel()
    s=least_squares(r,np.clip(cam0,LO,HI),bounds=(LO,HI),loss='soft_l1',f_scale=f_scale*W/2048,max_nfev=8000)
    return s.x, np.linalg.norm(r(s.x).reshape(-1,2),axis=1)
