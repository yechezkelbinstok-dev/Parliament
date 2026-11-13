import numpy as np, json, html, sys
from model4 import *
from model4 import _seg
from names2026 import SEATS, SPEAKER
vpath=sys.argv[1] if len(sys.argv)>1 else 'cur_v.npy'; out=sys.argv[2] if len(sys.argv)>2 else 'Knesset_26_seating.svg'
NM=[s[0] for s in SPEC]; v=np.load(vpath); q=dict(zip(NM,v[:len(NM)]))
OFF=0.80          # chair centre behind the desk front, in seat-pitch units
S=42.0; R=0.25*S  # px per unit, dot radius
SPEAKER_Y=-10.0
seats=[]
for el,n in COUNTS.items():
    for i in range(n):
        p,nrm,z=_seg(el,i,q); c=p+OFF*nrm
        seats.append((el,i,c[0],c[1],SEATS[el][i]))
seats.append(('SP',0,0.0,SPEAKER_Y,SPEAKER))
xs=[s[2] for s in seats]; ys=[s[3] for s in seats]; m=1.0
x0,x1,y0,y1=min(xs)-m,max(xs)+m,min(ys)-m,max(ys)+m
W=(x1-x0)*S; H=(y1-y0)*S
def X(x): return (x-x0)*S
def Y(y): return (y1-y)*S          # back of hall at top, Speaker at bottom
parties=json.load(open('parties.json')); who={}
for p in parties:
    for n in p['names']: who[n]=p
groups={p['id']:[] for p in parties}; groups['Non-MK-ministers']=[]; groups['Empty-seats']=[]
for el,i,x,y,name in seats:
    if name is None: groups['Empty-seats'].append((x,y,'Empty seat'))
    elif name in who: groups[who[name]['id']].append((x,y,f"{name} ({who[name]['title'].rsplit(' (',1)[0]})"))
    else: groups['Non-MK-ministers'].append((x,y,f"{name} (minister, not an MK)"))
meta={p['id']:(p['color'],p['title']) for p in parties}
meta['Non-MK-ministers']=('#9e9e9e',f"Ministers who are not MKs ({len(groups['Non-MK-ministers'])})")
meta['Empty-seats']=('#e6e6e6',f"Empty seats ({len(groups['Empty-seats'])})")
L=[f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.2f} {H:.2f}">',
   '    <!-- Seat positions measured from photographs of the Knesset plenum (2023-2026) fitted with a 3D model;',
   '         occupants from the Knesset seating chart updated 10.11.2026. Speaker at the bottom, coalition on the left. -->']
for gid,items in groups.items():
    if not items: continue
    col,title=meta[gid]
    st=f'fill:{col}' + (';stroke:#bdbdbd;stroke-width:1.2' if gid=='Empty-seats' else '')
    L.append(f'    <g style="{st}" id="{gid}">'); L.append(f'        <title>{html.escape(title)}</title>')
    for x,y,t in items:
        L.append(f'        <circle cx="{X(x):.2f}" cy="{Y(y):.2f}" r="{R:.2f}"><title>{html.escape(t)}</title></circle>')
    L.append('    </g>')
L.append('</svg>')
open(out,'w').write('\n'.join(L)+'\n')
print('wrote',out,f'{W:.0f}x{H:.0f}', {k:len(v) for k,v in groups.items()})
