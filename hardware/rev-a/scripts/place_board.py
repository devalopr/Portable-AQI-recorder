"""Resolve footprint courtyard collisions around preferred circuit positions.
This is placement assistance; electrical loop and mechanical review still follow.
"""
import json,sys,math
from pathlib import Path
import pcbnew as p
folder=Path(sys.argv[1]);d=json.loads((folder/'design.json').read_text());name=d['name'];project_path=folder/(name+'.kicad_pro');saved_project=project_path.read_text();b=p.LoadBoard(str(folder/(name+'.kicad_pcb')))
W,H=d['width'],d['height'];mm=p.FromMM
F={f.GetReference():f for f in b.GetFootprints()};D={c['ref']:c for c in d['components']};placed=[];result={}
def box(f):
 r=f.GetBoundingBox(False,False)
 return [p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())]
def intersects(a,b,gap=.32):return a[0]<b[2]+gap and a[2]>b[0]-gap and a[1]<b[3]+gap and a[3]>b[1]-gap
def setcenter(f,x,y):
 bb=box(f);pos=f.GetPosition();f.SetPosition(p.VECTOR2I(pos.x+mm(x-(bb[0]+bb[2])/2),pos.y+mm(y-(bb[1]+bb[3])/2)))
def valid(f):
 bb=box(f);side=f.GetLayer()
 # Full body bounds conservatively fit inside board except connector actuator allowance below.
 if bb[0]<.5 or bb[1]<.5 or bb[2]>W-.5 or bb[3]>H-.5:return False
 if any(intersects(bb,v) for ly,v in placed if ly is None or ly==side):return False
 if f.GetReference()!='U1' and name=='AQI_Main' and intersects(bb,[27.5,H-7,W,H],0):return False
 return True
priority=['J1','J5','U1','SW1','SW2','SW3','SW4','J2','J3','J4','J6','U8','U9','U5','L1','U6','L2','U10','U2','U3','U4','U7','L3','Q3','C9','C10','C12','C13','C30','C31'] if name=='AQI_Main' else ['J2','J1','J3','J4','U1','U2','L1','U3','L2','U4','U5','Q2','U6','C1','C3','C7','C8','C9','C10','C11','C13','C14']
targets={'J1':(7.5,H-5),'J5':(22,4.5),'U1':(35,H-10),'SW1':(8,66),'SW2':(22,66),'SW3':(36,66),'SW4':(3,56),'J2':(39,51),'J3':(4.5,24),'J4':(4.5,45),'J6':(15,35),'U8':(10,15),'U9':(29,40),'U5':(25,51),'L1':(31.5,51),'U6':(32,23),'L2':(38,23),'U10':(30,12),'U2':(20,69),'U3':(15,57),'U4':(21,57),'U7':(21,15),'L3':(12,27),'Q3':(16,28),'C9':(20,50),'C10':(31.5,55),'C12':(27,23),'C13':(38,27.5),'C30':(8,27),'C31':(12,31.5)} if name=='AQI_Main' else {'J1':(5.5,H-5),'J2':(22,43)}
# All major components first. Remaining parts placed by descending body area.
rest=[r for r in F if r not in priority]
rest.sort(key=lambda r:-(box(F[r])[2]-box(F[r])[0])*(box(F[r])[3]-box(F[r])[1]))
for ref in [r for r in priority if r in F]+rest:
 f=F[ref]; orig=f.GetPosition();x,y=targets.get(ref,D[ref]['xy']); choices=[]
 for dx in range(-70,71):
  for dy in range(-70,71):
   cost=dx*dx+dy*dy
   choices.append((cost,dx*.5,dy*.5))
 choices.sort()
 ok=False
 for _,dx,dy in choices:
  setcenter(f,x+dx,y+dy)
  if valid(f):ok=True;break
 if not ok:raise RuntimeError('Cannot fit '+ref)
 bb=box(f);placed.append((None if ref=="J1" else f.GetLayer(),bb))
 # Through-hole pads and locating holes occupy both PCB faces.
 for pad in f.Pads():
  if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]:
   r=pad.GetBoundingBox(); placed.append((None,[p.ToMM(r.GetLeft())-.3,p.ToMM(r.GetTop())-.3,p.ToMM(r.GetRight())+.3,p.ToMM(r.GetBottom())+.3]))
 pos=f.GetPosition()
 result[ref]={'xy':[round(p.ToMM(pos.x),4),round(p.ToMM(pos.y),4)],'rot':D[ref].get('rot',0),'side':D[ref].get('side','front')}
 if math.hypot(dx,dy)>8:print(ref,'moved',round(math.hypot(dx,dy),1),'mm')
(folder/'placement.json').write_text(json.dumps(result,indent=2));p.SaveBoard(str(folder/(name+'.kicad_pcb')),b)
print('Placed',len(result),'footprints without bbox overlap')

project_path.write_text(saved_project)
