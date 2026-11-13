"""Build the dot map from the fitted hall model.

    python3 makesvg.py [--params fit.json] [--out FILE.svg] [--no-number] [--size PX]

--params takes fit.json (default) or a raw parameter vector saved as .npy.
The total is written like on the Wikipedia arch diagrams (bold, a tenth of the
width unless --size is given) where the horseshoe opens toward the Speaker, just
below the front ends of the rows; --no-number leaves it out.
Seats without an MK are drawn as on the Spanish Congress diagram: ministers who are
not MKs dark grey, empty seats light grey (the total counts MKs only);
--members-only leaves them out.
"""
import numpy as np, json, html, argparse, itertools
from model6 import *
from model6 import _seg
from names2026 import SEATS, SPEAKER
ap=argparse.ArgumentParser()
ap.add_argument('--params',default='fit.json'); ap.add_argument('--out',default='../knesset-26-seating.svg')
ap.add_argument('--no-number',action='store_true',help='leave out the total')
ap.add_argument('--size',type=float,help='text size in px (default: a tenth of the width)')
ap.add_argument('--members-only',action='store_true',help='leave out empty seats and ministers who are not MKs')
a=ap.parse_args()
NM=[s[0] for s in SPEC]
if a.params.endswith('.json'): q=json.load(open(a.params))['params']; q={k:q[k] for k in NM}
else: v=np.load(a.params); q=dict(zip(NM,v[:len(NM)]))
OFF=0.80          # chair centre behind the desk front, in seat-pitch units
S=42.0; R=0.25*S  # px per unit, dot radius
SPEAKER_Y=-10.1      # measured in speaker.py: on the axis (x=0), where the Speaker sits
seats=[]
for el,n in COUNTS.items():
    for i in range(n):
        p,nrm,z=_seg(el,i,q); c=p+OFF*nrm
        seats.append((el,i,c[0],c[1],SEATS[el][i]))
seats.append(('SP',0,0.0,SPEAKER_Y,SPEAKER))
P_=np.array([[s[2],s[3]] for s in seats]); dmin=min(np.linalg.norm(a_-b_) for a_,b_ in itertools.combinations(P_,2))
R=0.48*dmin*S; print('closest seats',round(dmin,3),'units -> dot radius',round(R/S,3))
xs=[s[2] for s in seats]; ys=[s[3] for s in seats]; m=1.0
x0,x1,y0,y1=min(xs)-m,max(xs)+m,min(ys)-m,max(ys)+m
# Number: same style as the arch diagrams and, by default, the same size relative to the
# picture (36 px text on a 360 px wide arch, a tenth of the width).
FS=round(a.size or (x1-x0)*S*36/360); CAP=0.72*FS/S   # text size in px; height of the digits in units
parties=json.load(open('parties.json')); who={}
for p in parties:
    for n in p['names']: who[n]=p
shown=[s for s in seats if s[4] in who and s[0]!='SP']   # drawn dots (ministers who are not MKs get none)
front=min(s[3] for s in shown)                         # frontmost MK's dot (nearest the Speaker)
arm=min(s[3] for s in shown if s[0] in ('GL','GR'))    # front ends of the table's arms
ny=min(front-CAP,arm-R/S-0.3-CAP)   # baseline: top of the digits level with the frontmost dot, clear of the table's arms
W=(x1-x0)*S; H=(y1-y0)*S
def X(x): return (x-x0)*S
def Y(y): return (y1-y)*S          # back of hall at top, Speaker at bottom
groups={p['id']:[] for p in parties}
for el,i,x,y,name in seats:
    if name in who: groups[who[name]['id']].append((x,y,f"{name} ({who[name]['title'].rsplit(' (',1)[0]})"))
meta={p['id']:(p['color'],p['title']) for p in parties}
# seats without an MK (not counted in the total)
others={'Ministers-not-MKs':('#808080','Ministers who are not MKs',[]),'Empty-seats':('#cccccc','Empty seats',[])}
for el,i,x,y,name in seats:
    if name in who: continue
    if name: others['Ministers-not-MKs'][2].append((x,y,f'{name} (minister, not an MK)'))
    else: others['Empty-seats'][2].append((x,y,'Empty seat'))
L=[f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.2f} {H:.2f}">',
   '    <!-- Seat positions measured from photographs of the Knesset plenum (2023-2026) fitted with a 3D model;',
   '         occupants from the Knesset seating chart updated 10.11.2026. Speaker at the bottom, coalition on the left. -->']
if not a.no_number:
    total=sum(len(v) for v in groups.values())
    L.append(f'    <text x="{X(0):.2f}" y="{Y(ny):.2f}" style="font-size:{FS}px;font-weight:bold;text-align:center;text-anchor:middle;font-family:sans-serif">{total}</text>')
for gid,items in groups.items():
    if not items: continue
    col,title=meta[gid]
    st=f'fill:{col}'
    L.append(f'    <g style="{st}" id="{gid}">'); L.append(f'        <title>{html.escape(title)}</title>')
    for x,y,t in items:
        L.append(f'        <circle cx="{X(x):.2f}" cy="{Y(y):.2f}" r="{R:.2f}"><title>{html.escape(t)}</title></circle>')
    L.append('    </g>')
if not a.members_only:
    for gid,(col,title,items) in others.items():
        if not items: continue
        L.append(f'    <g style="fill:{col}" id="{gid}">'); L.append(f'        <title>{html.escape(title)} ({len(items)})</title>')
        for x,y,t in items:
            L.append(f'        <circle cx="{X(x):.2f}" cy="{Y(y):.2f}" r="{R:.2f}"><title>{html.escape(t)}</title></circle>')
        L.append('    </g>')
L.append('</svg>')
open(a.out,'w').write('\n'.join(L)+'\n')
print('wrote',a.out,f'{W:.0f}x{H:.0f}', {k:len(v) for k,v in groups.items()})
