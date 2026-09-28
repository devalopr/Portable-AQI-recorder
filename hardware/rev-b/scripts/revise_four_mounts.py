"""Four M3 edge notches, centered spaced edge outputs, outward USB mouth."""
from pathlib import Path
import pcbnew as p,json,math,shutil
from kicad_common import parse,ser,children,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';bak=R/'review/before-four-mounts.kicad_pcb'
assert not bak.exists(),'Already revised';shutil.copy2(path,bak)
pro=path.with_suffix('.kicad_pro');settings=pro.read_text();raw=parse(path.read_text())
# Remove the previous four edge power branches by their saved exact geometry.
routes=json.loads((R/'review/finish-routes.json').read_text());edges=set();vias=set()
for r in routes:
 for a,z in zip(r['path'],r['path'][1:]):
  if a[2]!=z[2]:vias.add(tuple(a[:2]))
  else:edges.add((tuple(a[:2]),tuple(z[:2]),'F.Cu' if a[2]==0 else 'B.Cu'))
def discard(a):
 if not isinstance(a,list):return False
 if a[0]=='zone':return True
 if a[0].startswith('gr_') and child(a,'layer') and val(child(a,'layer')[1])=='Edge.Cuts':return True
 if a[0]=='segment':
  s=tuple(float(v) for v in child(a,'start')[1:3]);e=tuple(float(v) for v in child(a,'end')[1:3]);l=val(child(a,'layer')[1]);return (s,e,l) in edges or (e,s,l) in edges
 if a[0]=='via' and tuple(float(v) for v in child(a,'at')[1:3]) in vias:return True
 return False
raw[:]=[a for a in raw if not discard(a)];path.write_text(ser(raw));b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()};mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
# Stretch existing J7 escape ends with the footprint, preserving electrical connectivity.
f=fs['J7'];old=[(a,a.GetPosition()) for a in f.Pads()];f.SetPosition(v(13.25,4.3))
for a,pos in old:
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):continue
  if t.GetStart()==pos:t.SetStart(a.GetPosition())
  if t.GetEnd()==pos:t.SetEnd(a.GetPosition())
for m in f.Models():m.m_Offset.y=-2.03
for ref,x,y,rot in [('SW1',13.25,86.8,0),('C54',3.8,86,0),('R9',5.8,90.5,90)]+[(ref,x,y,0) for ref,x,y in [('TP9',1.2,39),('TP10',1.2,49),('TP11',1.2,59),('TP12',25.3,39),('TP13',25.3,49),('TP14',25.3,59)]]:
 f=fs[ref];f.SetPosition(v(x,y));f.SetOrientationDegrees(rot)
# Chamfered outline with left/right semicircles near each end.
def line(a,z):
 t=p.PCB_SHAPE();t.SetShape(p.SHAPE_T_SEGMENT);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetLayer(p.Edge_Cuts);t.SetWidth(mm(.05));b.Add(t)
for a,z in [((1.5,0),(25,0)),((25,0),(26.5,1.5)),((26.5,96.5),(25,98)),((25,98),(1.5,98)),((1.5,98),(0,96.5)),((0,1.5),(1.5,0))]:line(a,z)
for x in [0,26.5]:
 for lo,hi in [(1.5,3.6),(6.8,92.4),(95.6,96.5)]:line((x,lo),(x,hi))
 for y in [5.2,94]:
  arc=p.PCB_SHAPE();arc.SetShape(p.SHAPE_T_ARC);arc.SetArcGeometry(v(x,y-1.6),v(x+(1.6 if x==0 else -1.6),y),v(x,y+1.6));arc.SetLayer(p.Edge_Cuts);arc.SetWidth(mm(.05));b.Add(arc)
  for ly in [p.F_Cu,p.B_Cu]:
   z=p.ZONE(b);z.SetLayer(ly);z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(True);poly=z.Outline();poly.NewOutline()
   for i in range(33):
    a=-math.pi/2+i*math.pi/32;poly.Append(mm(x+(1 if x==0 else -1)*3.2*math.cos(a)),mm(y+3.2*math.sin(a)))
   b.Add(z)
for t in b.GetDrawings():
 if not isinstance(t,p.PCB_TEXT):continue
 text=t.GetText();x=p.ToMM(t.GetPosition().x)
 if t.GetLayer()==p.F_SilkS and round(x,1) in [1.2,25.3] and text in ['5V','GND','3V3']:t.SetPosition(v(x,{'5V':36.5,'GND':46.5,'3V3':56.5}[text]))
 if text in ['LOW','MID','HIGH']:t.SetPosition(v({'LOW':10,'MID':13,'HIGH':16.5}[text],83.2))
p.SaveBoard(str(path),b);pro.write_text(settings)
# Library model offset agrees with its mounting-tab pitch and seating plane.
fpath=R/'lib/AQI_Power.pretty/TYPE-C-SMD_TYPE-C-6P_1.kicad_mod';f=parse(fpath.read_text());child(child(child(f,'model'),'offset'),'xyz')[1:]=['0','-2.03','0'];fpath.write_text(ser(f)+'\n')
print('Mechanical revision applied')
