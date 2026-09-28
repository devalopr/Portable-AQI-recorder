"""Compact rear assembly placement; fixed mechanical interfaces, conservative courtyards."""
import pcbnew as p,json,math,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'battery';d=json.loads((r/'design.json').read_text());name=d['name'];b=p.LoadBoard(str(r/(name+'.kicad_pcb')));pro=(r/(name+'.kicad_pro')).read_text();F={f.GetReference():f for f in b.GetFootprints()};D={c['ref']:c for c in d['components']};mm=p.FromMM;W=d['width'];H=d['height'];occupied=[]
def bb(f):
 a=f.GetBoundingBox(False,False);return [p.ToMM(a.GetLeft()),p.ToMM(a.GetTop()),p.ToMM(a.GetRight()),p.ToMM(a.GetBottom())]
def overlap(a,b,g=.15):return a[0]<b[2]+g and a[2]>b[0]-g and a[1]<b[3]+g and a[3]>b[1]-g
def occupy(f):
 occupied.append((f.GetLayer(),bb(f)))
 for pad in f.Pads():
  if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]:
   a=pad.GetBoundingBox();occupied.append((None,[p.ToMM(a.GetLeft())-.15,p.ToMM(a.GetTop())-.15,p.ToMM(a.GetRight())+.15,p.ToMM(a.GetBottom())+.15]))
def valid(f):
 a=bb(f)
 return min(a[:2])>=.35 and a[2]<=W-.35 and a[3]<=H-.35 and not any((ly is None or ly==f.GetLayer()) and overlap(a,z) for ly,z in occupied)
fixed=['J2','J1','J7','J3','D1','J8','J9','TH1','SW1']
for ref in fixed:occupy(F[ref])
priority=['U1','L3','C2','C3','C4','C6','C16','C17','C1','U2','L1','C7','C8','C9','C10','U3','L2','C11','C12','C13','C14','Q2','U5','U6','U7','U8','U9','U10','U4','D2','Q3','Q4']
rest=[ref for ref in F if ref not in fixed+priority];rest.sort(key=lambda ref:-(bb(F[ref])[2]-bb(F[ref])[0])*(bb(F[ref])[3]-bb(F[ref])[1]))
choices=sorted((dx*dx+dy*dy,dx*.25,dy*.25) for dx in range(-96,97) for dy in range(-320,321))
for ref in priority+rest:
 f=F[ref];x,y=D[ref]['xy'];ok=False
 for cost,dx,dy in choices:
  f.SetPosition(p.VECTOR2I(mm(x+dx),mm(y+dy)))
  if valid(f):ok=True;break
 if not ok:raise RuntimeError('No space '+ref)
 if math.hypot(dx,dy)>5:print(ref,'shift',round(math.hypot(dx,dy),2),flush=True)
 occupy(f)
for ref,f in F.items():
 pos=f.GetPosition();D[ref]['xy']=[round(p.ToMM(pos.x),4),round(p.ToMM(pos.y),4)];D[ref]['rot']=f.GetOrientationDegrees()
 f.Reference().SetVisible(False)
 for m in f.Models():
  if ref=='J2':m.m_Filename='${KIPRJMOD}/lib/3d/Keystone_1042.step'
(r/'design.json').write_text(json.dumps(d,indent=2)+'\n');p.SaveBoard(str(r/(name+'.kicad_pcb')),b);(r/(name+'.kicad_pro')).write_text(pro)
print('Placed',len(F),'footprints')
